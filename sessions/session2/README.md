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

Note: This will start postgres, superset, and related services. Ensure session1's postgres is running separately if using that database.

## Environment Variables

Create a `.env` file in session2 directory:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_db
DB_USER=postgres
DB_PASSWORD=postgres
```

### Superset Environment Variables (Optional)

Create a `.env.superset` file for Superset configuration:

```bash
SUPERSET_SECRET_KEY=change_this_to_a_random_secret_key_at_least_32_characters_long
REDIS_PASSWORD=redispass
```

Copy from example:
```bash
cp .env.superset.example .env.superset
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

### Step 4: Create Gold Layer

The gold layer contains business-ready aggregated metrics optimized for BI dashboards.

#### Using Python

```bash
cd sessions/session2
source .venv/bin/activate
python code/transform_gold.py

# Optional: DRY RUN mode
DRY_RUN=true python code/transform_gold.py
```

#### Using Docker

```bash
cd sessions/session2
docker compose \
  -f ../session1/docker-compose.yml \
  -f ./docker-compose.yml \
  run transform python code/transform_gold.py
```

### Step 5: Verify Gold Layer Results

Connect to PostgreSQL and verify the gold layer tables:

```bash
psql -h localhost -U postgres -d retail_db

# List tables in gold schema
\dt gold.*

# Verify monthly sales summary
SELECT * FROM gold.fact_sales_monthly ORDER BY year DESC, month DESC LIMIT 10;

# Verify product performance
SELECT
    stock_code,
    description,
    total_revenue,
    total_quantity,
    total_transactions
FROM gold.fact_product_performance
ORDER BY total_revenue DESC
LIMIT 10;

# Verify country sales
SELECT
    country,
    total_revenue,
    total_quantity,
    total_transactions
FROM gold.fact_country_sales
ORDER BY total_revenue DESC
LIMIT 10;

# Verify enhanced daily metrics with trend analysis
SELECT
    date,
    total_revenue,
    revenue_vs_previous_day,
    revenue_vs_previous_day_pct,
    is_weekend
FROM gold.fact_sales_daily_enhanced
ORDER BY date DESC
LIMIT 10;
```

### Step 6: Verify Silver Layer Results

```bash
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
│   ├── transform_bronze_to_silver.sql  # Bronze to Silver transformation
│   ├── transform.py          # Python script for Bronze to Silver
│   ├── fact_sales_monthly.sql          # Gold: Monthly sales summary schema
│   ├── fact_product_performance.sql    # Gold: Product performance schema
│   ├── fact_country_sales.sql          # Gold: Country sales summary schema
│   ├── fact_sales_daily_enhanced.sql   # Gold: Enhanced daily metrics schema
│   ├── transform_silver_to_gold.sql    # Silver to Gold transformation
│   └── transform_gold.py    # Python script for Silver to Gold
├── tests/
│   ├── __init__.py
│   └── test_transform.py     # Pytest test cases
├── docker/
│   └── Dockerfile            # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── Notes.md                  # Theoretical concepts (OLTP/OLAP, Star Schema, Gold Layer)
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

### Gold Layer Metrics

**fact_sales_monthly** (Monthly Aggregations):
- **total_revenue**: Total revenue for the month
- **total_quantity**: Total quantity sold
- **total_transactions**: Total number of transactions
- **total_products**: Number of unique products sold
- **total_countries**: Number of countries with sales
- **avg_revenue_per_transaction**: Average revenue per transaction
- **avg_quantity_per_transaction**: Average quantity per transaction
- **unique_customers**: Number of unique customers

**fact_product_performance** (Product-Level Metrics):
- **total_revenue**: Lifetime revenue for the product
- **total_quantity**: Total quantity sold
- **total_transactions**: Total number of transactions
- **total_days_sold**: Number of days with sales
- **total_countries**: Number of countries sold to
- **avg_revenue_per_day**: Average daily revenue
- **avg_quantity_per_day**: Average daily quantity
- **first_sale_date**: First date product was sold
- **last_sale_date**: Last date product was sold

**fact_country_sales** (Country-Level Metrics):
- **total_revenue**: Total revenue by country
- **total_quantity**: Total quantity sold by country
- **total_transactions**: Total transactions by country
- **total_products**: Number of unique products sold
- **total_days_active**: Number of days with sales
- **unique_customers**: Number of unique customers
- **top_product_id**: Best-selling product ID
- **top_product_revenue**: Revenue of best-selling product

**fact_sales_daily_enhanced** (Daily Metrics with Trends):
- All daily metrics from silver.fact_sales_daily
- **revenue_vs_previous_day**: Revenue change vs previous day
- **revenue_vs_previous_day_pct**: Revenue change percentage vs previous day
- **quantity_vs_previous_day**: Quantity change vs previous day
- **quantity_vs_previous_day_pct**: Quantity change percentage vs previous day
- **transactions_vs_previous_day**: Transactions change vs previous day
- **transactions_vs_previous_day_pct**: Transactions change percentage vs previous day
- **is_weekend**: Whether the day is a weekend
- **day_of_week**: Day of week (1-7)
- **quarter**: Quarter (1-4)

## Query Examples

### Gold Layer Queries

**Monthly Revenue Trend:**
```sql
SELECT
    year,
    month,
    total_revenue,
    total_quantity,
    total_transactions,
    avg_revenue_per_transaction
FROM gold.fact_sales_monthly
ORDER BY year DESC, month DESC;
```

**Top 10 Products by Revenue:**
```sql
SELECT
    stock_code,
    description,
    category,
    total_revenue,
    total_quantity,
    total_transactions,
    avg_revenue_per_transaction
FROM gold.fact_product_performance
ORDER BY total_revenue DESC
LIMIT 10;
```

**Revenue by Country:**
```sql
SELECT
    country,
    total_revenue,
    total_quantity,
    total_transactions,
    avg_revenue_per_transaction
