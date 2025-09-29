# Sistema Agéntico MVP - Documentación Definitiva para Desarrollo con IA

## Contexto y Filosofía del Proyecto

### 🎯 Visión del Sistema
**Sistema Agéntico MVP de Alojamientos** - Automatización completa de consultas y reservas para cabañas/departamentos en 10-12 días de desarrollo:
- **Canales**: WhatsApp Business API (texto/audio) + Email/IMAP.
- **Core**: Disponibilidad en tiempo real, pre-reservas con locks Redis, pagos Mercado Pago.
- **Sincronización**: iCal import/export (Airbnb, Booking, Para Irnos).
- **Stack Fijo**: FastAPI + PostgreSQL + Redis + Whisper STT + Dashboard staff.

### ⚡ Regla 0 - Principios Fundamentales para Gemini/Copilot
```
CONTEXTO: Sistema MVP reservas alojamientos - 10-12 días desarrollo
OBJETIVO: Código FUNCIONAL, NO perfecto - SHIPPING > elegancia
STACK FIJO: FastAPI/Postgres/Redis + integraciones específicas (WA/MP/iCal)
FILOSOFÍA: DONE IS BETTER THAN PERFECT
REGLAS NO NEGOCIABLES:
1. IMPLEMENTAR SOLO LO PEDIDO - Cero feature creep
2. SOLUCIÓN MÁS SIMPLE - Primera opción que funcione
3. VALIDAR ANTES DE CONTINUAR - Tests básicos obligatorios
4. NO REFACTORIZAR - Si pasa tests, no tocar
5. MVP SCOPE LOCK - Resistir sobrediseño
STOP CONDITIONS: Cuando cumple criterios GO/NO-GO = PARAR optimización
```

### 🚫 Anti-Patrones Críticos (Prohibidos)
- ❌ **Feature Creep**: "Sería fácil agregar...", "Ya que estamos...", "Por completitud...".
- ❌ **Sobreingeniería**: Abstracciones innecesarias, optimizaciones sin métricas.
- ❌ **Perfeccionismo**: Refactorizar código funcional, buscar "elegancia".
- ❌ **Scope Expansion**: Múltiples providers pago, channel manager propio.
- ❌ **Premature Optimization**: Cache sin evidencia lentitud, microservicios.

## Fases de Desarrollo Replanificadas

### Fase 1: Fundación Sólida (Días 1-3)

#### Día 1: Scaffolding Completo
```
OBJETIVO: Infraestructura base desplegable
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Crear estructura completa proyecto backend FastAPI
CONTEXTO: Sistema reservas alojamientos, stack FastAPI+Postgres+Redis+Docker
ESTRUCTURA EXACTA:
backend/
├── app/
│ ├── main.py (FastAPI app + CORS + middleware)
│ ├── core/ (config.py Settings, logging.py JSON, auth.py JWT)
│ ├── routers/ (webhooks.py, admin.py, health.py, ical.py)
│ ├── services/ (whatsapp.py, mercadopago.py, audio.py, nlu.py, reservations.py)
│ ├── models/ (sqlalchemy ORM completos)
│ ├── jobs/ (scheduler.py, import_ical.py, cleanup.py)
│ └── utils/ (helpers, validators)
├── requirements.txt (VERSIONES FIJAS - no >= ni ~)
├── Dockerfile (Python 3.11 slim + ffmpeg)
└── docker-compose.yml (postgres:16, redis:7, api, nginx)
ENTREGABLES:
- .env.template con TODAS variables comentadas
- /healthz endpoint funcional
- Conexión DB/Redis validada
- Comandos docker-compose up funcionando
CRITERIO ÉXITO: docker-compose up sin errores, /healthz 200
STOP CONDITION: Infraestructura estable conectada, NO optimizar configs
---
```

