"""
Failure Case: Idempotency Break

This script demonstrates what happens when idempotency logic fails.
Students learn:
- How idempotency can break in edge cases
- Detection of duplicate data
- Recovery from idempotency failures
- Implementing robust idempotency

Expected Error: Duplicate data and constraint violations
"""

import os
import sys
import psycopg2
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from code.idempotent_pipeline import IdempotentPipeline


def main():
    print("=" * 80)
    print("FAILURE CASE: Idempotency Break")
    print("=" * 80)
    print("\nThis script demonstrates idempotency failures and recovery.")
    print("It will break idempotency logic and show how to handle it.\n")

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

        pipeline = IdempotentPipeline(conn)

        print("1. Setting up test data...")
        print("-" * 50)

        # Create test data that will break idempotency
        with conn.cursor() as cur:
            # Insert test data into silver layer
            cur.execute("""
                INSERT INTO silver.fact_sales_daily 
                (date_id, product_id, country_id, total_sales, total_quantity, transaction_count)
                VALUES 
                ('2010-12-01', 1, 1, 100.00, 10, 5),
                ('2010-12-01', 2, 1, 200.00, 20, 8),
                ('2010-12-02', 1, 1, 150.00, 15, 7)
                ON CONFLICT (date_id, product_id, country_id) DO NOTHING
            """)

            # Insert some data into gold layer (to simulate partial processing)
            cur.execute("""
                INSERT INTO gold.fact_sales_monthly 
                (month_key, year, month, total_sales, total_quantity, transaction_count)
                VALUES ('2010-12', 2010, 12, 100.00, 10, 5)
                ON CONFLICT (month_key) DO NOTHING
            """)

            conn.commit()
            print("   ✓ Test data created")

        print("\n2. Running normal idempotent processing...")
        print("-" * 50)

        # Process month normally
        pipeline.process_month(2010, 12)

        # Check results
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count, SUM(total_sales) as sales
                FROM gold.fact_sales_monthly 
                WHERE month_key = '2010-12'
            """)
            result = cur.fetchone()
            print(f"   Gold layer: {result[0]} rows, {result[1]} total sales")

        print("\n3. Breaking idempotency logic...")
        print("-" * 50)

        # Method 1: Modify source data after processing
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE silver.fact_sales_daily 
                SET total_sales = total_sales * 2
                WHERE date_id LIKE '2010-12%'
            """)
            conn.commit()
            print("   ✓ Source data modified (breaks idempotency)")

        # Method 2: Break the ON CONFLICT logic by changing constraints
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "ALTER TABLE gold.fact_sales_monthly DROP CONSTRAINT fact_sales_monthly_pkey"
                )
                cur.execute(
                    "ALTER TABLE gold.fact_sales_monthly ADD CONSTRAINT fact_sales_monthly_pkey PRIMARY KEY (month_key, year)"
                )
                conn.commit()
                print("   ✓ Primary key constraint modified")
            except psycopg2.Error as e:
                print(f"   ⚠️  Could not modify constraint: {e}")

        print("\n4. Attempting reprocessing with broken idempotency...")
        print("-" * 50)

        try:
            # This should create duplicates or fail
            pipeline.process_month(2010, 12)

            # Check for duplicates
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT COUNT(*) as count, COUNT(DISTINCT month_key) as distinct_months
                    FROM gold.fact_sales_monthly 
                    WHERE month_key = '2010-12'
                """)
                result = cur.fetchone()

                if result[0] > result[1]:
                    print(
                        f"❌ DUPLICATES DETECTED: {result[0]} rows for {result[1]} distinct months"
                    )
                else:
                    print(f"✓ No duplicates: {result[0]} rows")

        except psycopg2.errors.UniqueViolation as e:
            print(f"❌ CONSTRAINT VIOLATION: {e}")

        print("\n📚 EXPLANATION:")
        print("   Idempotency can break due to:")
        print("   - Source data changes after initial processing")
        print("   - Modified database constraints")
        print("   - Race conditions in concurrent processing")
        print("   - Incorrect ON CONFLICT clauses")

        print("\n🔧 RECOVERY PROCEDURE:")
        print("   1. Identify duplicate or inconsistent data")
        print("   2. Determine the correct source of truth")
        print("   3. Clean up duplicates")
        print("   4. Restore proper constraints")
        print("   5. Re-process with fixed idempotency")

        print("\n5. Executing recovery...")
        print("-" * 50)

        with conn.cursor() as cur:
            # Step 1: Identify duplicates
            cur.execute("""
                SELECT month_key, COUNT(*) as duplicate_count
                FROM gold.fact_sales_monthly 
                WHERE month_key = '2010-12'
                GROUP BY month_key
                HAVING COUNT(*) > 1
            """)
            duplicates = cur.fetchall()

            if duplicates:
                print(f"   Found duplicates: {duplicates}")

                # Step 2: Keep only the most recent record
                cur.execute("""
                    DELETE FROM gold.fact_sales_monthly 
                    WHERE ctid NOT IN (
                        SELECT max(ctid) 
                        FROM gold.fact_sales_monthly 
                        WHERE month_key = '2010-12'
                        GROUP BY month_key
                    )
                """)
                conn.commit()
                print("   ✓ Duplicates removed")

            # Step 3: Restore proper primary key
            try:
                cur.execute(
                    "ALTER TABLE gold.fact_sales_monthly DROP CONSTRAINT fact_sales_monthly_pkey"
                )
                cur.execute(
                    "ALTER TABLE gold.fact_sales_monthly ADD CONSTRAINT fact_sales_monthly_pkey PRIMARY KEY (month_key)"
                )
                conn.commit()
                print("   ✓ Primary key constraint restored")
            except psycopg2.Error as e:
                print(f"   ⚠️  Could not restore constraint: {e}")

            # Step 4: Recalculate from source
            cur.execute("""
                DELETE FROM gold.fact_sales_monthly 
                WHERE month_key = '2010-12'
            """)

            cur.execute("""
                INSERT INTO gold.fact_sales_monthly 
                SELECT 
                    TO_CHAR(date_id, 'YYYY-MM') as month_key,
                    EXTRACT(YEAR FROM date_id)::INTEGER as year,
                    EXTRACT(MONTH FROM date_id)::INTEGER as month,
                    SUM(total_sales) as total_sales,
                    SUM(total_quantity) as total_quantity,
                    SUM(transaction_count) as transaction_count
                FROM silver.fact_sales_daily
                WHERE TO_CHAR(date_id, 'YYYY-MM') = '2010-12'
                GROUP BY TO_CHAR(date_id, 'YYYY-MM'), EXTRACT(YEAR FROM date_id), EXTRACT(MONTH FROM date_id)
            """)

            conn.commit()
            print("   ✓ Data recalculated from source")

        print("\n6. Verifying recovery...")
        print("-" * 50)

        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as count, SUM(total_sales) as sales
                FROM gold.fact_sales_monthly 
                WHERE month_key = '2010-12'
            """)
            result = cur.fetchone()
            print(f"   Final state: {result[0]} rows, {result[1]} total sales")

        print("\n✅ RECOVERY COMPLETE")

    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        if conn:
            conn.rollback()

    finally:
        try:
            if conn:
                conn.close()
        except:
            pass


if __name__ == "__main__":
    main()
