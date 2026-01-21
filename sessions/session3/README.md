# Session 3: Reliability & Business Logic

## Overview

Session 3 focuses on making the batch pipeline production-safe and reliable by working with the Gold layer data from Session 2. You'll implement idempotency, checkpoint mechanisms, structured logging, and retry logic to build a robust pipeline that can safely re-run.

## Prerequisites

- Completed Session 1 (Data ingestion pipeline - bronze.raw_transactions)
- Completed Session 2 (Data modeling - silver and gold schemas populated)
- Python 3.11 or higher
- PostgreSQL 15 or higher
- Docker and Docker Compose (optional but recommended)

**IMPORTANT**: Session 3 requires Session 2 to have been completed successfully, specifically:
- `silver.fact_sales_daily` table must be populated
- `gold.fact_sales_monthly` schema must exist
- `gold.fact_product_performance` schema must exist
- `gold.fact_country_sales` schema must exist

Run Session 2's `transform_gold.py` before Session 3:

## Learning Objectives

- Understand business requirement → technical design translation
- Implement idempotent month-based processing for gold layer
- Build checkpoint mechanism using ops.processed_months table
- Add retry logic with exponential backoff
- Implement structured JSON logging (info/warning/error)
- Make pipeline safe to re-run without double-counting
- Track pipeline execution with structured checkpoints

## Setup

### Option 1: Using uv (Recommended)

```bash
cd sessions/session3
uv venv
source .venv/bin/activate
uv pip install -r requirement.txt
```

### Option 2: Using pip

```bash
cd sessions/session3
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

### Option 3: Using Docker Compose

```bash
cd sessions/session3
docker-compose up -d postgres
```

This starts PostgreSQL on port 5433 to avoid conflicts with other sessions.

### Option 4: Connect to Existing Database

If you already have PostgreSQL running from Session 1 or 2, use that:

```bash
# No need to start new postgres
# Just use existing database on port 5432
# Ensure .env has correct DB_HOST and DB_PORT
```

## Environment Variables

Create a `.env` file in session3 directory:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_db
DB_USER=postgres
DB_PASSWORD=postgres
```

## Run Instructions

### Prerequisites Check

Before running Session 3 pipelines, ensure Session 2 gold layer is populated:

```bash
cd sessions/session2
source .venv/bin/activate
python code/transform_gold.py
```

Verify gold layer exists:
```bash
psql -h localhost -U postgres -d retail_db -c "\dt gold.*"
```

### Step 0: Initialize Session 3 Schemas (REQUIRED - Run once)

Before running any pipeline scripts, you must initialize the required ops schemas and tables:

```bash
cd sessions/session3
source .venv/bin/activate
python code/init_schemas.py
```

This creates:
- `ops` schema
- `ops.processed_months` table (for idempotency)
- `ops.pipeline_checkpoint` table (for checkpoint tracking)
- `ops.pipeline_logs` table (for structured logging)

### Step 1: Run Idempotent Pipeline

The idempotent pipeline processes gold layer data with month-level granularity, ensuring idempotency through checkpointing.

#### Using Python

```bash
cd sessions/session3
source .venv/bin/activate

# Process all unprocessed months
python code/idempotent_pipeline.py

# Process specific month
python code/idempotent_pipeline.py --year 2010 --month 12

# Process all months for specific year
python code/idempotent_pipeline.py --year 2010

# Reset all processed months (for testing)
python code/idempotent_pipeline.py --reset

# Dry run (show what would be processed)
python code/idempotent_pipeline.py --dry-run
```

#### Using Docker

```bash
cd sessions/session3
docker-compose --profile idempotent run idempotent python code/idempotent_pipeline.py --year 2010 --month 12
```

### Step 2: Run Reliable Pipeline

The reliable pipeline demonstrates structured logging, checkpointing, and retry logic when updating gold layer product and country metrics.

#### Using Python

```bash
cd sessions/session3
source .venv/bin/activate

# Run reliable pipeline with default logging
python code/reliable_pipeline.py

# Run with verbose logging
python code/reliable_pipeline.py --verbose
```

#### Using Docker

```bash
cd sessions/session3
docker-compose --profile reliable run reliable python code/reliable_pipeline.py
```

### Step 3: Verify Reliability Features

Connect to PostgreSQL and verify reliability tables:

```bash
psql -h localhost -U postgres -d retail_db

# List tables in ops schema
\dt ops.*

# View processed months (idempotency)
SELECT * FROM ops.processed_months ORDER BY month_key DESC;

# View checkpoints
SELECT * FROM ops.pipeline_checkpoint ORDER BY updated_at DESC LIMIT 20;

# View pipeline logs
SELECT * FROM ops.pipeline_logs ORDER BY timestamp DESC LIMIT 20;

# Check checkpoint recovery
SELECT pipeline_name, run_id, stage, status, checkpoint_value
FROM ops.pipeline_checkpoint
WHERE status = 'completed'
ORDER BY updated_at DESC;
```

