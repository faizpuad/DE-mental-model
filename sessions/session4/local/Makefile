.PHONY: help setup start stop logs pipeline clean reset test-db query

help:
	@echo "Session 4 Local Pipeline - Available Commands:"
	@echo "  make setup      - First-time setup (create .env, build images)"
	@echo "  make start      - Start all services"
	@echo "  make stop       - Stop all services"
	@echo "  make logs       - Show logs from all services"
	@echo "  make pipeline   - Run pipeline manually (one-time)"
	@echo "  make clean      - Stop services and remove volumes"

setup:
	@echo "Creating .env file..."
	@if [ ! -f .env ]; then cp .env.example .env; echo "✓ Created .env"; fi
	@echo "Building Docker images..."
	docker-compose build
	@echo "✓ Setup complete!"
	@echo ""
	@echo "Next: make start"

start:
	@echo "Starting services..."
	docker-compose up -d
	@echo "✓ Services started!"
	@echo ""
	@echo "Pipeline runs every 5 minutes (check CRON_SCHEDULE in .env)"
	@echo "View logs: make logs"
	@echo "Run manually: make pipeline"
	@echo "Superset: http://localhost:8088 (admin/admin)"

stop:
	docker-compose down

logs:
	docker-compose logs -f

pipeline:
	@echo "Running pipeline manually..."
	docker-compose exec pipeline python3 /app/scripts/pipeline.py

clean:
	docker-compose down -v
	rm -rf dbt_project/logs dbt_project/target logs/

reset:
	docker-compose down -v --rmi all
	docker builder prune -a -f

test-db:
	@echo "Testing database connection..."
	docker-compose exec postgres psql -U postgres -d retail_db -c "SELECT 'Connection OK' as status;"

query:
	@echo "Querying silver layer..."
	docker-compose exec postgres psql -U postgres -d retail_db -c "\
		SELECT 'dim_date' as table_name, COUNT(*) as row_count FROM silver.dim_date \
		UNION ALL \
		SELECT 'dim_product', COUNT(*) FROM silver.dim_product \
		UNION ALL \
		SELECT 'fact_sales_daily', COUNT(*) FROM silver.fact_sales_daily;"
