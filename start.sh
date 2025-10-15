#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z ${DB_HOST:-postgres} ${DB_PORT:-5432}; do
  sleep 0.5
done
echo "PostgreSQL started"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z ${REDIS_HOST:-redis} ${REDIS_PORT:-6379}; do
  sleep 0.5
done
echo "Redis started"

# Run database migrations
echo "Running database migrations..."
cd /app
alembic upgrade head

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers ${GUNICORN_WORKERS:-2} \
    --threads ${GUNICORN_THREADS:-1} \
    --bind 0.0.0.0:8000 \
    --timeout ${GUNICORN_TIMEOUT:-120} \
    --access-logfile - \
    --error-logfile - \
    --log-level ${LOG_LEVEL:-info}
