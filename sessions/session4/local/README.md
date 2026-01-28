# Session 4 - Local Pipeline

## Overview

Simple orchestrated data pipeline with:
- **Cron scheduling** (every 5 minutes for testing)
- **Python orchestrator** (sequential task execution)
- **dbt transformations** (bronze → silver)
- **Idempotent design** (safe to re-run)

## Architecture

```
Cron (every 5 min)
    ↓
pipeline.py
    ↓
├─ 1. ingest.py      (Excel → PostgreSQL bronze)
├─ 2. dbt run        (bronze → silver)
└─ 3. validate.py    (data quality checks)
    ↓
Logs (stdout + file)
```

## Quick Start

```bash
# 1. Setup
make setup

#################
## Not furnish yet. Run manual instead

# # 2. Start services
# make start

# # 3. View logs
# make logs

#################

# 4. Run manually (optional)
make pipeline
```

## Services

- **PostgreSQL**: Database (port 5432)
- **Pipeline**: Cron + Python orchestrator
- **Superset**: Dashboards (port 8088, admin/admin)

## Pipeline Schedule

Default: **Every 5 minutes** for testing

Edit in `.env`:
```bash
# Every 5 minutes (testing)
CRON_SCHEDULE=*/5 * * * *

# Daily at 2 AM (production)
CRON_SCHEDULE=0 2 * * *
```

## Monitoring

### View Pipeline Logs

```bash
# Real-time logs
make logs

# Specific log file
docker-compose exec pipeline tail -f /app/logs/pipeline_$(date +%Y%m%d).log

# Cron execution log
docker-compose exec pipeline tail -f /app/logs/cron.log
```

### Check Data

```bash
# Quick query
make query

# Connect to database
docker-compose exec postgres psql -U postgres -d retail_db

# Check bronze layer
SELECT COUNT(*) FROM bronze.raw_transactions;

# Check silver layer
SELECT COUNT(*) FROM silver.dim_date;
SELECT COUNT(*) FROM silver.dim_product;
SELECT COUNT(*) FROM silver.fact_sales_daily;
SELECT SUM(total_revenue) as total_revenue FROM silver.fact_sales_daily;
```

## Idempotency

Pipeline is **safe to re-run**:

1. **Ingestion**: `TRUNCATE` + `INSERT` (full refresh)
2. **dbt**: Creates tables from scratch each run
3. **No duplicates**: Same result every time

Test it:
```bash
# Run multiple times
make pipeline
make pipeline
make pipeline

# Check results are identical
make query
```

## Data Lineage
```bash
# perform bash thru exec command inside docker
docker-compose exec pipeline bash
cd /app/dbt_project

# generate docs and serve it thru dedicated port
dbt docs generate --profiles-dir /app/dbt_project
dbt docs serve --port 8000 --profiles-dir /app/dbt_project

# view docs
http://localhost:8080
```

## Troubleshooting

### Pipeline Not Running

```bash
# Check cron status
docker-compose exec pipeline crontab -l

# Check cron logs
docker-compose exec pipeline tail -f /app/logs/cron.log

# Run manually to see errors
make pipeline
```

### Database Connection Error

```bash
# Test connection
make test-db

# Check PostgreSQL
docker-compose exec postgres pg_isready
```

### dbt Errors

```bash
# Test dbt connection
docker-compose exec pipeline dbt debug --profiles-dir /app/dbt_project

# Compile models
docker-compose exec pipeline dbt compile --profiles-dir /app/dbt_project
```

## File Structure

```
local/
├── docker-compose.yml          # Services definition
├── Dockerfile                  # Pipeline container
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template
├── Makefile                    # Helper commands
├── scripts/
│   ├── pipeline.py             # Main orchestrator
│   ├── ingest.py               # Bronze layer ingestion
│   ├── validate.py             # Custom validation
│   └── start_cron.sh           # Cron initialization
├── dbt_project/
│   ├── dbt_project.yml         # dbt configuration
│   ├── profiles.yml            # Database connection
│   ├── packages.yml            # dbt packages
│   └── models/
│       ├── bronze/             # Source definitions
│       └── silver/             # Transformations
└── logs/                       # Pipeline logs
```

## Next Steps

After mastering local pipeline:
1. Review `../aws/` for cloud deployment
2. Compare local patterns with AWS services
3. Deploy same pipeline to AWS RDS
