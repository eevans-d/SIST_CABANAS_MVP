# Sistema de Reservas - MVP

MVP de sistema de reservas de alojamientos con foco en:
1. Prevención doble-booking (Redis lock + constraint Postgres)
2. Flujo conversacional (WhatsApp) + pagos (Mercado Pago) + iCal
3. Pre-reservas efímeras (expiran en 30 min) + confirmación atómica
4. Audio STT (fallback) + NLU heurístico
5. Observabilidad básica (healthz + métricas Prometheus)

Regla de oro: SHIPPING > PERFECCIÓN. Si pasa tests y cumple lógica crítica → listo.

## Arquitectura Breve

- FastAPI (async) + SQLAlchemy Async (Postgres principal / SQLite fallback en tests)
- Redis para locks y potencial cola ligera
- Mercado Pago Webhook idempotente
- iCal import/export (UID dedupe) para bloquear fechas externas
- Métricas Prometheus vía instrumentador + contadores custom
- Scheduler simple (job expiración)
- NLU: heurística palabras clave + dateparser (es-AR)
- Audio: faster-whisper (si instalado) con fallback a "audio_unclear" sin modelo

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
  - status: healthy | degraded | unhealthy
  - degraded: p.ej. ical warning sin otros errores

### Métricas
- GET /metrics (Prometheus)
  - reservations_created_total{channel}
  - reservations_date_overlap_total{channel}
  - reservations_lock_failed_total{channel}
  - prereservations_expired_total
  - prereservation_reminders_processed_total

### Audio / NLU
- POST /api/v1/audio/transcribe (si existe en el proyecto) -> transcripción + intent heurístico

### iCal
- GET /api/v1/ical/export/{token}.ics (token generado con HMAC ICS_SALT)
- POST /api/v1/ical/import (dedupe por UID usando internal_notes)

### Pagos (Mercado Pago)
- POST /api/v1/mercadopago/webhook (firma y idempotencia)

### WhatsApp
- POST /api/v1/whatsapp/webhook (firma HMAC X-Hub-Signature-256)

### Admin (mínimo)
- POST /api/v1/admin/login { email } -> devuelve JWT si email pertenece a ADMIN_ALLOWED_EMAILS (uso dev/test)
- GET /api/v1/admin/reservations (Bearer JWT)
- GET /api/v1/admin/reservations/export.csv (Bearer JWT)
- POST /api/v1/admin/actions/resend-email/{code} (Bearer JWT + header x-csrf-token)
  - Header ejemplo: `x-csrf-token: use-un-secreto-aleatorio-8+chars`

### Firmas Webhook (Seguridad)
Ambos webhooks (WhatsApp y Mercado Pago) validan HMAC cuando se configura el secreto correspondiente.

| Integración | Cabecera | Algoritmo | Formato | Variable Entorno |
|-------------|----------|-----------|---------|------------------|
| WhatsApp | `X-Hub-Signature-256` | HMAC-SHA256 | `sha256=<hex>` | `WHATSAPP_APP_SECRET` |
| Mercado Pago | `x-signature` | HMAC-SHA256 | `ts=<n>,v1=<hex>` (solo v1 requerido) | `MERCADOPAGO_WEBHOOK_SECRET` |

Flujo de validación:
1. Leer body crudo (solo una vez)
2. Calcular `hex = HMAC_SHA256(secret, body)`
3. Comparar con firma recibida (strict compare)
4. Si mismatch -> 403 `{"detail": "Invalid signature"}`
5. Si secreto ausente -> se acepta (modo desarrollo)

Tests incluidos:
- `test_whatsapp_signature.py`
- `test_mercadopago_signature.py`

Recomendación producción: siempre definir ambos secretos y exigir HTTPS.

## Pricing
- Base: base_price * noches
- Weekend multiplier (sábado/domingo) aplicado por noche -> campo `weekend_multiplier` (default 1.2 si no definido)
- Extensible a feriados (holidays lib) — fuera de scope MVP

## Anti Doble Booking
- Redis lock: key lock:acc:{id}:{checkin}:{checkout} TTL 30m
- Constraint Postgres EXCLUDE GIST (reservas pre_reserved | confirmed)
- Métricas: reservations_date_overlap_total{channel}
- Test de concurrencia pre-reserva y confirmación cubren integridad

## Expiración Pre-Reserva
- expires_at = now + 30m
- Job background: elimina / cancela expiradas (cambia a cancelled)
- Confirmación expired → error expired

## Concurrencia Confirmación
- UPDATE condicional evita doble confirmación
- Segundo intento: invalid_state

## Health Degradado
- ical sin datos => warning (status global degraded si nada crítico falla)

