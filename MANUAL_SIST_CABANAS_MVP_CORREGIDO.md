# Sistema MVP de Automatización de Reservas - SIST_CABANAS_MVP
## Documentación de Implementación y Uso - VERSIÓN CORREGIDA v1.0.0

> **⚠️ IMPORTANTE**: Este documento refleja el estado REAL del código implementado al 12 de octubre de 2025.
> Basado en auditoría técnica completa del repositorio.

---

## RESUMEN EJECUTIVO

Sistema MVP de automatización de reservas de alojamientos que procesa consultas y gestiona reservas a través de **WhatsApp únicamente** (entrada), con procesamiento de lenguaje natural basado en reglas y sincronización bidireccional con plataformas (Airbnb/Booking vía iCal). Integra pagos con Mercado Pago, previene doble-booking mediante constraints PostgreSQL + locks Redis, y expone métricas de observabilidad para monitoreo en tiempo real. Diseñado para despliegue rápido (10-12 días) con arquitectura monolítica FastAPI + PostgreSQL 16 + Redis 7.

**Capacidades actuales:**
- ✅ Recepción por WhatsApp con botones interactivos
- ✅ Envío de emails SMTP (confirmaciones, recordatorios)
- ✅ Audio STT con faster-whisper (local, no OpenAI API)
- ✅ NLU basado en regex + dateparser
- ✅ Anti doble-booking (PostgreSQL EXCLUDE USING gist + Redis locks)
- ✅ Integración Mercado Pago con idempotencia
- ✅ Sincronización iCal bidireccional
- ✅ Métricas Prometheus + health checks
- ✅ Rate limiting con fail-open
- ✅ Circuit breaker y retry logic avanzados

**Limitaciones del MVP:**
- ❌ NO recibe emails (no hay cliente IMAP implementado)
- ❌ NO persiste historial de conversaciones (no hay tablas messages/conversations)
- ❌ Dashboard admin básico (solo CRUD de alojamientos vía API)
- ❌ Sin sistema de roles/autenticación completo
- ❌ Sin funcionalidad "Pausar Sistema" ni "Escalamiento a Humano" en UI

---

## PERSPECTIVA 1 — AGENTE IA: "¿QUÉ ES Y QUÉ HACE?"

### Descripción Ejecutiva

SIST_CABANAS_MVP es un sistema de automatización de reservas de cabañas/alojamientos que gestiona el ciclo completo: desde la consulta inicial del cliente **por WhatsApp** hasta la confirmación de pago y sincronización con plataformas externas. Opera mediante procesamiento de lenguaje natural basado en reglas (NLU con regex + dateparser), recibe mensajes por WhatsApp Business Cloud API, detecta intenciones (consultar disponibilidad, reservar, cancelar), valida contra inventario en tiempo real y ejecuta acciones transaccionales previniendo solapamientos. Integra Mercado Pago para cobros y mantiene sincronización bidireccional con calendarios iCal de Airbnb/Booking.

---

### Capacidades Detalladas (IMPLEMENTADAS)

#### 1. Recepción WhatsApp con Validación de Seguridad ✅

**Qué hace:** Recibe mensajes de WhatsApp Business Cloud API, valida firmas criptográficas (HMAC-SHA256 con header `X-Hub-Signature-256`) y normaliza a contrato unificado.

**Cuándo se activa:** Al recibir webhook POST en `/api/v1/webhooks/whatsapp`

**Resultado esperado:** Mensaje validado, normalizado con estructura:
```json
{
  "message_id": "wamid.xxx",
  "canal": "whatsapp",
  "user_id": "+5491112345678",
  "timestamp_iso": "2025-10-12T14:30:00Z",
  "tipo": "text|audio|interactive",
  "texto": "Hola, necesito reservar",
  "media_url": null,
  "metadata": {"button_id": "confirm_yes", "button_type": "reply"}
}
```

**Código fuente:** `backend/app/routers/whatsapp.py` (líneas 1-272)

**Características especiales:**
- Soporte para **botones interactivos** (`button_reply`, `list_reply`)
- Handler completo de callbacks en `backend/app/services/button_handlers.py` (1,842 líneas)
- 20+ callbacks implementados para flujos conversacionales

---

#### 2. Procesamiento de Lenguaje Natural Basado en Reglas (NLU) ✅

**Qué hace:** Analiza texto con patrones regex para detectar intenciones:
- `disponibilidad` (regex: `disponib|libre|hay`)
- `precio` (regex: `precio|costo|sale|cuanto`)
- `reservar` (regex: `reserv|apart|tomo`)
- `servicios` (regex: `servicio|incluye|wifi`)

Extrae entidades:
- Fechas con `dateparser` (settings DMY para Argentina)
- Rango de fechas con regex `(\d{1,2}/\d{1,2}) al (\d{1,2}/\d{1,2})`
- Fin de semana → próximo sábado-domingo
- Cantidad de personas con regex `(\d+)\s*(personas?|pax|huéspedes?)`

**Cuándo se activa:** Tras normalización del mensaje entrante en routers de WhatsApp.

**Resultado esperado:**
```json
{
  "intents": ["reservar"],
  "dates": ["2025-10-20", "2025-10-22"],
  "guests": 2
}
```

**Código fuente:** `backend/app/services/nlu.py` (líneas 1-100)

---

#### 3. Transcripción de Audio (STT) ✅

**Qué hace:** Convierte mensajes de voz WhatsApp (formato OGG/Opus) a texto usando **faster-whisper** (ejecución local, NO OpenAI API).

**Proceso:**
1. FFmpeg convierte OGG → WAV 16kHz mono
2. faster-whisper modelo "base" transcribe (language="es", compute_type="int8")
3. Evalúa confianza (threshold configurable: `AUDIO_MIN_CONFIDENCE=0.6`)
4. Si confianza baja → solicita mensaje de texto

**Cuándo se activa:** Al recibir mensaje WhatsApp con `type: audio`

**Resultado esperado:**
```json
{
  "text": "Hola necesito reservar para el fin de semana",
  "confidence": 0.87,
  "duration_sec": 4.2
}
```

**Código fuente:** `backend/app/services/audio.py` + endpoint `/audio/transcribe` en `backend/app/routers/audio.py`

---

#### 4. Validación de Disponibilidad con Prevención de Doble-Booking ✅ **CRÍTICO**

**Qué hace:**

**Paso 1 - Lock Redis:**
```python
lock_key = f"lock:acc:{accommodation_id}:{check_in}:{check_out}"
lock_value = str(uuid.uuid4())
acquired = await redis.set(lock_key, lock_value, nx=True, ex=1800)  # TTL 30 min
```

**Paso 2 - Constraint PostgreSQL:**
```sql
-- Columna generada automáticamente (NO mapeada en ORM SQLAlchemy)
ALTER TABLE reservations
ADD COLUMN period daterange
GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;

-- Constraint de exclusión (garantía ACID contra race conditions)
ALTER TABLE reservations
ADD CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (
  accommodation_id WITH =,
  period WITH &&
)
WHERE (reservation_status IN ('pre_reserved', 'confirmed'));
```

**Cuándo se activa:** Al procesar intent `consultar_disponibilidad` o previo a crear pre-reserva.

**Resultado esperado:**
- Si disponible → lock adquirido + query exitoso
- Si solapamiento → `IntegrityError` de PostgreSQL + lock liberado + métrica `RESERVATIONS_DATE_OVERLAP` incrementada

**Código fuente:**
- Lock: `backend/app/core/redis.py` (funciones `acquire_lock`, `release_lock`)
- Service: `backend/app/services/reservations.py` (método `create_prereservation`, líneas 60-165)
- Constraint SQL: `backend/alembic/versions/001_initial_schema.py` (líneas 117-125)

---

#### 5. Gestión de Pre-Reservas con Expiración Automática ✅

**Qué hace:**

1. Crea reserva con `reservation_status='pre_reserved'`
2. Calcula precio con multiplicadores de fin de semana:
   ```python
   weekend_multiplier = Decimal('1.2')  # Campo en tabla accommodations
   # Detecta sábados/domingos en rango de fechas
   weekend_nights = sum(1 for i in range(nights)
                        if (check_in + timedelta(days=i)).weekday() in (5, 6))
   weekday_nights = nights - weekend_nights
   total_price = (base_price * weekday_nights) + (base_price * weekend_mult * weekend_nights)
   ```
