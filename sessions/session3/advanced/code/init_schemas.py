#!/usr/bin/env python3
"""
Initialize Session 3 Schemas and Tables
Creates all required schemas, tables, and indexes for the reliability features
This must be run before running any other session3 scripts
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "retail_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def execute_sql_file(conn, file_path, description):
    """Execute SQL file"""
    print(f"Creating {description}...")
    with open(file_path, "r") as f:
        sql_content = f.read()

    with conn.cursor() as cursor:
        cursor.execute(sql_content)
        conn.commit()
    print(f"  Created: {description}")


def create_ops_schema(conn):
    """Create ops schema"""
    print("Creating ops schema...")
    with conn.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS ops;")
        conn.commit()
    print("  Created: ops schema")


def main():
    print("=" * 60)
    print("Session 3 Schema Initialization")
    print("=" * 60)
    print()

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        print(f"Connected to database: {DB_NAME}")
        print()

        # Create ops schema
        create_ops_schema(conn)

        # Execute SQL files
        code_dir = Path(__file__).parent

        sql_files = [
            ("processed_months_schema.sql", "Processed months checkpoint table"),
            ("checkpoint_schema.sql", "Pipeline checkpoint table"),
            ("logging_schema.sql", "Structured logging table"),
        ]

        for sql_file, description in sql_files:
            file_path = code_dir / sql_file
            if file_path.exists():
                execute_sql_file(conn, file_path, description)
            else:
                print(f"  Warning: {sql_file} not found")

        print()
        print("=" * 60)
        print("Schema initialization completed successfully!")
        print("=" * 60)
        print()
        print("You can now run the session3 pipelines:")
        print("  python code/idempotent_pipeline.py")
        print("  python code/reliable_pipeline.py")

        conn.close()

    except Exception as e:
        print(f"\nError during schema initialization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
