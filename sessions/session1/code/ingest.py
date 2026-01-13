import os
import logging
from pathlib import Path
import pandas as pd
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataIngestor:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "retail_db")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            logger.info("Successfully connected to database")
            return self.conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def execute_sql_file(self, file_path):
        try:
            with open(file_path, "r") as f:
                sql_content = f.read()

            cursor = self.conn.cursor()
            cursor.execute(sql_content)
            self.conn.commit()
            cursor.close()
            logger.info(f"Successfully executed SQL file: {file_path}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error executing SQL file {file_path}: {e}")
            raise

    def read_excel(self, file_path):
        try:
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Loaded {len(df)} rows from Excel file")
            return df
        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise

    def clean_data(self, df):
        logger.info("Starting data cleaning")

        original_count = len(df)

        df = df.copy()

        df.columns = [col.lower().replace(" ", "") for col in df.columns]

        df = df.dropna(subset=["invoiceno", "stockcode", "invoicedate"])

        df["invoicedate"] = pd.to_datetime(df["invoicedate"], errors="coerce")
        df = df.dropna(subset=["invoicedate"])

        df["description"] = df["description"].fillna("Unknown")
        df["quantity"] = df["quantity"].fillna(0)
        df["unitprice"] = df["unitprice"].fillna(0.0)
        df["customerid"] = df["customerid"].astype(str).replace("nan", None)

        invalid_records = len(df[(df["unitprice"] < 0) | (df["unitprice"] > 10000)])
        if invalid_records > 0:
            logger.warning(f"Found {invalid_records} records with invalid unit prices")
            df = df[(df["unitprice"] >= 0) & (df["unitprice"] <= 10000)]

        logger.info(f"Cleaned data: {original_count} -> {len(df)} records")
        return df

    def insert_data(self, df, source_file):
        try:
            cursor = self.conn.cursor()

            insert_query = sql.SQL(
                """
                INSERT INTO bronze.raw_transactions (
                    invoiceno, stockcode, description, quantity, 
                    invoicedate, unitprice, customerid, country, source_file
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            )

            records = [
                (
                    str(row["invoiceno"]),
                    str(row["stockcode"]),
                    str(row["description"]),
                    int(row["quantity"]),
                    row["invoicedate"],
                    float(row["unitprice"]),
                    row["customerid"],
                    str(row["country"]),
                    source_file,
                )
                for _, row in df.iterrows()
            ]

            cursor.executemany(insert_query, records)
            self.conn.commit()
            cursor.close()

            logger.info(f"Successfully inserted {len(records)} records")
            return len(records)
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting data: {e}")
            raise

    def validate_ingestion(self, expected_rows):
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions;")
            actual_rows = cursor.fetchone()[0]
            cursor.close()

            logger.info(f"Expected rows: {expected_rows}, Actual rows: {actual_rows}")

            if actual_rows < expected_rows * 0.95:
                logger.warning(
                    f"Significant data loss: {(expected_rows - actual_rows)} rows missing"
                )
            else:
                logger.info("Data validation passed")

            return actual_rows
        except Exception as e:
            logger.error(f"Error validating ingestion: {e}")
            raise

    def get_data_summary(self):
        try:
            cursor = self.conn.cursor()

            summary_queries = [
                ("Total records", "SELECT COUNT(*) FROM bronze.raw_transactions"),
                (
                    "Total invoices",
                    "SELECT COUNT(DISTINCT invoiceno) FROM bronze.raw_transactions",
                ),
                (
                    "Total products",
                    "SELECT COUNT(DISTINCT stockcode) FROM bronze.raw_transactions",
                ),
                (
                    "Total customers",
                    "SELECT COUNT(DISTINCT customerid) FROM bronze.raw_transactions WHERE customerid IS NOT NULL",
                ),
                (
                    "Total countries",
                    "SELECT COUNT(DISTINCT country) FROM bronze.raw_transactions",
                ),
                (
                    "Date range start",
                    "SELECT MIN(invoicedate) FROM bronze.raw_transactions",
                ),
                (
                    "Date range end",
                    "SELECT MAX(invoicedate) FROM bronze.raw_transactions",
                ),
                (
                    "Total revenue",
                    "SELECT SUM(quantity * unitprice) FROM bronze.raw_transactions WHERE quantity > 0",
                ),
            ]

            logger.info("Data Summary:")
            for name, query in summary_queries:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                if name == "Total revenue":
                    logger.info(
                        f"  {name}: £{result:,.2f}" if result else f"  {name}: N/A"
                    )
                else:
                    logger.info(f"  {name}: {result:,}" if result else f"  {name}: N/A")

            cursor.close()
        except Exception as e:
            logger.error(f"Error generating data summary: {e}")


def main():
    data_dir = Path(__file__).parent.parent.parent / "session1" / "data"
    excel_file = data_dir / "online_retail.xlsx"

    if not excel_file.exists():
        logger.error(f"Data file not found: {excel_file}")
        return

    schema_file = Path(__file__).parent / "schema.sql"

    ingestor = DataIngestor()

    try:
        ingestor.connect()

        logger.info("Creating database schema")
        ingestor.execute_sql_file(schema_file)

        logger.info("Reading data from Excel file")
        df = ingestor.read_excel(excel_file)

        logger.info("Cleaning data")
        df_cleaned = ingestor.clean_data(df)

        logger.info("Inserting data into database")
        inserted_count = ingestor.insert_data(df_cleaned, str(excel_file))

        logger.info("Validating ingestion")
        ingestor.validate_ingestion(len(df_cleaned))

        logger.info("Generating data summary")
        ingestor.get_data_summary()

        logger.info("Data ingestion completed successfully")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        ingestor.disconnect()


if __name__ == "__main__":
    main()
