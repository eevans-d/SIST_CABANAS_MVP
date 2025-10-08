from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException, Header, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi.responses import StreamingResponse
from typing import Optional
import csv
import io

from app.core.database import get_db
from app.core.security import verify_jwt_token, create_access_token
from app.core.config import get_settings
from app.models.reservation import Reservation
from app.services.email import email_service

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


@router.get("/reservations")
async def list_reservations(
    status: Optional[str] = Query(default=None),
    accommodation_id: Optional[int] = Query(default=None),
    from_date: Optional[str] = Query(default=None),
    to_date: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
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
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "code": r.code,
            "accommodation_id": r.accommodation_id,
            "guest_name": r.guest_name,
            "guest_email": r.guest_email,
            "guest_phone": r.guest_phone,
            "check_in": r.check_in.isoformat() if r.check_in else None,
            "check_out": r.check_out.isoformat() if r.check_out else None,
            "status": r.reservation_status,
            "total_price": r.total_price,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/reservations/export.csv")
async def export_reservations_csv(
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_admin),
):
    stmt = select(Reservation)
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
    if not x_csrf_token or len(x_csrf_token) < 8:
        # CSRF muy simple: presencia de token en header (un secreto compartido via UI)
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    r = await db.scalar(select(Reservation).where(Reservation.code == code))
    if not r:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if not r.guest_email:
        raise HTTPException(status_code=400, detail="Reservation has no guest_email")
    subject = f"Reserva {r.code} - Estado {r.reservation_status}"
    try:
        html = email_service.render(
            "confirmation.html",
            {
                "guest_name": r.guest_name or "Cliente",
                "code": r.code,
                "accommodation_name": (
                    getattr(r, "accommodation", None).name
                    if getattr(r, "accommodation", None)
                    else str(r.accommodation_id)
                ),
                "check_in": str(r.check_in),
                "check_out": str(r.check_out),
                "total_price": str(getattr(r, "total_price", "")),
            },
        )
    except Exception:
        html = f"""
        <h3>Detalle de reserva {r.code}</h3>
        <p>Huésped: {r.guest_name}</p>
        <p>Check-in: {r.check_in}</p>
        <p>Check-out: {r.check_out}</p>
        <p>Estado: {r.reservation_status}</p>
        """
    ok = email_service.send_html(r.guest_email, subject, html)
    return {"sent": ok}
