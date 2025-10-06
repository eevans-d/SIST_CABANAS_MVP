FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Install Python dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://localhost:8000/api/v1/healthz || exit 1

# Run application with start script
COPY --chown=appuser:appuser start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Default values para gunicorn (pueden ser sobreescritos por environment variables)
ENV GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=60 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_KEEP_ALIVE=75

ENTRYPOINT ["/app/start.sh"]