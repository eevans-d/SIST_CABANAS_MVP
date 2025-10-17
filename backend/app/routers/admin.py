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


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    """Endpoint para estadísticas del dashboard.

    Retorna KPIs esenciales:
    - total_reservations: Cantidad total de reservas activas (pre_reserved + confirmed)
    - total_guests: Suma de huéspedes en reservas activas
    - monthly_revenue: Ingresos del mes actual (solo confirmed)
    - pending_confirmations: Cantidad de pre-reservas pendientes
    - avg_occupancy_rate: Tasa de ocupación promedio (last 30 days)
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_30_days = now - timedelta(days=30)

    # 1. Total reservas activas (pre_reserved + confirmed)
    active_stmt = select(func.count(Reservation.id)).where(
        Reservation.reservation_status.in_(["pre_reserved", "confirmed"])
    )
    active_result = await db.execute(active_stmt)
    total_reservations = active_result.scalar() or 0

    # 2. Total huéspedes en reservas activas
    guests_stmt = select(func.sum(Reservation.guests_count)).where(
        Reservation.reservation_status.in_(["pre_reserved", "confirmed"])
    )
    guests_result = await db.execute(guests_stmt)
    total_guests = guests_result.scalar() or 0

    # 3. Ingresos del mes actual (solo confirmed)
    revenue_stmt = select(func.sum(Reservation.total_price)).where(
        and_(
            Reservation.reservation_status == "confirmed",
            Reservation.created_at >= month_start,
        )
    )
    revenue_result = await db.execute(revenue_stmt)
    monthly_revenue = revenue_result.scalar() or Decimal("0.00")

    # 4. Pre-reservas pendientes de confirmación
    pending_stmt = select(func.count(Reservation.id)).where(
        Reservation.reservation_status == "pre_reserved"
    )
    pending_result = await db.execute(pending_stmt)
    pending_confirmations = pending_result.scalar() or 0

    # 5. Tasa de ocupación promedio (last 30 days) - simplificado
    # Asumimos que si hay reservas confirmed en los últimos 30 días = ocupado
    # Para cálculo preciso necesitaríamos: (días ocupados / días disponibles) * 100
    # Por ahora retornamos un estimado basado en reservas confirmed recientes
    occupancy_stmt = select(func.count(Reservation.id)).where(
        and_(
            Reservation.reservation_status == "confirmed",
            Reservation.check_in >= last_30_days,
        )
    )
    occupancy_result = await db.execute(occupancy_stmt)
    confirmed_last_30 = occupancy_result.scalar() or 0

    # Estimado: si hay 10+ reservas en 30 días = ~80% ocupación
    # Esto es simplificado para MVP, en producción usar: occupancy_days / total_available_days
    avg_occupancy_rate = (
        min(80.0, (confirmed_last_30 / 10.0) * 80.0) if confirmed_last_30 > 0 else 0.0
    )

    return {
        "total_reservations": total_reservations,
        "total_guests": total_guests,
        "monthly_revenue": float(monthly_revenue),
        "pending_confirmations": pending_confirmations,
        "avg_occupancy_rate": round(avg_occupancy_rate, 1),
        "last_updated": now.isoformat(),
    }


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


@router.get("/calendar/availability")
async def get_calendar_availability(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2024, le=2030),
    accommodation_id: Optional[int] = Query(None),
    admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Retorna disponibilidad de calendario para un mes específico.

    Args:
        month: Mes (1-12)
        year: Año (2024-2030)
        accommodation_id: ID opcional de alojamiento específico

    Returns:
        Objeto con disponibilidad por día y alojamiento
    """
    from calendar import monthrange
    from datetime import date

    from app.models.accommodation import Accommodation

    # Calcular rango de fechas del mes
    _, last_day = monthrange(year, month)
    start_date = date(year, month, 1)
    end_date = date(year, month, last_day)

    # Obtener todos los alojamientos o uno específico
    acc_query = select(Accommodation).where(Accommodation.active is True)
    if accommodation_id:
        acc_query = acc_query.where(Accommodation.id == accommodation_id)

    result = await db.execute(acc_query)
    accommodations = result.scalars().all()

    if not accommodations:
        return {"month": f"{year}-{month:02d}", "year": year, "accommodations": []}

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

    # Crear mapa de disponibilidad
    response_data = []

    for acc in accommodations:
        # Generar todos los días del mes
        availability = []
        current = start_date

        while current <= end_date:
            # Buscar si hay reserva para este día y alojamiento
            day_status = "available"
            res_code = None
            guest_name = None
            res_check_in = None
            res_check_out = None

            for res in reservations:
                if res.accommodation_id == acc.id:
                    # Check si current está en el rango [check_in, check_out)
                    if res.check_in <= current < res.check_out:
                        day_status = res.reservation_status  # pre_reserved o confirmed
                        res_code = res.code
                        guest_name = res.guest_name
                        res_check_in = res.check_in.isoformat()
                        res_check_out = res.check_out.isoformat()
                        break

            day_data = {
                "date": current.isoformat(),
                "accommodation_id": acc.id,
                "accommodation_name": acc.name,
                "status": day_status,
            }

            if res_code:
                day_data["reservation_code"] = res_code
                day_data["guest_name"] = guest_name
                day_data["check_in"] = res_check_in
                day_data["check_out"] = res_check_out

            availability.append(day_data)
            current += timedelta(days=1)

        response_data.append({"id": acc.id, "name": acc.name, "availability": availability})

    return {"month": f"{year}-{month:02d}", "year": year, "accommodations": response_data}


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
    """WebSocket endpoint para alertas real-time.

    El cliente debe enviar el JWT token como query param: /admin/ws?token=xxx

    Una vez conectado, el servidor enviará notificaciones en formato JSON:
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
    """Helper para enviar notificaciones a todos los clientes WebSocket.

    Usar desde cualquier parte del código:
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
