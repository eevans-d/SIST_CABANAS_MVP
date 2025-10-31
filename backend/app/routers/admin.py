"""Router de administración para el sistema de reservas."""
from __future__ import annotations

import asyncio
import csv
import io
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Optional

import structlog
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_jwt_token
from app.models.reservation import Reservation
from app.schemas.admin import (
    ActionResponse,
    CalendarEvent,
    CalendarResponse,
    CancelReservationRequest,
    ConfirmReservationRequest,
    DashboardHealth,
    DashboardLast24h,
    DashboardPerformance,
    DashboardResponse,
    DashboardTotals,
    ReservationDetailResponse,
    TimelineEvent,
)
from app.services.email import email_service
from fastapi import (
    APIRouter,
    Body,
    Depends,
    Header,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


async def require_admin(authorization: str = Header(default="")) -> dict:
    """Valida JWT Bearer y que el email esté en whitelist."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = verify_jwt_token(token)
    email = payload.get("email")
    allowed = {e.strip().lower() for e in settings.ADMIN_ALLOWED_EMAILS.split(",") if e.strip()}
    if not email or email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Not allowed")
    return payload


@router.post("/login")
async def admin_login(email: str = Body(..., embed=True)):
    """Endpoint simple para emitir un JWT para correos whitelisted (sólo dev/test).

    Producción debería usar un IdP externo (Google/Microsoft) y validar dominio.
    """
    allowed = {e.strip().lower() for e in settings.ADMIN_ALLOWED_EMAILS.split(",") if e.strip()}
    if email.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Not allowed")
    token = create_access_token({"email": email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/dashboard/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Dashboard principal con KPIs y estado del sistema.

    Returns:
        - Totales: confirmadas, pre-reservas, canceladas, revenue
        - Conversión: tasa de pre-reserva → confirmada
        - Últimas 24h: nuevas reservas, pagos recibidos
        - Health: DB, Redis, iCal
        - Performance: error rate, P95
    """
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Totales generales
    confirmed_count = (
        await db.scalar(
            select(func.count(Reservation.id)).where(Reservation.reservation_status == "confirmed")
        )
        or 0
    )

    pre_reserved_count = (
        await db.scalar(
            select(func.count(Reservation.id)).where(
                Reservation.reservation_status == "pre_reserved"
            )
        )
        or 0
    )

    cancelled_count = (
        await db.scalar(
            select(func.count(Reservation.id)).where(Reservation.reservation_status == "cancelled")
        )
        or 0
    )

    # Revenue total y del mes
    total_revenue = await db.scalar(
        select(func.sum(Reservation.total_price)).where(
            Reservation.reservation_status == "confirmed"
        )
    ) or Decimal("0")

    month_revenue = await db.scalar(
        select(func.sum(Reservation.total_price)).where(
            and_(
                Reservation.reservation_status == "confirmed",
                Reservation.confirmed_at >= month_start,
            )
        )
    ) or Decimal("0")

    # Conversión (confirmadas / total de reservas creadas)
    total_created = await db.scalar(select(func.count(Reservation.id))) or 0
    conversion_rate = (
        round((confirmed_count / total_created) * 100, 2) if total_created > 0 else 0.0
    )

    # Últimas 24h
    new_reservations_24h = (
        await db.scalar(
            select(func.count(Reservation.id)).where(Reservation.created_at >= last_24h)
        )
        or 0
    )

    payments_received_24h = (
        await db.scalar(
            select(func.count(Reservation.id)).where(
                and_(
                    Reservation.payment_status == "paid",
                    Reservation.confirmed_at >= last_24h,
                )
            )
        )
        or 0
    )

    # Health checks simplificado (en producción usar valores reales de /healthz)
    health_status_value = "healthy"  # Placeholder
    db_latency = 10  # Placeholder
    redis_latency = 5  # Placeholder
    ical_sync_age = 15  # Placeholder

    # Performance placeholder (en producción usar Prometheus metrics)
    error_rate = 0.5  # Placeholder
    p95_latency = 250  # Placeholder

    return DashboardResponse(
        totals=DashboardTotals(
            confirmed=confirmed_count,
            pre_reserved=pre_reserved_count,
            cancelled=cancelled_count,
            total_revenue=float(total_revenue),
            month_revenue=float(month_revenue),
        ),
        conversion_rate=conversion_rate,
        last_24h=DashboardLast24h(
            new_reservations=new_reservations_24h,
            payments_received=payments_received_24h,
        ),
        health=DashboardHealth(
            status=health_status_value,
            db_latency_ms=db_latency,
            redis_latency_ms=redis_latency,
            ical_last_sync_age_minutes=ical_sync_age,
        ),
        performance=DashboardPerformance(
            error_rate=error_rate,
            p95_latency_ms=p95_latency,
        ),
        timestamp=now.isoformat(),
    )


@router.get("/reservations")
async def list_reservations(
    status: Optional[str] = Query(default=None),
    accommodation_id: Optional[int] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    search: Optional[str] = Query(
        default=None, description="Buscar por nombre, email o teléfono del huésped"
    ),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Listar reservas con filtros opcionales."""
    filters = []
    if status:
        filters.append(Reservation.reservation_status == status)
    if accommodation_id:
        filters.append(Reservation.accommodation_id == accommodation_id)
    if from_date:
        filters.append(Reservation.check_in >= from_date)
    if to_date:
        filters.append(Reservation.check_out <= to_date)
    if search:
        # Búsqueda case-insensitive en guest_name, guest_email, guest_phone
        search_pattern = f"%{search}%"
        filters.append(
            or_(
                Reservation.guest_name.ilike(search_pattern),
                Reservation.guest_email.ilike(search_pattern),
                Reservation.guest_phone.ilike(search_pattern),
            )
        )

    stmt = select(Reservation).where(and_(*filters)) if filters else select(Reservation)

    # O4: Eager loading para prevenir N+1 queries
    # Si en el futuro se accede a r.accommodation.name, no generará queries adicionales
    stmt = stmt.options(selectinload(Reservation.accommodation))

    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "code": r.code,
            "accommodation_id": r.accommodation_id,
            "guest_name": r.guest_name,
            "guest_email": r.guest_email,
            "guest_phone": r.guest_phone,
            "check_in": getattr(r, "check_in").isoformat()
            if getattr(r, "check_in", None) is not None
            else None,
            "check_out": getattr(r, "check_out").isoformat()
            if getattr(r, "check_out", None) is not None
            else None,
            "status": r.reservation_status,
            "total_price": r.total_price,
            "created_at": getattr(r, "created_at").isoformat()
            if getattr(r, "created_at", None) is not None
            else None,
        }
        for r in rows
    ]


@router.get("/reservations/{reservation_id}", response_model=ReservationDetailResponse)
async def get_reservation_detail(
    reservation_id: int,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Detalle completo de una reserva con timeline, webhooks y logs de pago."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(
            status_code=404,
            detail=f"Reservation {reservation_id} not found",
        )

    # Construir timeline de eventos
    timeline = [
        TimelineEvent(
            event="pre_reserved",
            timestamp=reservation.created_at.isoformat() if reservation.created_at else None,
            description="Pre-reserva creada",
            metadata={"channel": reservation.channel_source},
        )
    ]

    if reservation.confirmed_at:
        timeline.append(
            TimelineEvent(
                event="confirmed",
                timestamp=reservation.confirmed_at.isoformat(),
                description="Reserva confirmada y pago recibido",
                metadata={"payment_status": reservation.payment_status},
            )
        )

    if reservation.reservation_status == "cancelled":
        timeline.append(
            TimelineEvent(
                event="cancelled",
                timestamp=datetime.utcnow().isoformat(),  # Placeholder
                description="Reserva cancelada",
            )
        )

    # TODO: Implementar webhooks y payment logs cuando se agreguen las tablas
    webhooks = []  # Lista de WebhookLog
    payment_logs = []  # Lista de PaymentLog

    return ReservationDetailResponse(
        id=reservation.id,
        code=reservation.code,
        accommodation_id=reservation.accommodation_id,
        guest_name=reservation.guest_name,
        guest_phone=reservation.guest_phone,
        guest_email=reservation.guest_email,
        check_in=reservation.check_in.isoformat() if reservation.check_in else None,
        check_out=reservation.check_out.isoformat() if reservation.check_out else None,
        guests_count=reservation.guests_count,
        total_price=float(reservation.total_price),
        deposit_percentage=float(reservation.deposit_percentage),
        deposit_amount=float(reservation.deposit_amount),
        payment_status=reservation.payment_status,
        reservation_status=reservation.reservation_status,
        channel_source=reservation.channel_source,
        created_at=reservation.created_at.isoformat() if reservation.created_at else None,
        confirmed_at=reservation.confirmed_at.isoformat() if reservation.confirmed_at else None,
        expires_at=reservation.expires_at.isoformat() if reservation.expires_at else None,
        notes=reservation.notes,
        timeline=timeline,
        webhooks=webhooks,
        payment_logs=payment_logs,
    )


@router.post("/reservations/{reservation_id}/confirm", response_model=ActionResponse)
async def confirm_reservation(
    reservation_id: int,
    request: ConfirmReservationRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Confirmar manualmente una pre-reserva."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.reservation_status != "pre_reserved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot confirm reservation with status: {reservation.reservation_status}",
        )

    # Actualizar estado
    reservation.reservation_status = "confirmed"
    reservation.payment_status = "paid"
    reservation.confirmed_at = datetime.utcnow()

    if request.notes:
        reservation.notes = (reservation.notes or "") + f"\n[Admin] {request.notes}"

    await db.commit()

    # Broadcast notification a WebSockets
    await broadcast_notification(
        "reservation_confirmed",
        {
            "reservation_id": reservation.id,
            "reservation_code": reservation.code,
            "guest_name": reservation.guest_name,
        },
    )

    return ActionResponse(
        success=True,
        message="Reservation confirmed successfully",
        reservation_id=reservation.id,
        new_status="confirmed",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.post("/reservations/{reservation_id}/cancel", response_model=ActionResponse)
async def cancel_reservation(
    reservation_id: int,
    request: CancelReservationRequest,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Cancelar una reserva (pre-reserva o confirmada)."""
    result = await db.execute(select(Reservation).where(Reservation.id == reservation_id))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    if reservation.reservation_status == "cancelled":
        raise HTTPException(status_code=400, detail="Reservation already cancelled")

    # Actualizar estado
    previous_status = reservation.reservation_status
    reservation.reservation_status = "cancelled"

    # Agregar nota de cancelación
    cancellation_note = f"\n[Admin Cancellation] Reason: {request.reason}"
    if request.refund_amount:
        cancellation_note += f" | Refund: ${request.refund_amount}"

    reservation.notes = (reservation.notes or "") + cancellation_note

    await db.commit()

    # Broadcast notification
    await broadcast_notification(
        "reservation_cancelled",
        {
            "reservation_id": reservation.id,
            "reservation_code": reservation.code,
            "guest_name": reservation.guest_name,
            "previous_status": previous_status,
            "reason": request.reason,
        },
    )

    return ActionResponse(
        success=True,
        message="Reservation cancelled successfully",
        reservation_id=reservation.id,
        new_status="cancelled",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/reservations/export.csv")
async def export_reservations_csv(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Exportar reservas a CSV."""
    # O4: Eager loading proactivo para export
    stmt = select(Reservation).options(selectinload(Reservation.accommodation))
    result = await db.execute(stmt)
    rows = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "code",
            "accommodation_id",
            "guest_name",
            "guest_email",
            "guest_phone",
            "check_in",
            "check_out",
            "status",
            "total_price",
            "created_at",
        ]
    )
    for r in rows:
        writer.writerow(
            [
                r.code,
                r.accommodation_id,
                r.guest_name,
                r.guest_email,
                r.guest_phone,
                r.check_in,
                r.check_out,
                r.reservation_status,
                r.total_price,
                r.created_at,
            ]
        )
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv")


@router.post("/actions/resend-email/{code}")
async def resend_email(
    code: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
    x_csrf_token: str | None = Header(default=None),
):
    """Reenviar notificación de email para una reserva.

    Requiere autenticación admin y token CSRF básico.
    """
    if not x_csrf_token or len(x_csrf_token) < 8:
        # CSRF muy simple: presencia de token en header (un secreto compartido via UI)
        raise HTTPException(status_code=403, detail="Missing CSRF token")

    r = await db.scalar(select(Reservation).where(Reservation.code == code))
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")

    # Forzar conversión de todos los valores a tipos nativos Python
    guest_email_val = getattr(r, "guest_email", None)
    if guest_email_val is None or (isinstance(guest_email_val, str) and not guest_email_val):
        raise HTTPException(status_code=400, detail="Reservation has no guest_email")

    # Obtener nombre de alojamiento
    accommodation_name = str(getattr(r, "accommodation_id"))
    if hasattr(r, "accommodation") and r.accommodation:
        accommodation_name = str(getattr(r.accommodation, "name"))

    # Determinar tipo de email según estado
    email_type = "prereservation"
    reservation_status_val = str(getattr(r, "reservation_status"))
    if reservation_status_val == "confirmed":
        email_type = "confirmed"
    elif reservation_status_val == "cancelled":
        email_type = "expired"

    # Enviar email según tipo
    success = False
    try:
        # Extraer todos los valores
        code_val = str(getattr(r, "code"))
        guest_name_val = str(getattr(r, "guest_name", "Cliente") or "Cliente")
        check_in_val = str(getattr(r, "check_in"))
        check_out_val = str(getattr(r, "check_out"))
        guests_count_val = int(getattr(r, "guests_count", 1))
        total_price_val = float(getattr(r, "total_price", 0))
        expires_at_val = getattr(r, "expires_at", None)
        expires_at_str = expires_at_val.isoformat() if expires_at_val is not None else ""

        if email_type == "prereservation":
            success = await email_service.send_prereservation_confirmation(
                guest_email=str(guest_email_val),
                guest_name=guest_name_val,
                reservation_code=code_val,
                accommodation_name=accommodation_name,
                check_in=check_in_val,
                check_out=check_out_val,
                guests_count=guests_count_val,
                total_amount=total_price_val,
                expires_at=expires_at_str,
            )
        elif email_type == "confirmed":
            success = await email_service.send_reservation_confirmed(
                guest_email=str(guest_email_val),
                guest_name=guest_name_val,
                reservation_code=code_val,
                accommodation_name=accommodation_name,
                check_in=check_in_val,
                check_out=check_out_val,
                guests_count=guests_count_val,
                total_amount=total_price_val,
            )
        elif email_type == "expired":
            success = await email_service.send_reservation_expired(
                guest_email=str(guest_email_val),
                guest_name=guest_name_val,
                reservation_code=code_val,
                accommodation_name=accommodation_name,
                check_in=check_in_val,
                check_out=check_out_val,
            )
    except Exception as e:
        logger.error("admin_resend_email_failed", code=code, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return {"sent": success, "email_type": email_type}


@router.get("/calendar/availability", response_model=CalendarResponse)
async def get_calendar_availability(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024, le=2030),
    accommodation_id: Optional[int] = Query(None),
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retorna disponibilidad de calendario mensual con eventos y tasa de ocupación.

    Args:
        month: Mes (1-12)
        year: Año (2024-2030)
        accommodation_id: ID opcional de alojamiento específico

    Returns:
        CalendarResponse con lista de eventos y métricas
    """
    from calendar import monthrange
    from datetime import date

    # Calcular rango de fechas del mes
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # Obtener reservas que se solapen con el mes
    res_query = select(Reservation).where(
        and_(
            Reservation.reservation_status.in_(["pre_reserved", "confirmed"]),
            or_(
                # Reservas que empiezan en el mes
                and_(Reservation.check_in >= start_date, Reservation.check_in <= end_date),
                # Reservas que terminan en el mes
                and_(Reservation.check_out >= start_date, Reservation.check_out <= end_date),
                # Reservas que abarcan todo el mes
                and_(Reservation.check_in <= start_date, Reservation.check_out >= end_date),
            ),
        )
    )

    if accommodation_id:
        res_query = res_query.where(Reservation.accommodation_id == accommodation_id)

    result = await db.execute(res_query)
    reservations = result.scalars().all()

    # Convertir reservas a eventos
    events = [
        CalendarEvent(
            id=r.id,
            code=r.code,
            accommodation_id=r.accommodation_id,
            guest_name=r.guest_name,
            check_in=r.check_in.isoformat() if r.check_in else "",
            check_out=r.check_out.isoformat() if r.check_out else "",
            status=r.reservation_status,
            total_price=float(r.total_price),
            channel_source=r.channel_source,
        )
        for r in reservations
    ]

    # Calcular tasa de ocupación del mes
    total_days_in_month = last_day
    occupied_days = 0

    for res in reservations:
        if res.reservation_status == "confirmed":
            # Contar días ocupados dentro del mes
            res_start = max(res.check_in, start_date) if res.check_in else start_date
            res_end = min(res.check_out, end_date) if res.check_out else end_date
            days = (res_end - res_start).days
            occupied_days += max(0, days)

    occupancy_rate = (
        round((occupied_days / total_days_in_month) * 100, 1) if total_days_in_month > 0 else 0.0
    )

    return CalendarResponse(
        events=events,
        month=f"{year}-{month:02d}",
        occupancy_rate=occupancy_rate,
    )


# WebSocket connection manager
class ConnectionManager:
    """Gestiona conexiones WebSocket activas para alertas real-time."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Connect a new websocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """Disconnect a websocket client."""
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        """Send a message to all connected clients.

        Args:
            message: Message dictionary to broadcast
        """
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_send_failed", error=str(e))
                dead_connections.append(connection)

        # Limpiar conexiones muertas
        for conn in dead_connections:
            try:
                self.disconnect(conn)
            except ValueError:
                pass  # Ya removida


# Instancia global del connection manager
ws_manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """Real-time alerts WebSocket endpoint for admin dashboard.

    Client must send JWT token as query param: /admin/ws?token=xxx

    Once connected, server will send JSON notifications:
    {
        "type": "nueva_reserva" | "pago_confirmado" | "checkin_hoy" | "reservation_expired",
        "data": {
            "reservation_code": "RES...",
            "guest_name": "...",
            "accommodation_name": "...",
            "total_amount": 123.45,
            ...
        },
        "timestamp": "2025-10-17T12:00:00Z"
    }
    """
    # Validar token
    try:
        payload = verify_jwt_token(token)
        email = payload.get("email")
        allowed = {e.strip().lower() for e in settings.ADMIN_ALLOWED_EMAILS.split(",") if e.strip()}
        if not email or email.lower() not in allowed:
            await websocket.close(code=4003, reason="Not authorized")
            return
    except Exception as e:
        logger.error("websocket_auth_failed", error=str(e))
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Conectar
    await ws_manager.connect(websocket)

    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json(
            {
                "type": "connected",
                "data": {"message": "Conectado al sistema de alertas"},
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )

        # Mantener conexión viva (el servidor enviará notificaciones via broadcast)
        while True:
            # Esperar mensajes del cliente (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                # Echo para keep-alive
                if data == "ping":
                    await websocket.send_json(
                        {"type": "pong", "timestamp": datetime.now(UTC).isoformat()}
                    )
            except asyncio.TimeoutError:
                # Enviar ping periódico
                await websocket.send_json(
                    {"type": "ping", "timestamp": datetime.now(UTC).isoformat()}
                )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("websocket_client_disconnected")
    except Exception as e:
        logger.error("websocket_error", error=str(e))
        ws_manager.disconnect(websocket)


async def broadcast_notification(
    notification_type: str,
    data: dict,
):
    """Broadcast notification to all connected WebSocket clients.

    Use from anywhere in the code:
        await broadcast_notification("nueva_reserva", {
            "reservation_code": res.code,
            "guest_name": res.guest_name,
            ...
        })
    """
    message = {"type": notification_type, "data": data, "timestamp": datetime.now(UTC).isoformat()}
    await ws_manager.broadcast(message)
    logger.info(
        "websocket_notification_sent",
        type=notification_type,
        recipients=len(ws_manager.active_connections),
    )
