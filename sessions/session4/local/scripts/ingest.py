#!/usr/bin/env python3
"""
Data Ingestion Script
Reads Excel file and loads to PostgreSQL bronze layer
Reuses Session 1 ingestion logic with idempotency
"""

import argparse
import sys
import logging
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ingest')


class DataIngestor:
    """Data ingestion to bronze layer (idempotent)"""

    def __init__(self, db_host, db_port, db_name, db_user, db_password):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.conn = None

    def connect(self):
        """Connect to PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=10,
            )
            logger.info(f"Connected to database: {self.db_host}:{self.db_port}/{self.db_name}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Disconnect from PostgreSQL"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def ensure_schema(self):
        """Create bronze schema and table if not exists (idempotent)"""
        cursor = self.conn.cursor()
        try:
            # Create schema
            cursor.execute("CREATE SCHEMA IF NOT EXISTS bronze;")

            # Create table (Session 1 schema)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bronze.raw_transactions (
                    id SERIAL PRIMARY KEY,
                    invoiceno VARCHAR(10) NOT NULL,
                    stockcode VARCHAR(20) NOT NULL,
                    description VARCHAR(255),
                    quantity INTEGER,
                    invoicedate TIMESTAMP NOT NULL,
                    unitprice DECIMAL(10,2),
                    customerid VARCHAR(10),
                    country VARCHAR(100),
                    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source_file VARCHAR(255)
                );
            """)

            # Create indexes (IF NOT EXISTS supported in PostgreSQL 9.5+)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_transactions_invoiceno
                ON bronze.raw_transactions(invoiceno);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_transactions_stockcode
                ON bronze.raw_transactions(stockcode);
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_raw_transactions_invoicedate
                ON bronze.raw_transactions(invoicedate);
            """)

            self.conn.commit()
            logger.info("Bronze schema verified")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating schema: {e}")
            raise
        finally:
            cursor.close()

    def read_excel(self, file_path):
        """Read Excel file"""
        logger.info(f"Reading Excel file: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        df = pd.read_excel(file_path)
        logger.info(f"Loaded {len(df)} rows from Excel")
        return df

    def clean_data(self, df):
        """Clean DataFrame (Session 1 logic)"""
        logger.info("Cleaning data...")
        original_count = len(df)

        # Column normalization
        df = df.copy()
        df.columns = [col.lower().replace(' ', '') for col in df.columns]

        # Required fields
        df = df.dropna(subset=['invoiceno', 'stockcode', 'invoicedate'])

        # Date processing
        df['invoicedate'] = pd.to_datetime(df['invoicedate'], errors='coerce')
        df = df.dropna(subset=['invoicedate'])

        # Missing values
        df['description'] = df['description'].fillna('Unknown')
        df['quantity'] = df['quantity'].fillna(0)
        df['unitprice'] = df['unitprice'].fillna(0.0)
        df['customerid'] = df['customerid'].astype(str).replace('nan', None)

        # Data quality filtering
        invalid_count = len(df[(df['unitprice'] < 0) | (df['unitprice'] > 10000)])
        if invalid_count > 0:
            logger.warning(f"Removing {invalid_count} records with invalid prices")
            df = df[(df['unitprice'] >= 0) & (df['unitprice'] <= 10000)]

        logger.info(f"Cleaned: {original_count} → {len(df)} records")
        return df

    def truncate_bronze(self):
        """Truncate bronze table for idempotent full refresh"""
        cursor = self.conn.cursor()
        try:
            cursor.execute("TRUNCATE TABLE bronze.raw_transactions CASCADE;")
            self.conn.commit()
            logger.info("Truncated bronze.raw_transactions (full refresh)")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error truncating table: {e}")
            raise
        finally:
            cursor.close()

    def insert_data(self, df, source_file):
        """Insert DataFrame to bronze.raw_transactions"""
        cursor = self.conn.cursor()
        try:
            insert_query = sql.SQL("""
                INSERT INTO bronze.raw_transactions (
                    invoiceno, stockcode, description, quantity,
                    invoicedate, unitprice, customerid, country, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """)

            records = [
                (
                    str(row['invoiceno']),
                    str(row['stockcode']),
                    str(row['description']),
                    int(row['quantity']),
                    row['invoicedate'],
                    float(row['unitprice']),
                    row['customerid'],
                    str(row['country']),
                    source_file,
                )
                for _, row in df.iterrows()
            ]

            cursor.executemany(insert_query, records)
            self.conn.commit()

            inserted_count = cursor.rowcount
            logger.info(f"Inserted {inserted_count} records to bronze layer")
            return inserted_count
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting data: {e}")
            raise
        finally:
            cursor.close()

    def ingest(self, data_file):
        """Full ingestion pipeline (idempotent)"""
        try:
            self.connect()
            self.ensure_schema()

            # Read and clean
            df_raw = self.read_excel(data_file)
            df_clean = self.clean_data(df_raw)

            # Truncate + Insert for idempotency (full refresh pattern)
            self.truncate_bronze()
            inserted_count = self.insert_data(df_clean, data_file)

            logger.info(f"✓ Ingestion completed: {inserted_count} records")
            return inserted_count

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Ingest Excel data to PostgreSQL bronze layer')
    parser.add_argument('--data-file', required=True, help='Path to Excel file')
    parser.add_argument('--db-host', required=True, help='Database host')
    parser.add_argument('--db-port', default='5432', help='Database port')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')

    args = parser.parse_args()

    try:
        ingestor = DataIngestor(
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
        )

        ingestor.ingest(args.data_file)
        sys.exit(0)

    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
