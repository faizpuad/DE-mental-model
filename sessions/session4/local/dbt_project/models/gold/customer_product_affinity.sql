-- Customer Product Affinity
-- Grain: One row per customer per product
-- Purpose: Product recommendations, cross-sell analysis, customer preferences

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['customer_id', 'product_id']},
      {'columns': ['customer_id']},
      {'columns': ['product_id']},
      {'columns': ['total_product_revenue'], 'type': 'btree'}
    ]
) }}

WITH customer_product_purchases AS (
    SELECT
        f.customer_id,
        f.product_id,
        p.stock_code,
        p.description,
        p.category,

        -- Purchase metrics
        COUNT(DISTINCT f.date_id) AS times_purchased,
        SUM(f.total_transactions) AS total_orders,
        SUM(f.total_quantity) AS total_quantity_bought,

        -- Revenue
        SUM(f.total_revenue) AS total_product_revenue,
        AVG(f.total_revenue) AS avg_purchase_value,
        MAX(f.total_revenue) AS max_purchase_value,

        -- Time
        MIN(d.date) AS first_purchased_date,
        MAX(d.date) AS last_purchased_date,
        MAX(d.date) - MIN(d.date) AS days_buying_this_product

    FROM {{ ref('fact_sales_daily') }} f
    INNER JOIN {{ ref('dim_product') }} p
        ON f.product_id = p.product_id
    INNER JOIN {{ ref('dim_date') }} d
        ON f.date_id = d.date_id
    WHERE f.customer_id != -1
    GROUP BY
        f.customer_id,
        f.product_id,
        p.stock_code,
        p.description,
        p.category
),

customer_totals AS (
    SELECT
        customer_id,
        SUM(total_product_revenue) AS customer_total_revenue
    FROM customer_product_purchases
    GROUP BY customer_id
),

enriched AS (
    SELECT
        cpp.*,
        ct.customer_total_revenue,

        -- Calculate product share of customer's total spend
        (cpp.total_product_revenue / NULLIF(ct.customer_total_revenue, 0)) * 100 AS pct_of_customer_spend,

        -- Rank products within each customer
        ROW_NUMBER() OVER (
            PARTITION BY cpp.customer_id
            ORDER BY cpp.total_product_revenue DESC
        ) AS product_rank_by_revenue,

        ROW_NUMBER() OVER (
            PARTITION BY cpp.customer_id
            ORDER BY cpp.times_purchased DESC
        ) AS product_rank_by_frequency,

        -- Calculate purchase frequency (times per active period)
        CASE
            WHEN cpp.days_buying_this_product > 0
            THEN cpp.times_purchased::DECIMAL / (cpp.days_buying_this_product + 1)
            ELSE cpp.times_purchased::DECIMAL
        END AS purchase_frequency

    FROM customer_product_purchases cpp
    INNER JOIN customer_totals ct
        ON cpp.customer_id = ct.customer_id
),

final AS (
    SELECT
        customer_id,
        product_id,
        stock_code,
        description,
        category,

        -- Purchase behavior
        times_purchased,
        total_orders,
        total_quantity_bought,

        -- Revenue
        total_product_revenue,
        avg_purchase_value,
        max_purchase_value,

        -- Customer affinity metrics
        pct_of_customer_spend,
        product_rank_by_revenue,
        product_rank_by_frequency,
        purchase_frequency,

        -- Product preference indicator
        CASE
            WHEN product_rank_by_revenue <= 3 THEN 'Top 3 Product'
            WHEN product_rank_by_revenue <= 10 THEN 'Top 10 Product'
            WHEN pct_of_customer_spend >= 25 THEN 'Major Product (25%+ spend)'
            WHEN times_purchased >= 10 THEN 'Frequently Bought'
            ELSE 'Occasional Purchase'
        END AS affinity_level,

        -- Recency
        first_purchased_date,
        last_purchased_date,
        days_buying_this_product,
        CASE
            WHEN CURRENT_DATE - last_purchased_date <= 30 THEN 'Recent'
            WHEN CURRENT_DATE - last_purchased_date <= 90 THEN 'Moderate'
            ELSE 'Old'
        END AS recency_category,

        -- Metadata
        CURRENT_TIMESTAMP AS created_at,
        CURRENT_TIMESTAMP AS updated_at

    FROM enriched
)

SELECT * FROM final
ORDER BY customer_id, product_rank_by_revenue
