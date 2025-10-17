"""Router de administración para el sistema de reservas."""
from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import structlog
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_jwt_token
from app.models.reservation import Reservation
from app.services.email import email_service
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, func, select
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
