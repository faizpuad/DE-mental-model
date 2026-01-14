-- Data Transformation: Bronze to Silver
-- Purpose: Transform raw OLTP data to OLAP star schema
-- This script:
-- 1. Populates dim_date
-- 2. Populates dim_product
-- 3. Populates fact_sales_daily with aggregated metrics

-- Step 1: Populate dim_date from bronze.raw_transactions
INSERT INTO silver.dim_date (date_id, date, day, day_name, day_of_week, month, month_name, quarter, year, is_weekend)
SELECT DISTINCT
    EXTRACT(YEAR FROM invoicedate) * 10000 + EXTRACT(MONTH FROM invoicedate) * 100 + EXTRACT(DAY FROM invoicedate)::INTEGER as date_id,
    CAST(invoicedate AS DATE) as date,
    EXTRACT(DAY FROM invoicedate)::INTEGER as day,
    TO_CHAR(CAST(invoicedate AS DATE), 'Day') as day_name,
    EXTRACT(DOW FROM invoicedate)::INTEGER as day_of_week,
    EXTRACT(MONTH FROM invoicedate)::INTEGER as month,
    TO_CHAR(CAST(invoicedate AS DATE), 'Month') as month_name,
    EXTRACT(QUARTER FROM invoicedate)::INTEGER as quarter,
    EXTRACT(YEAR FROM invoicedate)::INTEGER as year,
    CASE
        WHEN EXTRACT(DOW FROM invoicedate) IN (0, 6) THEN TRUE
        ELSE FALSE
    END as is_weekend
FROM bronze.raw_transactions
ON CONFLICT (date) DO NOTHING;

-- Step 2: Populate dim_product from bronze.raw_transactions
INSERT INTO silver.dim_product (stock_code, description, category)
SELECT DISTINCT
    stockcode,
    description,
    CASE
        WHEN stockcode LIKE 'DISC%' THEN 'Discount'
        WHEN stockcode LIKE 'M%' THEN 'Manual'
        WHEN stockcode LIKE 'POST%' THEN 'Postage'
        WHEN stockcode LIKE 'C2%' THEN 'Carriage'
        WHEN stockcode LIKE 'BANK%' THEN 'Bank Charges'
        WHEN stockcode LIKE 'TEST%' THEN 'Test'
        WHEN stockcode LIKE 'PADS%' THEN 'Pads'
        ELSE 'General'
    END as category
FROM bronze.raw_transactions
WHERE description IS NOT NULL
    AND stockcode IS NOT NULL
ON CONFLICT (stock_code) DO NOTHING;

-- Step 3: Populate fact_sales_daily with daily aggregations
INSERT INTO silver.fact_sales_daily (date_id, product_id, country, total_transactions, total_quantity, total_revenue, avg_unit_price)
SELECT
    d.date_id,
    p.product_id,
    r.country,
    COUNT(DISTINCT r.invoiceno) as total_transactions,
    SUM(r.quantity) as total_quantity,
    SUM(r.quantity * r.unitprice) as total_revenue,
    AVG(r.unitprice) as avg_unit_price
FROM bronze.raw_transactions r
JOIN silver.dim_date d ON CAST(r.invoicedate AS DATE) = d.date
JOIN silver.dim_product p ON r.stockcode = p.stock_code
WHERE r.quantity > 0
    AND r.unitprice >= 0
    AND r.country IS NOT NULL
GROUP BY d.date_id, p.product_id, r.country
ON CONFLICT (date_id, product_id, country) DO UPDATE SET
    total_transactions = EXCLUDED.total_transactions,
    total_quantity = EXCLUDED.total_quantity,
    total_revenue = EXCLUDED.total_revenue,
    avg_unit_price = EXCLUDED.avg_unit_price,
    updated_at = CURRENT_TIMESTAMP;
