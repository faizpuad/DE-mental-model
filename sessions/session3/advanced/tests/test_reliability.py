import pytest
import psycopg2
import os
import time
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from reliable_pipeline import ReliablePipeline, CheckpointManager, PipelineLogger, retry_with_backoff


@pytest.fixture
def db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'retail_db'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres')
    }


@pytest.fixture
def db_connection(db_config):
    conn = psycopg2.connect(**db_config)
    yield conn
    conn.close()


@pytest.fixture
def reliable_pipeline():
    pipeline = ReliablePipeline()
    pipeline.connect()
    pipeline.create_schemas()
    yield pipeline
    pipeline.disconnect()


class TestCheckpointManager:
    def test_create_checkpoint(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_001', db_connection)
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'test_value')
        
        result = checkpoint_mgr.get_checkpoint('test_stage', 'test_key')
        assert result == 'test_value'

    def test_update_checkpoint(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_002', db_connection)
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'initial_value')
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'updated_value')
        
        result = checkpoint_mgr.get_checkpoint('test_stage', 'test_key')
        assert result == 'updated_value'

    def test_nonexistent_checkpoint(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_003', db_connection)
        result = checkpoint_mgr.get_checkpoint('test_stage', 'nonexistent_key')
        assert result is None

    def test_checkpoint_with_metadata(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_004', db_connection)
        metadata = {'records_processed': 100, 'duration_ms': 5000}
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'test_value', metadata=metadata)
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT metadata FROM ops.pipeline_checkpoint WHERE pipeline_name = 'test_pipeline' AND run_id = 'test_run_004'"
        )
        result = cursor.fetchone()[0]
        cursor.close()
        
        assert result is not None
        stored_metadata = json.loads(result)
        assert stored_metadata['records_processed'] == 100

    def test_checkpoint_unique_constraint(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_005', db_connection)
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'value1')
        checkpoint_mgr.set_checkpoint('test_stage', 'test_key', 'value2')
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ops.pipeline_checkpoint WHERE pipeline_name = 'test_pipeline' AND run_id = 'test_run_005' AND stage = 'test_stage' AND checkpoint_key = 'test_key'"
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        assert count == 1

    def test_checkpoint_status_tracking(self, reliable_pipeline, db_connection):
        checkpoint_mgr = CheckpointManager('test_pipeline', 'test_run_006', db_connection)
        checkpoint_mgr.start_stage('test_stage', 'test_key')
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT status FROM ops.pipeline_checkpoint WHERE pipeline_name = 'test_pipeline' AND run_id = 'test_run_006' AND stage = 'test_stage' AND checkpoint_key = 'test_key'"
        )
        status = cursor.fetchone()[0]
        cursor.close()
        
        assert status == 'in_progress'


class TestPipelineLogger:
    def test_log_to_database(self, reliable_pipeline, db_connection):
        logger = PipelineLogger('test_logger', 'test_run_001', db_connection)
        logger.info('Test message', metadata={'key': 'value'})
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ops.pipeline_logs WHERE logger = 'test_logger' AND level = 'INFO'"
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        assert count > 0

    def test_log_level_error(self, reliable_pipeline, db_connection):
        logger = PipelineLogger('test_logger', 'test_run_002', db_connection)
        logger.error('Error message', metadata={'error_code': 500})
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM ops.pipeline_logs WHERE logger = 'test_logger' AND level = 'ERROR'"
        )
        count = cursor.fetchone()[0]
        cursor.close()
        
        assert count > 0

    def test_log_metadata(self, reliable_pipeline, db_connection):
        logger = PipelineLogger('test_logger', 'test_run_003', db_connection)
        test_metadata = {'records': 100, 'duration': 5000, 'success': True}
        logger.info('Test message', metadata=test_metadata)
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT metadata FROM ops.pipeline_logs WHERE logger = 'test_logger' ORDER BY id DESC LIMIT 1"
        )
        result = cursor.fetchone()[0]
        cursor.close()
        
        stored_metadata = json.loads(result)
        assert stored_metadata == test_metadata

    def test_log_with_run_id(self, reliable_pipeline, db_connection):
        logger = PipelineLogger('test_logger', 'test_run_004', db_connection)
        logger.info('Test message')
        
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT run_id FROM ops.pipeline_logs WHERE logger = 'test_logger' ORDER BY id DESC LIMIT 1"
        )
        run_id = cursor.fetchone()[0]
        cursor.close()
        
        assert run_id == 'test_run_004'


class TestRetryLogic:
    def test_retry_on_failure(self):
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def flaky_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Simulated failure")
            return "success"
        
        result = flaky_function()
        assert result == "success"
        assert attempt_count == 2

    def test_retry_max_attempts_exceeded(self):
        attempt_count = 0
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def always_fail_function():
            nonlocal attempt_count
            attempt_count += 1
            raise Exception("Always fails")
        
        with pytest.raises(Exception):
            always_fail_function()
        
        assert attempt_count == 3

    def test_retry_with_backoff_delay(self):
        attempt_times = []
        
        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def flaky_function():
            attempt_times.append(time.time())
            if len(attempt_times) < 2:
                raise Exception("Simulated failure")
            return "success"
        
        flaky_function()
        
        assert len(attempt_times) == 2
        delay = attempt_times[1] - attempt_times[0]
        assert delay >= 0.1


class TestReliablePipeline:
    def test_pipeline_connection(self, reliable_pipeline):
        assert reliable_pipeline.conn is not None
        assert reliable_pipeline.logger is not None
        assert reliable_pipeline.checkpoint is not None

    def test_create_ops_schema(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'ops'"
        )
        result = cursor.fetchone()
        cursor.close()
        assert result is not None

    def test_checkpoint_table_exists(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'ops' AND table_name = 'pipeline_checkpoint')"
        )
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_pipeline_logs_table_exists(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'ops' AND table_name = 'pipeline_logs')"
        )
        result = cursor.fetchone()[0]
        cursor.close()
        assert result is True

    def test_pipeline_table_columns(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'ops' AND table_name = 'pipeline_checkpoint'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_columns = [
            'id', 'pipeline_name', 'run_id', 'stage', 'checkpoint_key',
            'checkpoint_value', 'status', 'start_time', 'end_time', 'duration_ms',
            'metadata', 'created_at', 'updated_at'
        ]
        assert columns == expected_columns

    def test_logs_table_columns(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'ops' AND table_name = 'pipeline_logs'
            ORDER BY ordinal_position;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        expected_columns = [
            'id', 'timestamp', 'level', 'message', 'logger', 'pipeline_name',
            'run_id', 'module', 'function', 'line', 'metadata'
        ]
        assert columns == expected_columns

    def test_pipeline_indexes_exist(self, db_connection):
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT indexname 
            FROM pg_indexes 
            WHERE schemaname = 'ops' 
            AND tablename IN ('pipeline_checkpoint', 'pipeline_logs')
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        assert len(indexes) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=../code', '--cov-report=html'])
