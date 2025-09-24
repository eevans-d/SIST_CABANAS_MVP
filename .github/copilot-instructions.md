# Instrucciones para Agentes de IA - Sistema Agéntico MVP de Alojamientos

## 🎯 Contexto Central
Este es un **Sistema MVP de reservas de alojamientos** con automatización completa para WhatsApp y email, diseñado para construirse en **10-12 días**. La filosofía es **SHIPPING > PERFECCIÓN**.

### Stack Fijo NO Negociable
- **Backend:** FastAPI + PostgreSQL 16 + Redis 7
- **Canales:** WhatsApp Business Cloud API + IMAP/SMTP
- **Integraciones:** Mercado Pago + iCal (Airbnb/Booking)
- **Audio:** Whisper STT + FFmpeg para OGG/Opus
- **Deploy:** Docker Compose + Nginx

## ⚡ Reglas de Oro para Implementación

### REGLA 0: Anti-Feature Creep
```
❌ NUNCA digas: "Sería fácil agregar...", "Ya que estamos...", "Por completitud..."
✅ SIEMPRE: Implementar SOLO lo pedido, solución MÁS SIMPLE que funcione
✅ STOP CONDITION: Cuando pasa tests = NO REFACTORIZAR
```

### REGLA 1: Prevención Doble-Booking es CRÍTICA
- **Constraint PostgreSQL OBLIGATORIO:**
  ```sql
  CREATE EXTENSION btree_gist;
  period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[]')) STORED
  CONSTRAINT no_overlap_reservations EXCLUDE USING gist
    (accommodation_id WITH =, period WITH &&)
    WHERE (reservation_status IN ('pre_reserved','confirmed'))
  ```
- **Locks Redis:** `SET lock:acc:{id}:{checkin}:{checkout} value NX EX 1800`
- **Testing:** Concurrencia simultánea DEBE fallar con IntegrityError

### REGLA 2: Estructura de Proyecto Fija
```
backend/
├── app/
│   ├── main.py (FastAPI + CORS + middleware)
│   ├── core/ (config.py, logging.py, auth.py)
│   ├── routers/ (webhooks.py, admin.py, health.py, ical.py)
│   ├── services/ (whatsapp.py, mercadopago.py, audio.py, nlu.py, reservations.py)
│   ├── models/ (SQLAlchemy ORM completos)
│   ├── jobs/ (scheduler.py, import_ical.py, cleanup.py)
│   └── utils/ (helpers, validators)
├── requirements.txt (VERSIONES FIJAS - no >= ni ~)
├── Dockerfile
└── docker-compose.yml
```

## 🔧 Patrones de Implementación Específicos

### WhatsApp Webhook Pattern
```python
# SIEMPRE validar firma X-Hub-Signature-256 con WHATSAPP_APP_SECRET
@router.post("/webhooks/whatsapp")
async def webhook_whatsapp(request: Request):
    signature = request.headers.get("X-Hub-Signature-256")
    # Validar HMAC SHA256 - CRÍTICO para seguridad
    # Normalizar a contrato unificado: {message_id, canal, user_id, timestamp_iso, tipo, texto, media_url}
```

### Pre-Reserva Service Pattern
```python
class ReservationService:
    async def create_prereservation(accommodation_id, check_in, check_out, guests, channel, contact):
        # 1. Lock Redis: SET lock:acc:{id}:{checkin}:{checkout} value NX EX 1800
        # 2. Si lock falla → {"error": "En proceso o no disponible"}
        # 3. Calcular precio: base_price * noches * multiplicadores
        # 4. INSERT reservation (pre_reserved, expires_at=now+30min)
        # 5. Si DB constraint falla → DELETE lock, return error
        # 6. Return {"code": "RES240915001", "expires_at": ..., "deposit": ...}
```

### Audio Pipeline Pattern
```python
# FFmpeg: OGG → WAV 16kHz mono
# ffmpeg -i input.ogg -ar 16000 -ac 1 output.wav
# faster-whisper: model="base", language="es", compute_type="int8"
# Si confidence < 0.6 → {"error": "audio_unclear"}
```

## 📋 Modelos de Datos Core

