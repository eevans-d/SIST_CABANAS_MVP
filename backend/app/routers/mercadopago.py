from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import verify_mercadopago_signature
from app.services.mercadopago import MercadoPagoService
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

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
async def mercadopago_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Procesa webhook de Mercado Pago.

    Si MERCADOPAGO_WEBHOOK_SECRET está configurado, exige cabecera 'x-signature'
    con formato que incluya v1=<hex>. Si la firma no coincide -> 403.
    """
    raw = await request.body()
    settings = get_settings()
    if settings.MERCADOPAGO_WEBHOOK_SECRET:
        ok = verify_mercadopago_signature(dict(request.headers), raw)
        if not ok:
            raise HTTPException(status_code=403, detail="Invalid signature")

    # Parsear JSON manualmente (evitamos doble lectura del body por Pydantic)
    try:
        payload = MPWebhookPayload.model_validate_json(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    service = MercadoPagoService(db)
    result: Dict[str, Any] = await service.process_webhook(payload.model_dump())
    if result.get("error"):
        return MPWebhookResponse(
            status="error", payment_id=payload.id, idempotent=False, error=result["error"]
        )
    return MPWebhookResponse(
        status="ok",
        payment_id=result["payment_id"],
        idempotent=result["idempotent"],
        reservation_id=result.get("reservation_id"),
        events_count=result.get("events_count"),
    )