## Variables Entorno Clave (.env)
```
# Entorno
ENVIRONMENT=development

# DB (Postgres principal)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/appdb
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=0

# Redis
REDIS_URL=redis://localhost:6379/0

# WhatsApp Cloud API
WHATSAPP_ACCESS_TOKEN=changeme
WHATSAPP_APP_SECRET=changeme
WHATSAPP_PHONE_ID=1234567890
WHATSAPP_VERIFY_TOKEN=optional_autogen

# Mercado Pago
MERCADOPAGO_ACCESS_TOKEN=changeme
MERCADOPAGO_WEBHOOK_SECRET=optional_signature

# Seguridad / JWT
JWT_SECRET=changeme
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# iCal
ICS_SALT=changemehex

# Audio / NLU
AUDIO_MODEL=base
AUDIO_MIN_CONFIDENCE=0.6

# App
BASE_URL=http://localhost:8000
ALLOWED_ORIGINS=http://localhost:3000
DOMAIN=localhost
JOB_EXPIRATION_INTERVAL_SECONDS=60
```

## Métricas de Observabilidad Futuras (no MVP aún)
- Latencia p95 por endpoint
- Contadores por intent NLU

## Ejecución Local
1. Crear `.env` (ver sección anterior)
2. (Opcional) Crear DB y extensión en Postgres:
  ```sql
  CREATE DATABASE appdb;
  \c appdb;
  CREATE EXTENSION IF NOT EXISTS btree_gist;
  ```
3. Lanzar servicios (ejemplo mínimo):
  ```bash
  docker run -d --name pg -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=user -e POSTGRES_DB=appdb -p 5432:5432 postgres:16
  docker run -d --name redis -p 6379:6379 redis:7-alpine
  ```
4. Instalar dependencias: `pip install -r requirements.txt`
5. Ejecutar: `uvicorn app.main:app --reload --port 8000`
6. Probar health: `curl http://localhost:8000/api/v1/healthz`
7. Crear pre-reserva -> confirmar -> cancelar (ver ejemplos en sección Reservas)

### Entorno de pruebas E2E rápido (opcional)
1. Levantar dependencias con Mailhog:
  - `docker compose -f docker-compose.test.yml up -d`
2. Sembrar datos de ejemplo (si aplica): `python scripts/seed.py`
3. Ejecutar smoke E2E: `pytest -q tests/test_journey_basic.py`
4. Ver emails en http://localhost:8025 (Mailhog)

## Alembic / Migraciones
Generar nueva migración (ejemplo):
```bash
alembic revision -m "payments reservation_id nullable" --autogenerate
alembic upgrade head
```

## Tests
Ejecutar suite completa (usa SQLite fallback si Postgres no está disponible):
```bash
pytest -q
```
Para forzar Postgres real (recomendado para anti-overlap): asegurar `TEST_DATABASE_URL` apunta a instancia con `btree_gist`.

## Tests
- pytest -q (usa SQLite fallback si Postgres no disponible)

## Limitaciones / Fuera de Scope MVP
- Sin interfaz admin (sólo API)
- Sin reintentos extendidos de lock Redis
- iCal last sync real pendiente (placeholder en health)
- Memory check simplificado
- No reporting avanzado ni multi-propietario
- No PMS externo (ADR explícito)

## Estrategia Anti Doble-Booking (Resumen Técnico)
1. Redis lock previo a INSERT (evita ráfagas simultáneas)
2. Constraint EXCLUDE GIST nivel DB (garantía fuerte)
3. Test de concurrencia asegura IntegrityError / métrica incremento
4. Confirmación atómica evita doble transición a confirmed

## NLU Heurístico
Palabras clave -> intents:
- disponibilidad: "disponib", "libre", "hay"
- precio: "precio", "costo", "cuanto", "sale"
- reservar: "reserv", "apart", "tomo"
- servicios: "servicio", "incluye", "wifi"
Fechas: dateparser (es), regex DD/MM, "finde" → próximo sábado-domingo.

## Audio
OGG/OPUS -> (si modelo) transcribe; si modelo ausente => retorna `audio_unclear` (permite no bloquear entorno mínimo).

## Observabilidad
- /metrics prom expose + custom counters
- /api/v1/healthz status consolidado + details
- Logs JSON estructurados (request_id) con structlog

## Checklist Diario (Operación Rápida)
- [ ] Ejecutar `pytest -q` (tiempo <5s)
- [ ] Revisar `healthz` (status healthy/degraded)
- [ ] Confirmar que métricas principales incrementan tras pre-reserva
- [ ] Inspeccionar logs de locks fallidos (si >1% investigar)
- [ ] Revisar expiraciones (reservas pre_reserved > 30m => bug)

## Política de "Done"
- Test pasa + métrica/lock comporta correcto => DONE
- No refactor si no hay bug o deuda que afecte SLO / security

## SLOs Objetivo
- P95 texto < 3s
- P95 audio < 15s
- iCal sync < 20m atrasado
- Error rate < 1%

## ADR Principal
No integrar PMS externo en MVP (ver documentación original). Foco en core pipeline (locks, expiraciones, pagos, iCal, audio/NLU básico).

---
Para mejoras futuras: auth admin, dashboard, sync iCal incremental, retry pagos, intents ML.