#### Día 2: Modelos + Constraint Anti-Doble-Booking
```
OBJETIVO: Base datos con prevención doble-booking 100% garantizada
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Modelos SQLAlchemy + migración con constraint exclusión crítico
CONTEXTO: Prevención doble-booking es CRÍTICA - fallo = proyecto fallido
MODELOS EXACTOS (NO agregar campos):
1. accommodations: id, name, type, capacity, base_price, description, amenities JSONB,
   photos JSONB, location JSONB, policies JSONB, ical_export_token, active, created_at
2. reservations: id, code UNIQUE, accommodation_id FK, guest_name, guest_phone,
   guest_email, check_in, check_out, guests_count, total_price, deposit_percentage,
   deposit_amount, payment_status, reservation_status, channel_source, expires_at,
   confirmation_code, notes, created_at, confirmed_at
3. availability_calendar, payment_records, whatsapp_conversations, messages,
   imported_blocks, pricing_rules, domain_events
CONSTRAINT CRÍTICO (NO NEGOCIABLE):
- CREATE EXTENSION btree_gist;
- period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED
- CONSTRAINT no_overlap_reservations EXCLUDE USING gist
  (accommodation_id WITH =, period WITH &&)
  WHERE (reservation_status IN ('pre_reserved','confirmed'))
TESTS OBLIGATORIOS:
- test_no_double_booking(): dos reservas solapadas → IntegrityError
- test_consecutive_ok(): reservas consecutivas → success
- test_cancelled_no_block(): reserva cancelled no interfiere
CRITERIO ÉXITO: Constraint previene 100% doble-booking
STOP CONDITION: Anti-solape funciona, NO validaciones extra
---
```

#### Día 3: Locks Redis + Pre-Reservas
```
OBJETIVO: Sistema locks temporales con TTL y extensión
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: ReservationService con locks Redis anti-doble-booking
CONTEXTO: Pre-reservas 30min + extensión opcional 15min
IMPLEMENTAR EXACTAMENTE:
class ReservationService:
    async def create_prereservation(accommodation_id, check_in, check_out, guests, channel, contact):
        # 1. Lock Redis: SET lock:acc:{id}:{checkin}:{checkout} value NX EX 1800
        # 2. Si lock falla → {"error": "En proceso o no disponible"}
        # 3. Calcular precio: base_price * noches * multiplicadores
        # 4. INSERT reservation (pre_reserved, expires_at=now+30min)
        # 5. Si DB constraint falla → DELETE lock, return error
        # 6. Return {"code": "RES240915001", "expires_at": ..., "deposit": ...}
    async def extend_prereservation(reservation_id):
        # Solo si no vencida y no ya extendida (flag)
        # EXPIRE lock +900, UPDATE expires_at +15min
    async def cancel_expired():
        # UPDATE reservations SET status='cancelled' WHERE expires_at < now()
PRICING BÁSICO:
- base_price * noches * weekend_multiplier(1.2) * holiday_multiplier(1.5)
- Código: RES{YYMMDD}{NNN} formato
TESTS CRÍTICOS:
- Concurrencia: create_prereservation simultáneo → solo uno éxito
- Extensión: extend_prereservation funciona UNA sola vez
- Limpieza: cancel_expired elimina vencidas
CRITERIO ÉXITO: Locks previenen doble-booking, TTL respetado
STOP CONDITION: Concurrencia controlada, NO optimizar limpieza
---
```

### Fase 2: Integración Canales (Días 4-6)

#### Día 4: WhatsApp Webhook Completo
```
OBJETIVO: Comunicación bidireccional WhatsApp segura
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Router WhatsApp Business Cloud API con verificación firma
CONTEXTO: Seguridad crítica - firma inválida = vulnerabilidad
IMPLEMENTAR:
1. GET /webhooks/whatsapp (verificación Meta):
   - Validar hub.mode, hub.verify_token vs WHATSAPP_VERIFY_TOKEN
   - Return hub.challenge si válido, 403 si no
2. POST /webhooks/whatsapp (recepción mensajes):
   - Validar X-Hub-Signature-256 con WHATSAPP_APP_SECRET (SHA256 HMAC)
   - Parse entry[].changes[].value.messages[]
   - Soportar type: text, audio
   - Normalizar a: {message_id, canal:"whatsapp", user_id, timestamp_iso, tipo, texto, media_url}
3. WhatsAppClient.send_text(to, body):
   - POST Graph API /{PHONE_ID}/messages
   - Headers: Authorization Bearer {ACCESS_TOKEN}
   - Body: {messaging_product:"whatsapp", to, text:{body}}
AUDIO HANDLING:
- Descargar media_url → temp file
- Validar formato OGG/Opus
- Store para pipeline STT
TESTS OBLIGATORIOS:
- Firma inválida → 403 Forbidden
- Mensaje texto → normalización correcta
- Audio → descarga y validación formato
CRITERIO ÉXITO: Bidireccional funcional, firma validada
STOP CONDITION: Webhook operativo, NO templates HSM aún
---
```

