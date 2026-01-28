-- Country-level sales performance
-- Gold layer: optimized for geographic analysis

{{ config(
    materialized='table',
    tags=['gold', 'business', 'geography']
) }}

WITH country_aggregates AS (
    SELECT
        f.country,
        COUNT(DISTINCT f.date_id) AS active_days,
        COUNT(DISTINCT f.product_id) AS unique_products,
        SUM(f.total_transactions) AS total_transactions,
        SUM(f.total_quantity) AS total_quantity,
        SUM(f.total_revenue) AS total_revenue,
        AVG(f.avg_unit_price) AS avg_unit_price,
        MIN(d.date) AS first_sale_date,
        MAX(d.date) AS last_sale_date
    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_date') }} d ON f.date_id = d.date_id
    GROUP BY f.country
)

SELECT
    country,
    active_days,
    unique_products,
    total_transactions,
    total_quantity,
    ROUND(total_revenue::NUMERIC, 2) AS total_revenue,
    ROUND(avg_unit_price::NUMERIC, 2) AS avg_unit_price,
    ROUND((total_revenue / NULLIF(active_days, 0))::NUMERIC, 2) AS avg_daily_revenue,
    first_sale_date,
    last_sale_date,
    CURRENT_TIMESTAMP AS created_at
FROM country_aggregates
ORDER BY total_revenue DESC
