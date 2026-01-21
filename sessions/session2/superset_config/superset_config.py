import os

# Database connection for Superset's own metadata
# Format: postgresql://USER:PASSWORD@HOST:PORT/DB_NAME
SQLALCHEMY_DATABASE_URI = "postgresql://superset:superset@superset_db:5432/superset"

# Security settings
SECRET_KEY = "thisismysecretkey1234567890"

# Allow the application to run behind a load balancer/proxy
ENABLE_PROXY_FIX = True

# Required for newer versions of Superset
TALISMAN_ENABLED = False