3. Genera código único de reserva (ej: `RES-A3B7-1012`)
4. Establece `expires_at` (default: 30 minutos después de `created_at`)
5. **[PENDIENTE VERIFICACIÓN]** Genera link de pago Mercado Pago
6. Envía link por WhatsApp
7. Lanza job background `expire_prereservations()` que revisa cada 60s (configurable `JOB_EXPIRATION_INTERVAL_SECONDS`)

**Cuándo se activa:** Tras confirmación explícita del usuario de disponibilidad y datos.

**Resultado esperado:**
```json
{
  "reservation_id": 12345,
  "code": "RES-A3B7-1012",
  "total_price": "15600.00",
  "payment_link": "https://mpago.li/abc123",
  "expires_at": "2025-10-12T15:00:00Z"
}
```

**Código fuente:**
- Service: `backend/app/services/reservations.py` (método `create_prereservation`)
- Background job: `backend/app/jobs/cleanup.py` (función `expire_prereservations`, líneas 25-110)
- Lanzamiento: `backend/app/main.py` (línea 57-73, `asyncio.create_task(expiration_worker())`)

---

#### 6. Integración de Pagos con Idempotencia ✅

**Qué hace:**

1. Procesa webhooks de Mercado Pago (`payment.created`, `payment.updated`)
2. Valida firma `x-signature` (formato: `ts=1234567890,v1=hash_hmac_sha256`)
3. Maneja idempotencia:
   - Tabla `payments` con campo `payment_external_id` UNIQUE
   - Tabla `idempotency_keys` para tracking de eventos webhook
4. Actualiza `reservation_status` a `confirmed` si pago aprobado
5. Envía email de confirmación con comprobante (SMTP)

**Cuándo se activa:** Al recibir POST en `/api/v1/mercadopago/webhook`

**Resultado esperado:**
```json
{
  "status": "ok",
  "payment_id": "MP-123456789",
  "idempotent": false,
  "reservation_id": 12345,
  "events_count": 1
}
```

**Código fuente:**
- Router: `backend/app/routers/mercadopago.py`
- Service: `backend/app/services/mercadopago.py` (método `process_webhook`)
- Validación firma: `backend/app/core/security.py` (función `verify_mercadopago_signature`)
- Modelo idempotencia: `backend/app/models/idempotency.py`

---

#### 7. Sincronización Bidireccional iCal (Airbnb/Booking) ✅

**Qué hace:**

**EXPORT:** Genera feed ICS con reservas `confirmed` y `pre_reserved` no expiradas:
```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MVP Alojamientos//ES
BEGIN:VEVENT
UID:RES-A3B7-1012@acc3
DTSTART;VALUE=DATE:20251020
DTEND;VALUE=DATE:20251022
SUMMARY:RESERVA RES-A3B7-1012
X-CODE:RES-A3B7-1012
X-SOURCE:WHATSAPP
END:VEVENT
END:VCALENDAR
```

**IMPORT:** Consume URLs iCal externas:
- Parser simplificado (busca bloques `BEGIN:VEVENT...END:VEVENT`)
- Extrae `UID`, `DTSTART`, `DTEND`, `SUMMARY`
- Crea bloqueos como reservas con:
  - `channel_source='airbnb'` o `'booking'`
  - `code='BLK-<hash_corta_del_UID>'`
  - `internal_notes` almacena UID original para dedupe
- Evita duplicación buscando UID en `internal_notes` existentes

**Job periódico:** Cada 300 segundos (5 min, configurable `JOB_ICAL_INTERVAL_SECONDS`)

**Cuándo se activa:**
- Export: GET `/api/v1/ical/export/{accommodation_id}?token={ical_export_token}`
- Import: Background worker `ical_worker()` en `backend/app/main.py` (línea 76-89)

**Resultado esperado:**
- Export: Calendario .ics descargable
- Import: N eventos creados, gauge `ical_last_sync_age_minutes` actualizado, campo `last_ical_sync_at` en tabla `accommodations`

**Código fuente:**
- Service: `backend/app/services/ical.py` (clases `ICalService`)
- Router: `backend/app/routers/ical.py`
- Background job: `backend/app/jobs/import_ical.py` (función `run_ical_sync`)

---

#### 8. Limitación de Velocidad y Observabilidad ✅

**Rate Limiting:**
- Middleware Redis per-IP+path
- Default: 60 requests / 60 segundos (configurable `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS`)
- Key pattern: `ratelimit:{client_ip}:{path}`
- Bypass en: `/api/v1/healthz`, `/api/v1/readyz`, `/metrics`
- Fail-open: Si Redis falla, permite tráfico (log error + métrica `RATE_LIMIT_REDIS_ERRORS`)
- Respuesta 429 Too Many Requests si excede límite

**Observabilidad Prometheus:**
- Instrumentación: `prometheus-fastapi-instrumentator`
- Endpoint: `/metrics` (no incluido en schema OpenAPI)
- Métricas custom:
  ```python
  # Gauge de sincronización iCal
  ical_last_sync_age_minutes = Gauge("ical_last_sync_age_minutes", "Minutes since last iCal sync", ["accommodation_id"])

  # Contadores de reservas
  RESERVATIONS_CREATED = Counter("reservations_created_total", "Total reservations created", ["channel", "status"])
  RESERVATIONS_CONFIRMED = Counter("reservations_confirmed_total", "Total reservations confirmed", ["channel"])
  RESERVATIONS_DATE_OVERLAP = Counter("reservations_date_overlap_total", "Date overlap attempts", ["channel"])
  RESERVATIONS_LOCK_FAILED = Counter("reservations_lock_failed_total", "Redis lock failures", ["channel"])

  # Rate limiting
  RATE_LIMIT_BLOCKED = Counter("rate_limit_requests_blocked_total", "Requests blocked by rate limit", ["path", "client_ip"])
  RATE_LIMIT_CURRENT_COUNT = Gauge("rate_limit_current_count", "Current request count in window", ["client_ip", "path"])
  RATE_LIMIT_REDIS_ERRORS = Counter("rate_limit_redis_errors_total", "Redis errors in rate limiting")

  # Background jobs
  PRE_RESERVATIONS_EXPIRED = Counter("pre_reservations_expired_total", "Expired pre-reservations")
  PRE_RESERVATIONS_REMINDERS_SENT = Counter("pre_reservations_reminders_sent_total", "Reminders sent")
  ICAL_IMPORT_SUCCESS = Counter("ical_import_success_total", "Successful iCal imports")
  ICAL_IMPORT_ERROR = Counter("ical_import_error_total", "Failed iCal imports")
  ```

**Cuándo se activa:**
- Rate limit: En cada request HTTP (middleware en `backend/app/main.py`, líneas 155-214)
- Métricas: Scraping externo de Prometheus desde `/metrics`

**Resultado esperado:**
- Protección contra abuse
- Métricas disponibles para Grafana/AlertManager

**Código fuente:**
- Middleware: `backend/app/main.py` (función `rate_limit`)
- Métricas: `backend/app/metrics.py` (declaración de todas las métricas)
- Tests: `backend/tests/test_rate_limiting.py`, `backend/tests/test_metrics.py`

---

### Características Técnicas del Comportamiento

#### Latencias y Tiempos de Respuesta (SLOs)

| Operación | Target P95 | Warning | Critical |
|-----------|------------|---------|----------|
| ACK webhook | < 500 ms | > 800 ms | > 1000 ms |
| NLU + query DB | < 3 s | > 4 s | > 6 s |
| Audio transcription | < 15 s | > 20 s | > 30 s |
| Payment webhook | < 2 s | > 3 s | > 5 s |

**Timeouts configurados:**
- ⚠️ **NO hay timeouts explícitos** para APIs externas (WhatsApp, Mercado Pago)
- ⚠️ **NO hay timeout** configurado para database sessions
- **RECOMENDACIÓN:** Agregar timeout HTTP client y DB session timeout

---

#### Estructura de Mensajes y Flujo Conversacional

**Procesamiento stateless:**
- Cada mensaje es analizado independientemente
- **NO se persiste historial** de conversaciones (no existen tablas `messages` ni `conversations` en el MVP)
- Logs estructurados a stdout capturan eventos pero no en BD relacional

