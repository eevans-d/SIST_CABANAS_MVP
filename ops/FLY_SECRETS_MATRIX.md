# Fly.io Secrets Matrix (Staging / Production)

> Usa `flyctl secrets set KEY=value -a <app-name>` para configurar cada secreto.

## Aplicación backend (FastAPI)

Requeridos para arranque (`start-fly.sh` valida estos):

- DATABASE_URL
  - Valor: URL de Fly Postgres (attach) en formato `postgresql://user:pass@<host>.internal:5432/<db>`
  - Nota: Alembic convertirá a `postgresql+asyncpg://` automáticamente via Settings
- REDIS_URL
  - Valor: URL de Upstash Redis, ej: `redis://:password@host:port/0`
- JWT_SECRET
  - Valor: cadena aleatoria segura (>= 32 chars)
- WHATSAPP_ACCESS_TOKEN
- WHATSAPP_APP_SECRET
- WHATSAPP_PHONE_ID
- WHATSAPP_VERIFY_TOKEN
- MERCADOPAGO_ACCESS_TOKEN
- MERCADOPAGO_WEBHOOK_SECRET (opcional)
- ADMIN_ALLOWED_EMAILS
  - Valor: lista separada por comas (ej: `admin@tu-dominio.com,otro@tu-dominio.com`)

## Recomendados / Operativos

- ALLOWED_ORIGINS
  - Valor: URLs del dashboard/web permitidos (ej: `https://tu-dominio.com,https://admin.tu-dominio.com`)
- DOMAIN
  - Valor: dominio base (ej: `tu-dominio.com`)
- ICS_SALT
  - Valor: cadena aleatoria para tokens ICS
- RATE_LIMIT_ENABLED ("true")
- RATE_LIMIT_REQUESTS ("100")
- RATE_LIMIT_WINDOW_SECONDS ("60")
- JOB_EXPIRATION_INTERVAL_SECONDS ("60")
- JOB_ICAL_INTERVAL_SECONDS ("300")

## Procedimiento de Carga (staging)

```bash
# Autenticarse
flyctl auth login

# Revisar app
flyctl status -a sist-cabanas-mvp

# Setear secretos principales (ejemplo)
flyctl secrets set \
  DATABASE_URL="postgresql://app:pass@sist-cabanas-db.internal:5432/alojamientos" \
  REDIS_URL="redis://:password@us1-merryhippo-12345.upstash.io:6379/0" \
  JWT_SECRET="$(openssl rand -base64 48)" \
  WHATSAPP_ACCESS_TOKEN="***" \
  WHATSAPP_APP_SECRET="***" \
  WHATSAPP_PHONE_ID="***" \
  WHATSAPP_VERIFY_TOKEN="***" \
  MERCADOPAGO_ACCESS_TOKEN="***" \
  MERCADOPAGO_WEBHOOK_SECRET="***" \
  ADMIN_ALLOWED_EMAILS="admin@tu-dominio.com" \
  ALLOWED_ORIGINS="https://tu-dominio.com,https://admin.tu-dominio.com" \
  ICS_SALT="$(openssl rand -hex 16)" \
  RATE_LIMIT_ENABLED="true" \
  RATE_LIMIT_REQUESTS="100" \
  RATE_LIMIT_WINDOW_SECONDS="60" \
  JOB_EXPIRATION_INTERVAL_SECONDS="60" \
  JOB_ICAL_INTERVAL_SECONDS="300" \
  -a sist-cabanas-mvp
```

## Validación Post-Deploy

1. `flyctl logs -a sist-cabanas-mvp -f` (sin errores)
2. `curl https://<app>.fly.dev/api/v1/healthz` → status healthy
3. `/metrics` accesible
4. Crear pre-reserva de prueba (o correr script de benchmark con BASE_URL pública)
5. Ejecutar `concurrency_overlap_test.py` con RUN_MUTATING=1 para validar anti solape