## File Structure

```
sessions/session3/
├── requirement.txt              # Python dependencies
├── code/
│   ├── init_schemas.py          # Initialize all schemas and tables (RUN FIRST)
│   ├── processed_months_schema.sql   # Processed months checkpoint table
│   ├── checkpoint_schema.sql     # Checkpoint table schema
│   ├── logging_schema.sql        # Structured logging table schema
│   ├── idempotent_pipeline.py   # Idempotent gold layer pipeline
│   └── reliable_pipeline.py     # Reliable pipeline with logging & checkpoints
├── tests/
│   ├── __init__.py
│   └── test_reliability.py    # Test cases for reliability features
├── docker/
│   └── Dockerfile              # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── Notes.md                   # Theory (idempotency, checkpoints, retry, logging)
└── README.md                  # This file
```

## Pipeline Details

### Idempotent Pipeline (`idempotent_pipeline.py`)

**Purpose**: Process gold layer data with idempotency guarantees

**How it works**:
1. Checks `ops.processed_months` table for already-processed months
2. Finds all months available in `silver.fact_sales_daily`
3. Processes only unprocessed months
4. Uses UPSERT (ON CONFLICT) to prevent duplicates
5. Marks each month as completed in checkpoint table

**Idempotency Example**:
```python
# Running pipeline multiple times produces same result
# First run: Processes 10 months → 10 rows in gold.fact_sales_monthly
# Second run: Processes 0 months (all already processed) → No changes
```

**Data Flow**:
```
silver.fact_sales_daily
    ↓ (aggregation by month)
gold.fact_sales_monthly (upsert for idempotency)
    ↓ (checkpoint)
ops.processed_months (track processed months)
```

### Reliable Pipeline (`reliable_pipeline.py`)

**Purpose**: Demonstrate reliability features (logging, checkpoints, retry)

**How it works**:
1. Creates structured JSON logs stored in `ops.pipeline_logs`
2. Sets checkpoints before and after each stage in `ops.pipeline_checkpoint`
3. Implements retry logic with exponential backoff
4. Updates `gold.fact_product_performance` and `gold.fact_country_sales`

**Logging Example**:
```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "message": "Database connection established",
  "pipeline_name": "reliable_gold_pipeline",
  "run_id": "550e8400-e29b-41d4-a716-4466554400000",
  "metadata": {
    "db_host": "localhost",
    "db_port": 5432
  }
}
```

**Checkpoint Example**:
```
Stage: product_performance → Start checkpoint → Process → End checkpoint
Stage: country_sales → Start checkpoint → Process → End checkpoint
```

**Retry Logic**:
```python
# Automatic retry with exponential backoff
Attempt 1: Fails → Wait 1s + random
Attempt 2: Fails → Wait 2s + random
Attempt 3: Fails → Wait 4s + random
Attempt 4: Fails → Raise exception
```

## Reliability Features

### 1. Idempotent Processing

Operations can be safely re-run without side effects:

```python
# Example: UPSERT with ON CONFLICT
INSERT INTO table (id, value)
VALUES (1, 'data')
ON CONFLICT (id) DO UPDATE SET value = EXCLUDED.value;
```

### 2. Checkpointing

Track progress and enable resumption from last successful point:

```python
# Set checkpoint
checkpoint.set_month_processed(year, month, 'completed')

# Get checkpoint on restart
processed_months = checkpoint.get_processed_months()
```

### 3. Retry Logic

Automatic retry with exponential backoff for transient failures:

```python
@retry_with_backoff(max_attempts=3, base_delay=1.0)
def process_month(year, month):
    # Operation that might fail temporarily
    pass
```

### 4. Structured Logging

Machine-readable JSON logs for analysis and monitoring:

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "message": "Data loaded successfully",
  "pipeline_name": "reliable_ingestion",
  "run_id": "550e8400-e29b-41d4-a716-4466554400000",
  "metadata": {
    "records_processed": 12345,
    "duration_ms": 2456
  }
}
```

## Schema Details

### processed_months Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| month_key | VARCHAR(7) | Month key (YYYY-MM) |
| year | INTEGER | Year value |
| month | INTEGER | Month value (1-12) |
| processed_at | TIMESTAMP | When month was processed |
| updated_at | TIMESTAMP | Last update time |
| status | VARCHAR(20) | Status: in_progress/completed/failed |

### pipeline_checkpoint Table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| pipeline_name | VARCHAR(100) | Pipeline identifier |
| run_id | VARCHAR(50) | Unique run identifier |
| stage | VARCHAR(100) | Pipeline stage |
| checkpoint_key | VARCHAR(255) | Checkpoint identifier |
| checkpoint_value | VARCHAR(255) | Checkpoint value |
| status | VARCHAR(20) | pending/in_progress/completed/failed |
| start_time | TIMESTAMP | Stage start time |
| end_time | TIMESTAMP | Stage end time |
| duration_ms | INTEGER | Stage duration in milliseconds |
| metadata | JSONB | Additional context |

### pipeline_logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | BIGSERIAL | Primary key |
| timestamp | TIMESTAMP | Log timestamp |
| level | VARCHAR(10) | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| message | TEXT | Log message |
| logger | VARCHAR(100) | Logger name |
| pipeline_name | VARCHAR(100) | Pipeline identifier |
| run_id | VARCHAR(50) | Run identifier |
| module | VARCHAR(100) | Module name |
| function | VARCHAR(100) | Function name |
| line | INTEGER | Line number |
| metadata | JSONB | Additional context |

## Query Examples

### Check Pipeline Health

```sql
SELECT
    pipeline_name,
    COUNT(*) as total_runs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
    AVG(duration_ms) as avg_duration_ms
