#!/bin/bash
set -e

echo "Waiting for database to be ready..."
# Add a small delay to ensure the database is ready
sleep 5

echo "Starting and Running Database Migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec fastapi run app/main.py --port 8000 --reload