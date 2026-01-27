#!/usr/bin/env python3
"""
Retail Data Pipeline - Local Orchestrator
Simple Python script that chains: ingestion → transformation → validation
Runs via cron for scheduled execution
"""

import os
import sys
import logging
import subprocess
from datetime import datetime
from pathlib import Path


# Absolute path to dbt CLI inside container
DBT_BIN = "/usr/local/bin/dbt"

# Configure logging
LOG_DIR = Path("/app/logs")
LOG_DIR.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("retail_pipeline")
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)

# File handler (rotating daily)
log_file = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)


class PipelineOrchestrator:
    """Simple orchestrator that runs pipeline steps sequentially"""

    def __init__(self):
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()

        # Configuration
        self.data_file = os.getenv("DATA_FILE", "/data/online_retail.xlsx")
        self.db_host = os.getenv("POSTGRES_HOST", "postgres")
        self.db_port = os.getenv("POSTGRES_PORT", "5432")
        self.db_name = os.getenv("POSTGRES_DB", "retail_db")
        self.db_user = os.getenv("POSTGRES_USER", "postgres")
        self.db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

        logger.info(f"=" * 70)
        logger.info(f"Pipeline Run ID: {self.run_id}")
        logger.info(f"=" * 70)

    def run_step(self, step_name, func):
        """Run a pipeline step with logging and error handling"""
        logger.info(f"Starting step: {step_name}")
        step_start = datetime.now()

        try:
            result = func()
            duration = (datetime.now() - step_start).total_seconds()
            logger.info(f"✓ Step completed: {step_name} ({duration:.2f}s)")
            return result
        except Exception as e:
            duration = (datetime.now() - step_start).total_seconds()
            logger.error(f"✗ Step failed: {step_name} ({duration:.2f}s)")
            logger.error(f"Error: {str(e)}", exc_info=True)
            raise

    def step_1_ingestion(self):
        """Step 1: Ingest data from Excel to bronze layer"""
        logger.info("Executing ingestion script...")

        result = subprocess.run(
            [
                sys.executable,
                "/app/scripts/ingest.py",
                "--data-file",
                self.data_file,
                "--db-host",
                self.db_host,
                "--db-port",
                self.db_port,
                "--db-name",
                self.db_name,
                "--db-user",
                self.db_user,
                "--db-password",
                self.db_password,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        logger.info(f"Ingestion output:\n{result.stdout}")
        return {"status": "success", "stdout": result.stdout}

    def step_2_transformation(self):
        """Step 2: Run dbt transformations (bronze → silver)"""
        logger.info("Executing dbt transformations...")

        # Set environment for dbt
        env = os.environ.copy()
        env["DBT_PROFILES_DIR"] = "/app/dbt_project"

        result = subprocess.run(
            [DBT_BIN, "run", "--profiles-dir", "/app/dbt_project"],
            cwd="/app/dbt_project",
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

        logger.info(f"dbt stdout:\n{result.stdout}")
        if result.stderr:
            logger.info(f"dbt stderr:\n{result.stderr}")
        return {"status": "success", "stdout": result.stdout}

    def step_3_validation(self):
        """Step 3: Run dbt tests and custom validation"""
        logger.info("Executing validation...")

        # Run dbt tests
        env = os.environ.copy()
        env["DBT_PROFILES_DIR"] = "/app/dbt_project"

        result = subprocess.run(
            [DBT_BIN, "test", "--profiles-dir", "/app/dbt_project"],
            cwd="/app/dbt_project",
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )

        logger.info(f"dbt test output:\n{result.stdout}")

        # Run custom validation
        validate_result = subprocess.run(
            [
                sys.executable,
                "/app/scripts/validate.py",
                "--db-host",
                self.db_host,
                "--db-port",
                self.db_port,
                "--db-name",
                self.db_name,
                "--db-user",
                self.db_user,
                "--db-password",
                self.db_password,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        logger.info(f"Validation output:\n{validate_result.stdout}")
        return {"status": "success", "stdout": result.stdout}

    def run(self):
        """Execute full pipeline"""
        try:
            # Step 1: Ingestion
            self.run_step("1. Data Ingestion", self.step_1_ingestion)

            # Step 2: Transformation
            self.run_step("2. dbt Transformation", self.step_2_transformation)

            # Step 3: Validation
            self.run_step("3. Validation", self.step_3_validation)

            # Summary
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.info(f"=" * 70)
            logger.info(f"✓ Pipeline completed successfully in {duration:.2f}s")
            logger.info(f"=" * 70)

            return 0

        except Exception as e:
            duration = (datetime.now() - self.start_time).total_seconds()
            logger.error(f"=" * 70)
            logger.error(f"✗ Pipeline failed after {duration:.2f}s")
            logger.error(f"Error: {str(e)}")
            logger.error(f"=" * 70)
            return 1


def main():
    """Main entry point"""
    try:
        orchestrator = PipelineOrchestrator()
        exit_code = orchestrator.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
