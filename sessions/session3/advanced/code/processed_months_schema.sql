-- Processed Months Checkpoint Table
-- Purpose: Track which months have been processed to avoid double-counting (idempotency)
DROP TABLE IF EXISTS ops.processed_months;

CREATE TABLE ops.processed_months (
    id SERIAL PRIMARY KEY,
    month_key VARCHAR(7) NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    UNIQUE(month_key)
);

CREATE INDEX idx_processed_months_key ON ops.processed_months(month_key);
CREATE INDEX idx_processed_months_status ON ops.processed_months(status);

COMMENT ON TABLE ops.processed_months IS 'Tracks processed months for idempotency in gold layer';
COMMENT ON COLUMN ops.processed_months.month_key IS 'Month key (YYYY-MM) that has been processed';
COMMENT ON COLUMN ops.processed_months.year IS 'Year value';
COMMENT ON COLUMN ops.processed_months.month IS 'Month value (1-12)';
COMMENT ON COLUMN ops.processed_months.status IS 'Status: in_progress, completed, failed';
