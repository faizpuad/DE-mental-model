-- Gold Layer: Product Performance Summary
-- Aggregated metrics by product for analysis
-- Optimized for product-level reporting and performance analysis

DROP TABLE IF EXISTS gold.fact_product_performance;

CREATE TABLE gold.fact_product_performance (
    id BIGSERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    stock_code VARCHAR(50) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    total_revenue NUMERIC(15, 2) NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_days_sold INTEGER NOT NULL,
    total_countries INTEGER NOT NULL,
    avg_revenue_per_day NUMERIC(15, 2),
    avg_quantity_per_day NUMERIC(10, 2),
    avg_revenue_per_transaction NUMERIC(15, 2),
    avg_quantity_per_transaction NUMERIC(10, 2),
    first_sale_date DATE,
    last_sale_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_product_performance_product FOREIGN KEY (product_id) REFERENCES silver.dim_product(product_id)
);

CREATE INDEX idx_fact_product_performance_product_id ON gold.fact_product_performance(product_id);
CREATE INDEX idx_fact_product_performance_stock_code ON gold.fact_product_performance(stock_code);
CREATE INDEX idx_fact_product_performance_revenue ON gold.fact_product_performance(total_revenue DESC);
CREATE INDEX idx_fact_product_performance_category ON gold.fact_product_performance(category);
CREATE INDEX idx_fact_product_performance_quantity ON gold.fact_product_performance(total_quantity DESC);

COMMENT ON TABLE gold.fact_product_performance IS 'Aggregated product-level metrics for performance analysis';
COMMENT ON COLUMN gold.fact_product_performance.total_revenue IS 'Total revenue across all time';
COMMENT ON COLUMN gold.fact_product_performance.total_quantity IS 'Total quantity sold';
COMMENT ON COLUMN gold.fact_product_performance.total_transactions IS 'Total number of transactions';
COMMENT ON COLUMN gold.fact_product_performance.total_days_sold IS 'Number of days with sales';
COMMENT ON COLUMN gold.fact_product_performance.total_countries IS 'Number of countries sold to';
