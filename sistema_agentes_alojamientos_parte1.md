# Parte 1 de 5 — Documentación Integral del Sistema Agéntico MVP de Alojamientos

## Índice orientativo de la documentación (5 partes)

- **Parte 1** — Estrategia, Alcance, Requisitos, KPIs y Decisiones
- **Parte 2** — Blueprint técnico, modelo de datos, interfaces y seguridad
- **Parte 3** — Implementación, DevOps y calidad
- **Parte 4** — Diseño conversacional, NLU/STT/TTS, Dashboard y posicionamiento
- **Parte 5** — Checklists maestros y prompts para Gemini/Copilot

---

## 1) Resumen ejecutivo y objetivo central

**Objetivo:** Automatizar el 80% de las consultas y reservas (WhatsApp texto/audio y leads por email), gestionar disponibilidad en tiempo real sin doble-booking, procesar señas (QR/link) y mejorar posicionamiento en Para Irnos, Booking y Airbnb con respuesta ultra-rápida.

**Filosofía:** Base de datos central como única fuente de verdad; iCal como sincronización multicanal; automatización con supervisión humana mínima.

**Resultado esperado (30 días):**
- Tasa de automatización: ≥70%
- Conversión consulta→pre-reserva: ≥25%
- Cero doble-bookings
- Tiempo promedio respuesta: <30s texto, <15s audio

## 2) Alcance funcional MVP

### Canales y plataformas
- **WhatsApp Business Cloud API:** recepción/envío texto; audios a texto con Whisper; plantillas predefinidas
- **Email/IMAP:** lectura de leads; respuestas automáticas; threading básico
- **Plataformas:** Para Irnos, Booking, Airbnb vía iCal import/export + parsing emails

### Reservas y calendario
- Calendario central por unidad: disponibilidad y precio por fecha
- Pre-reservas con lock Redis (TTL 30 min), extensión manual (+15 min 1 vez)
- Confirmación de reserva al pagar seña o validar comprobante

### Pagos
- **Mercado Pago:** generación de link/QR de seña (30% por defecto, configurable), webhook confirmación
- **Alternativa:** adjuntar comprobante transferencia; confirmación en dashboard

### NLU y audio
- spaCy/es + reglas para intents/entidades; Whisper STT para audios
- TTS opcional (eSpeak-NG) para responder con audio en casos clave

### Dashboard staff
- Conversaciones activas, pre-reservas por vencer, comprobantes por verificar
- "Confirmar pago" y "Tomar conversación" en un clic

## 3) Principios de diseño

- **Single Source of Truth:** DB central; iCal como sincronización hacia/desde portales
- **Anti-doble booking por diseño:** locks Redis + validación antes de confirmar
- **Simplicidad operativa:** 2 clics/10 segundos para acciones críticas
- **Supervisión humana inteligente:** escalamiento automático con contexto
- **Costos bajos y open-source:** stack FOSS, APIs oficiales
- **Seguridad y privacidad:** HTTPS, firmas webhooks, mínimos datos sensibles

## 4) Requisitos funcionales (FR) y no funcionales (NFR)

### Requisitos Funcionales

**FR1 — Consulta disponibilidad:**
- Entrada: texto/audio con fechas, huéspedes, tipo unidad opcional
- Salida: lista unidades disponibles con precio total y CTA pre-reserva

**FR2 — Pre-reserva y lock:**
- Crear pre-reserva (estado pre_reserved) y lock Redis (TTL 30 min)
- Notificar vencimiento y permitir una extensión

**FR3 — Pago y confirmación:**
- Generar MP link/QR por % seña
- Consumir webhook pago y confirmar; alternativa manual con comprobante

**FR4 — Sincronización plataformas:**
- Import iCal portales cada 15 min; export iCal propio por unidad
- Resolver conflictos por prioridad de fuente y alertar solapes

**FR5 — Conversación multimodal:**
- Transcribir audio; si confianza < 0.6, pedir texto
- Mantener contexto conversación con estado

**FR6 — Dashboard staff:**
- Lista pre-reservas por vencer y comprobantes pendientes
- Confirmación en un clic; historial y estado del sistema

### Requisitos No Funcionales