**Confirmación antes de acción crítica:**
```
Sistema: "Tengo disponibilidad en Cabaña A del 20 al 22 de octubre por $12,000 (2 noches). ¿Confirmás la reserva?"
Usuario: "sí" | "confirmar" | "dale"
→ Sistema procede a crear pre-reserva
```

**Plantillas predefinidas:**
- Respuestas estructuradas en `backend/app/services/messages.py`
- Templates para: disponibilidad, confirmación, error, fallback
- Personalización por alojamiento (nombre, capacidad, precio)

---

#### Reglas de Fallback y Escalamiento

**Intent no detectado:**
```
"No entendí tu solicitud. Podés preguntar por disponibilidad (ej: 'Disponibilidad para 2 personas del 20 al 22 de octubre'), consultar estado de reserva o cancelar."
```

**Error de API externa:**
- **Retry logic avanzado:** Decorador `@retry_async` en `backend/app/utils/retry.py`
  - Max attempts: configurable (default 3)
  - Backoff exponencial: `delay = base_delay * (2 ** attempt)` con jitter
  - Retry en: `Timeout`, `ConnectionError`, `500`, `502`, `503`, `504`
  - NO retry en: `400`, `401`, `403`, `404`
  - Métricas: `RETRY_ATTEMPTS`, `RETRY_FAILURES`, `RETRY_DELAY_SECONDS`

**Circuit breaker:**
- Implementado en `backend/app/utils/circuit_breaker.py`
- Estados: `CLOSED` → `OPEN` → `HALF_OPEN`
- Configuración:
  ```python
  failure_threshold=5,  # Fallos consecutivos para abrir
  recovery_timeout=60,  # Segundos en estado OPEN
  success_threshold=2   # Éxitos para cerrar desde HALF_OPEN
  ```
- Métricas: `CIRCUIT_BREAKER_STATE_CHANGES`, `CIRCUIT_BREAKER_REJECTIONS`

**Pago rechazado:**
- Notificación automática al cliente
- Pre-reserva permanece activa hasta `expires_at`
- Puede reintentar pago con mismo link (idempotencia garantizada)

**⚠️ Escalamiento a humano - NO IMPLEMENTADO:**
- No existe flag `requires_human_attention` en modelos
- No hay funcionalidad "Transferir a Operador" en el MVP
- **Workaround temporal:** Monitorear logs con `intent="desconocido"` y contactar manualmente

---

## PERSPECTIVA 2 — DUEÑO/ADMINISTRADOR: "¿CÓMO GESTIONO Y CONTROLO?"

### ⚠️ NOTA IMPORTANTE: Dashboard Admin en MVP

El MVP **NO incluye un dashboard web completo** como se describe en el documento original. La funcionalidad administrativa actual es:

**✅ LO QUE SÍ EXISTE:**
- API REST básica para CRUD de alojamientos (en `backend/app/routers/admin.py`)
- Endpoint `/api/v1/admin/accommodations` (GET, POST, PUT, DELETE)
- Endpoint `/api/v1/admin/reservations` (GET, PUT para actualizar estado)
- Health check endpoint `/api/v1/healthz` con detalles de sistema
- Métricas Prometheus en `/metrics` para monitoreo externo

**❌ LO QUE NO EXISTE:**
- UI/Dashboard web con login
- Sistema de autenticación JWT con roles (admin/operador/auditor)
- Función "Pausar Sistema" desde UI
- Función "Transferir a Operador" / gestión de conversaciones
- Modal de "Historial de Conversación" (no hay tabla `messages` ni `conversations`)
- Editor de templates de respuesta en UI
- Exportación de datos desde UI (CSV/Excel)

### Acceso al Sistema (Estado Real)

**CLI de Desarrollo (equipo técnico):**

Comandos Make disponibles en `Makefile`:
```bash
make up      # Levanta stack completo (PostgreSQL + Redis + backend)
make logs    # Tail de logs en tiempo real
make test    # Ejecuta suite pytest
make test-e2e # Tests end-to-end del flujo completo
make migrate  # Aplica migraciones Alembic a PostgreSQL
make shell   # Abre shell interactivo en contenedor backend
make down    # Detiene y limpia containers
```

**Acceso a Métricas:**
- URL: `https://[tu-dominio]/metrics` (Prometheus scraping)
- Health check: `https://[tu-dominio]/api/v1/healthz`
- Logs: `docker logs -f sist_cabanas_backend` o `make logs`

**Acceso a Base de Datos:**
```bash
# Conectar a PostgreSQL directamente
docker exec -it sist_cabanas_postgres psql -U postgres -d cabanas_db

# Ver reservas activas
SELECT code, guest_name, check_in, check_out, reservation_status
FROM reservations
WHERE reservation_status IN ('pre_reserved', 'confirmed')
ORDER BY created_at DESC;
```

---

### Métricas Clave que Puede Monitorear

#### Endpoint `/api/v1/healthz` - Health Check

**Respuesta JSON:**
```json
{
  "status": "healthy",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 12
    },
    "redis": {
      "status": "ok",
      "latency_ms": 3,
      "connected_clients": 2,
      "used_memory_mb": 1.2
    },
    "ical_sync": {
      "status": "ok",
      "last_sync_minutes_ago": 8,
      "threshold_minutes": 30
    }
  },
  "timestamp": "2025-10-12T15:32:00Z"
}
```

**Códigos de estado:**
- `200`: Healthy (todos los checks OK)
- `200` con `status: "degraded"`: iCal stale pero sistema funcional
- `503`: Unhealthy (DB o Redis caído)

**Referencia:** `backend/app/routers/health.py`

---

#### Endpoint `/metrics` - Métricas Prometheus

**Métricas implementadas:**

```promql
# Latencia por endpoint (histograma)
http_request_duration_seconds{method="POST",path="/api/v1/webhooks/whatsapp"}

# Contador de requests
http_requests_total{method="POST",path="/api/v1/webhooks/whatsapp",status="200"}

# Gauge de sincronización iCal (minutos desde última sync)
ical_last_sync_age_minutes{accommodation_id="uuid"}

# Contadores de reservas
reservations_created_total{channel="whatsapp",status="pre_reserved"}
reservations_created_total{channel="whatsapp",status="confirmed"}

# Errores de locks Redis
reservations_lock_failed_total{channel="whatsapp"}
reservations_date_overlap_total{channel="whatsapp"}

# Rate limiting
rate_limit_blocked_total{path="/api/v1/webhooks/whatsapp"}

# Circuit breaker
circuit_breaker_state{service="mercadopago"}  # 0=CLOSED, 1=OPEN, 2=HALF_OPEN
circuit_breaker_rejections_total{service="whatsapp"}

# Retry logic
retry_attempts_total{function="send_whatsapp_message"}
retry_failures_total{function="send_whatsapp_message"}
```

**Referencia:** `backend/app/metrics.py`

---

### KPIs Críticos y Umbrales de Alerta

| Métrica | Umbral Crítico | Acción Sugerida | Cómo Verificar |
|---------|---------------|-----------------|----------------|
| Tasa de error del sistema | > 2% en ventana de 10 min | Revisar logs, verificar conectividad con PostgreSQL/Redis/APIs externas | `rate(http_requests_total{status=~"5.."}[10m]) > 0.02` |
| Latencia P95 > 10 segundos | En cualquier endpoint | Escalar recursos (CPU/RAM), revisar queries SQL lentas | `histogram_quantile(0.95, http_request_duration_seconds) > 10` |
| `ical_last_sync_age_minutes` | > 60 minutos | Verificar URLs iCal de Airbnb/Booking, revisar logs del job scheduler | `ical_last_sync_age_minutes > 60` |
| Redis connection errors | > 5 en 5 min | Reiniciar contenedor Redis, verificar memoria disponible | `docker logs sist_cabanas_redis \| grep -i error` |
| Pago rechazado (rate > 30%) | En últimas 50 transacciones | Contactar soporte de Mercado Pago, revisar configuración de cuenta | Query manual a DB: `SELECT COUNT(*) FROM reservations WHERE payment_status='rejected'` |
| Locks Redis sin liberar | TTL expirado pero lock persiste | Flush manual de keys antiguas: `redis-cli KEYS "lock:acc:*"` | `redis-cli --scan --pattern "lock:acc:*"` |

---

### Funcionalidades de Control Disponibles

