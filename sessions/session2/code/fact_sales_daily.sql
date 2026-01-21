-- Sales Daily Fact Table
-- Purpose: Store aggregated daily sales metrics
-- Grain: One row per day, product, and country

DROP TABLE IF EXISTS silver.fact_sales_daily;

CREATE TABLE silver.fact_sales_daily (
    id SERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    country VARCHAR(100) NOT NULL,
    customer_id INTEGER,
    total_transactions INTEGER NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_revenue DECIMAL(15,2) NOT NULL,
    avg_unit_price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_id) REFERENCES silver.dim_date(date_id),
    FOREIGN KEY (product_id) REFERENCES silver.dim_product(product_id),
    UNIQUE(date_id, product_id, country)
);

-- Indexes for query performance
CREATE INDEX idx_fact_sales_daily_date_id ON silver.fact_sales_daily(date_id);
CREATE INDEX idx_fact_sales_daily_product_id ON silver.fact_sales_daily(product_id);
CREATE INDEX idx_fact_sales_daily_country ON silver.fact_sales_daily(country);
CREATE INDEX idx_fact_sales_daily_customer_id ON silver.fact_sales_daily(customer_id);
CREATE INDEX idx_fact_sales_daily_date_country ON silver.fact_sales_daily(date_id, country);
CREATE INDEX idx_fact_sales_daily_revenue ON silver.fact_sales_daily(total_revenue DESC);

-- Partition by date_id (range partitioning)
-- Note: This is implemented in PostgreSQL using declarative partitioning
-- Uncomment following section if you want to enable partitioning:

-- CREATE TABLE silver.fact_sales_daily_y2024 PARTITION OF silver.fact_sales_daily
--     FOR VALUES FROM (20240101) TO (20250101);
