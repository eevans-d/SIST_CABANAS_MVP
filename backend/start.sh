#!/bin/bash
set -e

echo "Starting API with Gunicorn..."
echo "Workers: $GUNICORN_WORKERS"
echo "Timeout: $GUNICORN_TIMEOUT"
echo "Graceful Timeout: $GUNICORN_GRACEFUL_TIMEOUT"
echo "Keep Alive: $GUNICORN_KEEP_ALIVE"

# Ejecutar las migraciones de base de datos si es necesario (puedes descomentar si quieres que ocurra en cada inicio)
# echo "Running database migrations..."
# alembic upgrade head

exec gunicorn \
    -k uvicorn.workers.UvicornWorker \
    -w "$GUNICORN_WORKERS" \
    --bind 0.0.0.0:8000 \
    --timeout "$GUNICORN_TIMEOUT" \
    --graceful-timeout "$GUNICORN_GRACEFUL_TIMEOUT" \
    --keep-alive "$GUNICORN_KEEP_ALIVE" \
    app.main:app
