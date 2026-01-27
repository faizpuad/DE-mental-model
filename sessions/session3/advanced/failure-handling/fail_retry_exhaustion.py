"""
Failure Case: Retry Exhaustion

This script demonstrates what happens when retry logic is exhausted.
Students learn:
- How to handle permanent failures
- Implementing circuit breakers
- Alerting on retry exhaustion
- Graceful degradation strategies

Expected Error: Retry exhaustion and permanent failure handling
"""

import os
import sys
import time
import psycopg2
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))

from code.reliable_pipeline import retry_with_backoff


def main():
    print("=" * 80)
    print("FAILURE CASE: Retry Exhaustion")
    print("=" * 80)
    print("\nThis script demonstrates retry exhaustion scenarios.")
    print("It will exhaust retry attempts and show proper handling.\n")

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

        print("1. Testing normal retry behavior...")
        print("-" * 50)

        # Test with a function that succeeds after a few retries
        attempt_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.5)
        def flaky_function_succeeds():
            nonlocal attempt_count
            attempt_count += 1
            print(f"   Attempt {attempt_count}: Processing...")

            if attempt_count < 3:
                raise psycopg2.OperationalError("Connection temporarily unavailable")

            return "Success after retries"

        try:
            result = flaky_function_succeeds()
            print(f"   ✓ {result}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")

        print("\n2. Testing retry exhaustion...")
        print("-" * 50)

        # Reset attempt counter
        attempt_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.5)
        def always_failing_function():
            nonlocal attempt_count
            attempt_count += 1
            print(f"   Attempt {attempt_count}: Trying...")

            # Simulate a permanent failure
            raise psycopg2.OperationalError("Database permanently unavailable")

        try:
            result = always_failing_function()
            print(f"   ✓ {result}")
        except Exception as e:
            print(f"   ❌ RETRY EXHAUSTED: {type(e).__name__}: {e}")
            print(f"   Total attempts made: {attempt_count}")

        print("\n3. Testing circuit breaker pattern...")
        print("-" * 50)

        class CircuitBreaker:
            def __init__(self, failure_threshold=3, timeout=60):
                self.failure_threshold = failure_threshold
                self.timeout = timeout
                self.failure_count = 0
                self.last_failure_time = None
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def call(self, func, *args, **kwargs):
                if self.state == "OPEN":
                    if time.time() - self.last_failure_time > self.timeout:
                        self.state = "HALF_OPEN"
                        print(f"   Circuit breaker transitioning to HALF_OPEN")
                    else:
                        raise Exception("Circuit breaker is OPEN - calls blocked")

                try:
                    result = func(*args, **kwargs)

                    if self.state == "HALF_OPEN":
                        self.state = "CLOSED"
                        self.failure_count = 0
                        print(f"   Circuit breaker closing - service recovered")

                    return result

                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.state = "OPEN"
                        print(
                            f"   Circuit breaker OPENING - {self.failure_count} failures detected"
                        )

                    raise e

        # Test circuit breaker
        circuit_breaker = CircuitBreaker(failure_threshold=2, timeout=5)

        def failing_service():
            raise psycopg2.OperationalError("Service unavailable")

        # Trigger failures to open circuit
        for i in range(3):
            try:
                circuit_breaker.call(failing_service)
            except Exception as e:
                print(f"   Call {i + 1}: {e}")

        print("\n4. Testing graceful degradation...")
        print("-" * 50)

        class GracefulDegradation:
            def __init__(self):
                self.primary_available = True
                self.cache_available = True

            def get_data(self, query):
                """Try primary, then cache, then default"""
                try:
                    if self.primary_available:
                        print("   Trying primary database...")
                        with conn.cursor() as cur:
                            cur.execute(query)
                            result = cur.fetchall()
                        print("   ✓ Primary database succeeded")
                        return result

                except Exception as e:
                    print(f"   ❌ Primary failed: {e}")
                    self.primary_available = False

                try:
                    if self.cache_available:
                        print("   Trying cache...")
                        # Simulate cache lookup
                        cache_result = [("2010-12-01", 100.00, 10)]
                        print("   ✓ Cache succeeded")
                        return cache_result

                except Exception as e:
                    print(f"   ❌ Cache failed: {e}")
                    self.cache_available = False

                print("   Using default/fallback data")
                return [("DEFAULT", 0.00, 0)]

        degradation = GracefulDegradation()

        # Simulate primary failure
        print("   Simulating primary database failure...")
        degradation.primary_available = False

        result = degradation.get_data(
            "SELECT date_id, total_sales, total_quantity FROM silver.fact_sales_daily LIMIT 1"
        )
        print(f"   Degraded result: {result}")

        print("\n📚 EXPLANATION:")
        print("   Retry exhaustion occurs when:")
        print("   - Permanent failures (not transient)")
        print("   - Service completely unavailable")
        print("   - Configuration issues")
        print("   - Resource exhaustion")

        print("\n🔧 HANDLING STRATEGIES:")
        print("   1. Circuit Breaker Pattern")
        print("      - Stop trying after threshold failures")
        print("      - Periodically test for recovery")
        print("   ")
        print("   2. Graceful Degradation")
        print("      - Fall back to cache or default data")
        print("      - Provide limited functionality")
        print("   ")
        print("   3. Alerting and Monitoring")
        print("      - Notify on retry exhaustion")
        print("      - Track failure patterns")
        print("   ")
        print("   4. Manual Intervention")
        print("      - Require human approval for retries")
        print("      - Document failure reasons")

        print("\n5. Implementing production-ready retry with circuit breaker...")
        print("-" * 50)

        class ProductionRetryHandler:
            def __init__(
                self, max_retries=3, backoff_base=1.0, circuit_breaker_threshold=5
            ):
                self.max_retries = max_retries
                self.backoff_base = backoff_base
                self.circuit_breaker = CircuitBreaker(
                    failure_threshold=circuit_breaker_threshold
                )
                self.alert_sent = False

            def execute_with_retry(self, operation, operation_name="unknown"):
                try:
                    return self.circuit_breaker.call(operation)

                except Exception as e:
                    if not self.alert_sent:
                        print(
                            f"   🚨 ALERT: {operation_name} - Circuit breaker OPEN or retry exhausted"
                        )
                        print(f"   📧 Alert email sent to ops team")
                        self.alert_sent = True

                    # Log for monitoring
                    print(f"   📊 METRIC: {operation_name}_failure = 1")
                    print(
                        f"   📊 METRIC: {operation_name}_circuit_state = {self.circuit_breaker.state}"
                    )

                    raise e

        # Test production handler
        prod_handler = ProductionRetryHandler(
            max_retries=2, circuit_breaker_threshold=2
        )

        def test_operation():
            raise psycopg2.OperationalError("Test failure")

        try:
            for i in range(4):
                prod_handler.execute_with_retry(test_operation, "test_operation")
        except Exception as e:
            print(f"   Final error: {e}")

        print("\n✅ RETRY EXHAUSTION HANDLING DEMONSTRATED")

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
