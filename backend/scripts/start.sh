#!/bin/bash

echo "Ensuring data directory exists..."
mkdir -p "$(dirname "$SQLLITE_FILE_NAME")"

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting FastAPI app..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"