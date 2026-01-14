-- Date Dimension Table
-- Purpose: Provide time-based attributes for analytics
-- Grain: One row per date

DROP TABLE IF EXISTS silver.dim_date;

CREATE TABLE silver.dim_date (
    date_id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    day INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    day_of_week INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    quarter INTEGER NOT NULL,
    year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date)
);

CREATE INDEX idx_dim_date_date ON silver.dim_date(date);
CREATE INDEX idx_dim_date_year_month ON silver.dim_date(year, month);