### Modelos NO Modificar (Schema Locked)
```python
# accommodations: id, name, type, capacity, base_price, description, amenities JSONB, photos JSONB, location JSONB, policies JSONB, ical_export_token, active, created_at

# reservations: id, code UNIQUE, accommodation_id FK, guest_name, guest_phone, guest_email, check_in, check_out, guests_count, total_price, deposit_percentage, deposit_amount, payment_status, reservation_status, channel_source, expires_at, confirmation_code, notes, created_at, confirmed_at
```

### Contrato Mensaje Unificado
```json
{
  "message_id": "str",
  "canal": "whatsapp|email", 
  "user_id": "telefono|email",
  "timestamp_iso": "2025-09-23T12:00:00Z",
  "tipo": "text|audio|image|pdf",
  "texto": "str|null",
  "media_url": "str|null",
  "metadata": {"duration_sec": 12, "confidence_stt": 0.82}
}
```

## 🔍 NLU Intent Detection
```python
# Keywords classification básico:
# "disponib|libre|hay" → disponibilidad
# "precio|costo|sale|cuanto" → precio  
# "reserv|apart|tomo" → reservar
# "servicio|incluye|wifi" → servicios
# dateparser + regex para fechas argentinas
# "finde|fin de semana" → próximo sábado-domingo
```

## 🚨 Testing Obligatorios por Feature
- **Locks:** test_no_double_booking() → IntegrityError esperado
- **WhatsApp:** test_invalid_signature() → 403 Forbidden
- **Audio:** test_low_confidence() → request_text response
- **Pagos:** test_webhook_idempotent() → mismo payment_id no duplica
- **iCal:** test_import_deduplication() → mismo evento no duplica

## 🎛️ Observabilidad y Health Checks
```python
# /healthz DEBE incluir:
# - DB connection: SELECT 1
# - Redis: PING
# - iCal last sync age < 20min
# - WhatsApp/MP API reachable
```

## 🚫 Anti-Patrones Prohibidos
- ❌ Microservicios o arquitectura compleja
- ❌ ORM abstractions innecesarias
- ❌ Cache sin evidencia de lentitud  
- ❌ Múltiples providers de pago
- ❌ Channel manager propio
- ❌ Optimizaciones prematuras
- ❌ Abstracciones "por si acaso"

## 📈 SLOs a Respetar
- **Texto P95:** < 3s (warning > 4s, critical > 6s)
- **Audio P95:** < 15s (warning > 20s, critical > 30s)
- **iCal sync:** < 20min desfase (warning > 30min)
- **Error rate:** < 1% (critical > 5%)

## 🔐 Seguridad Mandatoria
- HTTPS obligatorio (Let's Encrypt)
- Validar TODAS las firmas webhook (WhatsApp, MP)
- Variables de entorno para secretos
- No logs de datos sensibles
- JWT para dashboard admin

## 📦 Deploy y DevOps
- Docker Compose único archivo
- `.env.template` con TODAS las variables comentadas
- Health checks en containers
- Logs JSON estructurados con trace-id
- Alembic para migraciones DB

## 📌 ADR: No Integrar PMS Externo en el MVP
Decisión: NO se integrará ningún PMS (Odoo, HotelDruid, QloApps, etc.) durante el alcance del MVP (10–12 días).

Razones:
- Añade complejidad estructural y curva de aprendizaje que retrasa el time-to-market.
- No resuelve los diferenciadores clave del sistema (conversación WhatsApp, locks Redis, pre-reserva efímera, Mercado Pago, pipeline audio/NLU).
- Genera riesgo de dependencia externa y feature creep (reportes, multi-prop, contabilidad) fuera del scope.
- El modelo de datos interno necesario es mínimo y ya definido.

Regla Operativa:
- Cualquier propuesta de “usar un PMS para acelerar” → Rechazar y remitir a este ADR.
- Re-evaluación sólo post-MVP cuando >100 reservas/mes o necesidades avanzadas (multi-propietario / reporting fiscal).

Indicador de Desviación:
- Si aparece código o dependencias que intenten mapear entidades externas de un PMS → Detener PR y simplificar.

Resultado Esperado:
- Mayor control sobre lógica crítica (anti doble-booking) y velocidad de entrega.

---

**Recuerda:** Este MVP prioriza FUNCIONALIDAD sobre elegancia. Si cumple tests y SLOs = ¡ENVIAR A PRODUCCIÓN!