#### 1. Gestión de Alojamientos (API REST)

**Listar alojamientos:**
```bash
curl -X GET https://[tu-dominio]/api/v1/admin/accommodations
```

**Crear alojamiento:**
```bash
curl -X POST https://[tu-dominio]/api/v1/admin/accommodations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cabaña Nueva",
    "type": "cabin",
    "capacity": 6,
    "base_price": 15000,
    "description": "Cabaña con vista al lago",
    "amenities": ["wifi", "cocina", "aire_acondicionado"],
    "ical_url": "https://airbnb.com/calendar/ical/..."
  }'
```

**Actualizar alojamiento:**
```bash
curl -X PUT https://[tu-dominio]/api/v1/admin/accommodations/{id} \
  -H "Content-Type: application/json" \
  -d '{"base_price": 18000, "active": true}'
```

**Referencia:** `backend/app/routers/admin.py`

---

#### 2. Gestión de Reservas (API REST)

**Listar reservas con filtros:**
```bash
# Todas las reservas activas
curl "https://[tu-dominio]/api/v1/admin/reservations?status=confirmed&status=pre_reserved"

# Reservas por rango de fechas
curl "https://[tu-dominio]/api/v1/admin/reservations?check_in_from=2025-10-20&check_in_to=2025-10-31"
```

**Cancelar reserva manualmente:**
```bash
curl -X PUT https://[tu-dominio]/api/v1/admin/reservations/{id} \
  -H "Content-Type: application/json" \
  -d '{"reservation_status": "cancelled", "notes": "Cancelado por cliente"}'
```

**Confirmar reserva manualmente (pago offline):**
```bash
curl -X PUT https://[tu-dominio]/api/v1/admin/reservations/{id} \
  -H "Content-Type: application/json" \
  -d '{"payment_status": "approved", "reservation_status": "confirmed"}'
```

---

#### 3. Forzar Sincronización iCal

**❌ No existe endpoint específico en el MVP**

**Workaround:** Reiniciar el worker de iCal
```bash
# El worker se auto-ejecuta cada N minutos (configurado en settings.ICAL_SYNC_INTERVAL_MINUTES)
# Para forzar: reiniciar el contenedor backend
docker restart sist_cabanas_backend

# O ejecutar manualmente el script
docker exec -it sist_cabanas_backend python -m app.jobs.import_ical
```

**Referencia:** `backend/app/jobs/import_ical.py`, `backend/app/main.py` líneas 73-89

---

#### 4. Monitoreo de Logs Estructurados

**Filtrar por eventos específicos:**
```bash
# Ver webhooks de WhatsApp recibidos
docker logs sist_cabanas_backend | grep '"event":"whatsapp_webhook_received"'

# Ver errores de validación de firma
docker logs sist_cabanas_backend | grep '"event":"whatsapp_signature_invalid"'

# Ver reservas creadas
docker logs sist_cabanas_backend | grep '"event":"reservation_created"'

# Ver pagos procesados
docker logs sist_cabanas_backend | grep '"event":"payment_processed"'
```

**Logs JSON estructurados (formato):**
```json
{
  "timestamp": "2025-10-12T15:32:00.123Z",
  "level": "INFO",
  "logger": "app.routers.whatsapp",
  "event": "whatsapp_webhook_received",
  "message_id": "wamid.ABC123...",
  "user_id": "+5491112345678",
  "type": "text",
  "intent": "consultar_disponibilidad",
  "duration_ms": 234
}
```

---

### Queries SQL Útiles para Administración

**Ver reservas por estado:**
```sql
SELECT
  reservation_status,
  COUNT(*) as total,
  SUM(total_price) as revenue
FROM reservations
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY reservation_status
ORDER BY total DESC;
```

**Detectar locks Redis activos:**
```bash
redis-cli --scan --pattern "lock:acc:*" | wc -l
```

**Ver tasa de conversión (últimos 7 días):**
```sql
SELECT
  DATE(created_at) as fecha,
  COUNT(CASE WHEN reservation_status = 'pre_reserved' THEN 1 END) as pre_reservas,
  COUNT(CASE WHEN reservation_status = 'confirmed' THEN 1 END) as confirmadas,
  ROUND(
    COUNT(CASE WHEN reservation_status = 'confirmed' THEN 1 END)::numeric /
    NULLIF(COUNT(CASE WHEN reservation_status IN ('pre_reserved', 'confirmed') THEN 1 END), 0) * 100,
    2
  ) as tasa_conversion_pct
FROM reservations
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY fecha DESC;
```

**Verificar constraint de doble-booking:**
```sql
-- Intentar crear reserva solapada (debe fallar con EXCLUDE constraint error)
INSERT INTO reservations (
  uuid, code, accommodation_id, guest_name, guest_phone,
  check_in, check_out, guests_count, reservation_status
) VALUES (
  gen_random_uuid(), 'TEST001',
  (SELECT id FROM accommodations LIMIT 1),
  'Test', '+1234567890',
  '2025-10-20', '2025-10-22', 2, 'confirmed'
);
```

---

## PERSPECTIVA 3 — CLIENTE / USUARIO FINAL: "¿CÓMO USO ESTO?"

### Descripción de la Experiencia

El cliente inicia la interacción enviando un mensaje a través de **WhatsApp** (al número del negocio). No necesita descargar aplicaciones adicionales ni registrarse previamente. El sistema responde de manera automática y conversacional, detectando su intención (consultar disponibilidad, realizar reserva, cancelar, etc.) y guiándolo paso a paso.

**⚠️ IMPORTANTE:** El sistema **NO recibe emails** de clientes. Solo envía confirmaciones por email (SMTP saliente).

---

### ¿Qué Puede Pedirle al Sistema?

✅ **FUNCIONALIDADES IMPLEMENTADAS:**

1. **Consultar disponibilidad:**
   - Ejemplo: "Hola, necesito una cabaña para 4 personas del 20 al 22 de octubre."
   - El sistema valida disponibilidad en tiempo real

2. **Hacer una reserva:**
   - Tras confirmar disponibilidad, solicita datos faltantes (fechas, cantidad de personas)
   - Genera link de pago de Mercado Pago
   - Crea pre-reserva con expiración (default 30 min)

3. **Consultar estado de reserva:**
   - Ejemplo: "¿Cómo va mi reserva?" o "Estado de reserva #12345"
   - Proporciona información actualizada del estado de pago

4. **Enviar mensajes de voz:**
   - Puede enviar mensajes de audio por WhatsApp
   - El sistema los transcribe automáticamente usando faster-whisper
   - Luego procesa el texto transcrito con NLU

5. **Confirmar acciones con botones interactivos:**
   - El sistema envía botones de WhatsApp para confirmaciones
   - Ejemplo: "¿Confirmás la reserva?" → Botones [Sí] [No]
   - Implementado en `backend/app/services/button_handlers.py` (1,842 líneas)

❌ **LIMITACIONES:**

- No maneja consultas generales de turismo (ej: "¿Qué hay para hacer en la zona?")
- No procesa imágenes ni documentos adjuntos de WhatsApp
- No puede cancelar reservas confirmadas automáticamente (requiere contacto manual)
- No mantiene contexto conversacional entre sesiones
- No puede modificar fechas de reservas existentes directamente

---

### Flujo Típico de Interacción (Paso a Paso)

#### Escenario: Cliente reserva cabaña para fin de semana

**Paso 1: Inicio de Conversación**
- Cliente envía mensaje por WhatsApp: "Hola, quiero reservar una cabaña para el fin de semana."

**Paso 2: Extracción de Datos Faltantes**
- Sistema detecta intent `consultar_disponibilidad` pero falta información
- Respuesta automática: "¡Hola! Para ayudarte mejor, necesito saber: ¿Para cuántas personas? ¿Qué fechas específicas (ej: del 20 al 22 de octubre)?"

**Paso 3: Cliente Completa Datos**
- Cliente: "Para 2 personas, del 20 al 22 de octubre."

**Paso 4: Consulta de Disponibilidad**
- Sistema valida contra PostgreSQL (constraint EXCLUDE gist), adquiere lock Redis
- Respuesta: "¡Perfecto! Tengo disponibilidad en **Cabaña A** (capacidad 6 personas) del 20 al 22 de octubre por **$12,000** (2 noches). ¿Confirmás la reserva?"

