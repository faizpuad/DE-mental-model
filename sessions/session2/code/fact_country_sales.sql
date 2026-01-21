-- Gold Layer: Country Sales Summary
-- Aggregated metrics by country for regional analysis
-- Optimized for geographical reporting and market analysis

DROP TABLE IF EXISTS gold.fact_country_sales;

CREATE TABLE gold.fact_country_sales (
    id BIGSERIAL PRIMARY KEY,

    country VARCHAR(100) NOT NULL,

    total_revenue NUMERIC(15, 2) NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_products INTEGER NOT NULL,
    total_days_active INTEGER NOT NULL,

    unique_customers INTEGER NOT NULL,

    avg_revenue_per_transaction NUMERIC(15, 2),
    avg_quantity_per_transaction NUMERIC(10, 2),

    top_product_id INTEGER,
    top_product_revenue NUMERIC(15, 2),

    first_transaction_date DATE,
    last_transaction_date DATE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_fact_country_sales_country UNIQUE (country)
);

CREATE INDEX idx_fcs_revenue ON gold.fact_country_sales (total_revenue DESC);

COMMENT ON TABLE gold.fact_country_sales IS 'Aggregated country-level metrics for regional analysis';
COMMENT ON COLUMN gold.fact_country_sales.top_product_id IS 'ID of the best-selling product';
COMMENT ON COLUMN gold.fact_country_sales.top_product_revenue IS 'Revenue of the best-selling product';
