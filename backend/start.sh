#!/bin/bash
# ============================================================================
# Start script for Sistema MVP de Automatización de Reservas
# ============================================================================

set -e

echo "🏠 Starting Sistema MVP de Automatización de Reservas..."
echo "Environment: ${ENVIRONMENT:-development}"

# Run Alembic migrations
echo "🔧 Running database migrations..."
alembic upgrade head || {
    echo "⚠️ Migrations failed, continuing anyway (might be first run)"
}

# Check if we're in development mode
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🚀 Starting in DEVELOPMENT mode with auto-reload..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
elif [ "$ENVIRONMENT" = "staging" ]; then
    echo "🚀 Starting in STAGING mode..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
elif [ "$ENVIRONMENT" = "production" ]; then
    echo "🚀 Starting in PRODUCTION mode with Gunicorn..."

    # Default Gunicorn settings for production
    export GUNICORN_WORKERS=${GUNICORN_WORKERS:-4}
    export GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT:-30}
    export GUNICORN_GRACEFUL_TIMEOUT=${GUNICORN_GRACEFUL_TIMEOUT:-30}
    export GUNICORN_KEEP_ALIVE=${GUNICORN_KEEP_ALIVE:-2}

    echo "Workers: $GUNICORN_WORKERS"
    echo "Timeout: $GUNICORN_TIMEOUT"

    exec gunicorn \
        -k uvicorn.workers.UvicornWorker \
        -w "$GUNICORN_WORKERS" \
        --bind 0.0.0.0:8000 \
        --timeout "$GUNICORN_TIMEOUT" \
        --graceful-timeout "$GUNICORN_GRACEFUL_TIMEOUT" \
        --keep-alive "$GUNICORN_KEEP_ALIVE" \
        app.main:app
else
    echo "🚀 Starting with default uvicorn..."
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
fi
