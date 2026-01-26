-- Structured Logging Table
-- Purpose: Store structured logs for analysis and monitoring
DROP TABLE IF EXISTS ops.pipeline_logs;

CREATE TABLE ops.pipeline_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    level VARCHAR(10) NOT NULL,
    message TEXT NOT NULL,
    logger VARCHAR(100),
    pipeline_name VARCHAR(100),
    run_id VARCHAR(50),
    module VARCHAR(100),
    function VARCHAR(100),
    line INTEGER,
    metadata JSONB
);

-- Indexes for querying logs
CREATE INDEX idx_logs_timestamp ON ops.pipeline_logs(timestamp DESC);
CREATE INDEX idx_logs_level ON ops.pipeline_logs(level);
CREATE INDEX idx_logs_pipeline_run ON ops.pipeline_logs(pipeline_name, run_id);
CREATE INDEX idx_logs_metadata ON ops.pipeline_logs USING GIN(metadata);

-- Partitioning by month for better performance (optional)
-- Uncomment to enable partitioning:
-- CREATE TABLE ops.pipeline_logs_y2024m01 PARTITION OF ops.pipeline_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

COMMENT ON TABLE ops.pipeline_logs IS 'Structured logs from pipeline execution';
COMMENT ON COLUMN ops.pipeline_logs.level IS 'Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL';
COMMENT ON COLUMN ops.pipeline_logs.metadata IS 'Additional context in JSON format';

-- Function to insert logs
CREATE OR REPLACE FUNCTION log_pipeline_event(
    p_level VARCHAR,
    p_message TEXT,
    p_logger VARCHAR,
    p_pipeline_name VARCHAR,
    p_run_id VARCHAR,
    p_module VARCHAR,
    p_function VARCHAR,
    p_line INTEGER,
    p_metadata JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO ops.pipeline_logs (
        timestamp, level, message, logger, pipeline_name, run_id,
        module, function, line, metadata
    ) VALUES (
        CURRENT_TIMESTAMP, p_level, p_message, p_logger, p_pipeline_name, p_run_id,
        p_module, p_function, p_line, p_metadata
    );
END;
$$ LANGUAGE plpgsql;