FROM ops.pipeline_checkpoint
GROUP BY pipeline_name;
```

### Analyze Pipeline Failures

```sql
SELECT
    stage,
    COUNT(*) as failure_count,
    MAX(updated_at) as last_failure
FROM ops.pipeline_checkpoint
WHERE status = 'failed'
GROUP BY stage
ORDER BY failure_count DESC;
```

### Log Analysis by Level

```sql
SELECT
    level,
    COUNT(*) as log_count,
    COUNT(DISTINCT run_id) as affected_runs
FROM ops.pipeline_logs
WHERE timestamp > NOW() - INTERVAL '24 hours'
GROUP BY level
ORDER BY log_count DESC;
```

### Identify Slow Stages

```sql
SELECT
    stage,
    AVG(duration_ms) as avg_duration_ms,
    MAX(duration_ms) as max_duration_ms,
    COUNT(*) as executions
FROM ops.pipeline_checkpoint
WHERE status = 'completed'
GROUP BY stage
ORDER BY avg_duration_ms DESC;
```

### Trace Pipeline Execution

```sql
SELECT
    cp.run_id,
    cp.stage,
    cp.status,
    cp.start_time,
    cp.end_time,
    cp.duration_ms,
    l.level,
    l.message
FROM ops.pipeline_checkpoint cp
LEFT JOIN ops.pipeline_logs l ON cp.run_id = l.run_id
WHERE cp.run_id = 'your-run-id'
ORDER BY cp.start_time;
```

## Troubleshooting

### Checkpoint Issues

```bash
# View recent processed months
psql -h localhost -U postgres -d retail_db -c "
SELECT month_key, year, month, status
FROM ops.processed_months
ORDER BY month_key DESC LIMIT 10;
"

# Reset checkpoint if stuck
psql -h localhost -U postgres -d retail_db -c "
DELETE FROM ops.processed_months;
"
```

### Log Analysis

```bash
# View recent errors
psql -h localhost -U postgres -d retail_db -c "
SELECT timestamp, level, message, metadata
FROM ops.pipeline_logs
WHERE level IN ('ERROR', 'CRITICAL')
ORDER BY timestamp DESC LIMIT 20;
"

# Search for specific error
psql -h localhost -U postgres -d retail_db -c "
SELECT * FROM ops.pipeline_logs
WHERE message ILIKE '%connection%'
ORDER BY timestamp DESC;
"
```

### Retry Exhaustion

```bash
# Check for operations hitting retry limit
psql -h localhost -U postgres -d retail_db -c "
SELECT COUNT(*) as retry_exhaustion_count
FROM ops.pipeline_logs
WHERE message ILIKE '%retry%' AND level = 'ERROR';
"
```

## Best Practices

### Idempotency
- Use UPSERT operations (INSERT ON CONFLICT)
- Design with unique constraints
- Track source system versions
- Implement deduplication

### Checkpointing
- Update checkpoints atomically with data
- Use appropriate checkpoint granularity
- Clean up old checkpoints
- Implement recovery logic

### Retry Logic
- Use exponential backoff with jitter
- Set maximum retry attempts
- Implement circuit breakers
- Distinguish transient vs permanent failures

### Logging
- Log all errors with full context
- Use structured JSON format
- Include correlation IDs
- Set appropriate log levels
- Rotate logs regularly

## Next Steps

After completing Session 3:
- Review the `Notes.md` file for theoretical concepts
- Experiment with retry logic and backoff strategies
- Test idempotent operations by re-running pipeline
- Analyze logs to identify patterns
- Practice Git collaboration exercises
- Move to Session 4: Orchestration & Operations

## References

- [Idempotency in Distributed Systems](https://blog.algomaster.io/p/idempotency-in-distributed-systems)
- [Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Structured Logging](https://clickhouse.com/resources/engineering/structured-logging)
- [Checkpoints in Data Pipelines](https://medium.com/@vivekburman1997/how-to-data-engineer-the-etlfunnel-way-bc4b23429545)
