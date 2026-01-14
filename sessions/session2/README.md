# Session 2: Data Modeling & Analytics

## Overview

Session 2 focuses on transforming raw OLTP data into an analytics-ready OLAP star schema. You will learn about data modeling fundamentals, star schema design, and implementing daily sales aggregations.

## Prerequisites

- Completed Session 1 (Data ingestion and raw_transactions table populated)
- Python 3.11 or higher
- PostgreSQL 15 or higher
- Docker and Docker Compose (optional but recommended)

## Learning Objectives

- Understand OLTP vs OLAP data models
- Learn ER (Entity Relationship) model fundamentals
- Design and implement Star Schema for analytics
- Understand Medallion Architecture (Bronze → Silver → Gold)
- Create dimension tables (dim_date, dim_product)
- Build fact_sales_daily table with daily metrics
- Add indexes and partitioning for query optimization

## Setup

### Option 1: Using uv (Recommended)

```bash
cd sessions/session2
uv venv
source .venv/bin/activate
uv pip install -r requirement.txt
```

### Option 2: Using pip

```bash
cd sessions/session2
python -m venv .venv
source .venv/bin/activate
pip install -r requirement.txt
```

### Option 3: Using Docker Compose

```bash
cd sessions/session2
docker-compose up -d
```

## Environment Variables

Create a `.env` file in the session2 directory:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_db
DB_USER=postgres
DB_PASSWORD=postgres
```

## Run Instructions

### Step 1: Verify Session 1 Data

Ensure that you have completed Session 1 and have the `bronze.raw_transactions` table populated:

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d retail_db

# Check if bronze schema and raw_transactions table exist
\dt bronze.*

# Verify data exists
SELECT COUNT(*) FROM bronze.raw_transactions;
```

### Step 2: Run Transformation

*Note:* Ensure previous docker postgres from session1 is running and has bronze schema and data populated.
```bash
docker-compose -f ../session1/docker-compose.yml up -d postgres
```

#### Using Python

```bash
cd sessions/session2
source .venv/bin/activate
python code/transform.py

# optional to DRY RUN mode
# run query without actual insert data
DRY_RUN=true python code/transform.py
```

#### Using Docker

```bash
cd sessions/session2
docker compose \
  -f ../session1/docker-compose.yml \
  -f ./docker-compose.yml \
  up -d postgres transform
```

### Step 3: Run Tests

#### Using pytest

```bash
cd sessions/session2
source .venv/bin/activate
pytest tests/ -v --cov=code --cov-report=html
```

#### Using Docker

```bash
cd sessions/session2
docker-compose run transform python -m pytest tests/ -v --cov=code --cov-report=html
```

### Step 4: Verify Results

Connect to PostgreSQL and verify the tables:

```bash
psql -h localhost -U postgres -d retail_db

# List tables in silver schema
\dt silver.*

# Check dim_date data
SELECT * FROM silver.dim_date LIMIT 10;

# Check dim_product data
SELECT * FROM silver.dim_product LIMIT 10;

# Check fact_sales_daily data
SELECT * FROM silver.fact_sales_daily LIMIT 10;

# Verify aggregations
SELECT 
    d.date,
    SUM(fsd.total_revenue) as daily_revenue,
    SUM(fsd.total_quantity) as daily_quantity,
    SUM(fsd.total_transactions) as daily_transactions
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY d.date
ORDER BY d.date DESC
LIMIT 10;
```

## File Structure

```
sessions/session2/
├── requirement.txt           # Python dependencies
├── code/
│   ├── dim_date.sql          # Date dimension table schema
│   ├── dim_product.sql       # Product dimension table schema
│   ├── fact_sales_daily.sql  # Sales daily fact table schema
│   ├── transform_bronze_to_silver.sql  # Data transformation logic
│   └── transform.py          # Python script to execute SQL
├── tests/
│   ├── __init__.py
│   └── test_transform.py     # Pytest test cases
├── docker/
│   └── Dockerfile           # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── Notes.md                  # Theoretical concepts (OLTP/OLAP, Star Schema)
└── README.md                 # This file
```

## Data Model

### Star Schema

```
                    ┌─────────────────┐
                    │   dim_date      │
                    │                 │
                    │ - date_id (PK)  │
                    │ - date          │
                    │ - day, month... │
                    └────────┬────────┘
                             │
                             │
                    ┌────────┴────────┐
                    │fact_sales_daily │
                    │                 │
                    │ - id (PK)       │
                    │ - date_id (FK)  │
                    │ - product_id(FK)│
                    │ - country       │
                    │ - total_revenue │
                    │ - total_qty     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │  dim_product    │
                    │                 │
                    │ - product_id(PK)│
                    │ - stock_code    │
                    │ - description   │
                    │ - category      │
                    └─────────────────┘
```

### Metrics

The `fact_sales_daily` table contains:
- **total_transactions**: Number of unique invoices per day/product/country
- **total_quantity**: Sum of quantities sold per day/product/country
- **total_revenue**: Sum of revenue (quantity × unit_price) per day/product/country
- **avg_unit_price**: Average unit price per day/product/country

## Query Examples

### Top 10 Products by Revenue

```sql
SELECT 
    dp.description,
    SUM(fsd.total_revenue) as total_revenue,
    SUM(fsd.total_quantity) as total_quantity
FROM silver.fact_sales_daily fsd
JOIN silver.dim_product dp ON fsd.product_id = dp.product_id
GROUP BY dp.description
ORDER BY total_revenue DESC
LIMIT 10;
```

### Daily Revenue Trend

```sql
SELECT 
    d.date,
    SUM(fsd.total_revenue) as daily_revenue
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY d.date
ORDER BY d.date;
```

### Revenue by Country

```sql
SELECT 
    fsd.country,
    SUM(fsd.total_revenue) as total_revenue,
    COUNT(DISTINCT fsd.date_id) as active_days
FROM silver.fact_sales_daily fsd
GROUP BY fsd.country
ORDER BY total_revenue DESC;
```

## Performance Optimization

### Indexes

The following indexes have been created for query performance:
- `idx_fact_sales_daily_date_id` on date_id
- `idx_fact_sales_daily_product_id` on product_id
- `idx_fact_sales_daily_country` on country
- `idx_fact_sales_daily_date_country` on (date_id, country)
- `idx_fact_sales_daily_revenue` on total_revenue (descending)

### Partitioning

The `fact_sales_daily` table is designed for date-based partitioning. To enable partitioning, uncomment the partition definition in `fact_sales_daily.sql` and create partitions for specific date ranges.

## Troubleshooting

### Connection Issues

```bash
# Check if PostgreSQL is running
ps aux | grep postgres

# Test connection
psql -h localhost -U postgres -d retail_db -c "SELECT 1;"
```

### Missing Data

```bash
# Verify raw_transactions has data
psql -h localhost -U postgres -d retail_db -c "SELECT COUNT(*) FROM bronze.raw_transactions;"

# If empty, run Session 1 ingestion first
```

### Test Failures

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Check test coverage report
open htmlcov/index.html
```

## Next Steps

After completing Session 2:
- Review the `Notes.md` file for theoretical concepts
- Experiment with different queries on the star schema
- Move to Session 3: Reliability & Business Logic

## References

- [Star Schema - Databricks](https://www.databricks.com/glossary/star-schema)
- [OLTP vs OLAP - AWS](https://docs.aws.amazon.com/redshift/latest/dg/c_what_is_data_warehouse.html)
- [PostgreSQL Indexing](https://www.postgresql.org/docs/current/indexes.html)