**NFR1 — Rendimiento:** P95 texto < 3s; P95 audio < 15s
**NFR2 — Confiabilidad:** Uptime > 99%; 0% doble-booking
**NFR3 — Seguridad:** TLS, firma webhooks, roles mínimos, retención
**NFR4 — Observabilidad:** Health checks, logs estructurados, métricas, alertas
**NFR5 — Portabilidad:** Docker Compose; migrable SQLite a Postgres

## 5) Casos de uso y flujos por intent

### Intent: disponibilidad
- Extrae fechas y huéspedes (dateparser; regex; spaCy)
- Chequea DB central + bloques iCal; calcula precio
- Devuelve opciones y CTA "Hacer pre-reserva"

### Intent: reservar
- Crea pre-reserva + lock Redis; calcula seña; envía link/QR MP
- Indica vencimiento (30 min) y política extensión (+15 min)

### Intent: servicios/políticas/ubicación
- Respuestas directas desde campos accommodations.policies/amenities/location

### Fallback/habla con humano
- Marca conversación waiting_human; alerta propietario

### Contrato mensaje unificado (WhatsApp/Email):
```json
{
  "message_id": "str",
  "canal": "whatsapp|email",
  "user_id": "telefono|email",
  "timestamp_iso": "2025-09-23T12:00:00Z",
  "tipo": "text|audio|image|pdf",
  "texto": "str|null",
  "media_url": "str|null",
  "metadata": {
    "duration_sec": 12,
    "confidence_stt": 0.82
  }
}
```

## 6) KPIs, SLI/SLO y alertas

### KPIs de negocio
- Conversión consulta→pre-reserva ≥ 25%
- Conversión pre-reserva→confirmada ≥ 60%
- Tiempo consulta→reserva confirmada < 20 min
- Reviews: tasa respuesta follow-up ≥ 40%

### SLIs técnicos
- Latencia P95 texto/audio
- Error rate 5xx
- Desfase iCal (última sincronización)
- Precisión STT (proxy: % audios sin "request_text")

### SLOs y umbrales
- Texto P95 < 3s (warning > 4s; critical > 6s por 5 min)
- Audio P95 < 15s (warning > 20s; critical > 30s por 5 min)
- 5xx < 1% (warning > 3%; critical > 5% por 5 min)
- iCal desfase < 20 min (warning > 30; critical > 60)

### Alertas
- Warning: email/Slack/Discord
- Critical: SMS/WhatsApp al propietario + email

## 7) Datos, privacidad y retención (Ley 25.326 AR)

### Principios
- **Finalidad:** gestión de reservas y atención al huésped
- **Minimización:** no guardar datos sensibles fuera de necesidad operativa
- **Seguridad:** HTTPS, secretos en variables, firmas webhook

### Retención
- Conversaciones sin reserva: 60 días → anonimizar
- Audios: 30 días → eliminar
- Reservas confirmadas: según requisitos fiscales/contables

### Derechos de titulares
Mecanismo simple para acceso, rectificación y supresión

## 8) ADR — Registros de decisiones

**ADR-001** — Base de datos central vs PMS
- **Decisión:** DB central + iCal; no PMS en MVP
- **Razones:** simplicidad, control total, menor tiempo implementación

**ADR-002** — WhatsApp Business Cloud API (oficial)
- **Razón:** cumplimiento, estabilidad, documentación; evita bloqueos

**ADR-003** — MP (Mercado Pago) para señas
- **Razón:** adopción masiva en AR, webhook robusto, costo transacción aceptable

**ADR-004** — NLU: spaCy + reglas (Rasa opcional)
- **Razón:** bajo costo, suficiente para intents MVP; upgrade posterior si escala

**ADR-005** — STT: Whisper "base" local o faster-whisper
- **Razón:** calidad en español; costo nulo computacional local (VPS)

**ADR-006** — iCal como canal de sincronización
- **Razón:** estándar universal; evita integraciones API costosas/privadas

## 9) Riesgos y mitigaciones

### Principales riesgos
- **Falta iCal en plataforma:** parsing emails para bloqueos; prioridad manual
- **Desfasaje sincronización:** lock al crear pre-reserva; alertar conflictos
- **Caída WhatsApp/IMAP:** modo degradado con respuestas predefinidas
- **Rechazo pago/webhook fallido:** reintentos idempotentes; confirmación manual
- **STT baja confianza:** pedir texto; thresholds configurables

