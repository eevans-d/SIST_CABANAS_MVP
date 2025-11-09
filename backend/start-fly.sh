#!/bin/bash
# ============================================================================
# ✈️ Fly.io Start Script - SIST_CABAÑAS_MVP Backend
# ============================================================================
set -e

echo "🚀 Starting SIST_CABAÑAS_MVP Backend on Fly.io..."

# ============================================================================
# 1. ENVIRONMENT VALIDATION
# ============================================================================
echo "📋 Validating environment variables..."

# Integraciones opcionales: permite arrancar sin WhatsApp/Mercado Pago
# Usa INTEGRATIONS_REQUIRED=true|false (default: true)
INTEGRATIONS_REQUIRED=${INTEGRATIONS_REQUIRED:-true}

# Núcleo requerido siempre
CORE_REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "JWT_SECRET"
    "ADMIN_ALLOWED_EMAILS"
)

# Integraciones (se pueden omitir para pruebas iniciales)
INTEGRATIONS_VARS=(
    "WHATSAPP_ACCESS_TOKEN"
    "WHATSAPP_APP_SECRET"
    "WHATSAPP_PHONE_ID"
    "WHATSAPP_VERIFY_TOKEN"
    "MERCADOPAGO_ACCESS_TOKEN"
    "MERCADOPAGO_WEBHOOK_SECRET"
)

MISSING_VARS=0

echo "🔹 Checking core variables..."
for var in "${CORE_REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ ERROR: Missing required core environment variable: $var"
        MISSING_VARS=$((MISSING_VARS + 1))
    else
        echo "✅ $var is set"
    fi
done

if [ "${INTEGRATIONS_REQUIRED}" = "true" ]; then
    echo "🔹 Checking integrations (WhatsApp/Mercado Pago)..."
    for var in "${INTEGRATIONS_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ ERROR: Missing required integration variable: $var"
            MISSING_VARS=$((MISSING_VARS + 1))
        else
            echo "✅ $var is set"
        fi
    done
else
    echo "⚠️  Integrations are disabled (INTEGRATIONS_REQUIRED=false). Skipping WhatsApp/Mercado Pago checks."
fi

if [ $MISSING_VARS -gt 0 ]; then
    echo ""
    echo "❌ ERROR: $MISSING_VARS required environment variable(s) missing!"
    echo "Configure them with: flyctl secrets set VARIABLE=value"
    echo ""
    echo "Required core variables:"
    for var in "${CORE_REQUIRED_VARS[@]}"; do
        echo "  - $var"
    done
    if [ "${INTEGRATIONS_REQUIRED}" = "true" ]; then
        echo "Also required integration variables:"
        for var in "${INTEGRATIONS_VARS[@]}"; do
            echo "  - $var"
        done
    else
        echo "Integrations are optional in this run (INTEGRATIONS_REQUIRED=false)."
    fi
    exit 1
fi

echo "✅ All required environment variables are set"

# ============================================================================
# 2. WAIT FOR DEPENDENCIES (PostgreSQL + Redis)
# ============================================================================
echo "⏳ Waiting for PostgreSQL..."

# Extract host and port from DATABASE_URL
# Format: postgresql://user:pass@host:port/db OR postgres://...
DB_HOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

if [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ]; then
    echo "⚠️  Could not parse DATABASE_URL, assuming Fly.io internal network"
    DB_HOST="localhost"
    DB_PORT="5432"
fi

echo "  → Database host: $DB_HOST:$DB_PORT"

# Wait for PostgreSQL (max 60 seconds)
MAX_RETRIES=60
RETRY_COUNT=0

while ! nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ ERROR: PostgreSQL not available after 60 seconds"
        echo "   DATABASE_URL: $DATABASE_URL"
        exit 1
    fi
    echo "  → Waiting for PostgreSQL... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 1
done

echo "✅ PostgreSQL is ready"

# ============================================================================
# 3. WAIT FOR REDIS
# ============================================================================
echo "⏳ Waiting for Redis..."

# Extract host and port from REDIS_URL
# Format: redis://[:password@]host:port[/db] or rediss:// (TLS)
REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
if [ -z "$REDIS_HOST" ]; then
    # No auth case: redis://host:port
    REDIS_HOST=$(echo "$REDIS_URL" | sed -n 's/redis[s]*:\/\/\([^:]*\):.*/\1/p')
fi

REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
if [ -z "$REDIS_PORT" ]; then
    REDIS_PORT=$(echo "$REDIS_URL" | sed -n 's/.*:\([0-9]*\)$/\1/p')
fi

if [ -z "$REDIS_HOST" ] || [ -z "$REDIS_PORT" ]; then
    echo "⚠️  Could not parse REDIS_URL, assuming Upstash Redis"
    # Upstash doesn't need nc check (external service)
    echo "✅ Redis URL configured (Upstash)"
else
    echo "  → Redis host: $REDIS_HOST:$REDIS_PORT"

    # Wait for Redis (max 30 seconds)
    MAX_RETRIES=30
    RETRY_COUNT=0

    while ! nc -z "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "⚠️  WARNING: Redis not reachable after 30 seconds"
            echo "   Assuming external Redis (Upstash) - continuing..."
            break
        fi
        echo "  → Waiting for Redis... ($RETRY_COUNT/$MAX_RETRIES)"
        sleep 1
    done

    echo "✅ Redis is ready"
fi

# ============================================================================
# 4. DATABASE MIGRATIONS
# ============================================================================
echo "🔄 Running database migrations..."

cd /app

if ! alembic upgrade head; then
    echo "❌ ERROR: Database migrations failed"
    echo "   This could mean:"
    echo "   1. Database connection is invalid"
    echo "   2. Database user lacks permissions"
    echo "   3. Migration conflict or error"
    echo ""
    echo "   Check logs and DATABASE_URL configuration"
    exit 1
fi

echo "✅ Database migrations completed"

# ============================================================================
# 5. DOWNLOAD WHISPER MODEL (if needed)
# ============================================================================
echo "🎤 Checking Whisper STT model..."

# The model will be downloaded on first use, but we can pre-download it
python3 -c "from faster_whisper import WhisperModel; WhisperModel('base', device='cpu', compute_type='int8')" 2>/dev/null || {
    echo "⚠️  Whisper model not pre-downloaded (will download on first use)"
}

echo "✅ Whisper model ready"

# ============================================================================
# 6. START APPLICATION
# ============================================================================
echo ""
echo "🚀 Starting Gunicorn + Uvicorn workers..."
echo ""
echo "  Environment: ${ENVIRONMENT:-production}"
echo "  Workers: ${GUNICORN_WORKERS:-2}"
echo "  Timeout: ${GUNICORN_TIMEOUT:-120}s"
echo "  Port: ${PORT:-8080}"
echo "  Region: ${FLY_REGION:-unknown}"
echo "  App: ${FLY_APP_NAME:-unknown}"
echo ""

# Fly.io provides PORT env variable (default 8080)
PORT=${PORT:-8080}

exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${GUNICORN_WORKERS:-2}" \
    --threads "${GUNICORN_THREADS:-1}" \
    --bind "0.0.0.0:${PORT}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile - \
    --log-level "${LOG_LEVEL:-info}" \
    --preload
