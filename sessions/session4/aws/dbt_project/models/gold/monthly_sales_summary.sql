-- Monthly sales summary for business reporting
-- Gold layer: pre-aggregated for dashboards

{{ config(
    materialized='table',
    tags=['gold', 'business', 'monthly']
) }}

WITH monthly_aggregates AS (
    SELECT
        d.year,
        d.month,
        d.month_name,
        COUNT(DISTINCT f.product_id) AS unique_products,
        COUNT(DISTINCT f.country) AS unique_countries,
        SUM(f.total_transactions) AS total_transactions,
        SUM(f.total_quantity) AS total_quantity,
        SUM(f.total_revenue) AS total_revenue,
        AVG(f.avg_unit_price) AS avg_unit_price
    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_date') }} d ON f.date_id = d.date_id
    GROUP BY d.year, d.month, d.month_name
)

SELECT
    year,
    month,
    month_name,
    unique_products,
    unique_countries,
    total_transactions,
    total_quantity,
    ROUND(total_revenue::NUMERIC, 2) AS total_revenue,
    ROUND(avg_unit_price::NUMERIC, 2) AS avg_unit_price,
    CURRENT_TIMESTAMP AS created_at
FROM monthly_aggregates
ORDER BY year, month
