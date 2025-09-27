# Deployment Tuning (Producción)

Recomendaciones iniciales; ajustar según métricas reales y SLOs:

- Gunicorn
  - Workers: 2–4 por CPU (env: GUNICORN_WORKERS)
  - Timeout: 60–90s (GUNICORN_TIMEOUT)
  - Keep-alive: 75s (GUNICORN_KEEP_ALIVE)
- Base de Datos (SQLAlchemy / Async)
  - DB_POOL_SIZE ≈ workers*2 (inicio 10)
  - DB_MAX_OVERFLOW: 3–10
  - Pre-ping habilitado (ya activo) para reciclar conexiones muertas
- Nginx
  - /api: proxy_read_timeout 30s; /webhooks: 10s
  - Rate limit: 10r/s general; 50r/s para /webhooks (ajustar según proveedor)
- Redis
  - Memoria 256–512MB; política allkeys-lru
  - Usar DB separada para locks vs. colas si crece el uso
- Observabilidad
  - Healthz incluye "runtime" (workers, pool). Consúmelo en dashboards
  - /metrics expone contadores de reservas, expiraciones y recordatorios
- Sizing inicial
  - vCPU: 2–4, RAM: 2–4GB, Disco: SSD 20GB+
  - Postgres: 1 vCPU, 1–2GB RAM, storage con IOPS decentes
- Backups
  - Base diaria + WAL si aplica; verificar script `deploy.sh backup`
