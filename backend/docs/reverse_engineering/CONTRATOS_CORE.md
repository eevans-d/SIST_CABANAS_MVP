# Contratos Core (API + Webhooks)

Prefijo API: `/api/v1` (ver `app/main.py` para inclusión de routers).

## Health
- GET /healthz → { status: healthy|degraded|unhealthy, timestamp, checks: { database, redis, disk, memory, ical, whatsapp, mercadopago, runtime } }
- GET /readyz → { status: "ready", timestamp }

## Reservations
- POST /reservations/pre-reserve
  - Request (JSON): { accommodation_id:int, check_in:date(YYYY-MM-DD), check_out:date, guests:int, channel:str, contact_name:str, contact_phone:str, contact_email?:str }
  - Response (200 JSON): { code?:str, expires_at?:iso, deposit_amount?:str, total_price?:str, nights?:int, error?:"invalid_dates|invalid_guests|accommodation_not_found|processing_or_unavailable|date_overlap" }
- POST /reservations/{code}/confirm → { code, status:"confirmed"|..., confirmed_at?:iso, error?:"not_found|invalid_state|expired" }
- POST /reservations/{code}/cancel (JSON: {reason?:str}) → { code, status:"cancelled"|..., cancelled_at?:iso, error? }
- GET /reservations/accommodations → [{ id, name, type, capacity, base_price, active }]
- GET /reservations/{code} → detalle de reserva (para tests/E2E)

## WhatsApp Webhook (Meta)
- GET /webhooks/whatsapp (onboarding)
  - Query: hub.mode=subscribe, hub.challenge, hub.verify_token
  - Debe comparar con `WHATSAPP_VERIFY_TOKEN` y devolver challenge (texto plano)
- POST /webhooks/whatsapp
  - Seguridad: Cabecera obligatoria X-Hub-Signature-256 = sha256=<hex> (HMAC con `WHATSAPP_APP_SECRET`)
  - Entrada (Meta payload simplificado): `entry[].changes[].value.messages[]`
  - Salida (normalizada):
    {
      "message_id": "str",
      "canal": "whatsapp",
      "user_id": "telefono",
      "timestamp_iso": "ISO",
      "tipo": "text|audio|image|pdf",
      "texto": "str|null",
      "media_url": "str|null",
      "metadata": { ... },
      "auto_action"?: "needs_slots|pre_reserved|error|button_callback",
      "pre_reservation"?: { code, expires_at, ... },
      "missing"?: ["accommodation_id","check_in","check_out","guests"],
      "button_result"?: { ... }
    }

## Mercado Pago Webhook
- POST /webhook
  - Firma: si `MERCADOPAGO_WEBHOOK_SECRET` definido ⇒ header `x-signature` debe incluir `v1=<hex>` y coincidir HMAC-SHA256(body)
  - Request (JSON): { id:str, status?:str, amount?:float, currency?:"ARS", external_reference?:str }
  - Response (JSON): { status:"ok|error", payment_id:str, idempotent:bool, reservation_id?:int, events_count?:int, error?:str }

## iCal
- GET /ical/export/{accommodation_id}/{token}
  - Seguridad: token HMAC derivado con `ICS_SALT` y almacenado en accommodations. 200 text/calendar o 404.
- POST /ical/import
  - Request (JSON): { accommodation_id:int, source:str, ical_text:str }
  - Response: { created:int }

## Audio
- POST /audio/transcribe (multipart/form-data, file: OGG/Opus)
  - Response:
    - ok: { status:"ok", text:str, confidence:float, nlu:{ intents:[...], dates:[iso...] } }
    - low-confidence/error: { status:"needs_text", error?:str, confidence?:float }

## NLU
- POST /nlu/analyze
  - Request: { text:str, accommodation_id?:int }
  - Response:
    - slots incompletos → { nlu:{...}, action:"needs_slots", data:{ missing:[...] } }
    - slots completos → { nlu:{...}, action:"pre_reserved", data:{ code, expires_at, ... } }

## Admin (MVP)
- POST /admin/login
  - Body: { email } (whitelist en `ADMIN_ALLOWED_EMAILS`). Response: { access_token, token_type }
- Secured (Bearer JWT + whitelist):
  - GET /admin/dashboard/stats → KPIs (total_reservations, total_guests, monthly_revenue, pending_confirmations, avg_occupancy_rate)
  - GET /admin/reservations[?status&accommodation_id&from_date&to_date&search]
  - GET /admin/reservations/export.csv (CSV streaming)
  - POST /admin/actions/resend-email/{code} (Header: X-CSRF-Token requerido)
  - GET /admin/calendar/availability?month=&year=&accommodation_id=
- WebSocket: /admin/ws?token=JWT → eventos realtime (nueva_reserva, pago_confirmado, reservation_expired, ...)

## Contratos internos relevantes
- Mensaje unificado WhatsApp: ver POST /webhooks/whatsapp (arriba)
- Tokens iCal: HMAC(ICS_SALT, f"{accommodation_id}:{timestamp}") almacenado en accommodations. Verificaciones con compare_digest.
- JWT: HS256 con `JWT_SECRET`; expiración por `JWT_EXPIRATION_HOURS`.