**Paso 5: Confirmación del Cliente**
- Cliente: "Sí, confirmar." (o puede usar botón interactivo [Confirmar])

**Paso 6: Creación de Pre-Reserva y Link de Pago**
- Sistema crea reserva con `status=pre_reserved`, genera link de Mercado Pago
- Respuesta: "Reserva pre-confirmada! Tu código es **#12345**. Para completar, realizá el pago aquí: https://mpago.li/abc123 (válido por 30 minutos). Te avisamos cuando se confirme el pago."

**Paso 7: Cliente Realiza Pago**
- Cliente hace click en link, completa pago con tarjeta/otro método
- Mercado Pago envía webhook a sistema con `payment.updated`

**Paso 8: Confirmación Final**
- Sistema valida firma x-signature, actualiza reserva a `status=confirmed`
- Mensaje automático por WhatsApp: "✅ Pago confirmado! Tu reserva #12345 en **Cabaña A** del 20 al 22 de octubre está confirmada."
- Email automático con comprobante enviado a dirección registrada

**Paso 9 (Opcional): Recordatorio Automático**
- ⚠️ **NO IMPLEMENTADO en el MVP actual**
- Planeado: 24 hs antes del check-in enviar recordatorio con dirección

---

### Ejemplo de Conversación Real

**Diálogo Completo (WhatsApp):**

```
[15:30] 👤 Cliente (Juan):
Hola, cuánto sale una cabaña para 4 personas?

[15:30] 🤖 Sistema:
Hola Juan! Para darte el precio exacto, necesito las fechas.
¿Del X al X de qué mes? Por ejemplo: "del 20 al 22 de octubre".

[15:32] 👤 Cliente:
Del 25 al 27 de este mes

[15:32] 🤖 Sistema:
Perfecto! Tengo disponibilidad en **Cabaña B** (capacidad 6 personas)
del 25 al 27 de octubre por **$18,000** (2 noches).
¿Confirmás la reserva?

[Botones interactivos: Sí | No | Ver otras opciones]

[15:34] 👤 Cliente:
[Presiona botón "Sí"]

[15:34] 🤖 Sistema:
Reserva pre-confirmada! Tu código es **#12347**.

Para completar, realizá el pago aquí: https://mpago.li/xyz789
(válido por 30 minutos).

Te avisamos cuando se confirme el pago. 🙌

[15:40] 👤 Cliente:
Ya pagué!

[15:40] 🤖 Sistema:
Estamos verificando tu pago (puede demorar 1-2 minutos).
Te avisamos apenas se confirme 👍

[15:42] 🤖 Sistema:
✅ Pago confirmado!

Tu reserva #12347 en **Cabaña B** del **25 al 27 de octubre** está confirmada.

Te enviamos comprobante por email y los datos de acceso 24 hs antes del check-in.

¡Gracias por elegirnos! 🏡
```

---

### Canales de Acceso

#### WhatsApp Business ✅

**Número:** +54 9 11 XXXX-XXXX *(reemplazar con número real configurado en WhatsApp Business Cloud API)*

**Cómo contactar:**
- Agregar número a contactos y enviar mensaje
- Escanear QR code publicado en sitio web (redirect a `wa.me/[numero]`)

**Disponibilidad:** 24/7 (respuestas automáticas inmediatas)

**Características:**
- Soporte para mensajes de texto y audio (transcripción automática)
- Botones interactivos para confirmaciones (implementado)
- Mensajes multimedia: puede recibir imágenes/documentos pero no los procesa
- Rate limiting: 10 mensajes por minuto por usuario (configurable)

**Referencia:** `backend/app/routers/whatsapp.py`, `backend/app/services/button_handlers.py`

---

#### Email (Solo Salida) ✅

**Dirección:** reservas@[tu-dominio].com

**⚠️ IMPORTANTE:** El sistema **NO recibe emails de clientes** (no hay cliente IMAP).

**Uso actual:**
- **Solo envío SMTP** de confirmaciones automáticas:
  - Comprobante de pago tras confirmación
  - (Futuro) Recordatorios 24hs antes del check-in
  - (Futuro) Instrucciones de acceso

**No puede:**
- Procesar consultas enviadas por email
- Responder a emails de clientes automáticamente

**Referencia:** `backend/app/services/email.py` (solo funciones de envío SMTP)

---

#### Fallback para Urgencias

**Teléfono de contacto directo:** +54 9 11 YYYY-YYYY *(atención humana en horario comercial)*

**Email de soporte:** soporte@[tu-dominio].com *(para problemas técnicos)*

---

### Descripción Textual de Captura de Pantalla (Mockup de Chat WhatsApp)

**Escena:** Ventana de WhatsApp Web/App mostrando conversación con el Sistema

#### Elementos Visuales:

**Encabezado del Chat:**
- Avatar: Logo de la empresa (círculo, esquina superior izquierda)
- Nombre: "Cabañas [Nombre del Negocio]" (negrita)
- Estado: "en línea" (texto verde debajo del nombre)
- Botones: Ícono de videollamada y teléfono (deshabilitados/grisados), ícono de menú (tres puntos verticales)

**Historial de Mensajes** (fondo con wallpaper típico de WhatsApp):

1. **Mensaje del Cliente** (burbuja verde claro, alineada a derecha):
   ```
   Hola, necesito una cabaña para 4 personas del 25 al 27 de octubre
   ```
   Timestamp: `15:32` (gris, pequeño, debajo de la burbuja)

2. **Mensaje del Sistema** (burbuja blanca, alineada a izquierda):
   ```
   Perfecto! Tengo disponibilidad en **Cabaña B** (capacidad 6 personas)
   del 25 al 27 de octubre por **$18,000** (2 noches).
   ¿Confirmás la reserva?
   ```
   Timestamp: `15:32`
   Indicador de lectura: ✓✓ (doble check gris)

3. **Botones Interactivos** (debajo del mensaje del sistema):
   ```
   [Botón: Sí, confirmar]  [Botón: No, gracias]  [Botón: Ver otras opciones]
   ```

4. **Mensaje del Cliente** (verde claro, derecha):
   ```
   [Usuario presionó botón "Sí, confirmar"]
   ```
   Timestamp: `15:34`

5. **Mensaje del Sistema** (blanco, izquierda):
   ```
   Reserva pre-confirmada! Tu código es **#12347**.

   Para completar, realizá el pago aquí:
   https://mpago.li/xyz789
   (válido por 30 minutos).

   Te avisamos cuando se confirme el pago. 🙌
   ```
   Timestamp: `15:34`
   Elemento adicional: Link aparece subrayado y en azul (clicable)

6. **Mensaje del Sistema** (blanco, izquierda):
   ```
   ✅ Pago confirmado!

   Tu reserva #12347 en **Cabaña B** del **25 al 27 de octubre** está confirmada.

   Te enviamos comprobante por email y los datos de acceso 24 hs antes del check-in.

   ¡Gracias por elegirnos! 🏡
   ```
   Timestamp: `15:42`

**Input Area** (parte inferior del chat):
- Campo de texto: Placeholder "Escribe un mensaje" (gris claro)
- Botones:
  - Ícono de 😊 (selector de emojis)
  - Ícono de 📎 (adjuntar archivo)
  - Ícono de 🎤 (grabar audio - destacado en verde si activo)
  - Botón de envío ✈️ (verde)

**Indicadores Visuales Especiales:**
- Mensaje con link de pago: Resaltado con borde sutil azul o ícono de 💳 al lado del link
- Mensaje de confirmación: Emoji ✅ al inicio para destacar éxito
- Cronometraje: Marcas de tiempo visibles en formato 24hs (HH:MM)

---

## ANEXO TÉCNICO - Información Complementaria

### Comandos de Desarrollo (Referencia Rápida)

```bash
# Levantar stack completo
make up

# Ver logs en tiempo real
make logs

# Ejecutar tests (requiere containers corriendo)
make test

# Tests end-to-end (incluye flujo completo con Postgres real)
make test-e2end

# Aplicar migraciones de base de datos
make migrate

# Abrir shell en container backend
make shell

# Detener y limpiar
make down

# Acceso directo a PostgreSQL
docker exec -it sist_cabanas_postgres psql -U postgres -d cabanas_db

# Acceso a Redis CLI
docker exec -it sist_cabanas_redis redis-cli
```

