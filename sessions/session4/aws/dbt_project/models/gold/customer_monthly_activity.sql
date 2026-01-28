-- Customer Monthly Activity
-- Grain: One row per customer per month
-- Purpose: Track customer behavior over time, cohort analysis, retention

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['customer_id', 'year', 'month']},
      {'columns': ['customer_id']},
      {'columns': ['year', 'month']},
      {'columns': ['monthly_revenue'], 'type': 'btree'}
    ]
) }}

WITH customer_monthly AS (
    SELECT
        f.customer_id,
        f.country,
        d.year,
        d.month,

        -- Purchase metrics
        COUNT(DISTINCT f.date_id) AS purchase_days_in_month,
        COUNT(DISTINCT f.product_id) AS unique_products,
        SUM(f.total_transactions) AS monthly_orders,
        SUM(f.total_quantity) AS monthly_items,

        -- Revenue
        SUM(f.total_revenue) AS monthly_revenue,
        AVG(f.total_revenue) AS avg_daily_revenue,
        MAX(f.total_revenue) AS max_daily_revenue,

        -- Time
        MIN(d.date) AS first_purchase_in_month,
        MAX(d.date) AS last_purchase_in_month

    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_date') }} d
        ON f.date_id = d.date_id
    WHERE f.customer_id != -1
    GROUP BY f.customer_id, f.country, d.year, d.month
),

customer_metrics_enriched AS (
    SELECT
        *,

        -- Calculate average order value for the month
        CASE
            WHEN monthly_orders > 0
            THEN monthly_revenue / monthly_orders
            ELSE 0
        END AS avg_order_value,

        -- Month-over-month growth (using window function)
        LAG(monthly_revenue) OVER (
            PARTITION BY customer_id
            ORDER BY year, month
        ) AS prev_month_revenue,

        -- Is this the customer's first purchase month?
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY year, month
        ) = 1 AS is_first_month,

        -- Customer tenure (months since first purchase)
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY year, month
        ) AS customer_tenure_months

    FROM customer_monthly
),

final AS (
    SELECT
        customer_id,
        country,
        year,
        month,

        -- Purchase behavior
        purchase_days_in_month,
        unique_products,
        monthly_orders,
        monthly_items,

        -- Revenue
        monthly_revenue,
        avg_daily_revenue,
        avg_order_value,
        max_daily_revenue,

        -- Growth metrics
        prev_month_revenue,
        CASE
            WHEN prev_month_revenue IS NOT NULL AND prev_month_revenue > 0
            THEN ((monthly_revenue - prev_month_revenue) / prev_month_revenue) * 100
            ELSE NULL
        END AS revenue_growth_pct,

        -- Customer journey
        is_first_month,
        customer_tenure_months,

        -- Activity flags
        CASE
            WHEN monthly_revenue >= 1000 THEN 'High Spender'
            WHEN monthly_revenue >= 500 THEN 'Medium Spender'
            WHEN monthly_revenue >= 100 THEN 'Regular Spender'
            ELSE 'Occasional Spender'
        END AS spending_level,

        -- Time
        first_purchase_in_month,
        last_purchase_in_month,

        -- Metadata
        CURRENT_TIMESTAMP AS created_at,
        CURRENT_TIMESTAMP AS updated_at

    FROM customer_metrics_enriched
)

SELECT * FROM final
ORDER BY customer_id, year, month
