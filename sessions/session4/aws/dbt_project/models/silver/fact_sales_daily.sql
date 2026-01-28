-- Daily sales facts aggregated by date, product, and country
-- Reuses Session 2 logic

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['date_id']},
      {'columns': ['product_id']},
      {'columns': ['country']},
      {'columns': ['date_id', 'country']},
      {'columns': ['total_revenue'], 'type': 'btree'}
    ]
) }}

WITH daily_sales AS (
    SELECT
        d.date_id,
        p.product_id,
        r.country,

        -- Customer handling (degenerate dimension)
        MAX(COALESCE(NULLIF(SPLIT_PART(r.customerid, '.', 1), '')::INTEGER, -1)) AS customer_id,

        -- Aggregated metrics
        COUNT(DISTINCT r.invoiceno) AS total_transactions,
        SUM(r.quantity) AS total_quantity,
        SUM(r.quantity * r.unitprice) AS total_revenue,
        AVG(r.unitprice) AS avg_unit_price

    FROM {{ source('bronze', 'raw_transactions') }} r
    INNER JOIN {{ ref('dim_date') }} d
        ON DATE(r.invoicedate) = d.date
    INNER JOIN {{ ref('dim_product') }} p
        ON r.stockcode = p.stock_code

    WHERE r.quantity > 0          -- Filter returns/cancellations
        AND r.unitprice >= 0      -- Filter bad prices
        AND r.country IS NOT NULL -- Ensure dimension integrity

    GROUP BY d.date_id, p.product_id, r.country
)

SELECT
    date_id,
    product_id,
    country,
    customer_id,
    total_transactions,
    total_quantity,
    total_revenue,
    avg_unit_price,

    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at

FROM daily_sales