**Referencia:** `Makefile` en raíz del proyecto

---

### Arquitectura de Base de Datos

#### Tablas Principales Implementadas

**1. `accommodations` (Alojamientos)**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID PK | Identificador único |
| `uuid` | UUID UNIQUE | UUID para uso externo |
| `name` | VARCHAR(255) | Nombre del alojamiento |
| `type` | VARCHAR(50) | Tipo (cabin, apartment, room) |
| `capacity` | INTEGER | Capacidad máxima de huéspedes |
| `base_price` | DECIMAL(10,2) | Precio base por noche |
| `weekend_multiplier` | DECIMAL(3,2) | Multiplicador fines de semana (default 1.2) |
| `description` | TEXT | Descripción completa |
| `amenities` | JSONB | Servicios (ej: `["wifi", "cocina", "ac"]`) |
| `photos` | JSONB | URLs de fotos |
| `location` | JSONB | Datos de ubicación |
| `policies` | JSONB | Políticas de check-in/out, cancelación |
| `ical_url` | TEXT | URL iCal externa (Airbnb/Booking) |
| `ical_export_token` | VARCHAR(64) UNIQUE | Token para export iCal |
| `active` | BOOLEAN | Estado activo/inactivo |
| `created_at` | TIMESTAMPTZ | Fecha de creación |
| `updated_at` | TIMESTAMPTZ | Última actualización |

**Referencia:** `backend/app/models/accommodation.py`

---

**2. `reservations` (Reservas)**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID PK | Identificador único |
| `uuid` | UUID UNIQUE | UUID para uso externo |
| `code` | VARCHAR(20) UNIQUE | Código corto (ej: "ABC123") |
| `accommodation_id` | UUID FK | Referencia a alojamiento |
| `guest_name` | VARCHAR(255) | Nombre del huésped |
| `guest_phone` | VARCHAR(20) | Teléfono de contacto |
| `guest_email` | VARCHAR(255) NULLABLE | Email del huésped |
| `check_in` | DATE | Fecha de ingreso |
| `check_out` | DATE | Fecha de salida |
| `period` | DATERANGE | **GENERADO:** `daterange(check_in, check_out, '[)')` |
| `guests_count` | INTEGER | Cantidad de personas |
| `total_price` | DECIMAL(10,2) | Precio total calculado |
| `deposit_percentage` | DECIMAL(5,2) | % de seña (default 30) |
| `deposit_amount` | DECIMAL(10,2) | Monto de seña calculado |
| `payment_status` | ENUM | pending, approved, rejected, refunded |
| `reservation_status` | ENUM | pending, pre_reserved, confirmed, cancelled, expired |
| `payment_external_id` | VARCHAR(255) UNIQUE NULLABLE | ID de Mercado Pago |
| `payment_link` | TEXT NULLABLE | URL de pago generada |
| `channel_source` | VARCHAR(50) | whatsapp, email, api |
| `expires_at` | TIMESTAMPTZ NULLABLE | Timestamp de expiración pre-reserva |
| `confirmation_code` | VARCHAR(10) NULLABLE | Código de confirmación |
| `notes` | TEXT NULLABLE | Notas adicionales |
| `created_at` | TIMESTAMPTZ | Fecha de creación |
| `confirmed_at` | TIMESTAMPTZ NULLABLE | Fecha de confirmación de pago |
| `updated_at` | TIMESTAMPTZ | Última actualización |

**Constraints Críticos:**
```sql
-- Constraint anti doble-booking (IMPLEMENTADO)
CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (
  accommodation_id WITH =,
  period WITH &&
)
WHERE (reservation_status IN ('pre_reserved', 'confirmed'));

-- Check constraints
CONSTRAINT check_dates CHECK (check_out > check_in),
CONSTRAINT check_guests CHECK (guests_count > 0)
```

**⚠️ IMPORTANTE:** La columna `period` es **GENERADA por SQL** y NO existe en el modelo SQLAlchemy ORM.

**Referencia:**
- `backend/app/models/reservation.py`
- `backend/alembic/versions/001_initial_schema.py` líneas 117-125

---

**3. `ical_syncs` (Sincronizaciones iCal)**

| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | UUID PK | Identificador único |
| `accommodation_id` | UUID FK | Referencia a alojamiento |
| `source_url` | TEXT | URL iCal externa |
| `last_sync_at` | TIMESTAMPTZ | Última sincronización exitosa |
| `status` | VARCHAR(20) | success, failed |
| `events_imported` | INTEGER | Cantidad de eventos importados |
| `error_message` | TEXT NULLABLE | Mensaje de error si falló |
| `created_at` | TIMESTAMPTZ | Fecha de creación |

**Referencia:** `backend/app/services/ical.py`

---

#### Tablas NO Implementadas (del Documento Original)

❌ **`messages` - NO EXISTE:**
El documento original describe una tabla `messages` con campos:
- `id`, `conversation_id`, `message_id_external`, `canal`, `sender_user_id`
- `timestamp`, `tipo`, `contenido_raw`, `contenido_procesado`
- `intent_detectado`, `entidades_extraidas`, `respuesta_enviada`
- `estado_procesamiento`

**Realidad:** Esta tabla NO está implementada. Los mensajes se procesan stateless sin persistencia de historial conversacional.

---

❌ **`conversations` - NO EXISTE:**
El documento original describe una tabla `conversations` para mantener estado conversacional.

**Realidad:** No hay gestión de conversaciones persistentes. Cada mensaje se procesa independientemente.

---

### Constraint Crítico Anti Doble-Booking (Detalle Técnico)

#### SQL de Creación

```sql
-- 1. Activar extensión btree_gist (requerida para EXCLUDE con tipos no-geométricos)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 2. Agregar columna generada automáticamente
ALTER TABLE reservations
ADD COLUMN period daterange
GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;

-- 3. Crear índice GiST con constraint de exclusión
ALTER TABLE reservations
ADD CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (
  accommodation_id WITH =,
  period WITH &&
)
WHERE (reservation_status IN ('pre_reserved', 'confirmed'));
```

#### ¿Por Qué es Crítico?

Sin este constraint, dos requests simultáneos podrían:
1. Ambas verifican disponibilidad → ambas ven "disponible"
2. Ambas intentan insertar reserva → ambas exitosas
3. **Resultado: Doble-booking** ❌

**Con el constraint:**
1. Request A verifica disponibilidad → "disponible"
2. Request B verifica disponibilidad → "disponible"
3. Request A inserta reserva → **OK**
4. Request B intenta insertar → **IntegrityError** (constraint violation)
5. Sistema maneja error y notifica "ya no disponible"

**El lock Redis es complementario** (previene race conditions leves), pero el constraint PostgreSQL es la **única garantía ACID**.

**Referencia:**
- `database/init.sql` líneas 80-95
- `backend/alembic/versions/001_initial_schema.py`
- Tests: `backend/tests/test_double_booking.py`, `backend/tests/test_constraint_validation.py`

---

### Estructura de Métricas Prometheus (Completo)

#### Métricas Expuestas en `/metrics`

