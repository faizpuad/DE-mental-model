FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

COPY code/ ./code/
COPY tests/ ./tests/

ENV PYTHONPATH=/app

CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=code", "--cov-report=html"]
