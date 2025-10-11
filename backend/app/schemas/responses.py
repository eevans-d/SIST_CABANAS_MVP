"""
Enhanced Pydantic schemas for API responses with OpenAPI documentation
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class StatusEnum(str, Enum):
    """Estados del sistema"""

    SUCCESS = "success"
    ERROR = "error"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ReservationStatusEnum(str, Enum):
    """Estados de reserva"""

    PRE_RESERVED = "pre_reserved"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentStatusEnum(str, Enum):
    """Estados de pago"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ChannelEnum(str, Enum):
    """Canales de comunicación"""

    WHATSAPP = "whatsapp"
    EMAIL = "email"
    WEB = "web"
    PHONE = "phone"


# Base response schemas
class BaseResponse(BaseModel):
    """Respuesta base del sistema"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "timestamp": "2024-01-15T10:30:00Z",
                "message": "Operación completada exitosamente",
            }
        }
    )

    status: StatusEnum = Field(..., description="Estado de la operación")
    timestamp: datetime = Field(..., description="Timestamp de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")


class ErrorResponse(BaseResponse):
    """Respuesta de error estándar"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "error",
                "timestamp": "2024-01-15T10:30:00Z",
                "error": "validation_error",
                "detail": "Los datos proporcionados no son válidos",
                "code": "VAL_001",
            }
        }
    )

    status: StatusEnum = StatusEnum.ERROR
    error: str = Field(..., description="Tipo de error")
    detail: str = Field(..., description="Descripción detallada del error")
    code: Optional[str] = Field(None, description="Código de error interno")


# Health check schemas
class ComponentHealth(BaseModel):
    """Estado de un componente del sistema"""

    status: str = Field(..., description="Estado del componente (ok, error, slow)")
    latency_ms: Optional[int] = Field(None, description="Latencia en milisegundos")
    details: Optional[Dict[str, Any]] = Field(None, description="Información adicional")


class HealthResponse(BaseModel):
    """Respuesta completa de health check"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "checks": {
                    "database": {"status": "ok", "latency_ms": 45},
                    "redis": {
                        "status": "ok",
                        "latency_ms": 12,
                        "details": {"memory_usage": "85MB"},
                    },
                    "ical_sync": {"status": "ok", "details": {"last_sync_age_minutes": 8}},
                },
            }
        }
    )

    status: str = Field(..., description="Estado general del sistema")
    timestamp: datetime = Field(..., description="Timestamp del check")
    checks: Dict[str, ComponentHealth] = Field(..., description="Estado por componente")


# Reservation schemas
class AccommodationInfo(BaseModel):
    """Información básica del alojamiento"""

    id: int = Field(..., description="ID único del alojamiento")
    name: str = Field(..., description="Nombre del alojamiento")
    type: str = Field(..., description="Tipo (casa, departamento, cabaña)")
    capacity: int = Field(..., description="Capacidad máxima de huéspedes")
    base_price: Decimal = Field(..., description="Precio base por noche")


class ReservationResponse(BaseModel):
    """Respuesta de creación/consulta de reserva"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "RES-2024-001",
                "accommodation": {
                    "id": 1,
                    "name": "Cabaña Vista al Lago",
                    "type": "cabaña",
                    "capacity": 4,
                    "base_price": "25000.00",
                },
                "guest_name": "Juan Pérez",
                "guest_phone": "+541234567890",
                "guest_email": "juan@email.com",
                "check_in": "2024-02-15",
                "check_out": "2024-02-17",
                "guests_count": 2,
                "total_price": "150000.00",
                "deposit_amount": "45000.00",
                "payment_status": "pending",
                "reservation_status": "pre_reserved",
                "channel_source": "whatsapp",
                "expires_at": "2024-01-15T15:30:00Z",
                "payment_link": "https://mercadopago.com.ar/checkout/v1/redirect?pref_id=123456",
                "created_at": "2024-01-15T10:30:00Z",
            }
        }
    )

    code: str = Field(..., description="Código único de reserva")
    accommodation: AccommodationInfo = Field(..., description="Información del alojamiento")
    guest_name: str = Field(..., description="Nombre del huésped")
    guest_phone: str = Field(..., description="Teléfono del huésped")
    guest_email: Optional[str] = Field(None, description="Email del huésped")
    check_in: str = Field(..., description="Fecha de check-in (YYYY-MM-DD)")
    check_out: str = Field(..., description="Fecha de check-out (YYYY-MM-DD)")
    guests_count: int = Field(..., description="Cantidad de huéspedes")
    total_price: Decimal = Field(..., description="Precio total de la estadía")
    deposit_amount: Decimal = Field(..., description="Monto de seña requerida")
    payment_status: PaymentStatusEnum = Field(..., description="Estado del pago")
    reservation_status: ReservationStatusEnum = Field(..., description="Estado de la reserva")
    channel_source: ChannelEnum = Field(..., description="Canal de origen")
    expires_at: Optional[datetime] = Field(None, description="Expiración de pre-reserva")
    payment_link: Optional[str] = Field(None, description="Link de pago Mercado Pago")
    created_at: datetime = Field(..., description="Fecha de creación")
    confirmed_at: Optional[datetime] = Field(None, description="Fecha de confirmación")


