from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.services import nlu as nlu_service
from app.services.reservations import ReservationService
from app.models import Accommodation
from app.metrics import NLU_PRE_RESERVE

router = APIRouter(prefix="/nlu", tags=["nlu"])


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=2)
    accommodation_id: Optional[int] = None


class AnalyzeResponse(BaseModel):
    nlu: Dict[str, Any]
    action: str
    data: Optional[Dict[str, Any]] = None


def _parse_dates(dates: List[str]) -> Optional[tuple[date, date]]:
    if not dates:
        return None
    # Tomar los dos primeros si hay más
    parsed: List[date] = []
    for s in dates[:2]:
        try:
            parsed.append(date.fromisoformat(s))
        except Exception:
            pass
    if len(parsed) >= 2 and parsed[0] < parsed[1]:
        return parsed[0], parsed[1]
    return None


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(payload: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    analysis = nlu_service.analyze(payload.text)

    # Extraer slots
    dates = analysis.get("dates") or []
    guests = analysis.get("guests")
    parsed = _parse_dates(dates)
    check_in: Optional[date] = parsed[0] if parsed else None
    check_out: Optional[date] = parsed[1] if parsed else None

    # Resolver alojamiento
    acc_id = payload.accommodation_id
    if not acc_id:
        # Si hay exactamente 1 alojamiento activo, usarlo
        q = await db.execute(select(Accommodation).where(Accommodation.active.is_(True)).limit(2))
        rows = q.scalars().all()
        if len(rows) == 1:
            acc_id = rows[0].id

    missing: List[str] = []
    if not acc_id:
        missing.append("accommodation_id")
    if not check_in:
        missing.append("check_in")
    if not check_out:
        missing.append("check_out")
    if not guests:
        missing.append("guests")

    if missing:
        NLU_PRE_RESERVE.labels(action="needs_slots", source="api").inc()
        return AnalyzeResponse(nlu=analysis, action="needs_slots", data={"missing": missing})

    # Slots completos -> crear pre-reserva de forma mínima
    service = ReservationService(db)
    result = await service.create_prereservation(
        accommodation_id=acc_id,  # type: ignore[arg-type]
        check_in=check_in,  # type: ignore[arg-type]
        check_out=check_out,  # type: ignore[arg-type]
        guests=int(guests),
        channel="whatsapp",
        contact_name="Cliente WhatsApp",
        contact_phone="+000000000",
        contact_email=None,
    )

    if result.get("error"):
        NLU_PRE_RESERVE.labels(action="error", source="api").inc()
        return AnalyzeResponse(nlu=analysis, action="error", data=result)
    NLU_PRE_RESERVE.labels(action="pre_reserved", source="api").inc()
    return AnalyzeResponse(nlu=analysis, action="pre_reserved", data=result)
