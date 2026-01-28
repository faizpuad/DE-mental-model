-- Product dimension with categorization
-- Reuses Session 2 logic

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['stock_code'], 'unique': True},
      {'columns': ['category']}
    ]
) }}

WITH source_products AS (
    SELECT DISTINCT ON (stockcode)
        stockcode,
        description
    FROM {{ source('bronze', 'raw_transactions') }}
    WHERE stockcode IS NOT NULL
        AND description IS NOT NULL
    ORDER BY stockcode, description
)

SELECT
    ROW_NUMBER() OVER (ORDER BY stockcode) AS product_id,
    stockcode AS stock_code,
    description,

    -- Business rule-based categorization
    CASE
        WHEN stockcode LIKE 'DISC%' THEN 'Discount'
        WHEN stockcode LIKE 'M%' THEN 'Manual'
        WHEN stockcode LIKE 'POST%' THEN 'Postage'
        WHEN stockcode LIKE 'C2%' THEN 'Carriage'
        WHEN stockcode LIKE 'BANK%' THEN 'Bank Charges'
        WHEN stockcode LIKE 'TEST%' THEN 'Test'
        WHEN stockcode LIKE 'PADS%' THEN 'Pads'
        ELSE 'General'
    END AS category,

    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at

FROM source_products
ORDER BY stockcode
