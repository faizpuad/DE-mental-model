#!/usr/bin/env python3
"""
Initialize RDS PostgreSQL bronze schema and table.
Safe to rerun if already initialized.
Uses psycopg2-binary, no psql required.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load AWS config from previously generated env
ENV_PATH = os.path.join(os.path.dirname(__file__), "../aws_config.env")
if not os.path.exists(ENV_PATH):
    print(f"Error: {ENV_PATH} not found. Run deploy.sh first.", file=sys.stderr)
    sys.exit(1)

load_dotenv(dotenv_path=ENV_PATH)

DB_HOST = os.getenv("AWS_RDS_HOST")
DB_PORT = os.getenv("AWS_RDS_PORT", "5432")
DB_USER = os.getenv("AWS_RDS_USER", "postgres")
DB_PASSWORD = os.getenv("AWS_RDS_PASSWORD")
DB_NAME = os.getenv("AWS_RDS_DATABASE", "retail_db")

if not all([DB_HOST, DB_PASSWORD]):
    print("Error: Missing database credentials in aws_config.env", file=sys.stderr)
    sys.exit(1)

try:
    print("Connecting to RDS...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Create bronze schema
    print("Creating schema 'bronze' if not exists...")
    cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS bronze;"))

    # Create raw_transactions table
    print("Creating table 'bronze.raw_transactions' if not exists...")
    cur.execute(
        sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS bronze.raw_transactions (
                id SERIAL PRIMARY KEY,
                invoiceno VARCHAR(20),
                stockcode VARCHAR(20),
                description TEXT,
                quantity INTEGER,
                invoicedate TIMESTAMP,
                unitprice DECIMAL(10,2),
                customerid VARCHAR(20),
                country VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    )

    print("✓ Bronze schema and table initialized successfully.")

    # Optional: Check table row count
    cur.execute(sql.SQL("SELECT COUNT(*) FROM bronze.raw_transactions;"))
    count = cur.fetchone()[0]
    print(f"Current row count in bronze.raw_transactions: {count}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"Error initializing RDS: {e}", file=sys.stderr)
    sys.exit(1)