FROM gold.fact_country_sales
ORDER BY total_revenue DESC;
```

**Daily Revenue with Trend Analysis:**
```sql
SELECT
    date,
    day_of_week,
    is_weekend,
    total_revenue,
    revenue_vs_previous_day,
    revenue_vs_previous_day_pct
FROM gold.fact_sales_daily_enhanced
ORDER BY date DESC
LIMIT 30;
```

**Weekday vs Weekend Analysis:**
```sql
SELECT
    d.day_of_week,
    d.day_name,
    COUNT(*) as days,
    SUM(fsd.total_revenue) as total_revenue,
    AVG(fsd.total_revenue) as avg_daily_revenue,
    SUM(fsd.total_transactions) as total_transactions
FROM gold.fact_sales_daily_enhanced fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY d.day_of_week, d.day_name
ORDER BY d.day_of_week;
```

### Silver Layer Queries

**Top 10 Products by Revenue:**
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

**Daily Revenue Trend:**
```sql
SELECT
    d.date,
    SUM(fsd.total_revenue) as daily_revenue
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY d.date
ORDER BY d.date;
```

**Revenue by Country:**
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

## Data Visualization with Apache Superset

### Overview

Apache Superset is an open-source business intelligence web application that provides data exploration and visualization capabilities. This section shows how to run Superset and connect it to your PostgreSQL database.

### Start Superset

Using Docker Compose:

```bash
cd sessions/session2
docker-compose up -d superset
```

This will:
- Start Superset web server
- Start Redis for caching
- Start Celery workers for async queries
- Initialize the database

### Access Superset

1. Open browser to: `http://localhost:8088`
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
3. Change password on first login

### Connect to PostgreSQL

1. Go to **Data > Databases**
2. Click **+ Database**
3. Fill in connection details:
   - Display Name: `Retail DB`
   - SQLAlchemy URI: `postgresql://postgres:postgres@postgres:5432/retail_db`
   - Click **Test Connection**
   - Click **Connect**

4. Go to **Data > Datasets**
5. Click **+ Dataset**
6. Select **Retail DB** database
7. Select schema `gold`
8. Select table `fact_sales_monthly`
9. Click **Add**

Repeat for other tables: `fact_product_performance`, `fact_country_sales`, `fact_sales_daily_enhanced`

### Create Charts

**Monthly Revenue Chart:**
1. Click **+ Chart**
2. Select Dataset: `fact_sales_monthly`
3. Chart Type: **Line Chart**
4. X-Axis: `year`, `month`
5. Metrics: `total_revenue`
6. Time Range: Last 1 Year
7. Click **Update Chart**

**Top Products by Revenue:**
1. Click **+ Chart**
2. Select Dataset: `fact_product_performance`
3. Chart Type: **Bar Chart**
4. X-Axis: `description`
5. Metrics: `total_revenue`
6. Sort by: `total_revenue` descending
7. Limit to: 10
8. Click **Update Chart**

**Revenue by Country:**
1. Click **+ Chart**
2. Select Dataset: `fact_country_sales`
3. Chart Type: **World Map** or **Pie Chart**
4. Dimension: `country`
5. Metric: `total_revenue`
6. Click **Update Chart**

**Daily Revenue Trend:**
1. Click **+ Chart**
2. Select Dataset: `fact_sales_daily_enhanced`
3. Chart Type: **Line Chart**
4. X-Axis: `date`
5. Metrics: `total_revenue`
6. Metrics: `revenue_vs_previous_day_pct`
7. Click **Update Chart**

### Create Dashboard

1. Click **+ Dashboard**
2. Name: `Retail Analytics Dashboard`
3. Click **Save**
4. Click **Edit Dashboard**
5. Drag and drop charts onto dashboard
6. Resize and arrange as needed
7. Click **Save**

### Useful SQL Lab

Superset provides SQL Lab for writing custom queries:

1. Go to **SQL Lab**
2. Select Database: `Retail DB`
3. Select Schema: `gold`
4. Write query:

```sql
SELECT
    d.month_name,
    d.year,
    SUM(fsm.total_revenue) as monthly_revenue,
    SUM(fsm.total_quantity) as monthly_quantity
FROM gold.fact_sales_monthly fsm
JOIN silver.dim_date d ON fsm.month = d.month AND fsm.year = d.year
GROUP BY d.year, d.month, d.month_name
ORDER BY d.year, d.month;
```

5. Click **Run** to execute
6. Click **Visualize** to create chart from query

### Stop Superset

```bash
cd sessions/session2
docker-compose down
```

### Troubleshooting Superset

**Superset not accessible:**
```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs superset
```

**Database connection error:**
```bash
# Check postgres is accessible from superset
docker-compose exec superset ping -c 3 postgres
```

**Reset Superset:**
```bash
docker-compose down -v
docker-compose up -d
```

### Superset Features to Explore

- **Charts**: 50+ visualization types
- **Dashboards**: Interactive, filterable dashboards
- **SQL Lab**: Custom SQL query editor
- **Explore UI**: Drag-and-drop chart builder
- **Caching**: Redis caching for fast queries
- **Async Queries**: Celery for long-running queries
- **Row Level Security**: Control data access
- **Export**: Export to CSV, Excel, images

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
- Create visualizations in Apache Superset
- Build custom charts and dashboards
- Move to Session 3: Reliability & Business Logic

## References

- [Star Schema - Databricks](https://www.databricks.com/glossary/star-schema)
- [OLTP vs OLAP - AWS](https://docs.aws.amazon.com/redshift/latest/dg/c_what_is_data_warehouse.html)
- [PostgreSQL Indexing](https://www.postgresql.org/docs/current/indexes.html)