#### Día 5: STT + NLU Básico
```
OBJETIVO: Audio → texto → intents funcional
TIEMPO: 8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Pipeline STT + NLU para WhatsApp
CONTEXTO: Audio OGG → texto → intents (disponibilidad, precio, reservar)
AUDIO PIPELINE:
class AudioProcessor:
    async def transcribe_audio(audio_path):
        # 1. FFmpeg: OGG → WAV 16kHz mono
        # ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
        # 2. faster-whisper: model="base", language="es", compute_type="int8"
        # 3. Calcular confidence promedio segmentos
        # 4. Si confidence < 0.6 → {"error": "audio_unclear"}
        # 5. Return {"text": ..., "confidence": ...}
NLU BÁSICO:
class NLUProcessor:
    def detect_intent(text):
        # Keywords classification:
        # "disponib|libre|hay" → disponibilidad
        # "precio|costo|sale|cuanto" → precio
        # "reserv|apart|tomo" → reservar
        # "servicio|incluye|wifi" → servicios
        # Return {"intent": ..., "confidence": ...}
   
    def extract_entities(text):
        # dateparser + regex para fechas argentinas
        # "finde|fin de semana" → próximo sábado-domingo
        # r'(\d+)\s*(personas?|pax)' → huéspedes
        # Return {"check_in": date, "check_out": date, "guests": int}
CASOS ARGENTINOS:
- "este finde" → sábado-domingo próximos
- "25/12 al 28/12" → parse con año actual
- "para 4 personas" → guests: 4
TESTS:
- Audio 10s → transcripción conf > 0.6
- "Hay libre este finde para 4?" → intent:disponibilidad, guests:4, fechas
- "Cuánto sale?" → intent:precio
CRITERIO ÉXITO: STT funciona conf>0.6, NLU casos básicos
STOP CONDITION: Pipeline operativo, NO entrenar modelos custom
---
```

#### Día 6: Mercado Pago Integración
```
OBJETIVO: Pagos automáticos con webhook confirmación
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: MercadoPago preferencias + webhook validación
CONTEXTO: Señas 30% default, confirmación automática crítica
IMPLEMENTAR:
class MercadoPagoService:
    async def create_preference(reservation_code, amount, description):
        # Usar SDK MP o HTTP directo
        # items: [{"title": f"Seña Reserva {code}", "quantity": 1, "unit_price": amount}]
        # external_reference: reservation_code
        # notification_url: {BASE_URL}/webhooks/mercadopago
        # expiration_date_to: now + 24h
        # Return {"qr_code": ..., "payment_link": ..., "preference_id": ...}
POST /webhooks/mercadopago:
    # 1. Recibir {"topic": "payment", "id": payment_id}
    # 2. GET /v1/payments/{id} server-to-server validación
    # 3. Si status="approved" y external_reference válido:
    # - INSERT payment_records (mp_payment_id UNIQUE constraint)
    # - UPDATE reservation: payment_status="paid", status="confirmed"
    # - DELETE lock Redis: lock:acc:{id}:{dates}
    # - UPDATE availability_calendar marcar ocupado
    # 4. IDEMPOTENCIA: si mp_payment_id existe, skip
VALIDACIONES CRÍTICAS:
- amount >= deposit_amount requerido
- external_reference = código reserva existente
- mp_payment_id único (prevenir duplicados)
TESTS:
- create_preference → link/QR válido generado
- webhook approved → reserva confirmada
- webhook duplicado → idempotente (no error)
CRITERIO ÉXITO: Flujo pago → confirmación automática
STOP CONDITION: MP funciona, NO otros providers pago
---
```

### Fase 3: Sincronización y Dashboard (Días 7-9)

