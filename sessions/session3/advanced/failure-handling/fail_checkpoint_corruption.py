"""
Failure Case: Checkpoint Corruption

This script demonstrates what happens when checkpoint data becomes corrupted.
Students learn:
- How to detect corrupted checkpoints
- Recovery strategies for broken checkpoints
- Implementing checkpoint validation
- Safe checkpoint recreation

Expected Error: Data corruption detection and recovery procedures
"""

import os
import sys
import json
import psycopg2
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from code.idempotent_pipeline import CheckpointManager


def main():
    conn = None
    print("=" * 80)
    print("FAILURE CASE: Checkpoint Corruption")
    print("=" * 80)
    print("\nThis script demonstrates checkpoint corruption and recovery.")
    print("It will intentionally corrupt checkpoint data and show recovery.\n")

    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "retail_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )

        checkpoint_manager = CheckpointManager(conn)

        print("1. Setting up clean checkpoint data...")
        checkpoint_manager.set_month_processed(2010, 12, "completed")
        checkpoint_manager.set_month_processed(2011, 1, "completed")

        print("2. Verifying clean checkpoints...")
        processed = checkpoint_manager.get_processed_months()
        print(f"   Processed months: {processed}")

        print("\n3. Simulating checkpoint corruption...")
        print("-" * 50)

        # Corrupt checkpoint data
        with conn.cursor() as cur:
            # Insert invalid JSON metadata
            cur.execute("""
                UPDATE ops.processed_months 
                SET metadata = '{"invalid": json, "corrupted": true}'
                WHERE year = 2010 AND month = 12
            """)

            # Insert invalid status
            cur.execute("""
                UPDATE ops.processed_months 
                SET status = 'invalid_status_corrupted'
                WHERE year = 2011 AND month = 1
            """)

            # Insert null in critical fields
            cur.execute("""
                INSERT INTO ops.processed_months 
                (month_key, year, month, processed_at, updated_at, status)
                VALUES ('2011-02', NULL, NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'completed')
            """)

            conn.commit()

        print("   ✓ Checkpoint data corrupted")

        print("\n4. Attempting to read corrupted checkpoints...")
        print("-" * 50)

        # Try to detect corruption
        with conn.cursor() as cur:
            # Check for invalid JSON
            cur.execute("""
                SELECT month_key, metadata 
                FROM ops.processed_months 
                WHERE metadata IS NOT NULL
            """)

            corrupted_json = []
            for row in cur.fetchall():
                try:
                    if row[1]:
                        json.loads(row[1])
                except (json.JSONDecodeError, TypeError):
                    corrupted_json.append(row[0])

            if corrupted_json:
                print(f"❌ Invalid JSON found in checkpoints: {corrupted_json}")

            # Check for invalid statuses
            cur.execute("""
                SELECT DISTINCT status, COUNT(*) 
                FROM ops.processed_months 
                GROUP BY status
            """)

            invalid_statuses = []
            for status, count in cur.fetchall():
                if status not in ["in_progress", "completed", "failed"]:
                    invalid_statuses.append((status, count))

            if invalid_statuses:
                print(f"❌ Invalid statuses found: {invalid_statuses}")

            # Check for NULL critical fields
            cur.execute("""
                SELECT month_key 
                FROM ops.processed_months 
                WHERE year IS NULL OR month IS NULL
            """)

            null_fields = [row[0] for row in cur.fetchall()]
            if null_fields:
                print(f"❌ NULL critical fields in: {null_fields}")

        if not (corrupted_json or invalid_statuses or null_fields):
            print("✓ No corruption detected")
            return

        print("\n📚 EXPLANATION:")
        print("   Checkpoint corruption can occur due to:")
        print("   - Database write failures mid-transaction")
        print("   - Concurrent modifications")
        print("   - Application bugs")
        print("   - Storage issues")

        print("\n🔧 RECOVERY PROCEDURE:")
        print("   1. Identify corrupted checkpoints")
        print("   2. Backup current checkpoint table")
        print("   3. Clean corrupted entries")
        print("   4. Rebuild from source data if needed")

        print("\n5. Executing recovery...")
        print("-" * 50)

        # Recovery procedure
        with conn.cursor() as cur:
            # Backup corrupted data
            cur.execute("""
                CREATE TABLE IF NOT EXISTS ops.processed_months_backup AS
                SELECT * FROM ops.processed_months WHERE 1=0
            """)

            cur.execute("""
                INSERT INTO ops.processed_months_backup
                SELECT * FROM ops.processed_months
            """)
            conn.commit()
            print("   ✓ Backup created: ops.processed_months_backup")

            # Clean corrupted entries
            cur.execute("""
                DELETE FROM ops.processed_months 
                WHERE metadata IS NOT NULL AND metadata::text ILIKE '%corrupted%'
            """)

            cur.execute("""
                DELETE FROM ops.processed_months 
                WHERE status NOT IN ('in_progress', 'completed', 'failed')
            """)

            cur.execute("""
                DELETE FROM ops.processed_months 
                WHERE year IS NULL OR month IS NULL
            """)

            conn.commit()
            print("   ✓ Corrupted entries removed")

            # Reinsert clean data
            cur.execute("""
                INSERT INTO ops.processed_months 
                (month_key, year, month, processed_at, updated_at, status, metadata)
                VALUES 
                ('2010-12', 2010, 12, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'completed', '{"recovered": true}'),
                ('2011-01', 2011, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'completed', '{"recovered": true}')
                ON CONFLICT (month_key) DO UPDATE SET
                    status = EXCLUDED.status,
                    metadata = EXCLUDED.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """)

            conn.commit()
            print("   ✓ Clean checkpoints restored")

        print("\n6. Verifying recovery...")
        print("-" * 50)

        processed = checkpoint_manager.get_processed_months()
        print(f"   Processed months: {processed}")

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
