#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Starting and Running Database Migrations..."
alembic upgrade head

echo "Starting FastAPI application..."
exec fastapi run app/main.py --port 8080 --reload

####https://claude.ai/chat/545c0d7b-4641-4979-9aa6-4f8c1dc794f3