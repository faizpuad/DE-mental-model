-- Checkpoint Table
-- Purpose: Track pipeline execution progress for resumability
CREATE SCHEMA IF NOT EXISTS ops;

DROP TABLE IF EXISTS ops.pipeline_checkpoint;

CREATE TABLE ops.pipeline_checkpoint (
    id SERIAL PRIMARY KEY,
    pipeline_name VARCHAR(100) NOT NULL,
    run_id VARCHAR(50) NOT NULL,
    stage VARCHAR(100) NOT NULL,
    checkpoint_key VARCHAR(255) NOT NULL,
    checkpoint_value VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pipeline_name, run_id, stage, checkpoint_key)
);

-- Indexes for querying checkpoints
CREATE INDEX idx_checkpoint_pipeline_run ON ops.pipeline_checkpoint(pipeline_name, run_id);
CREATE INDEX idx_checkpoint_status ON ops.pipeline_checkpoint(status);
CREATE INDEX idx_checkpoint_created_at ON ops.pipeline_checkpoint(created_at);

COMMENT ON TABLE ops.pipeline_checkpoint IS 'Tracks pipeline execution checkpoints for resumability';
COMMENT ON COLUMN ops.pipeline_checkpoint.pipeline_name IS 'Name of the pipeline (e.g., ingestion, transformation)';
COMMENT ON COLUMN ops.pipeline_checkpoint.run_id IS 'Unique identifier for a pipeline run';
COMMENT ON COLUMN ops.pipeline_checkpoint.stage IS 'Pipeline stage (e.g., read, clean, load)';
COMMENT ON COLUMN ops.pipeline_checkpoint.checkpoint_key IS 'Identifier for checkpoint (e.g., last_processed_id, file_position)';
COMMENT ON COLUMN ops.pipeline_checkpoint.status IS 'Status: pending, in_progress, completed, failed';
COMMENT ON COLUMN ops.pipeline_checkpoint.metadata IS 'Additional context (record counts, file sizes, etc.)';
