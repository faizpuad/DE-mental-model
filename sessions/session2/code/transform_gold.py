#!/usr/bin/env python3
"""
Gold Layer Transformation Script
Transforms silver layer data into gold layer aggregated metrics
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2 import sql

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


def get_connection():
    """Establish database connection"""
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD
    )


def execute_sql_file(conn, file_path):
    """Execute SQL file"""
    with open(file_path, "r") as f:
        sql_content = f.read()

    if DRY_RUN:
        print(f"[DRY RUN] Would execute: {file_path}")
        print(f"[DRY RUN] SQL content length: {len(sql_content)} characters")
        return

    with conn.cursor() as cursor:
        cursor.execute(sql_content)
        conn.commit()
        print(f"Executed: {file_path}")


def create_schemas(conn):
    """Create gold schema if not exists"""
    sql = "CREATE SCHEMA IF NOT EXISTS gold;"
    if DRY_RUN:
        print(f"[DRY RUN] Would execute: {sql}")
        return

    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()
        print("Created gold schema")


def create_gold_tables(conn):
    """Create all gold layer tables"""
    code_dir = Path(__file__).parent

    gold_tables = [
        "fact_sales_monthly.sql",
        "fact_product_performance.sql",
        "fact_country_sales.sql",
        "fact_sales_daily_enhanced.sql",
    ]

    for table_file in gold_tables:
        table_path = code_dir / table_file
        if table_path.exists():
            execute_sql_file(conn, table_path)
        else:
            print(f"Warning: {table_file} not found")


def transform_silver_to_gold(conn):
    """Transform data from silver to gold layer"""
    transform_sql_path = Path(__file__).parent / "transform_silver_to_gold.sql"

    if not transform_sql_path.exists():
        print(f"Error: {transform_sql_path} not found")
        return

    execute_sql_file(conn, transform_sql_path)


def verify_gold_data(conn):
    """Verify gold layer data"""
    queries = {
        "fact_sales_monthly": "SELECT COUNT(*) FROM gold.fact_sales_monthly;",
        "fact_product_performance": "SELECT COUNT(*) FROM gold.fact_product_performance;",
        "fact_country_sales": "SELECT COUNT(*) FROM gold.fact_country_sales;",
        "fact_sales_daily_enhanced": "SELECT COUNT(*) FROM gold.fact_sales_daily_enhanced;",
    }

    print("\nGold Layer Data Verification:")
    print("=" * 50)

    if DRY_RUN:
        print("[DRY RUN] Would run verification queries:")
        for table, query in queries.items():
            print(f"  {table}: {query}")
        return

    with conn.cursor() as cursor:
        for table, query in queries.items():
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} rows")

    print("=" * 50)


def main():
    """Main execution function"""
    print(f"Gold Layer Transformation - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        with get_connection() as conn:
            print("Connected to database")

            # Step 1: Create gold schema
            print("\nStep 1: Creating gold schema...")
            create_schemas(conn)

            # Step 2: Create gold tables
            print("\nStep 2: Creating gold tables...")
            create_gold_tables(conn)

            # Step 3: Transform data
            print("\nStep 3: Transforming silver to gold...")
            transform_silver_to_gold(conn)

            # Step 4: Verify data
            print("\nStep 4: Verifying gold data...")
            verify_gold_data(conn)

        print("\n" + "=" * 60)
        print("Gold layer transformation completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError during transformation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