#### Día 7: iCal Import/Export
```
OBJETIVO: Sincronización calendarios plataformas
TIEMPO: 8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Sincronización iCal bidireccional con plataformas
CONTEXTO: Export reservas propias, import bloqueos externos
EXPORT ICS:
GET /ical/accommodation/{id}/{token}.ics:
    # Generar ICS RFC 5545 válido
    # VEVENT por reserva confirmed (NO pre_reserved)
    # UID: {reservation_code}@{domain}
    # DTSTART/DTEND: fechas reserva
    # SUMMARY: "Reservado - {accommodation_name}"
    # DESCRIPTION: "Reserva {code}"
IMPORT JOB (cada 15 min):
class ICalImporter:
    async def import_from_sources():
        # Por cada accommodation con import_urls:
        # 1. Download ICS (requests timeout 30s)
        # 2. Parse icalendar: extract UID, DTSTART, DTEND
        # 3. Upsert imported_blocks (source, uid, dates, last_seen)
        # 4. Update availability_calendar (is_available=false, source=platform)
       
    async def resolve_conflicts():
        # Prioridad: propia > booking > airbnb > para_irnos
        # Si mismo período múltiples fuentes → mayor prioridad gana
        # Si igual prioridad → log warning para revisión manual
CONFIGURACIÓN:
accommodations.ical_import_urls JSONB:
{
  "airbnb": "https://airbnb.com/calendar/ical/...",
  "booking": "https://booking.com/ical/...",
  "para_irnos": "https://parairnos.com/calendar/..."
}
TESTS:
- Export genera ICS parseable por icalendar lib
- Import procesa VEVENTs → availability_calendar
- Conflictos resueltos por prioridad correcta
CRITERIO ÉXITO: Sync bidireccional, conflictos controlados
STOP CONDITION: Import/export básico OK, NO conflict resolution avanzado
---
```

#### Día 8: Dashboard Staff Operativo
```
OBJETIVO: Interface gestión manual eficiente
TIEMPO: 8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Dashboard web Bootstrap 5 + Alpine.js
CONTEXTO: Mobile-first, 2-clics máximo, operación real
VISTAS:
1. /admin/dashboard (HTML):
   - Métricas día: consultas, pre-reservas, confirmadas, revenue $
   - ALERTAS ROJAS: pre-reservas vencen <10min, pagos pendientes
   - Lista conversaciones: phone, último mensaje, intent, hace cuánto
   - Calendario ocupación: colores por estado (libre/reservado/bloqueado)
2. /admin/dashboard-data (JSON):
{
  "conversations": [{"id", "phone", "last_message", "intent", "time_ago", "status"}],
  "pending_reservations": [{"id", "code", "guest_name", "expires_at", "deposit_amount"}],
  "payment_proofs": [{"id", "reservation_code", "image_url", "created_at"}],
  "metrics": {"messages_today", "reservations_today", "revenue_today"},
  "calendar": [{"date", "accommodation_id", "status", "guest_name"}]
}
ACCIONES CRÍTICAS (2-clics máximo):
- POST /admin/reservations/{id}/confirm-payment → confirma manual
- POST /admin/pre-reservations/{id}/extend → +15min extensión
- POST /admin/conversations/{id}/escalate → marca waiting_human
UI REQUIREMENTS:
- Bootstrap responsive móvil
- Botones touch-friendly grandes
- Estados visuales claros (badges colores)
- Auto-refresh cada 30s
AUTENTICACIÓN:
- JWT simple /admin/login
- Token 24h, renovación manual
TESTS:
- Dashboard carga <2s
- Acciones responden correctamente
- Mobile responsive funcional
CRITERIO ÉXITO: Staff opera <10s por acción
STOP CONDITION: Dashboard operación diaria, NO analytics avanzados
---
```

