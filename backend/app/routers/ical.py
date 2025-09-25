from __future__ import annotations
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.ical import ICalService

router = APIRouter(prefix="/ical", tags=["ical"]) 

class ImportICalRequest(BaseModel):
    accommodation_id: int
    source: str
    ical_text: str

class ImportICalResponse(BaseModel):
    created: int

@router.get("/export/{accommodation_id}/{token}")
async def export_calendar(accommodation_id: int, token: str, db: AsyncSession = Depends(get_db)):
    service = ICalService(db)
    ics = await service.export_calendar(accommodation_id, token)
    if not ics:
        return Response(status_code=404)
    return Response(content=ics, media_type="text/calendar")

@router.post("/import", response_model=ImportICalResponse)
async def import_calendar(payload: ImportICalRequest, db: AsyncSession = Depends(get_db)):
    service = ICalService(db)
    created = await service.import_events(payload.accommodation_id, payload.ical_text, payload.source)
    return ImportICalResponse(created=created)
