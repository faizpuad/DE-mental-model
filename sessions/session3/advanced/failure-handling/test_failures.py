"""
Test Failure Handling Environment

Quick test to verify all failure scenarios can run.
"""

import subprocess
import sys
from pathlib import Path


def test_failure_script(script_name):
    """Test a single failure script"""
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        return False, f"Script not found: {script_name}"

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Success"
        else:
            return False, result.stderr[:200]  # First 200 chars of error

    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def main():
    print("=" * 60)
    print("Testing Failure Handling Scripts")
    print("=" * 60)

    # Test environment initialization first
    print("\n1. Testing environment initialization...")
    success, message = test_failure_script("init_environment.py")
    if success:
        print("   ✓ Environment initialization: SUCCESS")
    else:
        print(f"   ❌ Environment initialization: {message}")
        return

    # Test all failure scripts
    failure_scripts = [
        "fail_checkpoint_corruption.py",
        "fail_idempotency_break.py",
        "fail_retry_exhaustion.py",
        "fail_logging_failure.py",
    ]

    print("\n2. Testing failure scenarios...")
    for script in failure_scripts:
        print(f"\n   Testing {script}...")
        success, message = test_failure_script(script)
        if success:
            print(f"   ✓ {script}: SUCCESS")
        else:
            print(f"   ❌ {script}: {message}")

    print("\n✅ All tests completed!")
    print("\nTo run scripts manually:")
    print("   cd sessions/session3/advanced/failure-handling")
    print("   python init_environment.py")
    print("   python fail_checkpoint_corruption.py")
    print("   # ... and so on")


if __name__ == "__main__":
    main()
