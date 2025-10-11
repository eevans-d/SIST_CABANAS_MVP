"""
OpenAPI configuration and enhanced documentation
"""

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


def custom_openapi(app):
    """
    Configuración personalizada de OpenAPI con documentación mejorada
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="🏠 Sistema de Reservas API",
        version="1.0.0",
        description="""
## Sistema MVP de Automatización de Reservas de Alojamientos

**Sistema profesional de gestión automatizada de reservas** con integración completa para WhatsApp, pagos y sincronización iCal.

### 🚀 Características Principales

- **Automatización WhatsApp**: Conversación inteligente con procesamiento de audio y botones interactivos
- **Prevención Doble-Booking**: Sistema robusto con locks Redis y constraints PostgreSQL
- **Pagos Integrados**: Mercado Pago con webhooks seguros e idempotencia
- **Sincronización iCal**: Import/export bidireccional con Airbnb, Booking.com y otros OTAs
- **Observabilidad**: Métricas Prometheus, health checks y logging estructurado

### 🔒 Seguridad

- Validación de firmas webhook (HMAC-SHA256)
- Rate limiting por IP con fail-open
- Middleware de idempotencia para endpoints críticos
- JWT para autenticación admin

### 📊 Monitoreo

- **Health Check**: `/api/v1/healthz` - Estado del sistema completo
- **Métricas**: `/metrics` - Prometheus metrics
- **Logs**: JSON estructurado con trace-id

### 🏗️ Arquitectura

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │───▶│   FastAPI        │───▶│   PostgreSQL    │
│   Business API  │    │   + Redis        │    │   + btree_gist  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                       ┌──────┴──────┐
                       │ Mercado Pago │
                       │ + iCal Sync  │
                       └─────────────┘
```

### 📝 Flujo Principal

1. **Consulta WhatsApp** → NLU detecta intención → Respuesta automática
2. **Pre-reserva** → Lock Redis → Validación → Payment link MP
3. **Pago** → Webhook MP → Confirmación → Actualización iCal
4. **Seguimiento** → Recordatorios → Expiración automática

### 🔧 Endpoints Críticos

- `POST /api/v1/webhooks/whatsapp` - Recepción mensajes WhatsApp
- `POST /api/v1/mercadopago/webhook` - Notificaciones de pago
- `GET /api/v1/healthz` - Health check completo
- `POST /api/v1/reservations` - Crear pre-reserva
- `GET /api/v1/ical/export/{token}` - Export calendario público

### 🚨 SLOs de Rendimiento

- **Texto P95**: < 3s (crítico > 6s)
- **Audio P95**: < 15s (crítico > 30s)
- **Error Rate**: < 1% (crítico > 5%)
- **iCal Sync**: < 20min desfase

### 🏷️ Versiones

- **v1.0.0**: MVP completo con todas las funcionalidades base
- **Compatibilidad**: API versionada con `/api/v1/` prefix

---

*Desarrollado siguiendo principios SHIPPING > PERFECCIÓN para máxima velocidad de entrega.*
        """,
        routes=app.routes,
        servers=[
            {"url": "https://api.reservas.example.com", "description": "Producción"},
            {"url": "https://staging.reservas.example.com", "description": "Staging"},
            {"url": "http://localhost:8000", "description": "Desarrollo Local"},
        ],
        contact={
            "name": "Equipo de Desarrollo",
            "email": "dev@reservas.example.com",
            "url": "https://github.com/tu-org/sistema-reservas",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Configuración de seguridad global
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token para endpoints administrativos",
        },
        "WhatsAppSignature": {
            "type": "apiKey",
            "in": "header",
            "name": "X-Hub-Signature-256",
            "description": "HMAC-SHA256 signature para webhooks WhatsApp",
        },
        "MercadoPagoSignature": {
            "type": "apiKey",
            "in": "header",
            "name": "x-signature",
            "description": "Firma HMAC para webhooks Mercado Pago",
        },
    }

    # Tags para agrupar endpoints
    openapi_schema["tags"] = [
        {
            "name": "Health",
            "description": "**Sistema de observabilidad y health checks**\n\nEndpoints para monitoreo del estado del sistema, métricas y diagnósticos.",
        },
        {
            "name": "Reservations",
            "description": "**Gestión de reservas**\n\nCRUD completo de reservas con validación anti-doble-booking y transiciones de estado.",
        },
        {
            "name": "WhatsApp",
            "description": "**Integración WhatsApp Business**\n\nWebhooks, envío de mensajes, botones interactivos y procesamiento de audio.",
        },
        {
            "name": "Payments",
            "description": "**Integración Mercado Pago**\n\nWebhooks de pagos, generación de preference links y validación de transacciones.",
        },
        {
            "name": "iCal",
            "description": "**Sincronización de calendarios**\n\nImport/export iCal bidireccional con OTAs (Airbnb, Booking.com).",
        },
        {
            "name": "Audio",
            "description": "**Procesamiento de audio**\n\nTranscripción automática con Whisper STT y conversión de formatos.",
        },
        {
            "name": "NLU",
            "description": "**Procesamiento de lenguaje natural**\n\nDetección de intenciones, extracción de fechas y generación de respuestas.",
        },
        {
            "name": "Admin",
            "description": "**Panel administrativo**\n\nEndpoints protegidos para gestión de alojamientos, reportes y configuración.",
        },
    ]

    # Ejemplos de respuestas comunes
    openapi_schema["components"]["examples"] = {
        "SuccessResponse": {
            "summary": "Respuesta exitosa",
            "value": {"status": "success", "message": "Operación completada"},
        },
        "ErrorResponse": {
            "summary": "Error de validación",
            "value": {
                "error": "validation_error",
                "detail": "Los datos proporcionados no son válidos",
                "timestamp": "2024-01-15T10:30:00Z",
            },
        },
        "ReservationCreated": {
            "summary": "Reserva creada exitosamente",
            "value": {
                "code": "RES-2024-001",
                "status": "pre_reserved",
                "total_price": "150000.00",
                "expires_at": "2024-01-15T15:30:00Z",
                "payment_link": "https://mercadopago.com.ar/checkout/v1/redirect?pref_id=123456",
            },
        },
        "HealthResponse": {
            "summary": "Estado del sistema",
            "value": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "checks": {
                    "database": {"status": "ok", "latency_ms": 45},
                    "redis": {"status": "ok", "latency_ms": 12, "memory_usage": "85MB"},
                    "ical_sync": {"status": "ok", "last_sync_age_minutes": 8},
                },
            },
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_custom_swagger_ui_html():
    """
    HTML personalizado para Swagger UI con tema mejorado
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Sistema de Reservas API - Documentación",
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        swagger_ui_parameters={
            "defaultModelsExpandDepth": 2,
            "defaultModelExpandDepth": 2,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "showCommonExtensions": True,
            "tryItOutEnabled": True,
        },
    )
