-- Gold Layer: Daily Sales Summary
-- Enhanced daily metrics with calculated indicators
-- Optimized for day-to-day monitoring and KPI tracking

DROP TABLE IF EXISTS gold.fact_sales_daily_enhanced;

CREATE TABLE gold.fact_sales_daily_enhanced (
    id BIGSERIAL PRIMARY KEY,
    date_id INTEGER NOT NULL,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_of_month INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL,
    is_weekend BOOLEAN DEFAULT FALSE,
    is_holiday BOOLEAN DEFAULT FALSE,
    total_revenue NUMERIC(15, 2) NOT NULL,
    total_quantity INTEGER NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_products INTEGER NOT NULL,
    total_countries INTEGER NOT NULL,
    unique_customers INTEGER NOT NULL,
    avg_revenue_per_transaction NUMERIC(15, 2),
    avg_quantity_per_transaction NUMERIC(10, 2),
    revenue_vs_previous_day NUMERIC(15, 2),
    revenue_vs_previous_day_pct NUMERIC(5, 2),
    quantity_vs_previous_day INTEGER,
    quantity_vs_previous_day_pct NUMERIC(5, 2),
    transactions_vs_previous_day INTEGER,
    transactions_vs_previous_day_pct NUMERIC(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sales_daily_enhanced_date FOREIGN KEY (date_id) REFERENCES silver.dim_date(date_id),
    CONSTRAINT unique_date UNIQUE (date_id)
);

CREATE INDEX idx_fact_sales_daily_enhanced_date_id ON gold.fact_sales_daily_enhanced(date_id);
CREATE INDEX idx_fact_sales_daily_enhanced_date ON gold.fact_sales_daily_enhanced(date DESC);
CREATE INDEX idx_fact_sales_daily_enhanced_year_month ON gold.fact_sales_daily_enhanced(year DESC, month);
CREATE INDEX idx_fact_sales_daily_enhanced_quarter ON gold.fact_sales_daily_enhanced(year DESC, quarter);
CREATE INDEX idx_fact_sales_daily_enhanced_day_of_week ON gold.fact_sales_daily_enhanced(day_of_week);
CREATE INDEX idx_fact_sales_daily_enhanced_revenue ON gold.fact_sales_daily_enhanced(total_revenue DESC);
CREATE INDEX idx_fact_sales_daily_enhanced_is_weekend ON gold.fact_sales_daily_enhanced(is_weekend);

COMMENT ON TABLE gold.fact_sales_daily_enhanced IS 'Enhanced daily sales metrics with trend analysis indicators';
COMMENT ON COLUMN gold.fact_sales_daily_enhanced.revenue_vs_previous_day_pct IS 'Revenue change compared to previous day in percentage';
COMMENT ON COLUMN gold.fact_sales_daily_enhanced.is_weekend IS 'Whether the day is a weekend (Saturday or Sunday)';
