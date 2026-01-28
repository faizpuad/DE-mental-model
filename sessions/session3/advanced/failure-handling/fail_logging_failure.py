"""
Failure Case: Logging System Failures

This script demonstrates what happens when logging systems fail.
Students learn:
- How to handle logging system failures
- Implementing fallback logging
- Preserving critical error information
- Log correlation and recovery

Expected Error: Logging failures and fallback mechanisms
"""

import os
import sys
import json
import logging
import psycopg2
from pathlib import Path
from datetime import datetime

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))


def main():
    print("=" * 80)
    print("FAILURE CASE: Logging System Failures")
    print("=" * 80)
    print("\nThis script demonstrates logging system failures and fallback strategies.")
    print("It will break logging systems and show recovery mechanisms.\n")

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

        print("1. Testing normal structured logging...")
        print("-" * 50)

        # Create a logger that writes to database
        class DatabaseLogger:
            def __init__(self, conn):
                self.conn = conn
                self.run_id = "test-run-123"
                self.pipeline_name = "failure-test-pipeline"

            def log(self, level, message, **metadata):
                try:
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "level": level,
                        "message": message,
                        "pipeline_name": self.pipeline_name,
                        "run_id": self.run_id,
                        "metadata": metadata,
                    }

                    with self.conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO ops.pipeline_logs 
                            (timestamp, level, message, pipeline_name, run_id, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                            (
                                log_entry["timestamp"],
                                log_entry["level"],
                                log_entry["message"],
                                log_entry["pipeline_name"],
                                log_entry["run_id"],
                                json.dumps(log_entry["metadata"]),
                            ),
                        )
                    self.conn.commit()
                    print(f"   ✓ Logged to database: {message}")

                except Exception as e:
                    print(f"   ❌ Database logging failed: {e}")
                    raise

        db_logger = DatabaseLogger(conn)

        # Test normal logging
        db_logger.log("INFO", "Pipeline started", {"step": "initialization"})
        db_logger.log("INFO", "Processing data", {"records_processed": 100})
        db_logger.log("WARNING", "Slow query detected", {"duration_ms": 5000})

        print("\n2. Simulating logging system failures...")
        print("-" * 50)

        class FailingLogger:
            def __init__(self):
                self.failure_modes = []

            def add_failure_mode(self, mode):
                """Add a failure mode for testing"""
                self.failure_modes.append(mode)

            def log(self, level, message, **metadata):
                # Simulate different logging failures
                if "database_down" in self.failure_modes:
                    raise psycopg2.OperationalError("Connection to database lost")

                if "invalid_json" in self.failure_modes:
                    # This would cause JSON serialization error
                    bad_metadata = {"invalid": object()}  # Non-serializable object
                    return self._log_to_db(level, message, bad_metadata)

                if "disk_full" in self.failure_modes:
                    raise OSError("No space left on device")

                if "corrupted_schema" in self.failure_modes:
                    # Try to log to non-existent table
                    raise psycopg2.errors.UndefinedTable(
                        "Table 'ops.pipeline_logs' does not exist"
                    )

                # Normal case
                return self._log_to_db(level, message, metadata)

            def _log_to_db(self, level, message, metadata):
                """Original database logging method"""
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO ops.pipeline_logs 
                            (timestamp, level, message, pipeline_name, run_id, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                            (
                                datetime.utcnow().isoformat() + "Z",
                                level,
                                message,
                                "test-pipeline",
                                "test-run",
                                json.dumps(metadata, default=str),
                            ),
                        )
                    conn.commit()
                    print(f"   ✓ Logged: {message}")

                except Exception as e:
                    print(f"   ❌ Logging failed: {e}")
                    raise

        failing_logger = FailingLogger()

        # Test different failure modes
        failure_scenarios = [
            ("Database Connection Lost", ["database_down"]),
            ("Invalid JSON Metadata", ["invalid_json"]),
            ("Disk Full", ["disk_full"]),
            ("Corrupted Schema", ["corrupted_schema"]),
        ]

        for scenario_name, failure_modes in failure_scenarios:
            print(f"\n   Testing: {scenario_name}")
            failing_logger.failure_modes = failure_modes

            try:
                failing_logger.log(
                    "ERROR", f"Testing {scenario_name.lower()}", {"test": True}
                )
                print(f"   ⚠️  Unexpected success")
            except Exception as e:
                print(f"   ❌ Expected failure: {type(e).__name__}: {e}")

        print("\n3. Implementing fallback logging strategies...")
        print("-" * 50)

        class RobustLogger:
            def __init__(self, conn):
                self.conn = conn
                self.run_id = "robust-run-456"
                self.pipeline_name = "robust-pipeline"
                self.file_log_path = Path(__file__).parent / "fallback.log"
                self.critical_log_path = Path(__file__).parent / "critical.log"

                # Ensure log files exist
                self.file_log_path.touch()
                self.critical_log_path.touch()

            def log(self, level, message, **metadata):
                """Robust logging with multiple fallbacks"""
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "level": level,
                    "message": message,
                    "pipeline_name": self.pipeline_name,
                    "run_id": self.run_id,
                    "metadata": metadata,
                }

                # Strategy 1: Try database logging first
                if self._log_to_database(log_entry):
                    return

                # Strategy 2: Fallback to file logging
                if self._log_to_file(log_entry):
                    return

                # Strategy 3: Critical fallback for emergencies
                self._log_to_critical_file(log_entry, message)

            def _log_to_database(self, log_entry):
                """Try to log to database"""
                try:
                    with self.conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO ops.pipeline_logs 
                            (timestamp, level, message, pipeline_name, run_id, metadata)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                            (
                                log_entry["timestamp"],
                                log_entry["level"],
                                log_entry["message"],
                                log_entry["pipeline_name"],
                                log_entry["run_id"],
                                json.dumps(log_entry["metadata"], default=str),
                            ),
                        )
                    self.conn.commit()
                    print(f"   ✓ Database log: {log_entry['message']}")
                    return True

                except Exception as e:
                    print(f"   ⚠️  Database logging failed: {e}")
                    return False

            def _log_to_file(self, log_entry):
                """Fallback to file logging"""
                try:
                    log_line = json.dumps(log_entry) + "\n"
                    with open(self.file_log_path, "a") as f:
                        f.write(log_line)
                    print(f"   ✓ File log fallback: {log_entry['message']}")
                    return True

                except Exception as e:
                    print(f"   ⚠️  File logging failed: {e}")
                    return False

            def _log_to_critical_file(self, log_entry, simple_message):
                """Last resort critical logging"""
                try:
                    critical_line = f"{log_entry['timestamp']} - {log_entry['level']} - {simple_message}\n"
                    with open(self.critical_log_path, "a") as f:
                        f.write(critical_line)
                    print(f"   🚨 Critical log fallback: {simple_message}")

                except Exception as e:
                    print(f"   💀 All logging failed: {e}")
                    # Last resort - print to stderr
                    import sys

                    print(f"CRITICAL: {simple_message}", file=sys.stderr)

            def cleanup_logs(self):
                """Clean up test log files"""
                for log_path in [self.file_log_path, self.critical_log_path]:
                    if log_path.exists():
                        log_path.unlink()
                        print(f"   🧹 Cleaned up {log_path.name}")

        robust_logger = RobustLogger(conn)

        # Test robust logging with simulated failures
        print("\n   Testing robust logging with database failure...")
        robust_logger.log("INFO", "Testing robust logger", {"fallback_test": True})

        # Simulate database connection failure
        conn.close()

        print("\n   Testing fallback to file logging...")
        robust_logger.log(
            "WARNING", "Database down, using file fallback", {"fallback": "file"}
        )

        print("\n   Testing critical fallback...")
        robust_logger.log("ERROR", "All systems failing", {"critical": True})

        # Reconnect for cleanup
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "retail_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
        )
        robust_logger.conn = conn

        print("\n4. Implementing log correlation and recovery...")
        print("-" * 50)

        class LogRecovery:
            def __init__(self, conn):
                self.conn = conn

            def recover_file_logs(self, file_path):
                """Recover logs from fallback file to database"""
                if not file_path.exists():
                    print(f"   No fallback log file found: {file_path}")
                    return

                try:
                    recovered_count = 0
                    with open(file_path, "r") as f:
                        for line in f:
                            if line.strip():
                                log_entry = json.loads(line)

                                with self.conn.cursor() as cur:
                                    cur.execute(
                                        """
                                        INSERT INTO ops.pipeline_logs 
                                        (timestamp, level, message, pipeline_name, run_id, metadata)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """,
                                        (
                                            log_entry["timestamp"],
                                            log_entry["level"],
                                            log_entry["message"],
                                            log_entry["pipeline_name"],
                                            log_entry["run_id"],
                                            json.dumps(
                                                log_entry["metadata"], default=str
                                            ),
                                        ),
                                    )
                                recovered_count += 1

                    self.conn.commit()
                    print(f"   ✓ Recovered {recovered_count} log entries to database")

                except Exception as e:
                    print(f"   ❌ Log recovery failed: {e}")

            def check_log_gaps(self, run_id):
                """Check for gaps in logging for a specific run"""
                with self.conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) as log_count,
                               MIN(timestamp) as first_log,
                               MAX(timestamp) as last_log
                        FROM ops.pipeline_logs
                        WHERE run_id = %s
                    """,
                        (run_id,),
                    )

                    result = cur.fetchone()
                    print(
                        f"   Run {run_id}: {result[0]} logs from {result[1]} to {result[2]}"
                    )

        log_recovery = LogRecovery(conn)

        # Recover fallback logs
        log_recovery.recover_file_logs(robust_logger.file_log_path)

        # Check for log gaps
        log_recovery.check_log_gaps("robust-run-456")

        print("\n📚 EXPLANATION:")
        print("   Logging system failures can occur due to:")
        print("   - Database connectivity issues")
        print("   - Storage failures (disk full)")
        print("   - Network problems")
        print("   - Schema corruption")
        print("   - Serialization errors")

        print("\n🔧 LOGGING STRATEGIES:")
        print("   1. Multi-tier Fallback")
        print("      - Primary: Database logging")
        print("      - Secondary: File logging")
        print("      - Tertiary: Critical file logging")
        print("      - Last resort: stderr")
        print("   ")
        print("   2. Log Recovery")
        print("      - Batch recovery from fallback files")
        print("      - Log gap detection")
        print("      - Correlation ID preservation")
        print("   ")
        print("   3. Monitoring and Alerting")
        print("      - Monitor logging system health")
        print("      - Alert on fallback usage")
        print("      - Track log volumes")

        # Cleanup
        robust_logger.cleanup_logs()

        print("\n✅ LOGGING FAILURE HANDLING DEMONSTRATED")

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
