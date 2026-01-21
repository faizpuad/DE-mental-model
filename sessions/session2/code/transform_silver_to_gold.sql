-- Gold Layer: Transform Silver to Gold
-- Aggregates silver data into business-ready gold tables

-- 1. Populate fact_sales_monthly
INSERT INTO gold.fact_sales_monthly (
    year,
    month,
    total_revenue,
    total_quantity,
    total_transactions,
    total_products,
    total_countries,
    avg_revenue_per_transaction,
    avg_quantity_per_transaction,
    unique_customers,
    cancelled_transactions,
    cancelled_revenue
)
SELECT
    d.year,
    d.month,
    SUM(fsd.total_revenue) as total_revenue,
    SUM(fsd.total_quantity) as total_quantity,
    SUM(fsd.total_transactions) as total_transactions,
    COUNT(DISTINCT fsd.product_id) as total_products,
    COUNT(DISTINCT fsd.country) as total_countries,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_revenue_per_transaction,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_quantity_per_transaction,
    COUNT(DISTINCT NULLIF(fsd.customer_id, -1)) AS unique_customers,
    0 as cancelled_transactions,
    0.00 as cancelled_revenue
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY d.year, d.month
ON CONFLICT (year, month) DO UPDATE SET
    total_revenue = EXCLUDED.total_revenue,
    total_quantity = EXCLUDED.total_quantity,
    total_transactions = EXCLUDED.total_transactions,
    total_products = EXCLUDED.total_products,
    total_countries = EXCLUDED.total_countries,
    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
    unique_customers = EXCLUDED.unique_customers,
    updated_at = CURRENT_TIMESTAMP;

-- 2. Populate fact_product_performance
INSERT INTO gold.fact_product_performance (
    product_id,
    stock_code,
    description,
    category,
    total_revenue,
    total_quantity,
    total_transactions,
    total_days_sold,
    total_countries,
    avg_revenue_per_day,
    avg_quantity_per_day,
    avg_revenue_per_transaction,
    avg_quantity_per_transaction,
    first_sale_date,
    last_sale_date
)
SELECT
    dp.product_id,
    dp.stock_code,
    dp.description,
    dp.category,
    SUM(fsd.total_revenue) as total_revenue,
    SUM(fsd.total_quantity) as total_quantity,
    SUM(fsd.total_transactions) as total_transactions,
    COUNT(DISTINCT fsd.date_id) as total_days_sold,
    COUNT(DISTINCT fsd.country) as total_countries,
    CASE
        WHEN COUNT(DISTINCT fsd.date_id) > 0
        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / COUNT(DISTINCT fsd.date_id), 2)
        ELSE 0
    END as avg_revenue_per_day,
    CASE
        WHEN COUNT(DISTINCT fsd.date_id) > 0
        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / COUNT(DISTINCT fsd.date_id), 2)
        ELSE 0
    END as avg_quantity_per_day,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_revenue_per_transaction,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_quantity_per_transaction,
    MIN(d.date) as first_sale_date,
    MAX(d.date) as last_sale_date
FROM silver.fact_sales_daily fsd
JOIN silver.dim_product dp ON fsd.product_id = dp.product_id
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY dp.product_id, dp.stock_code, dp.description, dp.category
ON CONFLICT (product_id) DO UPDATE SET
    total_revenue = EXCLUDED.total_revenue,
    total_quantity = EXCLUDED.total_quantity,
    total_transactions = EXCLUDED.total_transactions,
    total_days_sold = EXCLUDED.total_days_sold,
    total_countries = EXCLUDED.total_countries,
    avg_revenue_per_day = EXCLUDED.avg_revenue_per_day,
    avg_quantity_per_day = EXCLUDED.avg_quantity_per_day,
    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
    first_sale_date = EXCLUDED.first_sale_date,
    last_sale_date = EXCLUDED.last_sale_date,
    updated_at = CURRENT_TIMESTAMP;

-- 3. Populate fact_country_sales
INSERT INTO gold.fact_country_sales (
    country,
    total_revenue,
    total_quantity,
    total_transactions,
    total_products,
    total_days_active,
    unique_customers,
    avg_revenue_per_transaction,
    avg_quantity_per_transaction,
    top_product_id,
    top_product_revenue,
    first_transaction_date,
    last_transaction_date
)
SELECT
    fsd.country,
    SUM(fsd.total_revenue) as total_revenue,
    SUM(fsd.total_quantity) as total_quantity,
    SUM(fsd.total_transactions) as total_transactions,
    COUNT(DISTINCT fsd.product_id) as total_products,
    COUNT(DISTINCT fsd.date_id) as total_days_active,
    COUNT(DISTINCT NULLIF(fsd.customer_id, -1)) AS unique_customers,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_revenue_per_transaction,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END as avg_quantity_per_transaction,
    (
        SELECT fsd2.product_id
        FROM silver.fact_sales_daily fsd2
        WHERE fsd2.country = fsd.country
        GROUP BY fsd2.product_id
        ORDER BY SUM(fsd2.total_revenue) DESC
        LIMIT 1
    ) as top_product_id,
    (
        SELECT SUM(fsd3.total_revenue)
        FROM silver.fact_sales_daily fsd3
        WHERE fsd3.country = fsd.country AND fsd3.product_id = (
            SELECT fsd2.product_id
            FROM silver.fact_sales_daily fsd2
            WHERE fsd2.country = fsd.country
            GROUP BY fsd2.product_id
            ORDER BY SUM(fsd2.total_revenue) DESC
            LIMIT 1
        )
    ) as top_product_revenue,
    MIN(d.date) as first_transaction_date,
    MAX(d.date) as last_transaction_date
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY fsd.country
ON CONFLICT (country) DO UPDATE SET
    total_revenue = EXCLUDED.total_revenue,
    total_quantity = EXCLUDED.total_quantity,
    total_transactions = EXCLUDED.total_transactions,
    total_products = EXCLUDED.total_products,
    total_days_active = EXCLUDED.total_days_active,
    unique_customers = EXCLUDED.unique_customers,
    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
    top_product_id = EXCLUDED.top_product_id,
    top_product_revenue = EXCLUDED.top_product_revenue,
    first_transaction_date = EXCLUDED.first_transaction_date,
    last_transaction_date = EXCLUDED.last_transaction_date,
    updated_at = CURRENT_TIMESTAMP;

