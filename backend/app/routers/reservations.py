"""Reservations API endpoints for creating, managing, and querying reservations."""
from datetime import date
from typing import Any, Dict, Optional

from app.core.database import get_db
from app.models import Accommodation, Reservation
from app.services.reservations import ReservationService
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/reservations", tags=["reservations"])


class PreReservationRequest(BaseModel):
    """Request model for creating a pre-reservation."""

    accommodation_id: int = Field(..., gt=0)
    check_in: date
    check_out: date
    guests: int = Field(..., gt=0)
    channel: str = Field("whatsapp")
    contact_name: str
    contact_phone: str
    contact_email: Optional[str] = None


class PreReservationResponse(BaseModel):
    """Response model for pre-reservation creation."""

    code: Optional[str] = None
    expires_at: Optional[str] = None
    deposit_amount: Optional[str] = None
    total_price: Optional[str] = None
    nights: Optional[int] = None
    error: Optional[str] = None


class ConfirmReservationResponse(BaseModel):
    """Response model for reservation confirmation."""

    code: Optional[str]
    status: Optional[str]
    confirmed_at: Optional[str] = None
    error: Optional[str] = None
    model_config = {
        "from_attributes": True,
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "use_enum_values": True,
        "populate_by_name": True,
    }


class CancelReservationRequest(BaseModel):
    """Request model for cancelling a reservation."""

    reason: Optional[str] = None


class CancelReservationResponse(BaseModel):
    """Response model for reservation cancellation."""

    code: Optional[str]
    status: Optional[str]
    cancelled_at: Optional[str] = None
    error: Optional[str] = None


@router.post("/pre-reserve", response_model=PreReservationResponse)
async def create_pre_reservation(
    payload: PreReservationRequest, db: AsyncSession = Depends(get_db)
):
    """Create a new pre-reservation with expiration timestamp."""
    service = ReservationService(db)
    result: Dict[str, Any] = await service.create_prereservation(
        accommodation_id=payload.accommodation_id,
        check_in=payload.check_in,
        check_out=payload.check_out,
        guests=payload.guests,
        channel=payload.channel,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        contact_email=payload.contact_email,
    )
    return result


@router.post(
    "/{code}/confirm",
    response_model=ConfirmReservationResponse,
    response_model_exclude_none=True,
)
async def confirm_reservation(code: str, db: AsyncSession = Depends(get_db)):
    """Confirm a pre-reservation (usually after payment)."""
    service = ReservationService(db)
    return await service.confirm_reservation(code)


@router.post("/{code}/cancel", response_model=CancelReservationResponse)
async def cancel_reservation(
    code: str, payload: CancelReservationRequest, db: AsyncSession = Depends(get_db)
):
    """Cancel a reservation with optional reason."""
    service = ReservationService(db)
    return await service.cancel_reservation(code, reason=payload.reason)


@router.get("/accommodations")
async def list_accommodations(db: AsyncSession = Depends(get_db)):
    """List all active accommodations (for E2E tests)."""
    result = await db.execute(select(Accommodation).where(Accommodation.active.is_(True)))
    accommodations = result.scalars().all()
    return [
        {
            "id": acc.id,
            "name": acc.name,
            "type": acc.type,
            "capacity": acc.capacity,
            "base_price": str(acc.base_price),
            "active": acc.active,
        }
        for acc in accommodations
    ]


@router.get("/{code}")
async def get_reservation(code: str, db: AsyncSession = Depends(get_db)):
    """Get reservation details by code (for E2E tests)."""
    result = await db.execute(select(Reservation).where(Reservation.code == code))
    reservation = result.scalar_one_or_none()

    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")

    return {
        "id": reservation.id,
        "code": reservation.code,
        "accommodation_id": reservation.accommodation_id,
        "guest_name": reservation.guest_name,
        "guest_phone": reservation.guest_phone,
        "guest_email": reservation.guest_email,
        "check_in": str(reservation.check_in),
        "check_out": str(reservation.check_out),
        "guests_count": reservation.guests_count,
        "total_price": str(reservation.total_price),
        "payment_status": reservation.payment_status,
        "reservation_status": reservation.reservation_status,
        "channel_source": reservation.channel_source,
        "created_at": reservation.created_at.isoformat() if reservation.created_at else None,
        "confirmed_at": reservation.confirmed_at.isoformat() if reservation.confirmed_at else None,
        "expires_at": reservation.expires_at.isoformat() if reservation.expires_at else None,
    }
