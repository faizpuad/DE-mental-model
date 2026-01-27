-- Dimension table for dates
-- Reuses Session 2 logic

{{ config(
    materialized='table',
    indexes=[
      {'columns': ['date'], 'unique': True},
      {'columns': ['year', 'month']}
    ]
) }}

WITH source_dates AS (
    SELECT DISTINCT
        DATE(invoicedate) AS date
    FROM {{ source('bronze', 'raw_transactions') }}
    WHERE invoicedate IS NOT NULL
)

SELECT
    -- Generate date_id in YYYYMMDD format
    EXTRACT(YEAR FROM date)::INTEGER * 10000 +
    EXTRACT(MONTH FROM date)::INTEGER * 100 +
    EXTRACT(DAY FROM date)::INTEGER AS date_id,

    date,

    -- Day attributes
    EXTRACT(DAY FROM date)::INTEGER AS day,
    TO_CHAR(date, 'Day') AS day_name,
    EXTRACT(DOW FROM date)::INTEGER AS day_of_week,

    -- Month attributes
    EXTRACT(MONTH FROM date)::INTEGER AS month,
    TO_CHAR(date, 'Month') AS month_name,

    -- Year and quarter
    EXTRACT(QUARTER FROM date)::INTEGER AS quarter,
    EXTRACT(YEAR FROM date)::INTEGER AS year,

    -- Derived attributes
    CASE
        WHEN EXTRACT(DOW FROM date) IN (0, 6) THEN TRUE
        ELSE FALSE
    END AS is_weekend,

    FALSE AS is_holiday,

    CURRENT_TIMESTAMP AS created_at

FROM source_dates
ORDER BY date
