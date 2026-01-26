-- Processed Dates Checkpoint Table
-- Purpose: Track which dates have been processed to avoid double-counting (idempotency)
DROP TABLE IF EXISTS ops.processed_dates;

CREATE TABLE ops.processed_dates (
    id SERIAL PRIMARY KEY,
    date_value VARCHAR(10) NOT NULL,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,
    UNIQUE(date_value)
);

CREATE INDEX idx_processed_dates_value ON ops.processed_dates(date_value);
CREATE INDEX idx_processed_dates_status ON ops.processed_dates(status);

COMMENT ON TABLE ops.processed_dates IS 'Tracks processed transaction dates for idempotency';
COMMENT ON COLUMN ops.processed_dates.date_value IS 'Date value (YYYY-MM-DD) that has been processed';
COMMENT ON COLUMN ops.processed_dates.status IS 'Status: in_progress, completed';
