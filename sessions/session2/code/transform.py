import os
import logging
from pathlib import Path
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataTransformer:

    NON_CHUNKED_SQL_FILES = {"fact_sales_daily_triggers.sql"}

    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "retail_db")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        self.conn = None
        self.dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

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

            # 🔒 Non-chunked SQL (functions, triggers, DO $$)
            if file_path.name in self.NON_CHUNKED_SQL_FILES:
                logger.info(f"Executing non-chunked SQL file: {file_path.name}")
                if not self.dry_run:
                    cursor.execute(sql_content)
                    self.conn.commit()
                return

            # ✅ Chunked SQL
            raw_statements = sql_content.split(";")
            statements = []

            for stmt in raw_statements:
                cleaned = "\n".join(
                    line
                    for line in stmt.splitlines()
                    if not line.strip().startswith("--")
                ).strip()

                if cleaned:
                    statements.append(cleaned)

            for i, statement in enumerate(statements, start=1):
                logger.info(f"Executing statement {i} in {file_path.name}")

                if self.dry_run:
                    continue

                try:
                    cursor.execute(statement)
                    self.conn.commit()
                except Exception as stmt_error:
                    self.conn.rollback()
                    logger.error(
                        f"Error in {file_path.name}, statement {i}:\n{statement}\nError: {stmt_error}"
                    )
                    raise

            cursor.close()
            logger.info(f"Successfully executed SQL file: {file_path}")

        except Exception as e:
            logger.error(f"Error executing SQL file {file_path}: {e}")
            raise

    def create_silver_schema(self):
        try:
            cursor = self.conn.cursor()
            cursor.execute("CREATE SCHEMA IF NOT EXISTS silver;")
            self.conn.commit()
            cursor.close()
            logger.info("Silver schema created or already exists")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating silver schema: {e}")
            raise

    def run_transformations(self):
        sql_dir = Path(__file__).parent

        sql_files = [
            "dim_date.sql",
            "dim_product.sql",
            "fact_sales_daily.sql",
            "transform_bronze_to_silver.sql",
            "fact_sales_daily_triggers.sql",
        ]

        self.create_silver_schema()

        for sql_file in sql_files:
            file_path = sql_dir / sql_file
            if file_path.exists():
                logger.info(f"Executing: {sql_file}")
                self.execute_sql_file(file_path)
            else:
                logger.warning(f"SQL file not found: {file_path}")

    def validate_transformation(self):
        try:
            cursor = self.conn.cursor()

            validation_queries = [
                ("dim_date count", "SELECT COUNT(*) FROM silver.dim_date"),
                ("dim_product count", "SELECT COUNT(*) FROM silver.dim_product"),
                (
                    "fact_sales_daily count",
                    "SELECT COUNT(*) FROM silver.fact_sales_daily",
                ),
                (
                    "fact_sales_daily total revenue",
                    "SELECT SUM(total_revenue) FROM silver.fact_sales_daily",
                ),
            ]

            for name, query in validation_queries:
                cursor.execute(query)
                result = cursor.fetchone()
                logger.info(f"{name}: {result[0]}")

            cursor.close()
            logger.info("Transformation validation completed")
        except Exception as e:
            logger.error(f"Error validating transformation: {e}")
            raise


def main():
    transformer = DataTransformer()

    try:
        transformer.connect()
        transformer.run_transformations()
        transformer.validate_transformation()
        logger.info("Data transformation completed successfully")
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        raise
    finally:
        transformer.disconnect()


if __name__ == "__main__":
    main()
