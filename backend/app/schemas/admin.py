"""Schemas Pydantic para endpoints de administración."""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Dashboard Schemas
# ============================================================================
class DashboardTotals(BaseModel):
    """Totales generales del sistema."""

    confirmed: int = Field(description="Total de reservas confirmadas")
    pre_reserved: int = Field(description="Total de pre-reservas activas")
    cancelled: int = Field(description="Total de reservas canceladas")
    total_revenue: float = Field(description="Revenue total (confirmadas)")
    month_revenue: float = Field(description="Revenue del mes actual")


class DashboardLast24h(BaseModel):
    """Actividad en las últimas 24 horas."""

    new_reservations: int = Field(description="Nuevas reservas creadas")
    payments_received: int = Field(description="Pagos confirmados")


class DashboardHealth(BaseModel):
    """Estado de salud del sistema."""

    status: str = Field(description="healthy | degraded | unhealthy")
    db_latency_ms: int = Field(description="Latencia DB en ms")
    redis_latency_ms: int = Field(description="Latencia Redis en ms")
    ical_last_sync_age_minutes: int = Field(description="Minutos desde última sync iCal")


class DashboardPerformance(BaseModel):
    """Métricas de performance."""

    error_rate: float = Field(description="Tasa de error (%)")
    p95_latency_ms: int = Field(description="P95 latencia en ms")


class DashboardResponse(BaseModel):
    """Respuesta del dashboard principal."""

    totals: DashboardTotals
    conversion_rate: float = Field(description="Tasa de conversión (%)")
    last_24h: DashboardLast24h
    health: DashboardHealth
    performance: DashboardPerformance
    timestamp: str = Field(description="Timestamp ISO 8601")


# ============================================================================
# Reservations List Schemas
# ============================================================================
class ReservationListItem(BaseModel):
    """Item de reserva en la lista."""

    id: int
    code: str
    accommodation_id: int
    guest_name: str
    guest_phone: str
    guest_email: Optional[str]
    check_in: Optional[str]
    check_out: Optional[str]
    guests_count: int
    total_price: float
    payment_status: str
    reservation_status: str
    channel_source: str
    created_at: Optional[str]
    expires_at: Optional[str]


class PaginationMeta(BaseModel):
    """Metadata de paginación."""

    page: int
    page_size: int
    total: int
    total_pages: int


class ReservationListFilters(BaseModel):
    """Filtros aplicados en la lista."""

    status: Optional[str]
    channel: Optional[str]
    check_in_from: Optional[str]
    check_in_to: Optional[str]
    q: Optional[str]
    sort: str


class ReservationListResponse(BaseModel):
    """Respuesta de lista de reservas."""

    items: List[ReservationListItem]
    pagination: PaginationMeta
    filters_applied: ReservationListFilters


# ============================================================================
# Reservation Detail Schemas
# ============================================================================
class TimelineEvent(BaseModel):
    """Evento en la timeline de una reserva."""

    event: str = Field(description="Tipo de evento: pre_reserved, confirmed, etc.")
    timestamp: Optional[str] = Field(description="Timestamp ISO 8601")
    description: str = Field(description="Descripción del evento")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata adicional")


class WebhookLog(BaseModel):
    """Log de webhook asociado a la reserva."""

    id: int
    webhook_type: str = Field(description="whatsapp | mercadopago")
    event_type: str = Field(description="Tipo de evento del webhook")
    status: str = Field(description="success | failed | pending")
    timestamp: str
    payload_summary: Optional[Dict[str, Any]]


class PaymentLog(BaseModel):
    """Log de pago asociado a la reserva."""

    id: int
    payment_id: str
    amount: float
    status: str
    timestamp: str
    gateway: str = Field(description="mercadopago | stripe | etc.")


class ReservationDetailResponse(BaseModel):
    """Detalle completo de una reserva."""

    id: int
    code: str
    accommodation_id: int
    guest_name: str
    guest_phone: str
    guest_email: Optional[str]
    check_in: Optional[str]
    check_out: Optional[str]
    guests_count: int
    total_price: float
    deposit_percentage: float
    deposit_amount: float
    payment_status: str
    reservation_status: str
    channel_source: str
    created_at: Optional[str]
    confirmed_at: Optional[str]
    expires_at: Optional[str]
    notes: Optional[str]
    timeline: List[TimelineEvent]
    webhooks: List[WebhookLog]
    payment_logs: List[PaymentLog]


# ============================================================================
# Actions Schemas
# ============================================================================
class ConfirmReservationRequest(BaseModel):
    """Request para confirmar una pre-reserva."""

    payment_id: Optional[str] = Field(default=None, description="ID de pago externo")
    notes: Optional[str] = Field(default=None, description="Notas adicionales")


class CancelReservationRequest(BaseModel):
    """Request para cancelar una reserva."""

    reason: str = Field(description="Motivo de cancelación")
    refund_amount: Optional[float] = Field(
        default=None, description="Monto a reembolsar (si aplica)"
    )


class ActionResponse(BaseModel):
    """Respuesta genérica de acciones."""

    success: bool
    message: str
    reservation_id: int
    new_status: str
    timestamp: str


# ============================================================================
# Calendar Schemas
# ============================================================================
class CalendarEvent(BaseModel):
    """Evento en el calendario."""

    id: int
    code: str
    accommodation_id: int
    guest_name: str
    check_in: str
    check_out: str
    status: str = Field(description="pre_reserved | confirmed | blocked")
    total_price: float
    channel_source: str


class CalendarResponse(BaseModel):
    """Respuesta del calendario mensual."""

    events: List[CalendarEvent]
    month: str = Field(description="Mes en formato YYYY-MM")
    occupancy_rate: float = Field(description="Tasa de ocupación del mes (%)")


# ============================================================================
# Webhooks Monitor Schemas
# ============================================================================
class WebhookEventItem(BaseModel):
    """Item de evento webhook."""

    id: int
    webhook_type: str
    event_type: str
    status: str
    timestamp: str
    reservation_id: Optional[int]
    error_message: Optional[str]


class WebhookMonitorResponse(BaseModel):
    """Respuesta del monitor de webhooks."""

    items: List[WebhookEventItem]
    pagination: PaginationMeta
    error_rate: float = Field(description="Tasa de error en las últimas 24h (%)")
    last_24h_count: int = Field(description="Total de webhooks en 24h")
