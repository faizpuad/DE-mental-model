import os
import sys
import logging
import uuid
import time
import random
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from functools import wraps

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "retail_db")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")


class CheckpointManager:
    def __init__(self, db_conn):
        self.db_conn = db_conn

    def get_processed_months(self) -> List[str]:
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT month_key FROM ops.processed_months ORDER BY month_key;")
        months = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return months

    def set_month_processed(self, year: int, month: int, status: str = "completed"):
        month_key = f"{year}-{month:02d}"
        cursor = self.db_conn.cursor()
        cursor.execute(
            """
            INSERT INTO ops.processed_months (month_key, year, month, processed_at, status)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP, %s)
            ON CONFLICT (month_key) DO UPDATE SET
                status = EXCLUDED.status,
                processed_at = CURRENT_TIMESTAMP;
        """,
            (month_key, year, month, status),
        )
        self.db_conn.commit()
        cursor.close()
        logger.info(f"Marked month {month_key} as {status}")

    def reset_processed_months(self):
        cursor = self.db_conn.cursor()
        cursor.execute("DELETE FROM ops.processed_months;")
        self.db_conn.commit()
        cursor.close()
        logger.info("Reset all processed months")


def retry_with_backoff(max_attempts: int = 3, base_delay: float = 1.0):
    def decorator(func):
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
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s: {e}"
                        )
                        time.sleep(delay)
            raise last_exception

        return wrapper

    return decorator


@retry_with_backoff(max_attempts=3, base_delay=1.0)
def process_month_gold(year: int, month: int, conn) -> dict:
    """
    Process gold layer data - recalculate monthly aggregates
    This demonstrates idempotency by using UPSERT
    """
    cursor = conn.cursor()

    try:
        # Aggregate from silver fact_sales_daily to gold fact_sales_monthly
        cursor.execute(
            """
            INSERT INTO gold.fact_sales_monthly (
                year, month,
                total_revenue, total_quantity, total_transactions,
                total_products, total_countries,
                avg_revenue_per_transaction, avg_quantity_per_transaction,
                unique_customers
            )
            SELECT
                d.year,
                d.month,
                SUM(fsd.total_revenue),
                SUM(fsd.total_quantity),
                SUM(fsd.total_transactions),
                COUNT(DISTINCT fsd.product_id),
                COUNT(DISTINCT fsd.country),
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
                COUNT(DISTINCT fsd.customer_id)
            FROM silver.fact_sales_daily fsd
            JOIN silver.dim_date d ON fsd.date_id = d.date_id
            WHERE d.year = %s AND d.month = %s
            GROUP BY d.year, d.month
            ON CONFLICT (year, month) DO UPDATE SET
                total_revenue = EXCLUDED.total_revenue,
                total_quantity = EXCLUDED.total_quantity,
                total_transactions = EXCLUDED.total_transactions,
                total_products = EXCLUDED.total_products,
                total_countries = EXCLUDED.total_countries,
                avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
                avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
                unique_customers = EXCLUDED.unique_customers,
                updated_at = CURRENT_TIMESTAMP;
        """,
            (year, month),
        )

        conn.commit()
        row_count = cursor.rowcount
        cursor.close()

        logger.info(f"Processed {year}-{month:02d}: {row_count} rows affected")

        return {"success": True, "rows": row_count}

    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing month {year}-{month:02d}: {e}")
        cursor.close()
        raise


def get_distinct_months(conn) -> List[tuple]:
    """Get all distinct year-month combinations from silver.fact_sales_daily"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT d.year, d.month
        FROM silver.fact_sales_daily fsd
        JOIN silver.dim_date d ON fsd.date_id = d.date_id
        ORDER BY d.year, d.month;
    """)
    months = cursor.fetchall()
    cursor.close()
    logger.info(f"Found {len(months)} distinct months in silver layer")
    return months


def main():
    parser = argparse.ArgumentParser(
        description="Run idempotent batch pipeline for gold layer"
    )
    parser.add_argument("--year", type=int, help="Process specific year")
    parser.add_argument("--month", type=int, help="Process specific month (1-12)")
    parser.add_argument(
        "--reset", action="store_true", help="Reset all processed months"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    args = parser.parse_args()

    run_id = str(uuid.uuid4())
    logger.info(f"Starting pipeline run {run_id}")
    logger.info(f"Event: {vars(args)}")

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        logger.info("Connected to database")

        checkpoint_mgr = CheckpointManager(conn)

        if args.reset:
            checkpoint_mgr.reset_processed_months()
            logger.info("All processed months have been reset")
            conn.close()
            return

        processed_months = checkpoint_mgr.get_processed_months()
        all_months = get_distinct_months(conn)

        # Filter based on arguments
        if args.year and args.month:
            all_months = [(args.year, args.month)]
        elif args.year:
            all_months = [(y, m) for y, m in all_months if y == args.year]

        unprocessed_months = [
            m for m in all_months if f"{m[0]}-{m[1]:02d}" not in processed_months
        ]

        if not unprocessed_months:
            logger.info("No new months to process")
            conn.close()
            return

        logger.info(f"Processing {len(unprocessed_months)} unprocessed months")

        if args.dry_run:
            print("DRY RUN - Would process the following months:")
            for year, month in unprocessed_months:
                print(f"  {year}-{month:02d}")
            conn.close()
            return

        total_processed = 0

        for year, month in unprocessed_months:
            checkpoint_mgr.set_month_processed(year, month, "in_progress")

            result = process_month_gold(year, month, conn)
            total_processed += result.get("rows", 0)

            checkpoint_mgr.set_month_processed(year, month, "completed")

        logger.info(f"Pipeline completed: {total_processed} rows processed")

        conn.close()

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