## 10) Criterios GO/NO-GO

### GO
- WhatsApp funcionando (texto+audio) con intents MVP
- Pre-reserva+lock Redis con TTL, vencimiento y extensión
- Pago MP con webhook y confirmación manual alternativa
- iCal import/export operativos sin conflictos en pruebas
- Dashboard: confirmar pagos, ver pre-reservas, calendario
- SLI/SLO mínimos: texto P95 < 3s; audio P95 < 15s; iCal < 20 min

### NO-GO
- Cualquier caso doble-booking en pruebas concurrentes
- Webhooks sin verificación; falta HTTPS; secretos expuestos
- Caída canal sin alerta crítica
- iCal con conflictos no detectados
- Staff no puede confirmar pagos en 2 clics

---

## Anexo — Blueprint de alto nivel

### Canales
- WhatsApp Webhook (Meta) → Message Gateway
- IMAP Poll (leads plataformas) → Message Gateway

### Orquestador (FastAPI)
- NLU (spaCy + reglas) y normalización fechas/personas
- Audio Pipeline (FFmpeg + Whisper)
- Reservation Service (locks Redis, pre-reservas, precios, confirmaciones)
- Payments (MP QR/link, webhook)
- iCal Service (import/export)
- Notifications/Alerts

### Persistencia
- PostgreSQL (reservas, calendario, conversaciones, pagos)
- Redis (locks, colas, caché corto)

### Dashboard
- FastAPI templates/Bootstrap: conversaciones, pre-reservas, comprobantes, calendario, métricas

---

# Parte 2 de 5 — Blueprint técnico, modelo de datos, interfaces y seguridad

## 1) Arquitectura lógica y de despliegue

### 1.1 Componentes principales
- **API Core (FastAPI + Uvicorn)**
  - Orquestación intents, reglas de negocio reservas, precios, pagos
  - Exposición webhooks (WhatsApp, Mercado Pago) y endpoints admin
- **NLU + Audio**
  - spaCy/es + reglas para intents/entidades
  - Pipeline STT: FFmpeg + faster-whisper para OGG/Opus de WhatsApp
  - TTS opcional (eSpeak-NG) para audio respuesta
- **Sincronización Calendarios**
  - Import iCal (Airbnb, Booking, Para Irnos, AlquilerArgentina)
  - Export iCal propio por unidad
- **Pagos**
  - Mercado Pago (preferencias, webhook, verificación server-to-server)
- **Persistencia**
  - PostgreSQL 16 (datos negocio, auditoría)
  - Redis 7 (locks, caché, colas ligeras)
- **Dashboard Staff**
  - FastAPI templates + Bootstrap/Alpine.js. Modo Operador
- **Jobs/Workers**
  - APScheduler para polling IMAP/ICal y limpieza pre-reservas vencidas

### 1.2 Dependencias y comunicación
- API Core → Postgres (SQLAlchemy/psycopg)
- API Core → Redis (aioredis)
- API Core → WhatsApp Cloud (HTTP Graph API)
- API Core → Mercado Pago (SDK/HTTP REST)
- API Core → IMAP/SMTP (imaplib/smtplib)
- Dashboard → API Core (REST/JSON)
- Jobs → API Core/DB (funciones internas + consultas directas)

### 1.3 Despliegue (Docker Compose)
- Servicios: api, postgres, redis, nginx, certbot, optional worker
- Health checks: /healthz (API), conexión DB y Redis
- Escalabilidad: api x N réplicas (stateless). Redis y Postgres únicos

## 2) Interfaces y contratos

