-- Gold Layer: Monthly Sales Summary
-- Aggregated metrics for monthly reporting
-- Optimized for BI dashboards and monthly trend analysis

CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.fact_sales_monthly;

CREATE TABLE gold.fact_sales_monthly (
    id BIGSERIAL PRIMARY KEY,

    year INTEGER NOT NULL,
    month INTEGER NOT NULL,

    total_revenue NUMERIC(15, 2) NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_products INTEGER NOT NULL,
    total_countries INTEGER NOT NULL,

    avg_revenue_per_transaction NUMERIC(15, 2),
    avg_quantity_per_transaction NUMERIC(10, 2),

    unique_customers INTEGER NOT NULL,

    cancelled_transactions INTEGER DEFAULT 0,
    cancelled_revenue NUMERIC(15, 2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_fact_sales_monthly_year_month UNIQUE (year, month)
);

CREATE INDEX idx_fsm_year_month ON gold.fact_sales_monthly (year DESC, month);
CREATE INDEX idx_fsm_revenue ON gold.fact_sales_monthly (total_revenue DESC);

-- Add comment for documentation
COMMENT ON TABLE gold.fact_sales_monthly IS 'Monthly aggregated sales metrics for reporting and analytics';
COMMENT ON COLUMN gold.fact_sales_monthly.year IS 'Sales year';
COMMENT ON COLUMN gold.fact_sales_monthly.month IS 'Sales month (1-12)';
COMMENT ON COLUMN gold.fact_sales_monthly.total_revenue IS 'Total revenue for the month';
COMMENT ON COLUMN gold.fact_sales_monthly.total_quantity IS 'Total quantity sold for the month';
COMMENT ON COLUMN gold.fact_sales_monthly.total_transactions IS 'Total number of transactions for the month';
COMMENT ON COLUMN gold.fact_sales_monthly.total_products IS 'Number of unique products sold';
COMMENT ON COLUMN gold.fact_sales_monthly.total_countries IS 'Number of countries with sales';
COMMENT ON COLUMN gold.fact_sales_monthly.avg_revenue_per_transaction IS 'Average revenue per transaction';
COMMENT ON COLUMN gold.fact_sales_monthly.avg_quantity_per_transaction IS 'Average quantity per transaction';
COMMENT ON COLUMN gold.fact_sales_monthly.unique_customers IS 'Number of unique customers';
COMMENT ON COLUMN gold.fact_sales_monthly.cancelled_transactions IS 'Number of cancelled transactions';
COMMENT ON COLUMN gold.fact_sales_monthly.cancelled_revenue IS 'Revenue from cancelled transactions';