```promql
# === HTTP Request Metrics ===
# Latencia por endpoint (histograma)
http_request_duration_seconds_bucket{method="POST",path="/api/v1/webhooks/whatsapp",le="0.1"}
http_request_duration_seconds_bucket{method="POST",path="/api/v1/webhooks/whatsapp",le="0.5"}
http_request_duration_seconds_bucket{method="POST",path="/api/v1/webhooks/whatsapp",le="1.0"}
http_request_duration_seconds_sum{method="POST",path="/api/v1/webhooks/whatsapp"}
http_request_duration_seconds_count{method="POST",path="/api/v1/webhooks/whatsapp"}

# Contador de requests
http_requests_total{method="POST",path="/api/v1/webhooks/whatsapp",status="200"}
http_requests_total{method="POST",path="/api/v1/webhooks/whatsapp",status="403"}
http_requests_total{method="POST",path="/api/v1/webhooks/whatsapp",status="500"}

# === Reservations Metrics ===
# Contador de reservas creadas
reservations_created_total{channel="whatsapp",status="pre_reserved"} 45
reservations_created_total{channel="whatsapp",status="confirmed"} 32

# Errores de locks Redis
reservations_lock_failed_total{channel="whatsapp"} 2

# Conflictos de solapamiento
reservations_date_overlap_total{channel="whatsapp"} 5

# === iCal Sync Metrics ===
# Gauge: minutos desde última sincronización exitosa
ical_last_sync_age_minutes{accommodation_id="uuid-cabaña-a"} 8.5
ical_last_sync_age_minutes{accommodation_id="uuid-cabaña-b"} 12.3

# Contador de sincronizaciones
ical_sync_total{accommodation_id="uuid-cabaña-a",status="success"} 120
ical_sync_total{accommodation_id="uuid-cabaña-a",status="failed"} 2

# === Rate Limiting Metrics ===
# Requests bloqueados por rate limit
rate_limit_blocked_total{path="/api/v1/webhooks/whatsapp"} 15

# === Circuit Breaker Metrics ===
# Estado del circuit breaker (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
circuit_breaker_state{service="mercadopago"} 0
circuit_breaker_state{service="whatsapp"} 0

# Requests rechazados (circuit abierto)
circuit_breaker_rejections_total{service="whatsapp"} 0

# Cambios de estado
circuit_breaker_state_changes_total{service="mercadopago",from="CLOSED",to="OPEN"} 1

# === Retry Logic Metrics ===
# Intentos de retry
retry_attempts_total{function="send_whatsapp_message"} 23

# Reintentos fallidos (agotados max attempts)
retry_failures_total{function="send_whatsapp_message"} 2

# Delays acumulados por reintentos
retry_delay_seconds_sum{function="send_whatsapp_message"} 45.6
```

#### Queries Útiles para Alertas (Prometheus/AlertManager)

```yaml
# Alerta: Tasa de error alta
- alert: HighErrorRate
  expr: |
    rate(http_requests_total{status=~"5.."}[5m]) > 0.02
  for: 10m
  labels:
    severity: critical
  annotations:
    summary: "Tasa de error > 2% durante 10 minutos"
    description: "{{ $value | humanizePercentage }} de requests con error 5xx"

# Alerta: Latencia P95 alta
- alert: HighLatencyP95
  expr: |
    histogram_quantile(0.95,
      rate(http_request_duration_seconds_bucket[5m])
    ) > 10
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Latencia P95 > 10 segundos"

# Alerta: iCal sync antiguo
- alert: StaleICalSync
  expr: |
    ical_last_sync_age_minutes > 60
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Sincronización iCal retrasada > 60 min"
    description: "Alojamiento {{ $labels.accommodation_id }}"

# Alerta: Circuit breaker abierto
- alert: CircuitBreakerOpen
  expr: |
    circuit_breaker_state == 1
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Circuit breaker OPEN para {{ $labels.service }}"
    description: "Sistema de protección activado por fallos repetidos"
```

**Referencia:** `backend/app/metrics.py`

---

### Seguridad - Validación de Firmas (Código de Referencia)

#### Webhook de WhatsApp (HMAC-SHA256)

```python
import hmac
import hashlib

def verify_whatsapp_signature(signature: str, payload: bytes, secret: str) -> bool:
    """
    Valida firma X-Hub-Signature-256 de webhook WhatsApp

    Args:
        signature: Header "X-Hub-Signature-256" (formato: "sha256=hash")
        payload: Body del request (bytes sin procesar)
        secret: WHATSAPP_APP_SECRET de settings

    Returns:
        bool: True si firma válida, False caso contrario
    """
    if not signature or not signature.startswith("sha256="):
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
```

**⚠️ IMPORTANTE:** Usar `hmac.compare_digest()` para prevenir timing attacks.

**Referencia:** `backend/app/routers/whatsapp.py` líneas 45-60

---

#### Webhook de Mercado Pago (firma x-signature)

```python
import hmac
import hashlib
from urllib.parse import parse_qs

def verify_mp_signature(headers: dict, query_params: dict, secret: str) -> bool:
    """
    Valida firma x-signature de webhook Mercado Pago

    Header format: "ts=1234567890,v1=hash_value"
    Manifest: "id" + "data.id" + "ts"

    Args:
        headers: Headers del request
        query_params: Query params (?id=X&topic=Y&data.id=Z)
        secret: MERCADOPAGO_WEBHOOK_SECRET de settings

    Returns:
        bool: True si firma válida
    """
    signature = headers.get("x-signature")
    if not signature:
        return False

    # Parsear header: ts=...,v1=...
    parts = dict(item.split("=") for item in signature.split(","))
    ts = parts.get("ts")
    v1_hash = parts.get("v1")

    if not ts or not v1_hash:
        return False

    # Construir manifest
    manifest = f"{query_params.get('id')}{query_params.get('data.id')}{ts}"

    # Calcular hash esperado
    expected_hash = hmac.new(
        secret.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(v1_hash, expected_hash)
```

**Referencia:** `backend/app/routers/mercadopago.py` líneas 38-72

**⚠️ CRÍTICO:** NUNCA omitir validación de firmas en producción. Atacantes podrían enviar webhooks falsos para:
- Marcar reservas como "confirmadas" sin pagar
- Crear reservas fraudulentas
- Cancelar reservas legítimas

---

### Health Check - Criterios de Estado (Detallado)

#### Endpoint `/api/v1/healthz`

**Códigos de estado HTTP:**
- `200`: Sistema healthy o degraded
- `503`: Sistema unhealthy (DB o Redis caídos)

**Respuesta JSON:**
```json
{
  "status": "healthy",  // "healthy" | "degraded" | "unhealthy"
  "checks": {
    "database": {
      "status": "ok",  // "ok" | "slow" | "error"
      "latency_ms": 12
    },
    "redis": {
      "status": "ok",
      "latency_ms": 3,
      "connected_clients": 2,
      "used_memory_mb": 1.2,
      "peak_memory_mb": 2.5
    },
    "ical_sync": {
      "status": "ok",  // "ok" | "stale" | "error"
      "last_sync_minutes_ago": 8,
      "threshold_minutes": 30,
      "accommodations_count": 3
    }
  },
  "timestamp": "2025-10-12T15:32:00Z",
  "version": "1.0.0"
}
```

**Lógica de Estado:**

1. **Healthy:** Todos los checks "ok", latencias dentro de umbrales
2. **Degraded:** Algún check "slow" o "stale", pero sistema funcional
3. **Unhealthy:** DB o Redis "error", sistema no operativo

**Umbrales:**
- DB latency > 500ms → status "slow" → degraded
- Redis latency > 200ms → status "slow" → degraded
- iCal sync > 30 min → status "stale" → degraded
- iCal sync > 60 min → status "stale" → unhealthy (opcional)
- DB error → unhealthy (503)
- Redis error → unhealthy (503)

**Referencia:** `backend/app/routers/health.py`

---

### Configuración de Environment Variables

**Archivo `.env.template` (completar con valores reales):**

```bash
# === Database ===
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/cabanas_db

# === Redis ===
REDIS_URL=redis://localhost:6379/0

# === WhatsApp Business Cloud API ===
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_BUSINESS_ACCOUNT_ID=123456789012345
WHATSAPP_ACCESS_TOKEN=EAAxxxxx...
WHATSAPP_APP_SECRET=abc123...  # Para validar firmas

# === Mercado Pago ===
MERCADOPAGO_ACCESS_TOKEN=APP_USR-xxxxx...
MERCADOPAGO_PUBLIC_KEY=APP_USR-xxxxx...
MERCADOPAGO_WEBHOOK_SECRET=abc123...  # Para validar x-signature

# === SMTP (Email Saliente) ===
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=reservas@tudominio.com
SMTP_PASSWORD=xxxxx...
SMTP_FROM_EMAIL=reservas@tudominio.com
SMTP_FROM_NAME=Sistema de Reservas

# === Application ===
APP_ENV=production  # development | production
DEBUG=false
LOG_LEVEL=INFO

# === Security ===
SECRET_KEY=generate-a-random-secret-key-here
ALLOWED_ORIGINS=https://tudominio.com,https://www.tudominio.com

# === Rate Limiting ===
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_BURST=20

# === Reservations ===
PRERESERVATION_EXPIRATION_MINUTES=30
WEEKEND_PRICE_MULTIPLIER=1.2

# === iCal Sync ===
ICAL_SYNC_INTERVAL_MINUTES=15
ICAL_SYNC_MAX_AGE_MINUTES=30  # Para health check

# === Background Jobs ===
EXPIRATION_CHECK_INTERVAL_MINUTES=5
```

