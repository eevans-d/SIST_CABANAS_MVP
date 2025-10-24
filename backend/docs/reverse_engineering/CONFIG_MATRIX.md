# Matriz de Configuración (Settings)

Fuente de verdad: `backend/app/core/config.py` (Pydantic BaseSettings con `.env`).

- ENVIRONMENT: development|staging|production. Default: development.
- DATABASE_URL: requerido. PostgreSQL (postgresql+asyncpg://) o SQLite para tests. Validador fuerza asyncpg.
- DB_POOL_SIZE: tamaño pool SQLAlchemy. Default: 50.
- DB_MAX_OVERFLOW: overflow de pool. Default: 25.
- REDIS_URL: requerido. Formato redis://. Si REDIS_PASSWORD definido, se inyecta automáticamente si falta en URL.
- REDIS_PASSWORD: opcional. Se inserta en REDIS_URL si corresponde.
- WHATSAPP_ACCESS_TOKEN: token de envío (requerido en prod para WhatsApp).
- WHATSAPP_VERIFY_TOKEN: token de verificación GET webhook. Default aleatorio seguro.
- WHATSAPP_APP_SECRET: secreto HMAC-SHA256 para X-Hub-Signature-256 (requerido en prod).
- WHATSAPP_PHONE_ID: ID del teléfono en Cloud API.
- MERCADOPAGO_ACCESS_TOKEN: token API Mercado Pago (requerido en prod para pagos).
- MERCADOPAGO_WEBHOOK_SECRET: opcional. Si se define, firma x-signature v1 obligatoria.
- BASE_URL: URL base pública (links en emails, callbacks). Default None.
- DOMAIN: dominio público. Default localhost.
- JWT_SECRET: secreto JWT HS256. Default aleatorio seguro.
- JWT_ALGORITHM: HS256 (fijo).
- JWT_EXPIRATION_HOURS: exp horas. Default 24.
- JOB_EXPIRATION_INTERVAL_SECONDS: intervalo worker expiración pre-reservas. Default 60.
- JOB_ICAL_INTERVAL_SECONDS: intervalo sync iCal. Default 300.
- ICAL_SYNC_MAX_AGE_MINUTES: umbral health iCal. Default 20.
- RATE_LIMIT_ENABLED: habilitar rate limit Redis por IP+path. Default True.
- RATE_LIMIT_REQUESTS: 60 req por ventana (default).
- RATE_LIMIT_WINDOW_SECONDS: 60s ventana (default).
- ICS_SALT: sal HMAC para tokens iCal. Default aleatorio seguro.
- AUDIO_MODEL: modelo whisper (faster-whisper). Default base.
- AUDIO_MIN_CONFIDENCE: umbral confianza STT. Default 0.6.
- ALLOWED_ORIGINS: CORS. Default http://localhost:3000.
- SMTP_HOST, SMTP_PORT (587), SMTP_USER, SMTP_PASS, SMTP_FROM, SMTP_USE_TLS (True): placeholders para futuro envío real (MVP actual: logging).
- ADMIN_ALLOWED_EMAILS: lista blanca (coma-separado) para dashboard. Default admin@example.com.
- ADMIN_CSRF_SECRET: secreto simple CSRF para acciones admin. Default aleatorio seguro.

Notas:
- Health expone bandera de configuración para WhatsApp/MercadoPago en `GET /healthz`.
- Seguridad crítica en prod: definir JWT_SECRET, WHATSAPP_APP_SECRET, MERCADOPAGO_WEBHOOK_SECRET, ICS_SALT, REDIS_PASSWORD.
