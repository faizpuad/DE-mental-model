#!/usr/bin/env python3
"""
Ingest data from S3 to AWS RDS PostgreSQL
This script downloads data from S3 and loads it to RDS bronze layer
Similar to local/scripts/ingest.py but works with AWS services
"""

import os
import sys
import logging
import argparse
import tempfile
from pathlib import Path

import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ingest_s3_to_rds")


class S3ToRDSIngestion:
    """Ingest data from S3 to RDS bronze layer"""

    def __init__(
        self,
        s3_bucket,
        s3_key,
        db_host,
        db_port,
        db_name,
        db_user,
        db_password,
        aws_region,
    ):
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.aws_region = aws_region
        self.conn = None
        self.s3 = boto3.client("s3", region_name=aws_region)

    def connect_rds(self):
        """Connect to RDS PostgreSQL"""
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                connect_timeout=30,
                sslmode="require",
            )
            logger.info(
                f"Connected to RDS: {self.db_host}:{self.db_port}/{self.db_name}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to RDS: {e}")
            raise

    def disconnect_rds(self):
        """Disconnect from RDS"""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from RDS")

    def download_from_s3(self, local_path):
        """Download file from S3 to local temp directory"""
        try:
            logger.info(f"Downloading from S3: s3://{self.s3_bucket}/{self.s3_key}")
            self.s3.download_file(self.s3_bucket, self.s3_key, local_path)
            file_size = os.path.getsize(local_path)
            logger.info(f"Downloaded {file_size:,} bytes to {local_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to download from S3: {e}")
            raise

    def read_excel(self, file_path):
        """Read Excel file into pandas DataFrame"""
        try:
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path, engine="openpyxl")
            logger.info(f"Loaded {len(df):,} rows from Excel")
            return df
        except Exception as e:
            logger.error(f"Failed to read Excel: {e}")
            raise

    def clean_data(self, df):
        """Clean and normalize data"""
        logger.info("Cleaning data...")
        original_count = len(df)

        # Normalize column names
        df.columns = [col.lower().replace(" ", "") for col in df.columns]

        # Handle missing values
        df["description"] = df["description"].fillna("UNKNOWN")
        df["customerid"] = df["customerid"].fillna("")

        # Convert data types
        df["quantity"] = df["quantity"].astype(int)
        df["unitprice"] = df["unitprice"].astype(float)
        df["invoicedate"] = pd.to_datetime(df["invoicedate"])

        # Filter invalid data
        invalid_price = df["unitprice"] < 0
        if invalid_price.sum() > 0:
            logger.warning(
                f"Removing {invalid_price.sum()} records with invalid prices"
            )
            df = df[~invalid_price]

        cleaned_count = len(df)
        logger.info(f"Cleaned: {original_count:,} → {cleaned_count:,} records")

        return df

    def truncate_bronze(self):
        """Truncate bronze table for idempotent full refresh"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("TRUNCATE TABLE bronze.raw_transactions CASCADE;")
            self.conn.commit()
            cursor.close()
            logger.info("Truncated bronze.raw_transactions (full refresh)")
        except Exception as e:
            logger.error(f"Failed to truncate bronze: {e}")
            raise

    def insert_to_bronze(self, df):
        """Insert data to bronze layer using batch insert"""
        try:
            cursor = self.conn.cursor()

            # Prepare data tuples
            records = []
            for _, row in df.iterrows():
                records.append(
                    (
                        str(row["invoiceno"]),
                        str(row["stockcode"]),
                        str(row["description"]),
                        int(row["quantity"]),
                        row["invoicedate"],
                        float(row["unitprice"]),
                        str(row["customerid"]),
                        str(row["country"]),
                    )
                )

            # Batch insert
            insert_query = """
                INSERT INTO bronze.raw_transactions
                (invoiceno, stockcode, description, quantity, invoicedate,
                 unitprice, customerid, country)
                VALUES %s
            """

            execute_values(cursor, insert_query, records, page_size=5000)
            self.conn.commit()
            cursor.close()

            logger.info(f"Inserted {len(records):,} records to bronze layer")
        except Exception as e:
            logger.error(f"Failed to insert to bronze: {e}")
            self.conn.rollback()
            raise

    def run(self):
        """Execute the full ingestion pipeline"""
        try:
            # Download from S3
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            self.download_from_s3(tmp_path)

            # Read and clean data
            df = self.read_excel(tmp_path)
            df = self.clean_data(df)

            # Connect to RDS and load data
            self.connect_rds()
            self.truncate_bronze()
            self.insert_to_bronze(df)

            # Cleanup
            os.unlink(tmp_path)
            logger.info("✓ Ingestion completed successfully")

            return 0

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            return 1

        finally:
            self.disconnect_rds()


def main():
    parser = argparse.ArgumentParser(description="Ingest data from S3 to RDS")
    parser.add_argument("--s3-bucket", required=True, help="S3 bucket name")
    parser.add_argument("--s3-key", required=True, help="S3 object key")
    parser.add_argument("--db-host", required=True, help="RDS host")
    parser.add_argument("--db-port", default="5432", help="RDS port")
    parser.add_argument("--db-name", required=True, help="Database name")
    parser.add_argument("--db-user", required=True, help="Database user")
    parser.add_argument("--db-password", required=True, help="Database password")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region")

    args = parser.parse_args()

    try:
        ingestion = S3ToRDSIngestion(
            s3_bucket=args.s3_bucket,
            s3_key=args.s3_key,
            db_host=args.db_host,
            db_port=args.db_port,
            db_name=args.db_name,
            db_user=args.db_user,
            db_password=args.db_password,
            aws_region=args.aws_region,
        )

        exit_code = ingestion.run()
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
