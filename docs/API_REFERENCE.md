# API Reference - Sistema MVP Alojamientos

**Versión:** 0.9.8
**Base URL:** `https://api.alojamientos.example.com`
**Prefix:** `/api/v1`

---

## 📋 Índice

- [Authentication](#authentication)
- [Health & Metrics](#health--metrics)
- [Reservations](#reservations)
- [Webhooks](#webhooks)
- [iCal Export](#ical-export)
- [Admin (Future)](#admin-future)
- [Rate Limiting](#rate-limiting)
- [Error Responses](#error-responses)

---

## Authentication

### Webhooks

Requieren validación de firma HMAC. Ver sección [Webhooks](#webhooks).

### Admin API (Future)

```http
Authorization: Bearer <JWT_TOKEN>
```

---

## Health & Metrics

### GET /healthz

Health check endpoint con múltiples validaciones.

**Bypass Rate Limit:** ✅ Sí

#### Response 200 (Healthy)

```json
{
  "status": "healthy",
  "timestamp": "2025-10-02T21:30:00Z",
  "checks": {
    "database": {
      "status": "ok",
      "latency_ms": 2.3
    },
    "redis": {
      "status": "ok",
      "latency_ms": 1.1
    },
    "ical_sync": {
      "status": "ok",
      "max_age_minutes": 12,
      "threshold_minutes": 20
    }
  }
}
```

#### Response 200 (Degraded)

```json
{
  "status": "degraded",
  "timestamp": "2025-10-02T21:30:00Z",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2.1},
    "redis": {"status": "ok", "latency_ms": 1.0},
    "ical_sync": {
      "status": "degraded",
      "max_age_minutes": 25,
      "threshold_minutes": 20,
      "message": "iCal sync delay exceeds threshold"
    }
  }
}
```

#### Response 503 (Unhealthy)

```json
{
  "status": "unhealthy",
  "timestamp": "2025-10-02T21:30:00Z",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2.0},
    "redis": {
      "status": "error",
      "error": "Connection refused"
    },
    "ical_sync": {"status": "ok", "max_age_minutes": 10}
  }
}
```

**Status Codes:**
- `200`: Healthy o Degraded (service operational)
- `503`: Unhealthy (critical failure, load balancer should remove)

---

### GET /metrics

Prometheus metrics endpoint.

**Bypass Rate Limit:** ✅ Sí

#### Response 200

```prometheus
# HELP reservations_created_total Total reservations created
# TYPE reservations_created_total counter
reservations_created_total{channel_source="whatsapp"} 42.0
reservations_created_total{channel_source="email"} 13.0

# HELP ical_last_sync_age_minutes Minutes since last iCal sync
# TYPE ical_last_sync_age_minutes gauge
ical_last_sync_age_minutes{accommodation_id="1"} 8.2

# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="POST",endpoint="/api/v1/webhooks/whatsapp",status="200"} 156.0

# ... more metrics
```

**Content-Type:** `text/plain; version=0.0.4`

---

## Reservations

### POST /reservations/pre-reserve

Crear una pre-reserva (expira en 30 minutos).

#### Request Body

```json
{
  "accommodation_id": 1,
  "check_in": "2024-09-20",
  "check_out": "2024-09-22",
  "guests_count": 2,
  "guest_name": "Juan Pérez",
  "guest_phone": "+5491112345678",
  "guest_email": "juan@example.com",
  "channel_source": "whatsapp"
}
```

#### Response 201 (Success)

```json
{
  "code": "RES240915001",
  "accommodation_id": 1,
  "check_in": "2024-09-20",
  "check_out": "2024-09-22",
  "guests_count": 2,
  "total_price": 15000.00,
  "deposit_percentage": 30,
  "deposit_amount": 4500.00,
  "payment_url": "https://mpago.li/xyz123",
  "expires_at": "2024-09-15T12:30:00Z",
  "reservation_status": "pre_reserved"
}
```

#### Response 409 (Conflict - No Disponible)

```json
{
  "error": "overlap_detected",
  "message": "Accommodation not available for selected dates",
  "check_in": "2024-09-20",
  "check_out": "2024-09-22",
  "conflicting_reservations": [
    {
      "code": "RES240915000",
      "check_in": "2024-09-19",
      "check_out": "2024-09-21"
    }
  ]
}
```

#### Response 423 (Locked - En Proceso)

```json
{
  "error": "reservation_in_progress",
  "message": "Another reservation is being processed for these dates",
  "retry_after_seconds": 60
}
```

**Rate Limit:** 10 requests/min per IP

---

### POST /reservations/{code}/confirm

Confirmar una pre-reserva (requiere pago aprobado).

#### Path Parameters

- `code`: Reservation code (e.g., `RES240915001`)

#### Request Body

```json
{
  "payment_id": "12345678"
}
```

#### Response 200 (Success)

```json
{
  "code": "RES240915001",
  "reservation_status": "confirmed",
  "confirmed_at": "2024-09-15T12:15:00Z",
  "confirmation_code": "CONF-ABC123",
  "payment_status": "approved"
}
```

#### Response 400 (Pre-reserva Expirada)

```json
{
  "error": "reservation_expired",
  "message": "Pre-reservation expired, please create a new one",
  "expired_at": "2024-09-15T12:00:00Z"
}
```

#### Response 404 (No Encontrada)

```json
{
  "error": "reservation_not_found",
  "message": "Reservation code not found"
}
```

---

### POST /reservations/{code}/cancel

Cancelar una reserva.

#### Path Parameters

- `code`: Reservation code

#### Request Body

```json
{
  "reason": "change_of_plans",
  "notes": "Optional cancellation notes"
}
```

#### Response 200 (Success)

```json
{
  "code": "RES240915001",
  "reservation_status": "cancelled",
  "cancelled_at": "2024-09-15T13:00:00Z"
}
```

---

### GET /reservations/{code}

Obtener detalles de una reserva.

#### Response 200

```json
{
  "code": "RES240915001",
  "accommodation": {
    "id": 1,
    "name": "Cabaña Bosque Encantado",
    "type": "cabin",
    "capacity": 4
  },
  "check_in": "2024-09-20",
  "check_out": "2024-09-22",
  "guests_count": 2,
  "guest_name": "Juan Pérez",
  "guest_phone": "+5491112345678",
  "guest_email": "juan@example.com",
  "total_price": 15000.00,
  "deposit_amount": 4500.00,
  "payment_status": "approved",
  "reservation_status": "confirmed",
  "channel_source": "whatsapp",
  "created_at": "2024-09-15T12:00:00Z",
  "confirmed_at": "2024-09-15T12:15:00Z",
  "expires_at": null
}
```

---

## Webhooks

### POST /webhooks/whatsapp

Webhook de WhatsApp Business Cloud API.

**Authentication:** HMAC SHA-256 signature validation

#### Headers

```
X-Hub-Signature-256: sha256=<hex_signature>
Content-Type: application/json
```

#### Request Body (Text Message)

```json
{
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messaging_product": "whatsapp",
        "contacts": [{
          "profile": {"name": "Juan Pérez"},
          "wa_id": "5491112345678"
        }],
        "messages": [{
          "from": "5491112345678",
          "id": "wamid.xyz123",
          "timestamp": "1695042000",
          "type": "text",
          "text": {"body": "Hola, quiero reservar para el finde"}
        }]
      }
    }]
  }]
}
```

#### Request Body (Audio Message)

```json
{
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "5491112345678",
          "id": "wamid.audio789",
          "timestamp": "1695042100",
          "type": "audio",
          "audio": {
            "id": "audio_media_id_xyz",
            "mime_type": "audio/ogg; codecs=opus"
          }
        }]
      }
    }]
  }]
}
```

#### Response 200

```json
{
  "status": "received",
  "message_id": "wamid.xyz123"
}
```

#### Response 403 (Invalid Signature)

```json
{
  "error": "invalid_signature",
  "message": "Webhook signature validation failed"
}
```

**Validation:**

```python
expected = hmac.new(
    WHATSAPP_APP_SECRET.encode(),
    request.body,
    hashlib.sha256
).hexdigest()
assert header == f"sha256={expected}"
```

---

### GET /webhooks/whatsapp

Verificación de webhook WhatsApp.

#### Query Parameters

- `hub.mode`: "subscribe"
- `hub.verify_token`: Token de verificación configurado
- `hub.challenge`: String a retornar

#### Response 200

```
<hub.challenge>
```

---

### POST /webhooks/mercadopago

Webhook de Mercado Pago.

**Authentication:** HMAC SHA-256 signature validation (x-signature header)

#### Headers

```
x-signature: ts=1695042000,v1=<hex_signature>
x-request-id: <request_id>
Content-Type: application/json
```

#### Request Body

```json
{
  "action": "payment.updated",
  "data": {
    "id": "12345678"
  },
  "date_created": "2024-09-15T12:15:00Z",
  "id": 987654321,
  "live_mode": true,
  "type": "payment"
}
```

#### Response 200

```json
{
  "status": "processed",
  "payment_id": "12345678"
}
```

#### Response 403 (Invalid Signature)

```json
{
  "error": "invalid_signature",
  "message": "Webhook signature validation failed"
}
```

**Validation:**

```python
manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
expected = hmac.new(
    MERCADOPAGO_WEBHOOK_SECRET.encode(),
    manifest.encode(),
    hashlib.sha256
).hexdigest()
assert v1 == expected
```

---

## iCal Export

### GET /ical/export/{accommodation_id}/{token}

Exportar calendario iCal de un alojamiento.

**Authentication:** HMAC token en URL (no enumerable)

#### Path Parameters

- `accommodation_id`: ID del alojamiento
- `token`: Token HMAC (16 chars hex)

#### Response 200

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sistema Alojamientos//MVP//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Cabaña Bosque Encantado

BEGIN:VEVENT
UID:RES240915001@alojamientos.example.com
DTSTAMP:20240915T120000Z
DTSTART:20240920
DTEND:20240922
SUMMARY:RESERVADO
DESCRIPTION:Reserva confirmada
STATUS:CONFIRMED
TRANSP:OPAQUE
X-CODE:RES240915001
X-SOURCE:sistema_interno
END:VEVENT

END:VCALENDAR
```

**Content-Type:** `text/calendar; charset=utf-8`

#### Response 403 (Invalid Token)

```json
{
  "error": "invalid_token",
  "message": "Invalid iCal export token"
}
```

---

## Admin (Future)

### GET /admin/accommodations

Listar alojamientos (requiere JWT).

### POST /admin/accommodations

Crear nuevo alojamiento (requiere JWT).

### GET /admin/dashboard

Dashboard con métricas (requiere JWT).

---

## Rate Limiting

### Default Limits

- **Per IP + Path:** 60 requests / minute
- **Global:** 1000 requests / minute

### Bypass Paths

- `/api/v1/healthz`
- `/metrics`

### Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1695042060
```

### Response 429 (Rate Limit Exceeded)

```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests",
  "retry_after_seconds": 30,
  "limit": 60,
  "window_seconds": 60
}
```

**Fail-Open:** Si Redis falla, rate limit no se aplica (graceful degradation)

---

## Error Responses

### Standard Error Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "trace_id": "abc123"
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | `validation_error` | Invalid request data |
| 400 | `reservation_expired` | Pre-reservation expired |
| 401 | `unauthorized` | Missing or invalid auth |
| 403 | `forbidden` | Insufficient permissions |
| 403 | `invalid_signature` | Webhook signature invalid |
| 404 | `not_found` | Resource not found |
| 409 | `overlap_detected` | Reservation overlap |
| 423 | `reservation_in_progress` | Lock acquired by another request |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Unexpected server error |
| 503 | `service_unavailable` | Service unhealthy |

---

## Ejemplos de Uso

### cURL: Crear Pre-reserva

```bash
curl -X POST https://api.alojamientos.example.com/api/v1/reservations/pre-reserve \
  -H "Content-Type: application/json" \
  -d '{
    "accommodation_id": 1,
    "check_in": "2024-09-20",
    "check_out": "2024-09-22",
    "guests_count": 2,
    "guest_name": "Juan Pérez",
    "guest_phone": "+5491112345678",
    "guest_email": "juan@example.com",
    "channel_source": "whatsapp"
  }'
```

### Python: Confirmar Reserva

```python
import requests

response = requests.post(
    "https://api.alojamientos.example.com/api/v1/reservations/RES240915001/confirm",
    json={"payment_id": "12345678"}
)
print(response.json())
```

### JavaScript: Health Check

```javascript
fetch('https://api.alojamientos.example.com/api/v1/healthz')
  .then(res => res.json())
  .then(data => console.log(data.status));
```

---

## Changelog API

### v1 (2025-10-02)

- Initial release
- Reservations endpoints
- Webhooks (WhatsApp, Mercado Pago)
- iCal export
- Health checks
- Metrics endpoint

---

**Última actualización:** 2025-10-02
**Versión API:** v1
**Documentación Interactiva:** `https://api.alojamientos.example.com/docs` (Swagger UI)