# WhatsApp schemas
class WhatsAppMessageResponse(BaseModel):
    """Respuesta de envío de mensaje WhatsApp"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message_id": "wamid.HBgLMTU0MTIzNDU2Nzg5AB4CAA==",
                "status": "sent",
                "recipient": "+541234567890",
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    )

    message_id: str = Field(..., description="ID del mensaje enviado")
    status: str = Field(..., description="Estado del envío")
    recipient: str = Field(..., description="Número destinatario")
    timestamp: datetime = Field(..., description="Timestamp del envío")


class NLUResponse(BaseModel):
    """Respuesta del procesamiento NLU"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intent": "disponibilidad",
                "confidence": 0.85,
                "entities": {
                    "dates": ["2024-02-15", "2024-02-17"],
                    "guests": 2,
                    "accommodation_type": "cabaña",
                },
                "response_text": "Tenemos disponibilidad para esas fechas. ¿Te gustaría hacer una reserva?",
                "suggested_actions": ["show_availability", "create_prereservation"],
            }
        }
    )

    intent: str = Field(..., description="Intención detectada")
    confidence: float = Field(..., description="Confianza de la detección (0-1)")
    entities: Dict[str, Any] = Field(..., description="Entidades extraídas")
    response_text: str = Field(..., description="Respuesta generada")
    suggested_actions: List[str] = Field(..., description="Acciones sugeridas")


# Audio processing schemas
class AudioTranscriptionResponse(BaseModel):
    """Respuesta de transcripción de audio"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "Hola, quería consultar disponibilidad para el próximo fin de semana para dos personas",
                "confidence": 0.92,
                "duration_seconds": 8.5,
                "language": "es",
                "model_used": "whisper-base",
                "processing_time_ms": 1250,
            }
        }
    )

    text: str = Field(..., description="Texto transcrito")
    confidence: float = Field(..., description="Confianza de la transcripción (0-1)")
    duration_seconds: float = Field(..., description="Duración del audio")
    language: str = Field(..., description="Idioma detectado")
    model_used: str = Field(..., description="Modelo utilizado")
    processing_time_ms: int = Field(..., description="Tiempo de procesamiento")


# Payment schemas
class PaymentNotificationResponse(BaseModel):
    """Respuesta de notificación de pago"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "processed",
                "payment_id": "123456789",
                "reservation_code": "RES-2024-001",
                "amount": "45000.00",
                "payment_status": "approved",
                "processed_at": "2024-01-15T10:30:00Z",
            }
        }
    )

    status: str = Field(..., description="Estado del procesamiento")
    payment_id: str = Field(..., description="ID del pago en Mercado Pago")
    reservation_code: str = Field(..., description="Código de reserva asociada")
    amount: Decimal = Field(..., description="Monto pagado")
    payment_status: PaymentStatusEnum = Field(..., description="Estado del pago")
    processed_at: datetime = Field(..., description="Timestamp del procesamiento")


# iCal schemas
class ICalSyncResponse(BaseModel):
    """Respuesta de sincronización iCal"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "events_imported": 12,
                "events_updated": 3,
                "events_skipped": 5,
                "last_sync": "2024-01-15T10:30:00Z",
                "next_sync": "2024-01-15T10:35:00Z",
                "sources": ["airbnb", "booking"],
            }
        }
    )

    status: str = Field(..., description="Estado de la sincronización")
    events_imported: int = Field(..., description="Eventos importados")
    events_updated: int = Field(..., description="Eventos actualizados")
    events_skipped: int = Field(..., description="Eventos omitidos")
    last_sync: datetime = Field(..., description="Última sincronización")
    next_sync: datetime = Field(..., description="Próxima sincronización")
    sources: List[str] = Field(..., description="Fuentes sincronizadas")


# Admin schemas
class MetricsResponse(BaseModel):
    """Respuesta de métricas del sistema"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reservations": {
                    "total": 150,
                    "active": 45,
                    "revenue_current_month": "2250000.00",
                },
                "performance": {
                    "avg_response_time_ms": 250,
                    "error_rate_percent": 0.5,
                    "uptime_percent": 99.9,
                },
                "integrations": {
                    "whatsapp_messages_today": 89,
                    "payments_processed_today": 12,
                    "ical_last_sync_minutes_ago": 8,
                },
            }
        }
    )

    reservations: Dict[str, Union[int, Decimal]] = Field(..., description="Métricas de reservas")
    performance: Dict[str, float] = Field(..., description="Métricas de rendimiento")
    integrations: Dict[str, Union[int, float]] = Field(..., description="Estado integraciones")


# Generic schemas for flexibility
class GenericDataResponse(BaseModel):
    """Respuesta genérica con datos"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "data": {"key": "value", "items": [1, 2, 3]},
                "count": 3,
                "timestamp": "2024-01-15T10:30:00Z",
            }
        }
    )

    status: StatusEnum = StatusEnum.SUCCESS
    data: Dict[str, Any] = Field(..., description="Datos de respuesta")
    count: Optional[int] = Field(None, description="Cantidad de elementos")
    timestamp: datetime = Field(..., description="Timestamp de la respuesta")


class PaginatedResponse(BaseModel):
    """Respuesta paginada"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "total": 150,
                "page": 1,
                "per_page": 20,
                "pages": 8,
                "has_next": True,
                "has_prev": False,
            }
        }
    )

    items: List[Dict[str, Any]] = Field(..., description="Elementos de la página")
    total: int = Field(..., description="Total de elementos")
    page: int = Field(..., description="Página actual")
    per_page: int = Field(..., description="Elementos por página")
    pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Hay página siguiente")
    has_prev: bool = Field(..., description="Hay página anterior")