-- 4. Populate fact_sales_daily_enhanced with trend analysis
INSERT INTO gold.fact_sales_daily_enhanced (
    date_id,
    date,
    year,
    month,
    day_of_week,
    day_of_month,
    quarter,
    week_of_year,
    is_weekend,
    total_revenue,
    total_quantity,
    total_transactions,
    total_products,
    total_countries,
    unique_customers,
    avg_revenue_per_transaction,
    avg_quantity_per_transaction,
    revenue_vs_previous_day,
    revenue_vs_previous_day_pct,
    quantity_vs_previous_day,
    quantity_vs_previous_day_pct,
    transactions_vs_previous_day,
    transactions_vs_previous_day_pct
)
SELECT
    fsd.date_id,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.day AS day_of_month,
    d.quarter,
    EXTRACT(WEEK FROM d.date)::INTEGER AS week_of_year,
    d.is_weekend,
    SUM(fsd.total_revenue) AS total_revenue,
    SUM(fsd.total_quantity) AS total_quantity,
    SUM(fsd.total_transactions) AS total_transactions,
    COUNT(DISTINCT fsd.product_id) AS total_products,
    COUNT(DISTINCT fsd.country) AS total_countries,
    COUNT(DISTINCT NULLIF(fsd.customer_id, -1)) AS unique_customers,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_revenue)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END AS avg_revenue_per_transaction,
    CASE
        WHEN SUM(fsd.total_transactions) > 0
        THEN ROUND(SUM(fsd.total_quantity)::NUMERIC / SUM(fsd.total_transactions), 2)
        ELSE 0
    END AS avg_quantity_per_transaction,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL,
    NULL
FROM silver.fact_sales_daily fsd
JOIN silver.dim_date d ON fsd.date_id = d.date_id
GROUP BY
    fsd.date_id,
    d.date,
    d.year,
    d.month,
    d.day_of_week,
    d.day,
    d.quarter,
    d.is_weekend
ON CONFLICT (date_id) DO UPDATE SET
    total_revenue = EXCLUDED.total_revenue,
    total_quantity = EXCLUDED.total_quantity,
    total_transactions = EXCLUDED.total_transactions,
    total_products = EXCLUDED.total_products,
    total_countries = EXCLUDED.total_countries,
    unique_customers = EXCLUDED.unique_customers,
    avg_revenue_per_transaction = EXCLUDED.avg_revenue_per_transaction,
    avg_quantity_per_transaction = EXCLUDED.avg_quantity_per_transaction,
    updated_at = CURRENT_TIMESTAMP;

-- 5. Update trend metrics for fact_sales_daily_enhanced
UPDATE gold.fact_sales_daily_enhanced current
SET
    revenue_vs_previous_day = current.total_revenue - prev.total_revenue,
    revenue_vs_previous_day_pct = CASE
        WHEN prev.total_revenue > 0
        THEN ROUND(((current.total_revenue - prev.total_revenue) * 100.0 / prev.total_revenue), 2)
        ELSE NULL
    END,
    quantity_vs_previous_day = current.total_quantity - prev.total_quantity,
    quantity_vs_previous_day_pct = CASE
        WHEN prev.total_quantity > 0
        THEN ROUND(((current.total_quantity - prev.total_quantity) * 100.0 / prev.total_quantity), 2)
        ELSE NULL
    END,
    transactions_vs_previous_day = current.total_transactions - prev.total_transactions,
    transactions_vs_previous_day_pct = CASE
        WHEN prev.total_transactions > 0
        THEN ROUND(((current.total_transactions - prev.total_transactions) * 100.0 / prev.total_transactions), 2)
        ELSE NULL
    END
FROM gold.fact_sales_daily_enhanced prev
WHERE prev.date_id = (
    SELECT fsd.date_id
    FROM silver.fact_sales_daily fsd
    JOIN silver.dim_date d ON fsd.date_id = d.date_id
    WHERE d.date < (SELECT d2.date FROM silver.dim_date d2 WHERE d2.date_id = current.date_id)
    ORDER BY d.date DESC
    LIMIT 1
);
