.PHONY: help deploy upload ingest dbt-run dbt-test test logs cleanup

help:
	@echo "Session 4 AWS Pipeline - Available Commands:"
	@echo ""
	@echo "Setup & Deployment:"
	@echo "  make deploy       - Deploy AWS infrastructure (CloudFormation)"
	@echo "  make upload       - Upload data to S3"
	@echo "  make ingest       - Ingest data from S3 to RDS"
	@echo ""
	@echo "dbt Operations:"
	@echo "  make dbt-debug    - Test dbt connection to AWS RDS"
	@echo "  make dbt-run      - Run dbt models (create silver/gold layers)"
	@echo "  make dbt-test     - Run dbt tests"
	@echo "  make dbt-docs     - Generate and serve dbt documentation"
	@echo ""
	@echo "Testing & Monitoring:"
	@echo "  make test         - Run end-to-end pipeline tests"
	@echo "  make logs         - Tail Lambda function logs"
	@echo "  make rds-logs     - Tail RDS logs"
	@echo "  make verify       - Verify data in RDS"
	@echo "  make connect      - Connect to RDS via psql"
	@echo ""
	@echo "Cleanup:"
	@echo "  make cleanup      - Delete all AWS resources (DESTRUCTIVE!)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make deploy"
	@echo "  2. source aws_config.env"
	@echo "  3. make upload"
	@echo "  4. make ingest"
	@echo "  5. make dbt-run"
	@echo "  6. make test"

deploy:
	@echo "Deploying AWS infrastructure..."
	bash scripts/deploy.sh

upload:
	@echo "Uploading data to S3..."
	@if [ ! -f "aws_config.env" ]; then \
		echo "Error: aws_config.env not found. Run 'make deploy' first."; \
		exit 1; \
	fi
	bash scripts/upload_data.sh

ingest:
	@echo "Ingesting data from S3 to RDS..."
	@if [ ! -f "aws_config.env" ]; then \
		echo "Error: aws_config.env not found. Run 'make deploy' first."; \
		exit 1; \
	fi
	@source aws_config.env && \
	python3 scripts/ingest_from_s3_to_rds.py \
		--s3-bucket $$AWS_S3_BUCKET \
		--s3-key input/online_retail.xlsx \
		--db-host $$AWS_RDS_HOST \
		--db-port $$AWS_RDS_PORT \
		--db-name $$AWS_RDS_DATABASE \
		--db-user $$AWS_RDS_USER \
		--db-password $$AWS_RDS_PASSWORD \
		--aws-region $$AWS_REGION

dbt-debug:
	@echo "Testing dbt connection to AWS RDS..."
	cd ../local && dbt debug --profiles-dir ../aws/dbt_profile --target aws

dbt-run:
	@echo "Running dbt models..."
	cd ../local && dbt run --profiles-dir ../aws/dbt_profile --target aws

dbt-test:
	@echo "Running dbt tests..."
	cd ../local && dbt test --profiles-dir ../aws/dbt_profile --target aws

dbt-docs:
	@echo "Generating dbt documentation..."
	cd ../local && dbt docs generate --profiles-dir ../aws/dbt_profile --target aws
	cd ../local && dbt docs serve --profiles-dir ../aws/dbt_profile

test:
	@echo "Running end-to-end tests..."
	bash scripts/test_pipeline.sh

logs:
	@if [ ! -f "aws_config.env" ]; then \
		echo "Error: aws_config.env not found. Run 'make deploy' first."; \
		exit 1; \
	fi
	@source aws_config.env && \
	aws logs tail /aws/lambda/$${PROJECT_NAME}-s3-event-handler --follow --region $$AWS_REGION

rds-logs:
	@if [ ! -f "aws_config.env" ]; then \
		echo "Error: aws_config.env not found. Run 'make deploy' first."; \
		exit 1; \
	fi
	@source aws_config.env && \
	aws logs tail /aws/rds/instance/$${PROJECT_NAME}-$${ENVIRONMENT}/postgresql --follow --region $$AWS_REGION

verify:
	@echo "Verifying data in RDS..."
	@source aws_config.env && \
	PGPASSWORD=$$AWS_RDS_PASSWORD psql \
		-h $$AWS_RDS_HOST \
		-p $$AWS_RDS_PORT \
		-U $$AWS_RDS_USER \
		-d $$AWS_RDS_DATABASE \
		-c "SELECT 'bronze.raw_transactions' AS table_name, COUNT(*) AS row_count FROM bronze.raw_transactions \
		    UNION ALL SELECT 'public_silver.dim_date', COUNT(*) FROM public_silver.dim_date \
		    UNION ALL SELECT 'public_silver.dim_product', COUNT(*) FROM public_silver.dim_product \
		    UNION ALL SELECT 'public_silver.fact_sales_daily', COUNT(*) FROM public_silver.fact_sales_daily \
		    UNION ALL SELECT 'public_gold.monthly_sales_summary', COUNT(*) FROM public_gold.monthly_sales_summary \
		    ORDER BY table_name;"

connect:
	@echo "Connecting to RDS..."
	@source aws_config.env && \
	PGPASSWORD=$$AWS_RDS_PASSWORD psql \
		-h $$AWS_RDS_HOST \
		-p $$AWS_RDS_PORT \
		-U $$AWS_RDS_USER \
		-d $$AWS_RDS_DATABASE

cleanup:
	@echo "WARNING: This will delete all AWS resources!"
	@read -p "Are you sure? (yes/no): " confirm && [ "$$confirm" = "yes" ] && bash scripts/cleanup.sh || echo "Cleanup cancelled."
