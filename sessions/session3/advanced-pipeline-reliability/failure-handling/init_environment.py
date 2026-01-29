"""
Initialize Failure Handling Environment

This script sets up the database environment for failure scenario testing.
It ensures all required tables and data exist before running failure scripts.
"""

import os
import sys
import psycopg2
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))


def main():
    print("=" * 60)
    print("Initializing Failure Handling Environment")
    print("=" * 60)

    conn = None
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "retail_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )

        with conn.cursor() as cur:
            # Check if schemas exist
            cur.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name IN ('ops', 'silver', 'gold')
            """)
            existing_schemas = [row[0] for row in cur.fetchall()]

            print("Checking required schemas...")
            for schema in ["ops", "silver", "gold"]:
                if schema in existing_schemas:
                    print(f"   ✓ {schema} schema exists")
                else:
                    print(f"   ❌ {schema} schema missing")

            # Ensure ops schema exists
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS ops
            """)

            # Create ops.processed_months table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ops.processed_months (
                    id SERIAL PRIMARY KEY,
                    month_key VARCHAR(7) UNIQUE NOT NULL,
                    year INTEGER,
                    month INTEGER,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) DEFAULT 'in_progress',
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)

            # Create ops.pipeline_logs table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ops.pipeline_logs (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMP NOT NULL,
                    level VARCHAR(10) NOT NULL,
                    message TEXT NOT NULL,
                    logger VARCHAR(100),
                    pipeline_name VARCHAR(100),
                    run_id VARCHAR(50),
                    module VARCHAR(100),
                    function VARCHAR(100),
                    line INTEGER,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """)

            # Create ops.pipeline_checkpoint table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ops.pipeline_checkpoint (
                    id SERIAL PRIMARY KEY,
                    pipeline_name VARCHAR(100) NOT NULL,
                    run_id VARCHAR(50) NOT NULL,
                    stage VARCHAR(100) NOT NULL,
                    checkpoint_key VARCHAR(255) NOT NULL,
                    checkpoint_value VARCHAR(255),
                    status VARCHAR(20) DEFAULT 'pending',
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_ms INTEGER,
                    metadata JSONB DEFAULT '{}'::jsonb,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.commit()
            print("   ✓ ops schema and tables created")

            # Check for silver and gold tables
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('silver', 'gold')
                AND table_name IN ('fact_sales_daily', 'fact_sales_monthly')
            """)
            existing_tables = [(row[0], row[1]) for row in cur.fetchall()]

            required_tables = [
                ("silver", "fact_sales_daily"),
                ("gold", "fact_sales_monthly"),
            ]

            print("\nChecking required tables...")
            for schema, table in required_tables:
                if (schema, table) in existing_tables:
                    print(f"   ✓ {schema}.{table} exists")
                else:
                    print(f"   ⚠️  {schema}.{table} missing (will be created)")

            # Create minimal tables if they don't exist
            if ("silver", "fact_sales_daily") not in existing_tables:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS silver.fact_sales_daily (
                        date_id DATE NOT NULL,
                        product_id INTEGER NOT NULL,
                        country_id INTEGER NOT NULL,
                        total_sales DECIMAL(12,2) NOT NULL DEFAULT 0,
                        total_quantity INTEGER NOT NULL DEFAULT 0,
                        transaction_count INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (date_id, product_id, country_id)
                    )
                """)
                print("   ✓ Created silver.fact_sales_daily")

            if ("gold", "fact_sales_monthly") not in existing_tables:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS gold.fact_sales_monthly (
                        month_key VARCHAR(7) PRIMARY KEY,
                        year INTEGER NOT NULL,
                        month INTEGER NOT NULL,
                        total_sales DECIMAL(12,2) NOT NULL DEFAULT 0,
                        total_quantity INTEGER NOT NULL DEFAULT 0,
                        transaction_count INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("   ✓ Created gold.fact_sales_monthly")

            # Insert some test data if tables are empty
            cur.execute("SELECT COUNT(*) FROM silver.fact_sales_daily")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO silver.fact_sales_daily 
                    (date_id, product_id, country_id, total_sales, total_quantity, transaction_count)
                    VALUES 
                    ('2010-12-01', 1, 1, 100.00, 10, 5),
                    ('2010-12-01', 2, 1, 200.00, 20, 8),
                    ('2010-12-02', 1, 1, 150.00, 15, 7),
                    ('2011-01-01', 1, 1, 300.00, 25, 10)
                """)
                print("   ✓ Inserted test data into silver.fact_sales_daily")

            conn.commit()

            print("\n✅ Environment initialized successfully!")
            print("\nYou can now run failure scenarios:")
            print("   python fail_checkpoint_corruption.py")
            print("   python fail_idempotency_break.py")
            print("   python fail_retry_exhaustion.py")
            print("   python fail_logging_failure.py")

    except Exception as e:
        print(f"\n❌ Initialization failed: {type(e).__name__}: {e}")
        if conn:
            conn.rollback()
        return False

    finally:
        try:
            if conn:
                conn.close()
        except:
            pass

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
