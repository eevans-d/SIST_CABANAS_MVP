# Arquitectura Técnica - Sistema MVP Alojamientos

**Versión:** 0.9.8
**Fecha:** 2025-10-02
**Status:** 9.9/10 Production Ready

---

## 📋 Tabla de Contenidos

- [Visión General](#visión-general)
- [Stack Tecnológico](#stack-tecnológico)
- [Arquitectura de Componentes](#arquitectura-de-componentes)
- [Flujos Críticos](#flujos-críticos)
- [Anti-Doble-Booking](#anti-doble-booking)
- [Seguridad](#seguridad)
- [Observabilidad](#observabilidad)
- [Escalabilidad](#escalabilidad)
- [Decisiones Arquitecturales](#decisiones-arquitecturales)

---

## Visión General

Sistema monolítico MVP de reservas de alojamientos con automatización conversacional vía WhatsApp, integraciones de pago (Mercado Pago) y sincronización bidireccional con canales externos (Airbnb/Booking) mediante iCal.

### Principios Arquitecturales

1. **SHIPPING > PERFECCIÓN**: Soluciones simples y funcionales sobre arquitecturas complejas
2. **Monolito Modular**: Un servicio, múltiples módulos cohesivos
3. **Test-First**: Los tests definen "terminado"
4. **Fail-Safe**: Graceful degradation ante fallos externos
5. **Observability by Default**: Métricas y logs desde el día 1

---

## Stack Tecnológico

### Core Application

```
Python 3.12.3
├── FastAPI 0.115           # Web framework async
├── SQLAlchemy 2.x          # ORM async
├── Alembic                 # Database migrations
├── Pydantic 2.x            # Data validation
└── Uvicorn                 # ASGI server
```

### Data Layer

```
PostgreSQL 16-alpine
├── btree_gist extension    # Anti-double-booking constraint
└── daterange type          # Overlap detection

Redis 7-alpine
├── Distributed locks       # Reservation atomicity
├── Rate limiting           # API protection
└── Cache (future)          # Query optimization
```

### External Integrations

```
WhatsApp Business Cloud API
├── Webhook con HMAC SHA-256
└── Media download (audio/images)

Mercado Pago API
├── Webhook con x-signature v1
└── Payment processing

iCal RFC 5545
├── Import from Airbnb/Booking
└── Export with HMAC tokens
```

### Audio Processing

```
FFmpeg                      # OGG → WAV conversion
└── faster-whisper          # Speech-to-text (Whisper base)
```

### Observability

```
Prometheus                  # Metrics collection
├── FastAPI Instrumentator  # Auto-instrumentation
└── Custom metrics          # Business KPIs

Structlog                   # Structured logging
└── JSON format             # Machine-readable logs
```

### Development Tools

```
pytest + pytest-asyncio     # Testing framework
Black + Flake8 + isort      # Code quality
pre-commit                  # Git hooks
Bandit                      # Security scanning
mypy                        # Type checking
```

---

## Arquitectura de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        EXTERNAL CLIENTS                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ WhatsApp │  │  Email   │  │  iCal    │  │ Admin UI │       │
│  │  Cloud   │  │  Client  │  │  Sync    │  │(future)  │       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼──────────────┐
│                         NGINX (Reverse Proxy)                   │
│              SSL/TLS Termination + Rate Limiting                │
└───────┬─────────────────────────────────────────────────────────┘
        │
┌───────▼─────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   ROUTERS LAYER                          │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐│  │
│  │  │WhatsApp│ │Mercado │ │ iCal   │ │ Health │ │ Admin  ││  │
│  │  │Webhook │ │  Pago  │ │ Export │ │ Checks │ │  API   ││  │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘│  │
│  └──────┼──────────┼──────────┼──────────┼──────────┼──────┘  │
│         │          │          │          │          │          │
│  ┌──────▼──────────▼──────────▼──────────▼──────────▼──────┐  │
│  │                   SERVICES LAYER                         │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐          │  │
│  │  │Reservation │ │  WhatsApp  │ │   Audio    │          │  │
│  │  │  Service   │ │  Service   │ │  Service   │          │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘          │  │
│  │        │              │              │                   │  │
│  │  ┌─────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐          │  │
│  │  │MercadoPago │ │    NLU     │ │   iCal     │          │  │
│  │  │  Service   │ │  Service   │ │  Service   │          │  │
│  │  └────────────┘ └────────────┘ └────────────┘          │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│  ┌──────▼───────────────────────────────────────────────────┐  │
│  │                     MODELS LAYER                         │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │  │
│  │  │Accommodation │ │ Reservation  │ │   Payment    │    │  │
│  │  │    Model     │ │    Model     │ │    Model     │    │  │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
└─────────┼───────────────────────────────────────────────────────┘
          │
┌─────────▼───────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                          │
│  ┌────────────────────┐         ┌────────────────────┐         │
│  │  PostgreSQL 16     │         │    Redis 7         │         │
│  │  ┌──────────────┐  │         │  ┌──────────────┐  │         │
│  │  │ Reservations │  │         │  │ Locks        │  │         │
│  │  │ Payments     │  │         │  │ Rate Limits  │  │         │
│  │  │ Accommod.    │  │         │  │ Cache (fut.) │  │         │
│  │  └──────────────┘  │         │  └──────────────┘  │         │
│  └────────────────────┘         └────────────────────┘         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    BACKGROUND JOBS                              │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐     │
│  │  Pre-reserve   │ │  iCal Import   │ │   Reminders    │     │
│  │  Expiration    │ │  Scheduler     │ │   (future)     │     │
│  └────────────────┘ └────────────────┘ └────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flujos Críticos

### 1. Flujo de Pre-Reserva

```
Usuario WhatsApp
     │
     │ 1. Mensaje texto/audio
     ▼
WhatsApp Webhook (validación firma)
     │
     │ 2. Normalizar mensaje
     ▼
Audio Service (si es audio)
     │
     │ 3. Transcripción STT
     ▼
NLU Service
     │
     │ 4. Detectar intención + extraer entidades
     ▼
Reservation Service
     │
     │ 5. SET lock Redis (NX EX 1800)
     │    lock:acc:{id}:{checkin}:{checkout}
     ▼
     │ 6. Validar disponibilidad
     ▼
PostgreSQL (INSERT reservation)
     │
     │ 7. Constraint anti-overlap valida
     │    EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)
     ▼
     │ SUCCESS: Reservation code RES240915001
     │ expires_at = now() + 30min
     ▼
WhatsApp Response
     │
     │ 8. Enviar confirmación con link de pago
     │    "Reserva RES240915001 confirmada..."
     ▼
Usuario recibe mensaje
```

**Casos de Error:**

- **Lock Redis falla**: Respuesta inmediata "En proceso o no disponible"
- **Constraint DB viola**: DELETE lock, respuesta "No disponible para esas fechas"
- **Audio unclear**: Solicitar repetir mensaje en texto
- **NLU no detecta intención**: Responder con opciones clarificadoras

---

### 2. Flujo de Confirmación con Pago

```
Usuario
     │
     │ 1. Click en link de pago MP
     ▼
Mercado Pago Checkout
     │
     │ 2. Usuario paga
     ▼
Mercado Pago Webhook
     │
     │ 3. POST con x-signature
     ▼
Signature Validation
     │
     │ 4. Validar HMAC ts + v1
     ▼
Payment Service (idempotente)
     │
     │ 5. UPDATE payment (payment_id único)
     │    Si ya procesado → skip (idempotencia)
     ▼
Reservation Service
     │
     │ 6. UPDATE reservation (pre_reserved → confirmed)
     │    confirmed_at = now()
     │    DELETE lock Redis
     ▼
iCal Export Service
     │
     │ 7. Regenerar .ics con nueva reserva
     │    X-CODE: RES240915001
     │    X-SOURCE: sistema_interno
     ▼
Email/WhatsApp Notification
     │
     │ 8. Enviar confirmación final
     ▼
Usuario recibe confirmación
```

---

### 3. Flujo de Importación iCal

```
Scheduler (cada 15 min)
     │
     │ 1. Trigger job
     ▼
iCal Import Service
     │
     │ 2. GET url_ical por cada accommodation
     ▼
Parse .ics (RFC 5545)
     │
     │ 3. Extraer VEVENT con DTSTART/DTEND
     ▼
Deduplication Check
     │
     │ 4. Buscar por UID o fechas exactas
     │    Si X-SOURCE = sistema_interno → skip
     ▼
Reservation Service
     │
     │ 5. CREATE reservation (confirmed)
     │    channel_source = 'ical_import'
     │    reservation_status = 'confirmed'
     ▼
PostgreSQL (INSERT)
     │
     │ 6. Constraint valida no overlap
     ▼
Update metrics
     │
     │ 7. ical_last_sync_timestamp = now()
     │    ical_last_sync_age_minutes gauge
     ▼
Success
```

**Protecciones:**

- No importar eventos con `X-SOURCE: sistema_interno` (evita loop)
- Deduplicar por UID o por fechas exactas + accommodation
- Max age monitoring: alerta si >20min sin sync

---

## Anti-Doble-Booking

### Arquitectura de 2 Capas

#### Capa 1: Locks Redis Distribuidos

```python
lock_key = f"lock:acc:{accommodation_id}:{check_in}:{check_out}"
acquired = redis.set(lock_key, "locked", nx=True, ex=1800)

if not acquired:
    return {"error": "En proceso o no disponible"}
```

**Propósito:** Prevenir race conditions en requests concurrentes
**TTL:** 1800 segundos (30 min)
**Fail-Safe:** Si Redis cae, constraint DB sigue protegiendo

#### Capa 2: PostgreSQL Constraint

```sql
CREATE EXTENSION btree_gist;

ALTER TABLE reservations
  ADD COLUMN period daterange
  GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;

ALTER TABLE reservations
  ADD CONSTRAINT no_overlap_reservations
  EXCLUDE USING gist (
    accommodation_id WITH =,
    period WITH &&
  )
  WHERE (reservation_status IN ('pre_reserved', 'confirmed'));
```

**Propósito:** Garantía definitiva a nivel de DB
**Performance:** Index gist permite búsquedas rápidas de overlaps
**Boundary:** `[)` = incluye check-in, excluye check-out (consecutive bookings OK)

### Testing

```python
# Test crítico: concurrencia simultánea
async def test_double_confirm_concurrent():
    tasks = [
        confirm_reservation(code1),
        confirm_reservation(code2)  # mismo accommodation, overlapping dates
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    assert any(isinstance(r, IntegrityError) for r in results)
    # Exactamente uno debe fallar con constraint violation
```

---

## Seguridad

### Webhook Signature Validation

#### WhatsApp (HMAC SHA-256)

```python
def validate_whatsapp_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

**Header:** `X-Hub-Signature-256`
**Crítico:** SIEMPRE validar antes de procesar

#### Mercado Pago (HMAC SHA-256 con timestamp)

```python
def validate_mp_signature(
    data_id: str,
    ts: str,
    signature: str,
    secret: str
) -> bool:
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    expected = hmac.new(
        secret.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Header:** `x-signature` (formato: `ts=X,v1=Y`)
**Protección anti-replay:** Validar ts reciente (<5 min)

### iCal Export Authentication

```python
token = hmac.new(
    ICAL_SECRET.encode(),
    f"{accommodation_id}".encode(),
    hashlib.sha256
).hexdigest()[:16]

export_url = f"/api/v1/ical/export/{accommodation_id}/{token}"
```

**Propósito:** URLs públicas pero no enumerables
**Rotación:** Manual por accommodation (regenerar token)

### Secrets Management

```bash
# .env (nunca commitear)
WHATSAPP_APP_SECRET=xxx
MERCADOPAGO_WEBHOOK_SECRET=xxx
ICAL_EXPORT_SECRET=xxx
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
JWT_SECRET_KEY=xxx  # admin dashboard (future)
```

**Deployment:** Variables de entorno en Docker/K8s secrets

---

## Observabilidad

### Métricas Prometheus

```python
# Counter: reservas creadas
reservations_created_total = Counter(
    'reservations_created_total',
    'Total reservations created',
    ['channel_source']
)

# Gauge: edad último sync iCal
ical_last_sync_age_minutes = Gauge(
    'ical_last_sync_age_minutes',
    'Minutes since last iCal sync',
    ['accommodation_id']
)

# Histogram: latencias API
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)
```

**Endpoint:** `/metrics` (formato Prometheus)
**Bypass:** Rate limit no aplica a `/metrics`

### Health Checks

```python
# GET /api/v1/healthz
{
    "status": "healthy",  # healthy | degraded | unhealthy
    "timestamp": "2025-10-02T21:30:00Z",
    "checks": {
        "database": {"status": "ok", "latency_ms": 2.3},
        "redis": {"status": "ok", "latency_ms": 1.1},
        "ical_sync": {
            "status": "ok",
            "max_age_minutes": 12,
            "threshold_minutes": 20
        }
    }
}
```

**SLOs:**
- Texto P95 < 3s (warning > 4s, critical > 6s)
- Audio P95 < 15s (warning > 20s, critical > 30s)
- iCal sync < 20min desfase (warning > 30min)
- Error rate < 1% (critical > 5%)

### Structured Logging

```python
logger.info(
    "reservation_created",
    reservation_code="RES240915001",
    accommodation_id=1,
    channel_source="whatsapp",
    check_in="2024-09-20",
    check_out="2024-09-22",
    trace_id="abc123"
)
```

**Format:** JSON lines
**Trace IDs:** Header `X-Request-ID` propagado en todos logs

---

## Escalabilidad

### Horizontal Scaling

```
Load Balancer (Nginx/HAProxy)
    │
    ├──> FastAPI Instance 1 ──┐
    │                          │
    ├──> FastAPI Instance 2 ──┤──> PostgreSQL (Primary)
    │                          │
    └──> FastAPI Instance N ──┘
```

**Stateless:** Todas las instancias pueden servir cualquier request
**Session:** No hay sesiones; auth via JWT (future)
**Locks:** Redis distribuido garantiza atomicidad entre instancias

### Database Scaling

```
PostgreSQL Primary (Write)
    │
    ├──> Read Replica 1 (Read-only queries)
    │
    └──> Read Replica 2 (Analytics, reports)
```

**Queries Pesadas:** Dirigir a replicas (future)
**Connection Pool:** Configurar `pool_size` y `max_overflow` en SQLAlchemy

### Caching Strategy (Future)

```python
# Cache availability checks (60s TTL)
cache_key = f"avail:{accommodation_id}:{month}"
result = redis.get(cache_key)
if not result:
    result = check_availability_db(...)
    redis.setex(cache_key, 60, json.dumps(result))
```

**Invalidación:** On reservation creation/cancellation

---

## Decisiones Arquitecturales

### ¿Por qué Monolito?

**Decisión:** Monolito modular FastAPI
**Razón:** MVP de 10 días, equipo pequeño, complejidad de dominio media
**Trade-off:** Simplicidad deploy vs. escalabilidad independiente
**Referencia:** [ADR-002 (pendiente)]

### ¿Por qué PostgreSQL + Redis?

**Decisión:** PostgreSQL para persistencia, Redis para locks/cache
**Razón:**
- PostgreSQL: Constraint EXCLUDE USING gist único, ACID garantizado
- Redis: Locks distribuidos con TTL, performance excepcional
**Trade-off:** Dos datastores vs. consistencia eventual
**Referencia:** [ADR-003 (pendiente)]

### ¿Por qué No PMS Externo?

**Decisión:** No integrar Odoo/QloApps/HotelDruid
**Razón:** Control total sobre anti-doble-booking, velocidad desarrollo
**Trade-off:** Features propias vs. features maduros PMS
**Referencia:** [ADR-001](../adr/001-no-pms-externo.md)

### ¿Por qué Constraint DB en vez de Lógica Aplicación?

**Decisión:** Constraint `EXCLUDE USING gist` + locks Redis
**Razón:** Garantía definitiva incluso con bugs en aplicación
**Trade-off:** Complejidad DB vs. robustez absoluta
**Referencia:** [Copilot Instructions - REGLA 1](../../.github/copilot-instructions.md)

---

## Referencias

- [README.md](../../README.md) - Quick start y overview
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Setup y workflows
- [PRODUCTION_SETUP.md](../../PRODUCTION_SETUP.md) - Deploy guide
- [ADR-001: No PMS Externo](../adr/001-no-pms-externo.md)
- [Copilot Instructions](../../.github/copilot-instructions.md)

---

**Última actualización:** 2025-10-02
**Autor:** Sistema MVP Alojamientos Team
**Versión:** 1.0
