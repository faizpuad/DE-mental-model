# Failure Cases & Learning Materials Implementation Plan

## Overview

Add comprehensive failure case scenarios and educational materials to Sessions 1, 2, and 3. Each session will include separate failure scripts demonstrating what happens when things go wrong, integrated documentation in README.md and Notes.md files, and learning materials including expected outputs, troubleshooting guides, and comparisons of wrong vs right approaches.

## Current State Analysis

**What Exists:**
- Session 1: Basic data ingestion with `ingest.py`, minimal error handling
- Session 2: Data transformation with `transform.py`, statement-level rollback
- Session 3: Reliability features with `idempotent_pipeline.py`, retry logic and checkpointing
- Each session has README.md and Notes.md with theoretical concepts
- Each session has basic test coverage

**What's Missing:**
- Dedicated failure scenario scripts demonstrating common failure modes
- Educational materials showing expected error outputs
- Comprehensive troubleshooting guides in documentation
- Comparison examples of incorrect vs correct error handling
- Integration of failure cases into existing README and Notes files

**Key Constraints:**
- Must be educational - students should learn from failures
- Must cover all 4 categories: infrastructure, data quality, configuration, business logic
- Must provide expected outputs so students know what to look for
- Must integrate seamlessly with existing session structure
- Scripts must be runnable independently

## Desired End State

**Functional Verification:**
- Each session has `code/failures/` directory with 6-10 failure scripts
- Each failure script can be run independently: `python code/failures/fail_missing_file.py`
- README.md in each session includes "Failure Cases & Learning" section
- Notes.md in each session includes "Error Handling Theory" section
- Each failure script produces expected error output with clear messages

**Technical Verification:**
```bash
# Session 1 - Run failure case
cd sessions/session1
python code/failures/fail_missing_file.py
# Expected: Clear error message showing FileNotFoundError with explanation

# Session 2 - Run failure case
cd sessions/session2
python code/failures/fail_missing_bronze_table.py
# Expected: Clear error message showing missing dependency

# Session 3 - Run failure case
cd sessions/session3
python code/failures/fail_checkpoint_corruption.py
# Expected: Clear error message showing checkpoint recovery attempt

# Verify documentation updates
grep -r "Failure Cases" sessions/session*/README.md
# Expected: All three READMEs contain failure case section
```

## What We're NOT Doing

