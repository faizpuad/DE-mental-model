import os
import json
import logging
import uuid
import time
import random
import argparse
from pathlib import Path
from datetime import datetime
from functools import wraps
from typing import Callable, Optional

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if hasattr(record, "pipeline_name"):
            log_obj["pipeline_name"] = record.pipeline_name
        if hasattr(record, "run_id"):
            log_obj["run_id"] = record.run_id
        if hasattr(record, "metadata"):
            log_obj["metadata"] = record.metadata
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


class PipelineLogger:
    def __init__(self, pipeline_name: str, run_id: str, db_conn=None):
        self.pipeline_name = pipeline_name
        self.run_id = run_id
        self.db_conn = db_conn
        self.logger = logging.getLogger(pipeline_name)

        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _log_to_db(self, level: str, message: str, **kwargs):
        if not self.db_conn:
            return

        try:
            metadata = kwargs.get("metadata", {})
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                    INSERT INTO ops.pipeline_logs
                    (timestamp, level, message, logger, pipeline_name, run_id,
                     module, function, line, metadata)
                    VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    level,
                    message,
                    self.logger.name,
                    self.pipeline_name,
                    self.run_id,
                    kwargs.get("module"),
                    kwargs.get("function"),
                    kwargs.get("line"),
                    json.dumps(metadata) if metadata else None,
                ),
            )
            self.db_conn.commit()
            cursor.close()
        except Exception as e:
            self.logger.warning(f"Failed to log to database: {e}")

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)
        self._log_to_db("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)
        self._log_to_db("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)
        self._log_to_db("WARNING", message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)
        self._log_to_db("DEBUG", message, **kwargs)


class CheckpointManager:
    def __init__(self, pipeline_name: str, run_id: str, db_conn):
        self.pipeline_name = pipeline_name
        self.run_id = run_id
        self.db_conn = db_conn

    def get_checkpoint(self, stage: str, checkpoint_key: str) -> Optional[str]:
        if not self.db_conn:
            return None

        cursor = self.db_conn.cursor()
        cursor.execute(
            """
                SELECT checkpoint_value
                FROM ops.pipeline_checkpoint
                WHERE pipeline_name = %s AND run_id = %s AND stage = %s AND checkpoint_key = %s
            """,
            (self.pipeline_name, self.run_id, stage, checkpoint_key),
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def set_checkpoint(
        self,
        stage: str,
        checkpoint_key: str,
        checkpoint_value: str,
        status: str = "completed",
        metadata: dict = None,
    ):
        if not self.db_conn:
            return

        cursor = self.db_conn.cursor()

        metadata_json = json.dumps(metadata) if metadata else None
        current_time = datetime.utcnow()

        cursor.execute(
            """
                INSERT INTO ops.pipeline_checkpoint
                (pipeline_name, run_id, stage, checkpoint_key, checkpoint_value,
                 status, start_time, end_time, duration_ms, metadata, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (pipeline_name, run_id, stage, checkpoint_key)
                DO UPDATE SET
                    checkpoint_value = EXCLUDED.checkpoint_value,
                    status = EXCLUDED.status,
                    end_time = EXCLUDED.end_time,
                    duration_ms = EXCLUDED.duration_ms,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at
            """,
            (
                self.pipeline_name,
                self.run_id,
                stage,
                checkpoint_key,
                checkpoint_value,
                status,
                current_time,
                current_time,
                metadata.get("duration_ms", 0) if metadata else 0,
                metadata_json,
                current_time,
            ),
        )

        self.db_conn.commit()
        cursor.close()

    def start_stage(self, stage: str, checkpoint_key: str) -> None:
        if not self.db_conn:
            return

        cursor = self.db_conn.cursor()
        current_time = datetime.utcnow()

        cursor.execute(
            """
                INSERT INTO ops.pipeline_checkpoint
                (pipeline_name, run_id, stage, checkpoint_key, status, start_time)
                VALUES (%s, %s, %s, %s, 'in_progress', %s)
                ON CONFLICT (pipeline_name, run_id, stage, checkpoint_key) DO NOTHING
            """,
            (self.pipeline_name, self.run_id, stage, checkpoint_key, current_time),
        )

        self.db_conn.commit()
        cursor.close()


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2**attempt) + random.random()
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


class ReliablePipeline:
    def __init__(self):
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("DB_NAME", "retail_db")
        self.db_user = os.getenv("DB_USER", "postgres")
        self.db_password = os.getenv("DB_PASSWORD", "postgres")
        self.conn = None
        self.pipeline_name = "reliable_gold_pipeline"
        self.run_id = str(uuid.uuid4())
        self.logger = None
        self.checkpoint = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
            )
            self.logger = PipelineLogger(self.pipeline_name, self.run_id, self.conn)
            self.checkpoint = CheckpointManager(
                self.pipeline_name, self.run_id, self.conn
            )
            self.logger.info(
                "Database connection established",
                metadata={"db_host": self.db_host, "db_port": self.db_port},
            )
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        if self.conn:
            self.conn.close()

    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def update_product_performance(self):
        """Update product performance metrics with retry logic"""
        self.checkpoint.start_stage("product_performance", "start")

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO gold.fact_product_performance (
                    product_id, stock_code, description, category,
                    total_revenue, total_quantity, total_transactions,
                    total_days_sold, total_countries,
                    avg_revenue_per_day, avg_quantity_per_day,
                    avg_revenue_per_transaction, avg_quantity_per_transaction,
                    first_sale_date, last_sale_date
                )
                SELECT
                    dp.product_id,
                    dp.stock_code,
                    dp.description,
                    dp.category,
                    SUM(fsd.total_revenue),
                    SUM(fsd.total_quantity),
                    SUM(fsd.total_transactions),
                    COUNT(DISTINCT fsd.date_id),
                    COUNT(DISTINCT fsd.country),
                    CASE
                        WHEN COUNT(DISTINCT fsd.date_id) > 0
                        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / COUNT(DISTINCT fsd.date_id), 2)
                        ELSE 0
                    END,
                    CASE
                        WHEN COUNT(DISTINCT fsd.date_id) > 0
                        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / COUNT(DISTINCT fsd.date_id), 2)
                        ELSE 0
                    END,
                    CASE
                        WHEN SUM(fsd.total_transactions) > 0
                        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
                        ELSE 0
                    END,
                    CASE
                        WHEN SUM(fsd.total_transactions) > 0
                        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
                        ELSE 0
                    END,
                    MIN(d.date),
                    MAX(d.date)
                FROM silver.fact_sales_daily fsd
                JOIN silver.dim_product dp ON fsd.product_id = dp.product_id
                JOIN silver.dim_date d ON fsd.date_id = d.date_id
                GROUP BY dp.product_id, dp.stock_code, dp.description, dp.category
                ON CONFLICT (product_id) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_quantity = EXCLUDED.total_quantity,
                    total_transactions = EXCLUDED.total_transactions,
                    total_days_sold = EXCLUDED.total_days_sold,
                    total_countries = EXCLUDED.total_countries,
                    avg_revenue_per_day = EXCLUDED.avg_revenue_per_day,
                    avg_quantity_per_day = EXCLUDED.avg_quantity_per_day,
                    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
                    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
                    first_sale_date = EXCLUDED.first_sale_date,
                    last_sale_date = EXCLUDED.last_sale_date,
                    updated_at = CURRENT_TIMESTAMP;
            """)

            self.conn.commit()
            row_count = cursor.rowcount
            cursor.close()

            self.checkpoint.set_checkpoint(
                "product_performance",
                "end",
                "completed",
                metadata={"rows_updated": row_count},
            )
            self.logger.info(f"Updated {row_count} products in performance table")

            return row_count

        except Exception as e:
            self.conn.rollback()
            self.checkpoint.set_checkpoint("product_performance", "end", "failed")
            self.logger.error(f"Failed to update product performance: {e}")
            raise

    @retry_with_backoff(max_attempts=3, base_delay=1.0)
    def update_country_sales(self):
        """Update country sales metrics with retry logic"""
        self.checkpoint.start_stage("country_sales", "start")

        cursor = self.conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO gold.fact_country_sales (
                    country, total_revenue, total_quantity, total_transactions,
                    total_products, total_days_active, unique_customers,
                    avg_revenue_per_transaction, avg_quantity_per_transaction,
                    top_product_id, top_product_revenue,
                    first_transaction_date, last_transaction_date
                )
                SELECT
                    fsd.country,
                    SUM(fsd.total_revenue),
                    SUM(fsd.total_quantity),
                    SUM(fsd.total_transactions),
                    COUNT(DISTINCT fsd.product_id),
                    COUNT(DISTINCT fsd.date_id),
                    COUNT(DISTINCT fsd.customer_id),
                    CASE
                        WHEN SUM(fsd.total_transactions) > 0
                        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
                        ELSE 0
                    END,
                    CASE
                        WHEN SUM(fsd.total_transactions) > 0
                        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
                        ELSE 0
                    END,
                    (
                        SELECT fsd2.product_id
                        FROM silver.fact_sales_daily fsd2
                        WHERE fsd2.country = fsd.country
                        GROUP BY fsd2.product_id
                        ORDER BY SUM(fsd2.total_revenue) DESC
                        LIMIT 1
                    ),
                    (
                        SELECT SUM(fsd3.total_revenue)
                        FROM silver.fact_sales_daily fsd3
                        WHERE fsd3.country = fsd.country AND fsd3.product_id = (
                            SELECT fsd2.product_id
                            FROM silver.fact_sales_daily fsd2
                            WHERE fsd2.country = fsd.country
                            GROUP BY fsd2.product_id
                            ORDER BY SUM(fsd2.total_revenue) DESC
                            LIMIT 1
                        )
                    ),
                    MIN(d.date),
                    MAX(d.date)
                FROM silver.fact_sales_daily fsd
                JOIN silver.dim_date d ON fsd.date_id = d.date_id
                GROUP BY fsd.country
                ON CONFLICT (country) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_quantity = EXCLUDED.total_quantity,
                    total_transactions = EXCLUDED.total_transactions,
                    total_products = EXCLUDED.total_products,
                    total_days_active = EXCLUDED.total_days_active,
                    unique_customers = EXCLUDED.unique_customers,
                    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
                    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
                    top_product_id = EXCLUDED.top_product_id,
                    top_product_revenue = EXCLUDED.top_product_revenue,
                    first_transaction_date = EXCLUDED.first_transaction_date,
                    last_transaction_date = EXCLUDED.last_transaction_date,
                    updated_at = CURRENT_TIMESTAMP;
            """)

            self.conn.commit()
            row_count = cursor.rowcount
            cursor.close()

            self.checkpoint.set_checkpoint(
                "country_sales",
                "end",
                "completed",
                metadata={"rows_updated": row_count},
            )
            self.logger.info(f"Updated {row_count} countries in sales table")

            return row_count

        except Exception as e:
            self.conn.rollback()
            self.checkpoint.set_checkpoint("country_sales", "end", "failed")
            self.logger.error(f"Failed to update country sales: {e}")
            raise

    def run_pipeline(self):
        start_time = time.time()

        try:
            self.connect()
            self.logger.info(
                "Pipeline started",
                metadata={"run_id": self.run_id, "pipeline_name": self.pipeline_name},
            )

            product_rows = self.update_product_performance()
            country_rows = self.update_country_sales()

            duration = (time.time() - start_time) * 1000
            self.logger.info(
                "Pipeline completed successfully",
                metadata={
                    "duration_ms": duration,
                    "products_updated": product_rows,
                    "countries_updated": country_rows,
                },
            )

        except Exception as e:
            self.logger.error(
                f"Pipeline failed: {e}",
                metadata={"duration_ms": (time.time() - start_time) * 1000},
            )
            raise
        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Run reliable gold layer pipeline")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    pipeline = ReliablePipeline()
    pipeline.run_pipeline()


if __name__ == "__main__":
    main()
