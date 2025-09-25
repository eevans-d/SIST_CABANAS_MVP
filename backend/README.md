# Sistema de Reservas - MVP

## Endpoints Principales

### Reservas
- POST /api/v1/reservations/pre-reserve
  - Body: accommodation_id, check_in, check_out, guests, channel, contact_name, contact_phone, (contact_email)
  - Respuesta OK: { code, expires_at, deposit_amount, total_price, nights }
  - Errores: invalid_dates, invalid_guests, accommodation_not_found, processing_or_unavailable, date_overlap
- POST /api/v1/reservations/{code}/confirm
  - Respuesta OK: { code, status=confirmed, confirmed_at }
  - Errores: not_found, invalid_state, expired
- POST /api/v1/reservations/{code}/cancel
  - Body: { reason? }
  - Respuesta OK: { code, status=cancelled, cancelled_at }
  - Errores: not_found, invalid_state

### Health
- GET /api/v1/healthz -> estado consolidado (database, redis, disk, memory placeholder, ical, whatsapp, mercadopago)

### Métricas
- GET /metrics (Prometheus)
  - reservations_created_total{channel}
  - reservations_date_overlap_total{channel}
  - reservations_lock_failed_total{channel}

### Audio / NLU
- POST /api/v1/audio/transcribe (si existe en el proyecto) -> transcripción + intent heurístico

### iCal
- GET /api/v1/ical/export/{token}.ics (export futuro si implementado)
- POST /api/v1/ical/import (dedupe por UID)

### Pagos (Mercado Pago)
- POST /api/v1/mercadopago/webhook (firma y idempotencia)

### WhatsApp
- POST /api/v1/whatsapp/webhook (firma HMAC X-Hub-Signature-256)

## Pricing
- Base: base_price * noches
- Weekend multiplier (sábado/domingo) aplicado por noche -> campo `weekend_multiplier` en accommodation (default 1.2 si no definido)

## Anti Doble Booking
- Redis lock: key lock:acc:{id}:{checkin}:{checkout} TTL 30m
- Constraint Postgres EXCLUDE daterange (pre_reserved, confirmed)
- Tests: solapamiento produce IntegrityError y métrica incrementa reservations_date_overlap_total

## Expiración Pre-Reserva
- expires_at = now + 30m
- Worker background revisa expiraciones cada JOB_EXPIRATION_INTERVAL_SECONDS
- Confirmación expired -> error expired + estado pasado a cancelled

## Concurrencia Confirmación
- UPDATE condicional evita doble confirmación. Segundo intento devuelve invalid_state.

## Health Degradado
- ical sin datos => warning (status global degraded si no hay otros errores)

## Variables Entorno Clave
- DATABASE_URL (postgresql+asyncpg://... o sqlite en test)
- REDIS_URL
- WHATSAPP_ACCESS_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_PHONE_ID
- MERCADOPAGO_ACCESS_TOKEN
- JWT_SECRET

## Métricas de Observabilidad Futuras (no MVP aún)
- Latencia p95 por endpoint
- Contadores por intent NLU

## Ejecución Local (resumen)
1. Crear y exportar variables .env
2. Iniciar Postgres + Redis (docker-compose futuro) o usar instancias locales
3. uvicorn app.main:app --reload

## Tests
- pytest -q (usa SQLite fallback si Postgres no disponible)

## Limitaciones MVP
- Sin autenticación admin UI todavía
- Sin reintentos de locks ni extensión
- iCal last sync placeholder
- Memory check simplificado (sin psutil)
