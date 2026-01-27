FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    cron \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY scripts/ /app/scripts/
COPY dbt_project/ /app/dbt_project/

# Make scripts executable
RUN chmod +x /app/scripts/*.sh /app/scripts/*.py

# Create log directory
RUN mkdir -p /app/logs

# Return to app directory
WORKDIR /app

# Keep container running
CMD ["tail", "-f", "/dev/null"]
