#!/bin/bash
set -e

echo "=== Starting Pipeline Cron Service ==="

# Install dbt dependencies
echo "Installing dbt packages..."
cd /app/dbt_project && dbt deps || echo "dbt deps failed, continuing..."

# Get cron schedule from environment (default: every 5 minutes)
CRON_SCHEDULE="${CRON_SCHEDULE:-*/5 * * * *}"

echo "Cron schedule: $CRON_SCHEDULE"

# Create cron job
echo "$CRON_SCHEDULE cd /app && /usr/local/bin/python3 /app/scripts/pipeline.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/pipeline-cron

# Give execution rights
chmod 0644 /etc/cron.d/pipeline-cron

# Apply cron job
crontab /etc/cron.d/pipeline-cron

# Create cron log file
touch /app/logs/cron.log

echo "✓ Cron job created"
echo "✓ Pipeline will run: $CRON_SCHEDULE"
echo ""
echo "Run manually: docker-compose exec pipeline python3 /app/scripts/pipeline.py"
echo "View logs: docker-compose exec pipeline tail -f /app/logs/cron.log"
echo ""

# Run pipeline once immediately
echo "Running pipeline once immediately..."
python3 /app/scripts/pipeline.py

# Start cron in foreground
echo "Starting cron daemon..."
cron && tail -f /app/logs/cron.log
