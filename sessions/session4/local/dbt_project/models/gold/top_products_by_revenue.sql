-- Top 100 products by revenue
-- Gold layer: optimized for product performance analysis

{{ config(
    materialized='table',
    tags=['gold', 'business', 'products']
) }}

WITH product_revenue AS (
    SELECT
        p.stock_code,
        p.description,
        p.category,
        SUM(f.total_revenue) AS total_revenue,
        SUM(f.total_quantity) AS total_quantity,
        SUM(f.total_transactions) AS total_transactions,
        COUNT(DISTINCT f.date_id) AS days_sold,
        COUNT(DISTINCT f.country) AS countries_sold_in
    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_product') }} p ON f.product_id = p.product_id
    GROUP BY p.stock_code, p.description, p.category
)

SELECT
    stock_code,
    description,
    category,
    ROUND(total_revenue::NUMERIC, 2) AS total_revenue,
    total_quantity,
    total_transactions,
    days_sold,
    countries_sold_in,
    ROUND((total_revenue / NULLIF(total_quantity, 0))::NUMERIC, 2) AS avg_revenue_per_unit,
    CURRENT_TIMESTAMP AS created_at
FROM product_revenue
ORDER BY total_revenue DESC
LIMIT 100