**Referencia:** `backend/app/core/config.py`

---

### Diagramas de Arquitectura (Descripción Textual)

#### Diagrama 1: Flujo de Procesamiento de Reserva

```
[Cliente WhatsApp]
       |
       | Mensaje de texto/audio
       v
[WhatsApp Cloud API]
       |
       | Webhook POST
       v
[Nginx Reverse Proxy]
       |
       | Rate Limiting (per-IP)
       v
[FastAPI Backend]
       |
       |---> [Validar Firma HMAC-SHA256]
       |     |
       |     |--> ❌ Inválida → 403 Forbidden
       |     |
       |     |--> ✅ Válida
       |             |
       |             v
       |     [Normalizar Mensaje]
       |             |
       |             |---> Si tipo=audio:
       |             |     [FFmpeg OGG→WAV] → [faster-whisper STT]
       |             |
       |             v
       |     [NLU: Detectar Intent (regex + dateparser)]
       |             |
       |             |---> Intent: consultar_disponibilidad
       |             |     |
       |             |     v
       |             [Adquirir Lock Redis]
       |             |     (lock:acc:{id}:{checkin}:{checkout})
       |             |     TTL 1800s
       |             |
       |             v
       |     [Query PostgreSQL]
       |             |
       |             |---> Verificar EXCLUDE USING gist
       |             |     constraint sobre period
       |             |
       |             |---> ✅ Disponible
       |             |     |
       |             |     v
       |             [Enviar Opciones + Botones WhatsApp]
       |             |
       |             v
       |     [Usuario Confirma]
       |             |
       |             v
       |     [Crear Pre-Reserva]
       |             |     (status: pre_reserved)
       |             |     (expires_at: NOW() + 30 min)
       |             |
       |             v
       |     [Generar Link Pago Mercado Pago]
       |             |
       |             v
       |     [Enviar Link por WhatsApp + Email SMTP]
       |             |
       |             v
       |     [Background Job: Monitor Expiration]
       |
       v
[Cliente Paga en Mercado Pago]
       |
       | Webhook payment.updated
       v
[FastAPI Backend]
       |
       |---> [Validar Firma x-signature]
       |     |
       |     |--> ❌ Inválida → 403 Forbidden
       |     |
       |     |--> ✅ Válida
       |             |
       |             v
       |     [Verificar Idempotencia]
       |             |     (payment_external_id UNIQUE)
       |             |
       |             v
       |     [UPDATE reservations]
       |             |     SET status='confirmed'
       |             |     WHERE uuid=X
       |             |
       |             v
       |     [Enviar Confirmación WhatsApp + Email]
       |             |
       |             v
       |     [Liberar Lock Redis]
       |
       v
[Fin del Flujo]
```

---

#### Diagrama 2: Sincronización iCal (Background Job)

```
[Background Worker]
  (lanzado en app/main.py lifespan)
       |
       | Cada 15 minutos (configurable)
       v
[Iterar sobre accommodations.ical_url != NULL]
       |
       v
[Fetch URL iCal Externa]
       |     (ej: Airbnb calendar feed)
       |
       |---> ❌ Timeout/Error
       |     |
       |     v
       |     [Log Error + Update ical_syncs.status='failed']
       |     |
       |     v
       |     [Continuar con siguiente]
       |
       |---> ✅ Éxito
       |     |
       |     v
       [Parsear Eventos iCal]
       |     (icalendar library)
       |
       v
[Filtrar Eventos Futuros]
       |     (DTSTART >= TODAY)
       |
       v
[Para cada evento:]
       |
       |---> [Verificar si ya existe en DB]
       |     |     (por ical_uid unique)
       |     |
       |     |--> Ya existe: Skip
       |     |
       |     |--> No existe:
       |           |
       |           v
       |     [Crear Reserva "Externa"]
       |           |     source='ical'
       |           |     reservation_status='confirmed'
       |           |     (bloqueo de calendario)
       |           |
       |           v
       |     [PostgreSQL INSERT]
       |           |     (puede fallar por EXCLUDE constraint
       |           |      si hay solapamiento → esperado)
       |
       v
[Update ical_syncs]
       |     last_sync_at=NOW()
       |     status='success'
       |     events_imported=N
       |
       v
[Update Prometheus Metric]
       |     ical_last_sync_age_minutes.set(0)
       |
       v
[Sleep hasta próximo intervalo]
```

**Referencia:** `backend/app/services/ical.py`, `backend/app/main.py` líneas 73-89

---

### Testing Strategy (Resumen)

#### Tests Implementados

**1. Unitarios (`backend/tests/test_*.py`):**
- `test_nlu.py`: Detección de intents con regex
- `test_audio.py`: Transcripción con faster-whisper (mock)
- `test_reservations.py`: Lógica de creación de reservas
- `test_circuit_breaker.py`: Estados CLOSED/OPEN/HALF_OPEN
- `test_retry.py`: Retry logic con backoff exponencial

**2. Integración:**
- `test_double_booking.py`: **Requiere PostgreSQL real con btree_gist**
  - Verifica que constraint EXCLUDE previene solapamientos
  - Test concurrente con threading
- `test_constraint_validation.py`: Validación de check constraints
- `test_whatsapp_webhook.py`: Validación de firmas
- `test_mercadopago_webhook.py`: Idempotencia de pagos

**3. End-to-End:**
- `make test-e2e`: Flujo completo de reserva con todos los servicios corriendo

**Configuración:**
- `pytest.ini`: Configuración de pytest
- `backend/tests/conftest.py`: Fixtures compartidas (DB session, Redis client, HTTP client)

**⚠️ Nota Importante:** Tests de overlap de fechas **DEBEN ejecutarse contra PostgreSQL real**, NO SQLite. SQLite no soporta `EXCLUDE USING gist`.

---

### Roadmap Post-MVP (Funcionalidades Planeadas)

**❌ NO IMPLEMENTADAS - Futuro:**

1. **Persistencia de Conversaciones:**
   - Tablas `messages` y `conversations`
   - Historial completo de interacciones
   - Contexto conversacional entre sesiones

2. **Cliente Email IMAP:**
   - Recepción de consultas por email
   - Polling cada 5 minutos
   - Procesamiento igual que WhatsApp

3. **Dashboard Admin Completo:**
   - UI web con React/Vue
   - Autenticación JWT con roles
   - Gestión de conversaciones en tiempo real
   - Editor de templates
   - Exportación CSV/Excel
   - Función "Pausar Sistema"
   - Función "Transferir a Operador"

4. **Recordatorios Automáticos:**
   - Email 24hs antes del check-in
   - Instrucciones de acceso
   - Google Maps link

5. **Multi-idioma:**
   - Detección automática de idioma
   - Respuestas en español/inglés/portugués

6. **Analytics Avanzado:**
   - Dashboard de métricas de negocio
   - Funnel de conversión
   - Tiempo promedio de respuesta por tipo de consulta

---

## CONCLUSIÓN

Este documento refleja el estado **real** del sistema SIST_CABANAS_MVP al 12 de octubre de 2025.

**✅ Funcionalidades Core Implementadas:**
- Recepción WhatsApp con botones interactivos
- NLU basado en regex + dateparser
- Anti doble-booking (PostgreSQL EXCLUDE + Redis locks)
- Integración Mercado Pago con idempotencia
- Sincronización iCal bidireccional
- Audio STT con faster-whisper (local)
- Circuit breaker y retry logic avanzados
- Métricas Prometheus + health checks
- Rate limiting con fail-open

**❌ Limitaciones del MVP:**
- NO recibe emails (solo envío SMTP)
- NO persiste historial conversacional
- Dashboard admin básico (solo API REST)
- Sin sistema de roles/autenticación completo

**📚 Este documento debe ser compartido con:**
- **Equipo de producto:** Para presentaciones y roadmap
- **Operaciones:** Como manual de monitoreo y troubleshooting
- **Desarrolladores:** Para onboarding y referencia técnica
- **Usuarios finales:** Sección 3 como base para FAQ

---

**Versión:** 1.0.0 (Corregida)
**Fecha:** 12 de octubre de 2025
**Repositorio:** github.com/eevans-d/SIST_CABANAS_MVP
**Branch:** main
