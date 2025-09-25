from __future__ import annotations
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.mercadopago import MercadoPagoService

router = APIRouter()

class MPWebhookPayload(BaseModel):
    id: str
    status: Optional[str] = None
    amount: Optional[float] = 0
    currency: Optional[str] = "ARS"
    external_reference: Optional[str] = None

class MPWebhookResponse(BaseModel):
    status: str
    payment_id: str
    idempotent: bool
    reservation_id: Optional[int] = None
    events_count: Optional[int] = None
    error: Optional[str] = None

@router.post("/webhook", response_model=MPWebhookResponse)
async def mercadopago_webhook(payload: MPWebhookPayload, db: AsyncSession = Depends(get_db)):
    service = MercadoPagoService(db)
    result: Dict[str, Any] = await service.process_webhook(payload.dict())
    if result.get("error"):
        return MPWebhookResponse(status="error", payment_id=payload.id, idempotent=False, error=result["error"])
    return MPWebhookResponse(
        status="ok",
        payment_id=result["payment_id"],
        idempotent=result["idempotent"],
        reservation_id=result.get("reservation_id"),
        events_count=result.get("events_count"),
    )