- ❌ Not creating a failure injection framework (too complex for learning)
- ❌ Not modifying existing working scripts (keep original code intact)
- ❌ Not adding chaos engineering or production-level fault injection
- ❌ Not creating automated failure recovery (that's the learning exercise)
- ❌ Not adding failure cases to Session 4 or 5 (out of scope)
- ❌ Not creating video tutorials or interactive exercises

## Implementation Approach

**Strategy:**
Build failure cases incrementally session-by-session, starting with Session 1. For each session, create failure scripts first, then update documentation. This allows testing each failure scenario before documenting it.

**Rationale:**
- Session 1 establishes the pattern for failure case structure
- Session 2 builds on Session 1 patterns with transformation-specific failures
- Session 3 demonstrates advanced reliability failure scenarios
- Documentation integration ensures discoverability

**Educational Framework:**
Each failure script will follow this pattern:
1. Clear description of what's being tested
2. Intentional failure trigger
3. Expected error output
4. Explanation of why it failed
5. How to fix it

---

## Phase 1: Session 1 Failure Cases - Infrastructure & Scripts

### Overview
Create `code/failures/` directory in Session 1 and implement 10 failure scenario scripts covering all 4 failure categories. Each script demonstrates a specific failure mode students will encounter in real-world data engineering.

### Changes Required:

#### 1. Directory Structure
**Location:** `sessions/session1/code/failures/`

```bash
mkdir -p sessions/session1/code/failures
```

**Structure:**
```
sessions/session1/code/failures/
├── __init__.py
├── README.md                           # Quick reference for all failure scripts
├── fail_missing_file.py                # Infrastructure: File not found
├── fail_database_down.py               # Infrastructure: DB connection failure
├── fail_network_timeout.py             # Infrastructure: Network timeout
├── fail_corrupt_excel.py               # Data Quality: Corrupted file
├── fail_invalid_schema.py              # Data Quality: Schema mismatch
├── fail_missing_columns.py             # Data Quality: Missing required columns
├── fail_missing_env_vars.py            # Configuration: Missing .env variables
├── fail_wrong_credentials.py           # Configuration: Invalid DB credentials
├── fail_duplicate_primary_key.py       # Business Logic: Constraint violation
└── fail_negative_prices.py             # Business Logic: Business rule violation
```

#### 2. Infrastructure Failure Scripts

**File:** `sessions/session1/code/failures/fail_missing_file.py`

```python
"""
Failure Case: Missing Data File

This script demonstrates what happens when the input data file doesn't exist.
Students learn:
- How file path errors manifest
- Importance of input validation
- Proper error messaging

Expected Error: FileNotFoundError
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Missing Data File")
    print("=" * 70)
    print("\nThis script attempts to ingest a non-existent file.")
    print("Watch for the error and how it's handled.\n")

    ingestor = DataIngestor()

    # Intentionally use non-existent file
    fake_file = "../../data/this_file_does_not_exist.xlsx"

    print(f"Attempting to read: {fake_file}")
    print("-" * 70)

    try:
        df = ingestor.read_excel(fake_file)
        print("✓ File read successfully (this shouldn't happen!)")
    except FileNotFoundError as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   The file path doesn't exist. This commonly happens when:")
        print("   - File path is incorrect")
        print("   - File hasn't been downloaded/generated yet")
        print("   - Working directory is different than expected")
        print("\n🔧 HOW TO FIX:")
        print("   1. Verify the file exists: ls -la ../../data/")
        print("   2. Check your current working directory: pwd")
        print("   3. Use absolute paths or Path(__file__).parent for relative paths")
        print("   4. Add input validation before processing")
        print("\n✅ CORRECT APPROACH:")
        print("   from pathlib import Path")
        print("   file_path = Path('../../data/online_retail.xlsx')")
        print("   if not file_path.exists():")
        print("       raise FileNotFoundError(f'Data file not found: {file_path}')")
    except Exception as e:
        print(f"\n⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_database_down.py`

```python
"""
Failure Case: Database Connection Failure

This script demonstrates what happens when PostgreSQL is not running.
Students learn:
- Database connection error handling
- Importance of infrastructure checks
- Retry strategies

Expected Error: psycopg2.OperationalError
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Database Connection Failure")
    print("=" * 70)
    print("\nThis script attempts to connect to a non-existent database.")
    print("Ensure PostgreSQL is NOT running for this demo.\n")

    # Override with invalid port to simulate DB down
    os.environ["DB_PORT"] = "9999"

    ingestor = DataIngestor()

    print("Attempting to connect to database on port 9999...")
    print("-" * 70)

    try:
        conn = ingestor.connect()
        print("✓ Connected successfully (this shouldn't happen!)")
    except Exception as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Cannot connect to PostgreSQL. Common causes:")
        print("   - PostgreSQL service is not running")
        print("   - Wrong host/port configuration")
        print("   - Network connectivity issues")
        print("   - Firewall blocking connection")
        print("\n🔧 HOW TO FIX:")
        print("   1. Check if PostgreSQL is running:")
        print("      docker-compose ps")
        print("      ps aux | grep postgres")
        print("   2. Verify connection settings in .env file")
        print("   3. Test connection manually:")
        print("      psql -h localhost -U postgres -d retail_db")
        print("   4. Check Docker logs:")
        print("      docker-compose logs postgres")
        print("\n✅ CORRECT APPROACH:")
        print("   - Implement retry logic with exponential backoff")
        print("   - Add connection health checks before processing")
        print("   - Use connection pooling for production systems")
        print("   - Set appropriate timeouts")

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_network_timeout.py`

```python
"""
Failure Case: Network Timeout

This script demonstrates what happens when database operations timeout.
Students learn:
- Timeout configuration
- Long-running query handling
- Connection timeout vs query timeout

Expected Error: psycopg2.errors.QueryCanceled or timeout
"""

import os
import sys
from pathlib import Path
import psycopg2

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Network/Query Timeout")
    print("=" * 70)
    print("\nThis script simulates a long-running query that times out.\n")

    ingestor = DataIngestor()

    try:
        # Connect with very short timeout
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "retail_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            connect_timeout=1,
            options='-c statement_timeout=1000'  # 1 second timeout
        )

        print("Executing long-running query with 1-second timeout...")
        print("-" * 70)

        cursor = conn.cursor()
        # This query will sleep for 10 seconds
        cursor.execute("SELECT pg_sleep(10);")

        print("✓ Query completed (this shouldn't happen!)")

    except Exception as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Query exceeded the timeout limit. This happens when:")
        print("   - Query is too complex or inefficient")
        print("   - Database is under heavy load")
        print("   - Network latency is high")
        print("   - Timeout settings are too aggressive")
        print("\n🔧 HOW TO FIX:")
        print("   1. Optimize queries (add indexes, reduce joins)")
        print("   2. Adjust timeout settings appropriately:")
        print("      connect_timeout: Connection establishment (5-10s)")
        print("      statement_timeout: Query execution (30-300s)")
        print("   3. Implement batch processing for large datasets")
        print("   4. Monitor query performance with EXPLAIN ANALYZE")
        print("\n✅ CORRECT APPROACH:")
        print("   - Set realistic timeouts based on workload")
        print("   - Implement retry logic for transient failures")
        print("   - Use connection pooling with health checks")
        print("   - Monitor and alert on slow queries")

if __name__ == "__main__":
    main()
```

#### 3. Data Quality Failure Scripts

**File:** `sessions/session1/code/failures/fail_corrupt_excel.py`

```python
"""
Failure Case: Corrupted Excel File

This script demonstrates what happens when the input file is corrupted.
Students learn:
- File format validation
- Graceful error handling
- Data quality checks

Expected Error: BadZipFile or ValueError
"""

import os
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 70)
    print("FAILURE CASE: Corrupted Excel File")
    print("=" * 70)
    print("\nThis script attempts to read a corrupted Excel file.\n")

    # Create a fake corrupted file (text file with .xlsx extension)
    corrupt_file = Path(__file__).parent / "corrupt_test.xlsx"

    print(f"Creating fake corrupted file: {corrupt_file}")
    with open(corrupt_file, 'w') as f:
        f.write("This is not a valid Excel file, just plain text!")

    print(f"Attempting to read corrupted file...")
    print("-" * 70)

    try:
        df = pd.read_excel(corrupt_file)
        print("✓ File read successfully (this shouldn't happen!)")
    except Exception as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   The file is corrupted or not a valid Excel format. Causes:")
        print("   - File partially downloaded")
        print("   - Disk corruption")
        print("   - Wrong file extension")
        print("   - File still being written by another process")
        print("\n🔧 HOW TO FIX:")
        print("   1. Verify file integrity:")
        print("      file ../../data/online_retail.xlsx")
        print("   2. Check file size (should be > 0 bytes)")
        print("   3. Try opening file manually in Excel")
        print("   4. Re-download or regenerate the file")
        print("   5. Validate file format before processing:")
        print("\n✅ CORRECT APPROACH:")
        print("   import magic  # python-magic library")
        print("   mime = magic.from_file(file_path, mime=True)")
        print("   if mime not in ['application/vnd.ms-excel', 'application/vnd.openxmlformats']:")
        print("       raise ValueError('Invalid Excel file format')")
    finally:
        # Cleanup
        if corrupt_file.exists():
            corrupt_file.unlink()
            print(f"\n🧹 Cleaned up test file: {corrupt_file}")

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_missing_columns.py`

```python
"""
Failure Case: Missing Required Columns

This script demonstrates what happens when input data is missing required columns.
Students learn:
- Schema validation
- Data contract enforcement
- Defensive programming

Expected Error: KeyError
"""

import os
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Missing Required Columns")
    print("=" * 70)
    print("\nThis script processes data missing required columns.\n")

    # Create test CSV with missing columns
    test_file = Path(__file__).parent / "invalid_schema.csv"

    print(f"Creating test file with invalid schema: {test_file}")
    df_invalid = pd.DataFrame({
        'InvoiceNo': ['536365', '536366'],
        'StockCode': ['85123A', '71053'],
        # Missing: Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country
    })
    df_invalid.to_csv(test_file, index=False)

    print("Attempting to process file with missing columns...")
    print(f"Available columns: {list(df_invalid.columns)}")
    print("-" * 70)

    try:
        ingestor = DataIngestor()
        df = pd.read_csv(test_file)

        # This will fail when trying to access missing columns
        cleaned_df = ingestor.clean_data(df)

        print("✓ Data cleaned successfully (this shouldn't happen!)")
    except KeyError as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print(f"   Missing Column: {e}")
        print("\n📚 EXPLANATION:")
        print("   The input data is missing required columns. This happens when:")
        print("   - Source system schema changed")
        print("   - Wrong file provided")
        print("   - Data export was incomplete")
        print("   - Column names don't match expectations")
        print("\n🔧 HOW TO FIX:")
        print("   1. Verify source data schema matches expectations")
        print("   2. Add schema validation before processing:")
        print("\n✅ CORRECT APPROACH:")
        print("   REQUIRED_COLUMNS = [")
        print("       'InvoiceNo', 'StockCode', 'Description', 'Quantity',")
        print("       'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country'")
        print("   ]")
        print("   ")
        print("   missing = set(REQUIRED_COLUMNS) - set(df.columns)")
        print("   if missing:")
        print("       raise ValueError(f'Missing required columns: {missing}')")
        print("   ")
        print("   extra = set(df.columns) - set(REQUIRED_COLUMNS)")
        print("   if extra:")
        print("       logger.warning(f'Unexpected columns (will be ignored): {extra}')")
    finally:
        if test_file.exists():
            test_file.unlink()
            print(f"\n🧹 Cleaned up test file: {test_file}")

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_invalid_schema.py`

```python
"""
Failure Case: Data Type Mismatch

This script demonstrates what happens when data types don't match expectations.
Students learn:
- Type validation
- Data parsing errors
- Type coercion strategies

Expected Error: ValueError or TypeError
"""

import os
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Data Type Mismatch")
    print("=" * 70)
    print("\nThis script processes data with invalid data types.\n")

    # Create test CSV with wrong data types
    test_file = Path(__file__).parent / "invalid_types.csv"

    print(f"Creating test file with invalid data types: {test_file}")
    df_invalid = pd.DataFrame({
        'InvoiceNo': ['536365', '536366'],
        'StockCode': ['85123A', '71053'],
        'Description': ['WHITE HANGING HEART T-LIGHT HOLDER', 'WHITE METAL LANTERN'],
        'Quantity': ['NOT_A_NUMBER', 'INVALID'],  # Should be integers
        'InvoiceDate': ['2010-12-01 08:26:00', '2010-12-01 08:26:00'],
        'UnitPrice': ['2.55', 'abc'],  # 'abc' is not a valid price
        'CustomerID': ['17850', '17850'],
        'Country': ['United Kingdom', 'United Kingdom']
    })
    df_invalid.to_csv(test_file, index=False)

    print("Attempting to process file with invalid data types...")
    print("-" * 70)

    try:
        df = pd.read_csv(test_file)
        print(f"Loaded {len(df)} rows")
        print(f"Data types:\n{df.dtypes}\n")

        # Try to convert quantity to int
        df['Quantity'] = df['Quantity'].astype(int)

        print("✓ Data processed successfully (this shouldn't happen!)")
    except ValueError as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Data types don't match expectations. Common causes:")
        print("   - Manual data entry errors")
        print("   - Source system changes")
        print("   - Data corruption during transfer")
        print("   - Encoding issues")
        print("\n🔧 HOW TO FIX:")
        print("   1. Identify invalid values:")
        print("      df[pd.to_numeric(df['Quantity'], errors='coerce').isna()]")
        print("   2. Decide on strategy:")
        print("      - Reject entire batch (strict)")
        print("      - Reject invalid rows (moderate)")
        print("      - Coerce to default value (lenient)")
        print("   3. Add data quality checks")
        print("\n✅ CORRECT APPROACH:")
        print("   # Try to convert with error handling")
        print("   df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')")
        print("   ")
        print("   # Identify and log invalid rows")
        print("   invalid_rows = df[df['Quantity'].isna()]")
        print("   if len(invalid_rows) > 0:")
        print("       logger.warning(f'Found {len(invalid_rows)} rows with invalid quantities')")
        print("       invalid_rows.to_csv('errors/invalid_quantities.csv')")
        print("   ")
        print("   # Remove invalid rows")
        print("   df = df.dropna(subset=['Quantity'])")
    finally:
        if test_file.exists():
            test_file.unlink()
            print(f"\n🧹 Cleaned up test file: {test_file}")

if __name__ == "__main__":
    main()
```

#### 4. Configuration Failure Scripts

**File:** `sessions/session1/code/failures/fail_missing_env_vars.py`

```python
"""
Failure Case: Missing Environment Variables

This script demonstrates what happens when required .env variables are missing.
Students learn:
- Configuration management
- Environment variable validation
- Secure credential handling

Expected Error: KeyError or None values causing connection failure
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 70)
    print("FAILURE CASE: Missing Environment Variables")
    print("=" * 70)
    print("\nThis script attempts to connect without required env vars.\n")

    # Clear environment variables
    env_backup = {}
    env_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']

    print("Clearing environment variables...")
    for var in env_vars:
        if var in os.environ:
            env_backup[var] = os.environ[var]
            del os.environ[var]

    print("Attempting to create DataIngestor without env vars...")
    print("-" * 70)

    try:
        from code.ingest import DataIngestor
        ingestor = DataIngestor()

        print(f"DB_HOST: {ingestor.db_host}")
        print(f"DB_PORT: {ingestor.db_port}")
        print(f"DB_NAME: {ingestor.db_name}")
        print(f"DB_USER: {ingestor.db_user}")
        print(f"DB_PASSWORD: {'*' * len(ingestor.db_password) if ingestor.db_password else 'None'}")

        print("\n⚠️  WARNING: Using default values!")
        print("   This might work locally but will fail in production.")

    except Exception as e:
        print("\n❌ ERROR OCCURRED:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")

    print("\n📚 EXPLANATION:")
    print("   Environment variables are missing. This happens when:")
    print("   - .env file not created")
    print("   - .env file not loaded (missing python-dotenv)")
    print("   - Running in different environment (Docker, CI/CD)")
    print("   - Variables not exported in shell")
    print("\n🔧 HOW TO FIX:")
    print("   1. Create .env file from template:")
    print("      cp .env.example .env")
    print("   2. Fill in actual values:")
    print("      DB_HOST=localhost")
    print("      DB_PORT=5432")
    print("      DB_NAME=retail_db")
    print("      DB_USER=postgres")
    print("      DB_PASSWORD=your_password")
    print("   3. Ensure python-dotenv loads .env:")
    print("      from dotenv import load_dotenv")
    print("      load_dotenv()")
    print("\n✅ CORRECT APPROACH:")
    print("   # Validate required env vars on startup")
    print("   REQUIRED_ENV_VARS = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']")
    print("   missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]")
    print("   if missing:")
    print("       raise EnvironmentError(f'Missing required env vars: {missing}')")

    # Restore environment variables
    print("\n🔄 Restoring environment variables...")
    for var, value in env_backup.items():
        os.environ[var] = value

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_wrong_credentials.py`

```python
"""
Failure Case: Invalid Database Credentials

This script demonstrates what happens when database credentials are wrong.
Students learn:
- Authentication vs authorization
- Credential validation
- Security error handling

Expected Error: psycopg2.OperationalError (authentication failed)
"""

import os
import sys
from pathlib import Path
import psycopg2

sys.path.append(str(Path(__file__).parent.parent.parent))

def main():
    print("=" * 70)
    print("FAILURE CASE: Invalid Database Credentials")
    print("=" * 70)
    print("\nThis script attempts to connect with wrong credentials.\n")

    # Use wrong password
    print("Attempting to connect with invalid password...")
    print("-" * 70)

    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "retail_db"),
            user=os.getenv("DB_USER", "postgres"),
            password="WRONG_PASSWORD_12345"
        )

        print("✓ Connected successfully (this shouldn't happen!)")

    except psycopg2.OperationalError as e:
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Authentication failed. Common causes:")
        print("   - Wrong password in .env file")
        print("   - Password contains special characters (not escaped)")
        print("   - User doesn't exist")
        print("   - User doesn't have access to database")
        print("   - Password expired (in some systems)")
        print("\n🔧 HOW TO FIX:")
        print("   1. Verify credentials manually:")
        print("      psql -h localhost -U postgres -d retail_db")
        print("   2. Check .env file for typos")
        print("   3. Ensure user has proper permissions:")
        print("      GRANT ALL PRIVILEGES ON DATABASE retail_db TO postgres;")
        print("   4. Check pg_hba.conf for authentication method")
        print("\n✅ CORRECT APPROACH:")
        print("   - Never hardcode credentials in code")
        print("   - Use environment variables or secret management")
        print("   - Implement credential rotation")
        print("   - Use connection strings with URL encoding:")
        print("     postgresql://user:pass@host:port/db")
        print("   - Log authentication failures (without exposing credentials)")

    except Exception as e:
        print(f"\n⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    main()
```

#### 5. Business Logic Failure Scripts

**File:** `sessions/session1/code/failures/fail_duplicate_primary_key.py`

```python
"""
Failure Case: Duplicate Primary Key Violation

This script demonstrates what happens when trying to insert duplicate records.
Students learn:
- Primary key constraints
- Idempotency strategies
- UPSERT operations

Expected Error: psycopg2.errors.UniqueViolation
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2 import sql

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Duplicate Primary Key Violation")
    print("=" * 70)
    print("\nThis script attempts to insert duplicate records.\n")

    ingestor = DataIngestor()

    try:
        ingestor.connect()
        cursor = ingestor.conn.cursor()

        # Ensure table exists
        ingestor.execute_sql_file("code/schema.sql")

        print("Inserting first record...")
        cursor.execute("""
            INSERT INTO bronze.raw_transactions
            (invoiceno, stockcode, description, quantity, invoicedate, unitprice, customerid, country, source_file)
            VALUES
            ('TEST001', 'STOCK01', 'Test Product', 1, '2010-12-01', 10.00, '12345', 'UK', 'test.csv')
        """)
        ingestor.conn.commit()
        print("✓ First insert successful")

        print("\nAttempting to insert duplicate record with same invoiceno...")
        print("-" * 70)

        cursor.execute("""
            INSERT INTO bronze.raw_transactions
            (invoiceno, stockcode, description, quantity, invoicedate, unitprice, customerid, country, source_file)
            VALUES
            ('TEST001', 'STOCK01', 'Test Product', 1, '2010-12-01', 10.00, '12345', 'UK', 'test.csv')
        """)
        ingestor.conn.commit()

        print("✓ Duplicate insert successful (this shouldn't happen!)")

    except psycopg2.errors.UniqueViolation as e:
        ingestor.conn.rollback()
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Primary key constraint violation. This happens when:")
        print("   - Trying to insert duplicate records")
        print("   - Re-running pipeline without truncating table")
        print("   - Source data contains duplicates")
        print("   - Concurrent insertions of same key")
        print("\n🔧 HOW TO FIX:")
        print("   1. Make pipeline idempotent using TRUNCATE:")
        print("      TRUNCATE TABLE bronze.raw_transactions;")
        print("      -- Then insert data")
        print("   ")
        print("   2. Or use UPSERT (INSERT ON CONFLICT):")
        print("      INSERT INTO table (id, value)")
        print("      VALUES (1, 'data')")
        print("      ON CONFLICT (id) DO UPDATE")
        print("      SET value = EXCLUDED.value;")
        print("   ")
        print("   3. Or deduplicate source data first:")
        print("      df.drop_duplicates(subset=['invoiceno'], keep='first')")
        print("\n✅ CORRECT APPROACH:")
        print("   For batch pipelines: Use TRUNCATE + INSERT strategy")
        print("   For incremental pipelines: Use UPSERT with ON CONFLICT")
        print("   For append-only: Remove duplicates before insert")

    except Exception as e:
        ingestor.conn.rollback()
        print(f"\n⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")

    finally:
        # Cleanup test data
        try:
            cursor.execute("DELETE FROM bronze.raw_transactions WHERE invoiceno = 'TEST001'")
            ingestor.conn.commit()
            print("\n🧹 Cleaned up test data")
        except:
            pass
        ingestor.disconnect()

if __name__ == "__main__":
    main()
```

**File:** `sessions/session1/code/failures/fail_negative_prices.py`

```python
"""
Failure Case: Business Rule Violation (Negative Prices)

This script demonstrates what happens when data violates business rules.
Students learn:
- Data validation
- Business logic enforcement
- Check constraints

Expected Behavior: Data quality warning and filtering
"""

import os
import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.ingest import DataIngestor

def main():
    print("=" * 70)
    print("FAILURE CASE: Business Rule Violation")
    print("=" * 70)
    print("\nThis script processes data with negative prices (invalid).\n")

    # Create test data with negative prices
    test_file = Path(__file__).parent / "negative_prices.csv"

    print(f"Creating test file with invalid prices: {test_file}")
    df_invalid = pd.DataFrame({
        'InvoiceNo': ['536365', '536366', '536367'],
        'StockCode': ['85123A', '71053', '84029G'],
        'Description': ['Product A', 'Product B', 'Product C'],
        'Quantity': [6, 2, 4],
        'InvoiceDate': ['2010-12-01 08:26:00', '2010-12-01 08:26:00', '2010-12-01 08:27:00'],
        'UnitPrice': [2.55, -150.00, 12000.00],  # One negative, one too high
        'CustomerID': ['17850', '17850', '17851'],
        'Country': ['United Kingdom', 'United Kingdom', 'France']
    })
    df_invalid.to_csv(test_file, index=False)

    print(f"Test data created: {len(df_invalid)} rows")
    print(f"Invalid prices: {df_invalid[df_invalid['UnitPrice'] < 0]['UnitPrice'].tolist()}")
    print(f"Too high prices: {df_invalid[df_invalid['UnitPrice'] > 10000]['UnitPrice'].tolist()}")
    print("\nProcessing data through cleaning pipeline...")
    print("-" * 70)

    try:
        ingestor = DataIngestor()
        df = pd.read_csv(test_file)

        print(f"Before cleaning: {len(df)} rows")
        cleaned_df = ingestor.clean_data(df)
        print(f"After cleaning: {len(cleaned_df)} rows")

        removed = len(df) - len(cleaned_df)
        print(f"\n✓ Removed {removed} rows with invalid prices")

        print("\n📚 EXPLANATION:")
        print("   Business rules were violated. The cleaning function:")
        print("   - Detected negative prices (-150.00)")
        print("   - Detected unrealistic prices (12000.00 > 10000 threshold)")
        print("   - Filtered out invalid rows")
        print("   - Logged warnings")
        print("\n🔧 BUSINESS RULES ENFORCED:")
        print("   - UnitPrice must be >= 0 (no negative prices)")
        print("   - UnitPrice must be <= 10000 (reasonable maximum)")
        print("   - These rules prevent data quality issues")
        print("\n✅ CORRECT APPROACH:")
        print("   1. Define business rules explicitly:")
        print("      PRICE_MIN = 0")
        print("      PRICE_MAX = 10000")
        print("   ")
        print("   2. Validate data against rules:")
        print("      invalid = df[(df['UnitPrice'] < PRICE_MIN) | (df['UnitPrice'] > PRICE_MAX)]")
        print("   ")
        print("   3. Decide on action:")
        print("      - Reject entire batch (strict)")
        print("      - Filter invalid rows (current approach)")
        print("      - Cap values at min/max (transformation)")
        print("   ")
        print("   4. Log violations for investigation:")
        print("      invalid.to_csv('errors/price_violations.csv')")
        print("\n💡 ALTERNATIVE: Database CHECK Constraints")
        print("   ALTER TABLE raw_transactions")
        print("   ADD CONSTRAINT check_price_positive CHECK (unitprice >= 0);")
        print("   ")
        print("   This enforces rules at database level (fails on insert)")

    except Exception as e:
        print(f"\n⚠️  ERROR: {type(e).__name__}: {e}")

    finally:
        if test_file.exists():
            test_file.unlink()
            print(f"\n🧹 Cleaned up test file: {test_file}")

if __name__ == "__main__":
    main()
```

#### 6. Failures Directory README

**File:** `sessions/session1/code/failures/README.md`

```markdown
# Session 1 Failure Cases

This directory contains failure scenario scripts that demonstrate common errors in data ingestion pipelines.

## Purpose

These scripts are educational tools to help you:
- Understand what can go wrong in production
- Recognize error patterns
- Learn proper error handling techniques
- Practice debugging skills

## Running Failure Cases

Each script can be run independently:

\`\`\`bash
cd sessions/session1
python code/failures/fail_missing_file.py
\`\`\`

## Failure Categories

### Infrastructure Failures
- `fail_missing_file.py` - File not found errors
- `fail_database_down.py` - Database connection failures
- `fail_network_timeout.py` - Network and query timeouts

### Data Quality Failures
- `fail_corrupt_excel.py` - Corrupted file handling
- `fail_invalid_schema.py` - Data type mismatches
- `fail_missing_columns.py` - Missing required columns

### Configuration Failures
- `fail_missing_env_vars.py` - Missing environment variables
- `fail_wrong_credentials.py` - Invalid database credentials

### Business Logic Failures
- `fail_duplicate_primary_key.py` - Primary key constraint violations
- `fail_negative_prices.py` - Business rule violations

## Learning Approach

For each failure case:
1. Read the script docstring to understand the scenario
2. Run the script and observe the error
3. Read the explanation and troubleshooting guide
4. Compare with the correct approach
5. Try to fix it yourself before looking at solutions

## Expected Output Format

Each script produces structured output:
- 📋 Description of the failure scenario
- ❌ The actual error that occurred
- 📚 Explanation of why it happened
- 🔧 How to fix it
- ✅ Correct approach for production

## Common Patterns

All failure scripts follow this structure:
\`\`\`python
try:
    # Intentionally trigger failure
    risky_operation()
except SpecificError as e:
    # Show educational information
    explain_error(e)
    show_how_to_fix()
    show_correct_approach()
\`\`\`
```

### Success Criteria:

#### Automated Verification:
- [x] All 10 failure scripts execute without crashing
- [x] Each script produces expected error output
- [x] Scripts clean up test files after execution

#### Manual Verification:
- [x] Run each failure script and verify output is educational
- [x] Error messages are clear and actionable
- [x] Explanations are accurate and helpful
- [x] Correct approaches are demonstrated

---

## Phase 2: Session 1 Documentation Integration

### Overview
Update Session 1 README.md and Notes.md to integrate failure case learning materials, including a new "Failure Cases & Learning" section in README and "Error Handling Theory" section in Notes.

### Changes Required:

#### 1. README.md Updates
**File:** `sessions/session1/README.md`

Add new section after "Query Examples" section:

```markdown
## Failure Cases & Learning

Session 1 includes comprehensive failure scenarios to help you understand what happens when things go wrong. These educational scripts demonstrate real-world errors you'll encounter in production data pipelines.

### Running Failure Scenarios

All failure scripts are located in `code/failures/` directory:

\`\`\`bash
cd sessions/session1

# Run individual failure case
python code/failures/fail_missing_file.py
python code/failures/fail_database_down.py
python code/failures/fail_corrupt_excel.py

# Run all failure cases (educational)
for script in code/failures/fail_*.py; do
    echo "Running $script..."
    python "$script"
    echo ""
done
\`\`\`

### Failure Categories

#### 1. Infrastructure Failures

**Missing Data File** (`fail_missing_file.py`)
- **What it teaches:** File path validation and error handling
- **Expected error:** `FileNotFoundError`
- **Common causes:** Incorrect path, file not downloaded, wrong working directory
- **How to fix:** Use `Path.exists()` validation before processing

\`\`\`python
# ❌ Wrong: No validation
df = pd.read_excel('data.xlsx')

# ✅ Correct: Validate first
from pathlib import Path
file_path = Path('data.xlsx')
if not file_path.exists():
    raise FileNotFoundError(f'Data file not found: {file_path}')
df = pd.read_excel(file_path)
\`\`\`

**Database Connection Failure** (`fail_database_down.py`)
- **What it teaches:** Database connectivity and error handling
- **Expected error:** `psycopg2.OperationalError`
- **Common causes:** PostgreSQL not running, wrong host/port, network issues
- **How to fix:** Implement retry logic and health checks

\`\`\`python
# ❌ Wrong: No retry logic
conn = psycopg2.connect(...)

# ✅ Correct: Retry with backoff
import time
for attempt in range(3):
    try:
        conn = psycopg2.connect(...)
        break
    except psycopg2.OperationalError:
        if attempt < 2:
            time.sleep(2 ** attempt)
        else:
            raise
\`\`\`

**Network Timeout** (`fail_network_timeout.py`)
- **What it teaches:** Timeout configuration and query optimization
- **Expected error:** `psycopg2.errors.QueryCanceled`
- **Common causes:** Long-running queries, heavy load, network latency
- **How to fix:** Set appropriate timeouts and optimize queries

#### 2. Data Quality Failures

**Corrupted Excel File** (`fail_corrupt_excel.py`)
- **What it teaches:** File format validation
- **Expected error:** `BadZipFile` or `ValueError`
- **Common causes:** Partial download, disk corruption, wrong extension
- **How to fix:** Validate file format before processing

**Missing Required Columns** (`fail_missing_columns.py`)
- **What it teaches:** Schema validation and data contracts
- **Expected error:** `KeyError`
- **Common causes:** Source schema change, wrong file, incomplete export
- **How to fix:** Implement schema validation

\`\`\`python
# ✅ Correct: Validate schema
REQUIRED_COLUMNS = ['InvoiceNo', 'StockCode', 'Description', ...]
missing = set(REQUIRED_COLUMNS) - set(df.columns)
if missing:
    raise ValueError(f'Missing required columns: {missing}')
\`\`\`

**Invalid Data Types** (`fail_invalid_schema.py`)
- **What it teaches:** Type validation and coercion strategies
- **Expected error:** `ValueError` or `TypeError`
- **Common causes:** Manual entry errors, source changes, corruption
- **How to fix:** Use pandas type coercion with error handling

#### 3. Configuration Failures

**Missing Environment Variables** (`fail_missing_env_vars.py`)
- **What it teaches:** Configuration management and validation
- **Expected error:** `None` values or connection failures
- **Common causes:** .env file not created, not loaded, wrong environment
- **How to fix:** Validate required env vars on startup

\`\`\`python
# ✅ Correct: Validate env vars
REQUIRED_ENV_VARS = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    raise EnvironmentError(f'Missing required env vars: {missing}')
\`\`\`

**Invalid Credentials** (`fail_wrong_credentials.py`)
- **What it teaches:** Authentication and credential management
- **Expected error:** `psycopg2.OperationalError` (authentication failed)
- **Common causes:** Wrong password, special characters, user doesn't exist
- **How to fix:** Verify credentials manually, check .env file

#### 4. Business Logic Failures

**Duplicate Primary Key** (`fail_duplicate_primary_key.py`)
- **What it teaches:** Idempotency and constraint handling
- **Expected error:** `psycopg2.errors.UniqueViolation`
- **Common causes:** Re-running pipeline, duplicate source data
- **How to fix:** Use TRUNCATE strategy or UPSERT

\`\`\`sql
-- ✅ Option 1: TRUNCATE strategy (batch pipelines)
TRUNCATE TABLE bronze.raw_transactions;
INSERT INTO bronze.raw_transactions VALUES (...);

-- ✅ Option 2: UPSERT strategy (incremental pipelines)
INSERT INTO bronze.raw_transactions (invoiceno, ...)
VALUES ('12345', ...)
ON CONFLICT (invoiceno) DO UPDATE
SET description = EXCLUDED.description, ...;
\`\`\`

**Business Rule Violations** (`fail_negative_prices.py`)
- **What it teaches:** Data validation and business rules
- **Expected behavior:** Warnings and data filtering
- **Common causes:** Bad source data, data entry errors
- **How to fix:** Implement validation rules, log violations

### Troubleshooting Guide

#### Step 1: Identify Error Category

| Error Type | Category | First Action |
|------------|----------|--------------|
| FileNotFoundError | Infrastructure | Verify file exists: `ls -la data/` |
| OperationalError | Infrastructure | Check DB: `docker-compose ps` |
| QueryCanceled | Infrastructure | Review query performance |
| BadZipFile | Data Quality | Validate file format |
| KeyError | Data Quality | Check schema: `df.columns` |
| ValueError | Data Quality | Inspect data types: `df.dtypes` |
| UniqueViolation | Business Logic | Review idempotency strategy |

#### Step 2: Run Corresponding Failure Script

\`\`\`bash
# Example: Debugging file not found error
python code/failures/fail_missing_file.py
# Read the explanation and follow troubleshooting steps
\`\`\`

#### Step 3: Apply Fix

Each failure script provides:
- Root cause explanation
- Step-by-step fix instructions
- Correct code examples
- Prevention strategies

#### Step 4: Verify Fix

\`\`\`bash
# Run main pipeline to verify fix
python code/ingest.py

# Run tests to ensure no regressions
pytest tests/ -v
\`\`\`

### Common Error Patterns

#### Pattern 1: "It works on my machine"

**Symptom:** Pipeline works locally but fails in Docker/production

**Root cause:** Environment differences (file paths, environment variables)

**Solution:**
- Use environment variables for configuration
- Use relative paths with `Path(__file__).parent`
- Test in Docker before deploying

#### Pattern 2: "It worked yesterday"

**Symptom:** Pipeline suddenly fails after working previously

**Root cause:** Source data schema changed, disk full, credentials rotated

**Solution:**
- Implement schema validation
- Monitor disk space
- Implement credential rotation handling

#### Pattern 3: "It works with sample data"

**Symptom:** Pipeline works with small test data but fails with full dataset

**Root cause:** Memory issues, timeout issues, edge cases in production data

**Solution:**
- Use batch processing
- Set appropriate timeouts
- Test with production-sized data samples

### Learning Exercises

After running failure scenarios, try these exercises:

1. **Fix the Code**: Modify `code/ingest.py` to handle each failure gracefully
2. **Add Validation**: Implement pre-flight checks before processing
3. **Improve Logging**: Add structured logging for each failure scenario
4. **Write Tests**: Create pytest tests that verify error handling
5. **Create Alerts**: Design alerting strategy for production failures

### Expected vs Actual Output Comparison

#### Example: Missing File Scenario

**Expected Output (Failure Script):**
\`\`\`
======================================================================
FAILURE CASE: Missing Data File
======================================================================

This script attempts to ingest a non-existent file.
Watch for the error and how it's handled.

Attempting to read: ../../data/this_file_does_not_exist.xlsx
----------------------------------------------------------------------

❌ ERROR OCCURRED (Expected):
   Error Type: FileNotFoundError
   Error Message: [Errno 2] No such file or directory: '../../data/this_file_does_not_exist.xlsx'

📚 EXPLANATION:
   The file path doesn't exist. This commonly happens when:
   - File path is incorrect
   - File hasn't been downloaded/generated yet
   - Working directory is different than expected

🔧 HOW TO FIX:
   1. Verify the file exists: ls -la ../../data/
   2. Check your current working directory: pwd
   3. Use absolute paths or Path(__file__).parent for relative paths
   4. Add input validation before processing
\`\`\`

**Actual Output (Without Proper Handling):**
\`\`\`
Traceback (most recent call last):
  File "code/ingest.py", line 64, in read_excel
    df = pd.read_excel(file_path)
FileNotFoundError: [Errno 2] No such file or directory: 'this_file_does_not_exist.xlsx'
\`\`\`

**Correct Output (With Proper Handling):**
\`\`\`
2024-01-15 10:30:45 - ERROR - Data file not found: ../../data/online_retail.xlsx
Please ensure the file exists before running the pipeline.
Hint: Download the file from [source] or run: make download-data
\`\`\`
```

#### 2. Notes.md Updates
**File:** `sessions/session1/Notes.md`

Add new section after "Implementation Considerations":

```markdown
## Error Handling & Failure Patterns

### Types of Failures

Data pipelines can fail in four main categories:

#### 1. Infrastructure Failures

**Definition:** Issues with external systems and resources

**Examples:**
- Database server down
- Network connectivity issues
- Disk full
- Memory exhausted
- Container crashes

**Detection:**
- Connection errors
- Timeout errors
- Resource exhaustion errors

**Handling Strategy:**
- Implement retry logic with exponential backoff
- Set appropriate timeouts
- Monitor resource usage
- Use circuit breakers

**Code Pattern:**
\`\`\`python
import time
import random

def retry_with_exponential_backoff(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.random()
            time.sleep(wait)
\`\`\`

#### 2. Data Quality Failures

**Definition:** Issues with input data format, schema, or content

**Examples:**
- Missing required columns
- Invalid data types
- Corrupted files
- Encoding issues
- Null values in required fields

**Detection:**
- Schema validation
- Data type checks
- Null checks
- Format validation

**Handling Strategy:**
- Validate schema before processing
- Log invalid records
- Save failed records for review
- Implement data quality checks

**Code Pattern:**
\`\`\`python
def validate_schema(df, required_columns):
    missing = set(required_columns) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {missing}')

    extra = set(df.columns) - set(required_columns)
    if extra:
        logger.warning(f'Extra columns (ignored): {extra}')

    return df[required_columns]
\`\`\`

#### 3. Configuration Failures

**Definition:** Issues with environment setup and configuration

**Examples:**
- Missing environment variables
- Invalid credentials
- Wrong database name
- Incorrect file paths
- Missing dependencies

**Detection:**
- Environment variable validation
- Connection testing
- Configuration validation

**Handling Strategy:**
- Validate configuration on startup
- Provide clear error messages
- Use .env.example as template
- Document required configuration

**Code Pattern:**
\`\`\`python
def validate_environment():
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        raise EnvironmentError(
            f'Missing required environment variables: {missing}\n'
            f'Please create .env file from .env.example'
        )
\`\`\`

#### 4. Business Logic Failures

**Definition:** Issues with data violating business rules

**Examples:**
- Negative prices
- Duplicate primary keys
- Invalid foreign keys
- Data out of expected range
- Failed business rule validation

**Detection:**
- Business rule validation
- Constraint violations
- Data range checks

**Handling Strategy:**
- Define business rules explicitly
- Validate before insert
- Log violations
- Decide on rejection vs correction

**Code Pattern:**
\`\`\`python
def validate_business_rules(df):
    # Define rules
    rules = {
        'unitprice': (0, 10000),
        'quantity': (-100, 10000)
    }

    violations = []
    for column, (min_val, max_val) in rules.items():
        invalid = df[(df[column] < min_val) | (df[column] > max_val)]
        if len(invalid) > 0:
            violations.append(f'{column}: {len(invalid)} violations')
            invalid.to_csv(f'errors/{column}_violations.csv')

    if violations:
        logger.warning(f'Business rule violations: {violations}')

    # Filter out invalid rows
    for column, (min_val, max_val) in rules.items():
        df = df[(df[column] >= min_val) & (df[column] <= max_val)]

    return df
\`\`\`

### Error Handling Best Practices

#### 1. Fail Fast, Fail Clearly

**Principle:** Detect errors early and provide actionable messages

**Bad:**
\`\`\`python
try:
    process_data()
except:
    print("Error")
\`\`\`

**Good:**
\`\`\`python
try:
    validate_environment()
    validate_schema(df)
    validate_business_rules(df)
    process_data()
except FileNotFoundError as e:
    logger.error(f'Data file not found: {e}')
    logger.info('Hint: Run download-data.sh to fetch data')
    sys.exit(1)
except ValueError as e:
    logger.error(f'Schema validation failed: {e}')
    sys.exit(1)
\`\`\`

#### 2. Distinguish Transient vs Permanent Failures

**Transient:** Can be resolved by retrying (network blips, temporary locks)
**Permanent:** Cannot be resolved by retrying (invalid data, wrong credentials)

**Strategy:**
- Retry transient failures with backoff
- Fail fast on permanent failures
- Log appropriately for both

#### 3. Preserve Context

**Principle:** Log enough information to debug without re-running

**Good logging:**
\`\`\`python
logger.error(
    'Failed to process batch',
    extra={
        'batch_id': batch_id,
        'file_path': file_path,
        'row_count': len(df),
        'error': str(e),
        'timestamp': datetime.now().isoformat()
    }
)
\`\`\`

#### 4. Graceful Degradation

**Principle:** Handle partial failures gracefully

**Example:**
- Process valid rows, log invalid ones
- Continue pipeline even if non-critical steps fail
- Provide partial results when possible

#### 5. Defensive Programming

**Principle:** Assume everything can fail

**Checklist:**
- [ ] Validate inputs before processing
- [ ] Check external dependencies are available
- [ ] Set timeouts on all external calls
- [ ] Handle None/null values explicitly
- [ ] Test error paths, not just happy path

### Testing Error Handling

Error handling should be tested as rigorously as happy paths:

\`\`\`python
# Test file not found
def test_ingest_missing_file():
    with pytest.raises(FileNotFoundError):
        ingestor.read_excel('nonexistent.xlsx')

# Test invalid schema
def test_ingest_missing_columns():
    df = pd.DataFrame({'col1': [1, 2]})
    with pytest.raises(ValueError, match='Missing columns'):
        validate_schema(df, required_columns=['col1', 'col2'])

# Test connection failure
def test_connection_retry(mocker):
    mock_connect = mocker.patch('psycopg2.connect')
    mock_connect.side_effect = [
        psycopg2.OperationalError(),
        psycopg2.OperationalError(),
        MagicMock()  # Success on third try
    ]

    conn = retry_with_exponential_backoff(lambda: psycopg2.connect())
    assert mock_connect.call_count == 3
\`\`\`

### Production Considerations

#### Monitoring & Alerting

**Key Metrics:**
- Error rate (errors per hour)
- Error types (categorized)
- Retry counts
- Failed batch counts

**Alert Conditions:**
- Error rate > 5%
- Critical errors (database down)
- Persistent failures (> 3 retries)

#### Error Budget

**Concept:** Define acceptable failure rate (e.g., 99.9% success = 0.1% failure budget)

**Implementation:**
- Track success/failure rates
- Alert when approaching budget
- Review failures during postmortems

#### Dead Letter Queue

**Purpose:** Store unprocessable records for manual review

**Implementation:**
\`\`\`python
def process_with_dlq(df):
    valid_rows = []
    invalid_rows = []

    for idx, row in df.iterrows():
        try:
            validate_row(row)
            valid_rows.append(row)
        except Exception as e:
            invalid_rows.append({
                'row': row.to_dict(),
                'error': str(e),
                'timestamp': datetime.now()
            })

    # Save invalid rows to DLQ
    if invalid_rows:
        pd.DataFrame(invalid_rows).to_csv('errors/dlq.csv')

    return pd.DataFrame(valid_rows)
\`\`\`
```

### Success Criteria:

#### Automated Verification:
- [x] README.md contains "Failure Cases & Learning" section
- [x] Notes.md contains "Error Handling Theory" section
- [x] All code examples in documentation are syntactically correct
- [x] Links to failure scripts are accurate

#### Manual Verification:
- [x] Documentation provides clear learning path
- [x] Troubleshooting guide is actionable
- [x] Comparison examples show wrong vs right approaches
- [x] Documentation integrates naturally with existing content

---

## Phase 3: Session 2 Failure Cases - Infrastructure & Scripts

### Overview
Create `code/failures/` directory in Session 2 and implement 8 failure scenario scripts covering transformation-specific failures including missing dependencies, SQL errors, and data modeling issues.

### Changes Required:

#### 1. Directory Structure
**Location:** `sessions/session2/code/failures/`

```bash
mkdir -p sessions/session2/code/failures
```

**Structure:**
```
sessions/session2/code/failures/
├── __init__.py
├── README.md
├── fail_missing_bronze_table.py       # Infrastructure: Bronze table doesn't exist
├── fail_sql_syntax_error.py           # Configuration: Invalid SQL
├── fail_missing_dimension_data.py     # Data Quality: Empty dimension tables
├── fail_referential_integrity.py      # Business Logic: FK constraint violation
├── fail_duplicate_dimension.py        # Business Logic: Duplicate dimension keys
├── fail_aggregate_calculation.py      # Business Logic: Division by zero, nulls
├── fail_partition_error.py            # Infrastructure: Partition issues
└── fail_transaction_rollback.py       # Infrastructure: Transaction failures
```

#### 2. Session 2 Specific Failure Scripts

**File:** `sessions/session2/code/failures/fail_missing_bronze_table.py`

```python
"""
Failure Case: Missing Bronze Table (Dependency)

This script demonstrates what happens when trying to transform data
from a bronze table that doesn't exist.

Students learn:
- Dependency management in multi-stage pipelines
- Pre-flight checks
- Clear error messaging

Expected Error: psycopg2.errors.UndefinedTable
"""

import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.transform import DataTransformer

def main():
    print("=" * 70)
    print("FAILURE CASE: Missing Bronze Table")
    print("=" * 70)
    print("\nThis script attempts transformation without bronze data.\n")

    transformer = DataTransformer()

    try:
        transformer.connect()
        cursor = transformer.conn.cursor()

        # Try to query non-existent bronze table
        print("Attempting to query bronze.raw_transactions...")
        print("-" * 70)

        cursor.execute("SELECT COUNT(*) FROM bronze.raw_transactions;")
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"⚠️  Table exists but is empty (0 rows)")
        else:
            print(f"✓ Table exists with {count} rows")

    except Exception as e:
        print("\n❌ ERROR OCCURRED (Expected if Session 1 not completed):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   The bronze.raw_transactions table doesn't exist or is empty.")
        print("   This happens when:")
        print("   - Session 1 ingestion hasn't been run")
        print("   - Database was reset without re-ingestion")
        print("   - Wrong database selected")
        print("   - Table was accidentally dropped")
        print("\n🔧 HOW TO FIX:")
        print("   1. Complete Session 1 first:")
        print("      cd sessions/session1")
        print("      python code/ingest.py")
        print("   ")
        print("   2. Verify bronze data exists:")
        print("      psql -h localhost -U postgres -d retail_db \\")
        print("           -c 'SELECT COUNT(*) FROM bronze.raw_transactions;'")
        print("   ")
        print("   3. If table missing, check schema exists:")
        print("      psql -h localhost -U postgres -d retail_db \\")
        print("           -c '\\dn bronze'")
        print("\n✅ CORRECT APPROACH:")
        print("   # Add dependency check before transformation")
        print("   def check_dependencies(conn):")
        print("       cursor = conn.cursor()")
        print("       cursor.execute('''")
        print("           SELECT COUNT(*)")
        print("           FROM information_schema.tables")
        print("           WHERE table_schema = 'bronze'")
        print("           AND table_name = 'raw_transactions'")
        print("       ''')")
        print("       exists = cursor.fetchone()[0] > 0")
        print("       if not exists:")
        print("           raise RuntimeError('Bronze table not found. Run Session 1 first.')")
        print("   ")
        print("   check_dependencies(conn)")
        print("   # Then proceed with transformation")

    finally:
        transformer.disconnect()

if __name__ == "__main__":
    main()
```

**File:** `sessions/session2/code/failures/fail_sql_syntax_error.py`

```python
"""
Failure Case: SQL Syntax Error

This script demonstrates what happens when SQL files contain syntax errors.

Students learn:
- SQL debugging
- Statement-level error handling
- SQL validation

Expected Error: psycopg2.errors.SyntaxError
"""

import os
import sys
from pathlib import Path
import psycopg2

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.transform import DataTransformer

def main():
    print("=" * 70)
    print("FAILURE CASE: SQL Syntax Error")
    print("=" * 70)
    print("\nThis script executes SQL with intentional syntax errors.\n")

    transformer = DataTransformer()

    try:
        transformer.connect()
        cursor = transformer.conn.cursor()

        # Create a SQL file with syntax error
        bad_sql = """
        -- This SQL has intentional syntax errors
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100
            -- Missing closing parenthesis
        ;

        -- Another error: missing FROM
        SELECT * WHERE id = 1;
        """

        print("Executing SQL with syntax errors...")
        print("-" * 70)

        cursor.execute(bad_sql)
        transformer.conn.commit()

        print("✓ SQL executed successfully (this shouldn't happen!)")

    except psycopg2.errors.SyntaxError as e:
        transformer.conn.rollback()
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print(f"   Error Position: {e.cursor.query if hasattr(e, 'cursor') else 'N/A'}")
        print("\n📚 EXPLANATION:")
        print("   SQL syntax is invalid. Common causes:")
        print("   - Missing parentheses, commas, or keywords")
        print("   - Reserved words used as identifiers")
        print("   - Typos in SQL keywords")
        print("   - Wrong SQL dialect (MySQL vs PostgreSQL)")
        print("\n🔧 HOW TO FIX:")
        print("   1. Read error message carefully (shows position)")
        print("   2. Validate SQL in PostgreSQL client:")
        print("      psql -h localhost -U postgres -d retail_db")
        print("      \\i code/dim_date.sql")
        print("   3. Use SQL linter (sqlfluff):")
        print("      pip install sqlfluff")
        print("      sqlfluff lint code/*.sql")
        print("   4. Test SQL snippets incrementally")
        print("\n✅ CORRECT APPROACH:")
        print("   - Write SQL in small testable chunks")
        print("   - Test each SQL file independently")
        print("   - Use version control to track changes")
        print("   - Add SQL tests")
        print("   - Use SQL formatter (sqlfluff, pg_format)")

    except Exception as e:
        transformer.conn.rollback()
        print(f"\n⚠️  UNEXPECTED ERROR: {type(e).__name__}: {e}")

    finally:
        transformer.disconnect()

if __name__ == "__main__":
    main()
```

**File:** `sessions/session2/code/failures/fail_referential_integrity.py`

```python
"""
Failure Case: Foreign Key Constraint Violation

This script demonstrates what happens when fact table references
non-existent dimension keys.

Students learn:
- Referential integrity
- Dimension table population order
- Data validation before FK creation

Expected Error: psycopg2.errors.ForeignKeyViolation
"""

import os
import sys
from pathlib import Path
import psycopg2

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.transform import DataTransformer

def main():
    print("=" * 70)
    print("FAILURE CASE: Foreign Key Constraint Violation")
    print("=" * 70)
    print("\nThis script inserts fact data referencing non-existent dimension keys.\n")

    transformer = DataTransformer()

    try:
        transformer.connect()
        cursor = transformer.conn.cursor()

        # Ensure schemas exist
        cursor.execute("CREATE SCHEMA IF NOT EXISTS silver;")

        # Create simplified dimension table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS silver.dim_product_test (
                product_id SERIAL PRIMARY KEY,
                stock_code VARCHAR(20) UNIQUE NOT NULL,
                description VARCHAR(255)
            );
        """)

        # Create fact table with FK
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS silver.fact_sales_test (
                id SERIAL PRIMARY KEY,
                product_id INTEGER NOT NULL,
                quantity INTEGER,
                FOREIGN KEY (product_id) REFERENCES silver.dim_product_test(product_id)
            );
        """)

        transformer.conn.commit()

        print("Tables created with FK constraint")
        print("Attempting to insert fact record with non-existent product_id...")
        print("-" * 70)

        # Try to insert fact with non-existent dimension key
        cursor.execute("""
            INSERT INTO silver.fact_sales_test (product_id, quantity)
            VALUES (99999, 10);
        """)

        transformer.conn.commit()
        print("✓ Insert successful (this shouldn't happen!)")

    except psycopg2.errors.ForeignKeyViolation as e:
        transformer.conn.rollback()
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Foreign key constraint violation. The fact table is trying to")
        print("   reference a product_id that doesn't exist in dim_product_test.")
        print("   ")
        print("   This happens when:")
        print("   - Dimension tables not populated before fact tables")
        print("   - Source data contains invalid references")
        print("   - Dimension data was deleted but fact data wasn't")
        print("   - ETL execution order is wrong")
        print("\n🔧 HOW TO FIX:")
        print("   1. Ensure correct ETL execution order:")
        print("      a. Populate dimension tables first")
        print("      b. Then populate fact tables")
        print("   ")
        print("   2. Validate references before insert:")
        print("      SELECT COUNT(*) FROM dim_product WHERE product_id = ?")
        print("   ")
        print("   3. Use LEFT JOIN to find orphaned records:")
        print("      SELECT f.*")
        print("      FROM fact_sales f")
        print("      LEFT JOIN dim_product d ON f.product_id = d.product_id")
        print("      WHERE d.product_id IS NULL")
        print("\n✅ CORRECT APPROACH:")
        print("   # Transformation order in transform.py:")
        print("   sql_files = [")
        print("       'code/dim_date.sql',        # 1. Date dimension")
        print("       'code/dim_product.sql',     # 2. Product dimension")
        print("       'code/fact_sales_daily.sql' # 3. Fact table (references dimensions)")
        print("   ]")
        print("   ")
        print("   # Or use INSERT with validation:")
        print("   INSERT INTO fact_sales (product_id, quantity)")
        print("   SELECT p.product_id, 10")
        print("   FROM bronze.raw_transactions r")
        print("   JOIN dim_product p ON r.stockcode = p.stock_code")
        print("   -- This ensures product_id exists")

    finally:
        # Cleanup
        try:
            cursor.execute("DROP TABLE IF EXISTS silver.fact_sales_test CASCADE;")
            cursor.execute("DROP TABLE IF EXISTS silver.dim_product_test CASCADE;")
            transformer.conn.commit()
            print("\n🧹 Cleaned up test tables")
        except:
            pass
        transformer.disconnect()

if __name__ == "__main__":
    main()
```

**File:** `sessions/session2/code/failures/fail_duplicate_dimension.py`

```python
"""
Failure Case: Duplicate Dimension Keys

This script demonstrates what happens when dimension tables
have duplicate natural keys.

Students learn:
- Dimension deduplication
- Slowly Changing Dimensions (SCD)
- UNIQUE constraints

Expected Error: psycopg2.errors.UniqueViolation
"""

import os
import sys
from pathlib import Path
import psycopg2

sys.path.append(str(Path(__file__).parent.parent.parent))

from code.transform import DataTransformer

def main():
    print("=" * 70)
    print("FAILURE CASE: Duplicate Dimension Keys")
    print("=" * 70)
    print("\nThis script attempts to insert duplicate products into dim_product.\n")

    transformer = DataTransformer()

    try:
        transformer.connect()
        cursor = transformer.conn.cursor()

        # Ensure silver schema exists
        cursor.execute("CREATE SCHEMA IF NOT EXISTS silver;")

        # Create dim_product with UNIQUE constraint
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS silver.dim_product_test (
                product_id SERIAL PRIMARY KEY,
                stock_code VARCHAR(20) UNIQUE NOT NULL,
                description VARCHAR(255)
            );
        """)
        transformer.conn.commit()

        print("Inserting first product...")
        cursor.execute("""
            INSERT INTO silver.dim_product_test (stock_code, description)
            VALUES ('STOCK001', 'Product A');
        """)
        transformer.conn.commit()
        print("✓ First insert successful")

        print("\nAttempting to insert duplicate stock_code...")
        print("-" * 70)

        cursor.execute("""
            INSERT INTO silver.dim_product_test (stock_code, description)
            VALUES ('STOCK001', 'Product B - Different Description');
        """)
        transformer.conn.commit()

        print("✓ Duplicate insert successful (this shouldn't happen!)")

    except psycopg2.errors.UniqueViolation as e:
        transformer.conn.rollback()
        print("\n❌ ERROR OCCURRED (Expected):")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {e}")
        print("\n📚 EXPLANATION:")
        print("   Duplicate natural key in dimension table.")
        print("   ")
        print("   The UNIQUE constraint prevents the same stock_code from being")
        print("   inserted twice. This is intentional to maintain data integrity.")
        print("   ")
        print("   This happens when:")
        print("   - Source data contains duplicates")
        print("   - Pipeline re-runs without proper deduplication")
        print("   - Product attributes changed (needs SCD Type 2)")
        print("\n🔧 HOW TO FIX:")
        print("   Decision point: How to handle dimension changes?")
        print("   ")
        print("   Option 1: SCD Type 1 (Overwrite - current approach)")
        print("   - Keep only latest version")
        print("   - Use INSERT ON CONFLICT UPDATE")
        print("   ")
        print("   Option 2: SCD Type 2 (History tracking)")
        print("   - Keep all versions with effective dates")
        print("   - Add valid_from, valid_to columns")
        print("   ")
        print("   Option 3: Deduplication strategy")
        print("   - Keep first/last occurrence")
        print("   - Merge duplicate attributes")
        print("\n✅ CORRECT APPROACH - SCD Type 1 (Overwrite):")
        print("   INSERT INTO silver.dim_product (stock_code, description)")
        print("   VALUES ('STOCK001', 'Product B')")
        print("   ON CONFLICT (stock_code) DO UPDATE")
        print("   SET description = EXCLUDED.description,")
        print("       updated_at = CURRENT_TIMESTAMP;")
        print("   ")
        print("✅ CORRECT APPROACH - SCD Type 2 (History):")
        print("   -- Expire old record")
        print("   UPDATE silver.dim_product")
        print("   SET valid_to = CURRENT_DATE, is_current = FALSE")
        print("   WHERE stock_code = 'STOCK001' AND is_current = TRUE;")
        print("   ")
        print("   -- Insert new version")
        print("   INSERT INTO silver.dim_product")
        print("   (stock_code, description, valid_from, valid_to, is_current)")
        print("   VALUES ('STOCK001', 'Product B', CURRENT_DATE, '9999-12-31', TRUE);")

    finally:
        # Cleanup
        try:
            cursor.execute("DROP TABLE IF EXISTS silver.dim_product_test CASCADE;")
            transformer.conn.commit()
            print("\n🧹 Cleaned up test table")
        except:
            pass
        transformer.disconnect()

if __name__ == "__main__":
    main()
```

(Continue with additional Session 2 failure scripts: `fail_aggregate_calculation.py`, `fail_missing_dimension_data.py`, `fail_partition_error.py`, `fail_transaction_rollback.py` following similar patterns)

---

## Phase 4: Session 2 Documentation Integration

(Similar structure to Phase 2, updating Session 2's README.md and Notes.md with transformation-specific failure cases)

---

## Phase 5: Session 3 Failure Cases - Infrastructure & Scripts

### Overview
Create `code/failures/` directory in Session 3 and implement 8 failure scenario scripts covering reliability-specific failures including checkpoint corruption, retry exhaustion, and idempotency violations.

(Similar structure to Phase 1 and Phase 3, but focused on reliability patterns from Session 3)

---

## Phase 6: Session 3 Documentation Integration

(Similar structure to Phase 2 and Phase 4, updating Session 3's README.md and Notes.md with reliability-specific failure cases)

---

## Testing Strategy

### Unit Tests:
Each failure script should:
- Execute without crashing (even when demonstrating failures)
- Clean up test data/files after execution
- Produce expected error types
- Provide educational output

### Integration Tests:
- Verify all failure scripts can be run sequentially
- Confirm documentation links point to correct files
- Validate code examples in documentation are executable

### Manual Testing Steps:
1. Run each failure script individually
2. Verify error output matches documentation
3. Follow troubleshooting guide to fix each failure
4. Confirm learning materials are clear and actionable

## Performance Considerations

- Failure scripts should execute quickly (< 10 seconds each)
- Test data should be minimal (< 100 rows)
- Cleanup should be automatic (no manual intervention)
- Scripts should not interfere with existing session data

## Migration Notes

These failure cases are additive:
- No changes to existing working code
- Original scripts remain intact
- Documentation is enhanced, not replaced
- Students can skip failure cases if desired (but encouraged to explore)
