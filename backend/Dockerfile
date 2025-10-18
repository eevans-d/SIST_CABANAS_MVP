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
    netcat-openbsd \
    pkg-config \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libavdevice-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app

# Install Python dependencies
COPY --chown=appuser:appuser backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser backend/ /app

# Copy Fly.io start script
COPY --chown=appuser:appuser backend/start-fly.sh /app/start-fly.sh
RUN chmod +x /app/start-fly.sh

# Switch to non-root user
USER appuser

# Expose port (Fly.io usa 8080 por defecto)
EXPOSE 8080

# Health check (Fly.io maneja esto en fly.toml, pero incluimos por compatibilidad)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=5 \
    CMD curl -fsS http://localhost:${PORT:-8080}/api/v1/healthz || exit 1

# Default values para gunicorn (pueden ser sobreescritos por environment variables)
ENV GUNICORN_WORKERS=2 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_KEEP_ALIVE=75 \
    PORT=8080

# Fly.io CMD
CMD ["/app/start-fly.sh"]