### 2.1 Contrato mensaje unificado — JSON Schema
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "UnifiedMessage",
  "type": "object",
  "required": ["message_id", "canal", "user_id", "timestamp_iso", "tipo"],
  "properties": {
    "message_id": { "type": "string" },
    "canal": { "type": "string", "enum": ["whatsapp", "email"] },
    "user_id": { "type": "string" },
    "timestamp_iso": { "type": "string", "format": "date-time" },
    "tipo": { "type": "string", "enum": ["text", "audio", "image", "pdf"] },
    "texto": { "type": ["string", "null"] },
    "media_url": { "type": ["string", "null"], "format": "uri" },
    "metadata": {
      "type": "object",
      "properties": {
        "duration_sec": { "type": ["integer", "null"] },
        "confidence_stt": { "type": ["number", "null"], "minimum": 0, "maximum": 1 }
      }
    }
  }
}
```

### 2.2 WhatsApp Business Cloud API
- **Verificación webhook (GET):**
  - Parámetros hub.mode, hub.verify_token, hub.challenge
  - Responder 200 con hub.challenge si verify_token coincide
- **Recepción mensajes (POST /webhooks/whatsapp):**
  - Validar firma X-Hub-Signature-256
  - Parsear entry → changes → value → messages[]
  - Soportar tipos: text, audio
- **Envío mensajes (POST Graph /{PHONE_NUMBER_ID}/messages):**
  - Headers: Authorization: Bearer {ACCESS_TOKEN}
  - Ventana 24h para mensajes sesión. Fuera: plantilla preaprobada (HSM)

### 2.3 Mercado Pago
- **Crear preferencia (link/QR seña):**
  - Items: 1 x "Seña Reserva {code}"
  - external_reference = reservation_code
  - notification_url = https://tu-dominio/webhooks/mercadopago
- **Webhook (POST /webhooks/mercadopago):**
  - Validar firma X-Hmac-Signature o consultar MP
  - Idempotencia: usar external_reference (reservation_code)

### 2.4 iCal (RFC 5545)
- **Export (GET /ical/accommodation/{id}/{token}.ics):**
  - Generar ICS con VEVENT por reserva confirmada
- **Import (job cada 15 min):**
  - Descargar .ics por fuente
  - Mapear UID/FECHAS → availability_calendar con source = plataforma

## 3) Modelo de datos (PostgreSQL)

### 3.1 DDL principal
```sql
-- Alojamiento
CREATE TABLE accommodations (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  type TEXT CHECK (type IN ('cabaña','departamento','casa')) NOT NULL,
  capacity INT NOT NULL CHECK (capacity > 0),
  base_price NUMERIC(12,2) NOT NULL CHECK (base_price >= 0),
  description TEXT,
  amenities JSONB DEFAULT '[]',
  photos JSONB DEFAULT '[]',
  location JSONB,
  policies JSONB,
  ical_export_token VARCHAR(64) UNIQUE,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Calendario por día
CREATE TABLE availability_calendar (
  id BIGSERIAL PRIMARY KEY,
  accommodation_id INT REFERENCES accommodations(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  is_available BOOLEAN DEFAULT TRUE,
  price_override NUMERIC(12,2),
  season TEXT CHECK (season IN ('alta','media','baja','especial')),
  min_stay INT DEFAULT 1,
  source TEXT DEFAULT 'internal',
  UNIQUE (accommodation_id, date)
);

-- Reservas
CREATE TABLE reservations (
  id BIGSERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  accommodation_id INT REFERENCES accommodations(id) ON DELETE RESTRICT,
  guest_name VARCHAR(120) NOT NULL,
  guest_phone VARCHAR(30),
  guest_email VARCHAR(120),
  check_in DATE NOT NULL,
  check_out DATE NOT NULL,
  guests_count INT NOT NULL CHECK (guests_count > 0),
  total_price NUMERIC(12,2) NOT NULL CHECK (total_price >= 0),
  deposit_percentage INT DEFAULT 30,
  deposit_amount NUMERIC(12,2) NOT NULL CHECK (deposit_amount >= 0),
  payment_status TEXT CHECK (payment_status IN ('pending','partial','paid')) DEFAULT 'pending',
  reservation_status TEXT CHECK (reservation_status IN ('pre_reserved','confirmed','cancelled')) DEFAULT 'pre_reserved',
  channel_source TEXT,
  expires_at TIMESTAMP,
  confirmation_code VARCHAR(12),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  confirmed_at TIMESTAMP
);

-- Pagos
CREATE TABLE payment_records (
  id BIGSERIAL PRIMARY KEY,
  reservation_id BIGINT REFERENCES reservations(id) ON DELETE CASCADE,
  amount NUMERIC(12,2) NOT NULL,
  payment_method TEXT CHECK (payment_method IN ('mercadopago_qr','bank_transfer','cash')) NOT NULL,
  mp_payment_id VARCHAR(64),
  mp_preference_id VARCHAR(64),
  proof_image_url TEXT,
  verification_status TEXT CHECK (verification_status IN ('pending','verified','rejected')) DEFAULT 'pending',
  verified_by VARCHAR(64),
  verified_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Conversaciones WhatsApp
CREATE TABLE whatsapp_conversations (
  id BIGSERIAL PRIMARY KEY,
  phone_number VARCHAR(32) NOT NULL,
  guest_name VARCHAR(120),
  conversation_status TEXT CHECK (conversation_status IN ('active','waiting_human','resolved','escalated')) DEFAULT 'active',
  last_intent VARCHAR(64),
  context_data JSONB,
  escalated_at TIMESTAMP,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Mensajes
CREATE TABLE messages (
  id BIGSERIAL PRIMARY KEY,
  conversation_id BIGINT REFERENCES whatsapp_conversations(id) ON DELETE CASCADE,
  whatsapp_message_id VARCHAR(128),
  direction TEXT CHECK (direction IN ('incoming','outgoing')) NOT NULL,
  message_type TEXT CHECK (message_type IN ('text','audio','image','document')) NOT NULL,
  content TEXT,
  media_url TEXT,
  audio_duration INT,
  transcription TEXT,
  transcription_confidence NUMERIC(4,2),
  intent_detected VARCHAR(64),
  entities JSONB,
  response_time_ms INT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Prevención solapes — Exclusion Constraint
```sql
-- Requiere extensiones
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Agregar columna calculada para rango fechas
ALTER TABLE reservations ADD COLUMN period daterange
  GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED;

-- Excluir solapes por alojamiento cuando estado activo
ALTER TABLE reservations ADD CONSTRAINT no_overlap_reservations
  EXCLUDE USING gist (
    accommodation_id WITH =,
    period WITH &&
  )
  WHERE (reservation_status IN ('pre_reserved','confirmed'));
```

### 3.3 Eventos de dominio
```sql
CREATE TABLE domain_events (
  id BIGSERIAL PRIMARY KEY,
  event_type VARCHAR(80) NOT NULL,
  aggregate_type VARCHAR(80) NOT NULL,
  aggregate_id VARCHAR(64) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  processed_at TIMESTAMP
);
```

## 4) Locks anti doble-booking

### 4.1 Redis + DB (patrón híbrido)
- **Redis:** UX rápida y contención optimista
  - Key: `lock:acc:{accommodation_id}:{check_in}:{check_out}`
  - Valor: `{ session_id, phone, created_at, expires_at }`
  - TTL: 1800s (30 min), extensión +900s una vez
  - Comandos: `SET key val NX EX 1800`
- **DB:** Constraint no_overlap_reservations como autoridad final

### 4.2 Flujo atómico pre-reserva
1. **SETNX lock Redis.** Si falla → "ya reservado o en proceso"
2. **Calcular precio + insertar reservations** (pre_reserved) con period generado
   - Si DB lanza violación exclusión → liberar lock Redis y avisar "ya no disponible"
3. **Devolver code + expires_at,** generar preferencia MP si pidió reservar
4. **Limpieza:** job marca pre-reservas vencidas como cancelled

### 4.3 Extensión de lock
- Verificar que no esté vencido y siga pre_reserved
- `EXPIRE +900` y actualizar expires_at en fila reservations

## 5) Sincronización iCal

### 5.1 Import
- Cada 10-15 min por fuente/unidad:
  - Descargar ICS (retry con backoff)
  - Parse VEVENT → (UID, DTSTART, DTEND)
  - Upsert en imported_blocks (source, uid)
  - Reflejar bloqueos en availability_calendar

### 5.2 Export
- Endpoint ICS per-unit con token. Incluye reservas confirmed (no pre_reserved)

### 5.3 Resolución conflictos (prioridades)
**Prioridad por fuente:**
1. Propia confirmed (DB)
2. Booking
3. Airbnb
4. Para Irnos
5. Otros

## 6) Seguridad y secretos

### 6.1 Gestión secretos
**Variables entorno:**
- DATABASE_URL, REDIS_URL
- WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_ID, WHATSAPP_VERIFY_TOKEN
- MP_ACCESS_TOKEN, MP_WEBHOOK_SECRET
- SMTP_HOST, SMTP_USER, SMTP_PASS, IMAP_HOST, IMAP_USER, IMAP_PASS
- BASE_URL, DASHBOARD_SECRET, JWT_SECRET, ICS_SALT

### 6.2 Transporte y exposición
- HTTPS obligatorio (Nginx + Let's Encrypt)
- CORS cerrado al dashboard y dominios propios
- Rate limiting en /webhooks/* y /admin/*

### 6.3 Autenticación
- **Dashboard:** Login con JWT (rol OWNER, opcional STAFF). Sesión 24h
- **Admin API:** protegida Bearer JWT
- **Webhooks:** verificar X-Hub-Signature-256 (WhatsApp), firma MP

### 6.4 Auditoría y logs
- access_log (Nginx) y app logs JSON
- audit_log (tabla domain_events) para cambios estado reservas
- **Retención:** Logs app 30 días; conversaciones sin reserva 60 días → anonimizar; audios 30 días → eliminar

### 6.5 Backups y recuperación
- Backups diarios Postgres (pg_dump) con cifrado
- Política DR: RPO ≤ 24h, RTO ≤ 2h (MVP)

## 7) Endpoints principales

### 7.1 Health
```
GET /healthz → 200 { db:"ok", redis:"ok", whatsapp:"ok", mp:"ok", ical_age_min: 7 }
```

### 7.2 WhatsApp Webhook
```
GET /webhooks/whatsapp?hub.mode=...&hub.verify_token=... → 200 challenge
POST /webhooks/whatsapp (firma válida) → 200 {ok:true}
```

### 7.3 Mercado Pago Webhook
```
POST /webhooks/mercadopago → 200 {processed:true}
```

### 7.4 iCal
```
GET /ical/accommodation/{id}/{token}.ics → text/calendar 200
```

### 7.5 Admin
```
GET /admin/dashboard-data (JWT)
POST /admin/reservations/{id}/confirm-payment
POST /admin/pre-reservations/{id}/extend
POST /admin/conversations/{id}/escalate
```

## 8) Pseudocódigo clave

### 8.1 Pre-reserva (servicio)
```python
async def create_prereservation(acc_id, check_in, check_out, guest, channel):
    key = f"lock:acc:{acc_id}:{check_in}:{check_out}"
    if not await redis.set(key, "1", nx=True, ex=1800):
        return error("En proceso o no disponible")

    try:
        total = await pricing.calc_total(acc_id, check_in, check_out, guest.count)
        code = await codes.next("RES")  # RES240915001
        deposit = round(total * 0.30, 2)

        await db.insert_reservation(
            code=code, acc_id=acc_id, check_in=check_in, check_out=check_out,
            guests=guest.count, total=total, deposit=deposit,
            status="pre_reserved", channel=channel, expires_at=now()+30min)

        emit_event("PreReservationCreated", {"code": code, ...})
        return { "code": code, "expires_at": ..., "deposit": deposit }
    except DbExclusionViolation:
        await redis.delete(key)
        return error("Se acaba de ocupar, te propongo otras fechas")
    except Exception:
        await redis.delete(key)
        raise
```

### 8.2 Confirmación webhook MP
```python
async def mp_webhook(payload):
    payment_id = payload["data"]["id"]
    payment = await mp.get_payment(payment_id)
    code = payment["external_reference"]
    amount = Decimal(payment["transaction_amount"])
    status = payment["status"]

    if status == "approved":
        res = await db.get_reservation_by_code(code)
        if not res or res.status == "cancelled": return ok()

        await db.insert_payment(res.id, amount, "mercadopago_qr", 
                              mp_payment_id=payment_id, verification_status="verified")
        await db.update_reservation_status(code, payment_status="paid", 
                                         reservation_status="confirmed", confirmed_at=now())
        await redis.delete(f"lock:acc:{res.acc_id}:{res.check_in}:{res.check_out}")
        emit_event("ReservationConfirmed", {"code": code})
    return ok()
```