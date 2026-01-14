-- Product Dimension Table
-- Purpose: Provide product attributes for analytics
-- Grain: One row per unique product

DROP TABLE IF EXISTS silver.dim_product;

CREATE TABLE silver.dim_product (
    product_id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    description VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_code)
);

CREATE INDEX idx_dim_product_stock_code ON silver.dim_product(stock_code);
CREATE INDEX idx_dim_product_category ON silver.dim_product(category);