#### Día 9: Email + Observabilidad
```
OBJETIVO: Leads email + monitoreo completo
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: IMAP polling + /healthz completo + alertas
CONTEXTO: Email leads plataformas + monitoreo sistema
EMAIL PROCESSOR:
class EmailProcessor:
    async def poll_imap():
        # IMAP connect, SEARCH UNSEEN
        # Filtros: FROM domains plataformas (booking.com, airbnb.com, etc)
        # Parse básico: fechas, huéspedes, plataforma
        # Responder plantilla + CTA WhatsApp
        # STORE as READ
    def parse_lead_email(subject, body):
        # Regex: "2 guests", "Dec 15-18", etc
        # Return {"platform", "guests", "check_in", "check_out", "email"}
HEALTHZ COMPLETO:
GET /healthz:
{
  "status": "healthy|degraded|unhealthy",
  "checks": {
    "database": {"status": "ok", "latency_ms": 23},
    "redis": {"status": "ok", "keys_count": 15},
    "whatsapp": {"status": "ok", "last_webhook": "2024-09-23T10:30:00Z"},
    "mercadopago": {"status": "ok", "last_webhook": "2024-09-23T09:15:00Z"},
    "ical_sync": {"status": "warning", "minutes_since_last": 45}
  }
}
ALERTAS:
- WhatsApp webhook >5min sin recibir → CRITICAL
- MP webhook fallando → CRITICAL
- iCal desfase >60min → WARNING
- Error rate >5% → CRITICAL
- Envío: webhook Discord/Slack + email
LOGGING JSON:
{
  "timestamp": "2024-09-23T10:30:00Z",
  "level": "INFO",
  "request_id": "uuid",
  "endpoint": "/webhooks/whatsapp",
  "status": 200,
  "latency_ms": 150,
  "user_id": "phone_masked"
}
CRITERIO ÉXITO: Email procesa, /healthz real, alertas disparan
STOP CONDITION: Monitoreo operativo, NO analytics complejos
---
```

### Fase 4: Integración y Go-Live (Días 10-12)

#### Día 10: Tests E2E + Debugging
```
OBJETIVO: Validación flujo completo sin fallos
TIEMPO: 8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Tests integrales + corrección bugs críticos
CONTEXTO: E2E debe funcionar 100% sin intervención manual
TEST E2E PRINCIPAL:
async def test_complete_flow():
    # 1. Simular webhook WA: "Hay libre 15-18/12 para 2?"
    # 2. Verificar respuesta disponibilidad + precios
    # 3. Simular: "quiero reservar cabaña"
    # 4. Verificar pre-reserva + lock Redis + link MP
    # 5. Simular webhook MP approved
    # 6. Verificar confirmed + lock liberado + calendar updated
    # 7. Verificar export ICS incluye reserva
TEST CONCURRENCIA CRÍTICO:
async def test_no_double_booking():
    # Dos requests simultáneos misma unidad/fechas
    # Solo uno debe crear pre-reserva
    # Segundo debe recibir "no disponible"
    # VALIDAR: constraint DB + lock Redis funcionan
TESTS ROBUSTEZ:
- Webhook MP duplicado → idempotente
- Audio ruido → fallback texto
- iCal malformado → error handling graceful
- DB constraint violación → error message claro
BUG FIXES TÍPICOS:
- Timezone UTC vs local Argentina
- Decimal precision precios (round 2 decimales)
- Null handling campos opcionales
- Race conditions locks
CRITERIO ÉXITO: E2E completo, concurrencia OK, bugs críticos fixed
STOP CONDITION: Tests críticos pasan, NO optimizar performance aún
---
```

#### Día 11: Deployment Producción
```
OBJETIVO: Sistema en producción estable
TIEMPO: 6-8 horas
PROMPT PARA GEMINI/COPILOT:
---
TAREA: Configuración producción completa
CONTEXTO: VPS Ubuntu, SSL, backups, CI/CD
NGINX CONFIG:
server {
    listen 443 ssl http2;
    server_name tu-dominio.com;
   
    ssl_certificate /etc/letsencrypt/live/tu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/tu-dominio.com/privkey.pem;
   
    # Rate limiting crítico
    limit_req_zone $binary_remote_addr zone=webhooks:10m rate=30r/m;
   
    location /webhooks/ {
        limit_req zone=webhooks burst=10 nodelay;
        proxy_pass http://api:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
   
    location / {
        proxy_pass http://api:8000;
    }
}
DOCKER COMPOSE PROD:
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASS}
    volumes:
      - pg_data:/var/lib/postgresql/data
    restart: unless-stopped
   
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASS}
    restart: unless-stopped
   
  api:
    build: ./backend
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped
BACKUP AUTOMÁTICO:
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
docker exec postgres pg_dump -U ${DB_USER