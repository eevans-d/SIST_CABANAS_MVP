from fastapi import APIRouter, Depends, Body
from datetime import date
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.reservations import ReservationService

router = APIRouter(prefix="/reservations", tags=["reservations"])

class PreReservationRequest(BaseModel):
    accommodation_id: int = Field(..., gt=0)
    check_in: date
    check_out: date
    guests: int = Field(..., gt=0)
    channel: str = Field("whatsapp")
    contact_name: str
    contact_phone: str
    contact_email: Optional[str] = None

class PreReservationResponse(BaseModel):
    code: Optional[str] = None
    expires_at: Optional[str] = None
    deposit_amount: Optional[str] = None
    total_price: Optional[str] = None
    nights: Optional[int] = None
    error: Optional[str] = None

@router.post("/pre-reserve", response_model=PreReservationResponse)
async def create_pre_reservation(payload: PreReservationRequest, db: AsyncSession = Depends(get_db)):
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
