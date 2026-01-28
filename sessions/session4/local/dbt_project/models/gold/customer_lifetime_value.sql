-- Customer Lifetime Value Analysis
-- Grain: One row per customer
-- Purpose: Customer segmentation, CLV analysis, retention tracking

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['customer_id'], 'unique': True},
      {'columns': ['customer_segment']},
      {'columns': ['total_lifetime_value'], 'type': 'btree'}
    ]
) }}

WITH customer_by_country AS (
    SELECT
        f.customer_id,
        f.country,
        SUM(f.total_revenue) AS country_revenue
    FROM {{ ref('fact_sales_daily') }} f
    WHERE f.customer_id != -1
    GROUP BY f.customer_id, f.country
),

primary_country AS (
    -- Select country with most revenue for each customer
    SELECT DISTINCT ON (customer_id)
        customer_id,
        country AS primary_country
    FROM customer_by_country
    ORDER BY customer_id, country_revenue DESC
),

customer_metrics AS (
    SELECT
        f.customer_id,

        -- Purchase behavior (across ALL countries)
        COUNT(DISTINCT f.date_id) AS total_purchase_days,
        COUNT(DISTINCT CONCAT(f.date_id, f.product_id)) AS total_product_purchases,
        SUM(f.total_transactions) AS total_orders,
        SUM(f.total_quantity) AS total_items_purchased,

        -- Revenue metrics
        SUM(f.total_revenue) AS total_lifetime_value,
        AVG(f.total_revenue) AS avg_daily_revenue,
        MAX(f.total_revenue) AS max_daily_revenue,

        -- Time-based metrics
        MIN(d.date) AS first_purchase_date,
        MAX(d.date) AS last_purchase_date,
        MAX(d.date) - MIN(d.date) AS customer_lifespan_days,

        -- Product diversity
        COUNT(DISTINCT f.product_id) AS unique_products_purchased,
        COUNT(DISTINCT p.category) AS unique_categories_purchased

    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_date') }} d
        ON f.date_id = d.date_id
    INNER JOIN {{ ref('dim_product') }} p
        ON f.product_id = p.product_id
    WHERE f.customer_id != -1  -- Exclude null/unknown customers
    GROUP BY f.customer_id  -- Group by customer only, not country
),

customer_segmentation AS (
    SELECT
        *,

        -- Calculate average order value
        CASE
            WHEN total_orders > 0
            THEN total_lifetime_value / total_orders
            ELSE 0
        END AS avg_order_value,

        -- Calculate purchase frequency (purchases per active day)
        CASE
            WHEN customer_lifespan_days > 0
            THEN total_purchase_days::DECIMAL / customer_lifespan_days
            ELSE 0
        END AS purchase_frequency,

        -- Customer segment based on total spend
        CASE
            WHEN total_lifetime_value >= 10000 THEN 'VIP'
            WHEN total_lifetime_value >= 5000 THEN 'High Value'
            WHEN total_lifetime_value >= 1000 THEN 'Medium Value'
            WHEN total_lifetime_value >= 100 THEN 'Low Value'
            ELSE 'Very Low Value'
        END AS customer_segment,

        -- Recency category (days since last purchase)
        CASE
            WHEN CURRENT_DATE - last_purchase_date <= 30 THEN 'Active (0-30 days)'
            WHEN CURRENT_DATE - last_purchase_date <= 90 THEN 'Recent (31-90 days)'
            WHEN CURRENT_DATE - last_purchase_date <= 180 THEN 'At Risk (91-180 days)'
            ELSE 'Churned (180+ days)'
        END AS recency_category

    FROM customer_metrics
)

SELECT
    cs.customer_id,
    pc.primary_country AS country,

    -- Purchase metrics
    cs.total_purchase_days,
    cs.total_product_purchases,
    cs.total_orders,
    cs.total_items_purchased,

    -- Revenue metrics
    cs.total_lifetime_value,
    cs.avg_daily_revenue,
    cs.avg_order_value,
    cs.max_daily_revenue,

    -- Product diversity
    cs.unique_products_purchased,
    cs.unique_categories_purchased,

    -- Time-based metrics
    cs.first_purchase_date,
    cs.last_purchase_date,
    cs.customer_lifespan_days,
    cs.purchase_frequency,

    -- Segmentation
    cs.customer_segment,
    cs.recency_category,

    -- Metadata
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at

FROM customer_segmentation cs
INNER JOIN primary_country pc ON cs.customer_id = pc.customer_id
ORDER BY cs.total_lifetime_value DESC
