from __future__ import annotations
"""Servicio iCal MVP.

Export: Genera un feed ICS con reservas confirmed (y opcionalmente pre_reserved no expirada) para un accommodation.
Import: Consume calendarios externos (URLs registradas) y crea bloqueos como reservas PRE_RESERVED externas (canal airbnb/booking) evitando duplicación por UID.

Simplificaciones MVP:
- Almacenar eventos importados en tabla reservations con code = "BLK<hash corta>" si no existe ya un rango que solape (usando constraint) y guardando internal_notes con UID.
- Dedupe: se basa en UID encontrado en internal_notes (pattern UID:<value>).
"""
from typing import List, Optional
from datetime import datetime, date, timedelta, timezone
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Accommodation, Reservation
from app.models.enums import ReservationStatus, ChannelSource

ICS_HEADER = """BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//MVP Alojamientos//ES\nCALSCALE:GREGORIAN"""
ICS_FOOTER = "END:VCALENDAR"

def _format_dt(d: date) -> str:
    # Usamos formato date sin horas (alojamientos por noche)
    return f"{d:%Y%m%d}"  # DTSTART;VALUE=DATE:YYYYMMDD

class ICalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_calendar(self, accommodation_id: int, token: str) -> Optional[str]:
        # Validar accommodation + token
        acc_stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
        acc_res = await self.db.execute(acc_stmt)
        acc = acc_res.scalar_one_or_none()
        if not acc or acc.ical_export_token != token:
            return None

        # Traer reservas confirmed y pre_reserved no expirada
        stmt = select(Reservation).where(Reservation.accommodation_id == accommodation_id)
        result = await self.db.execute(stmt)
        rows: List[Reservation] = result.scalars().all()
        lines = [ICS_HEADER]
        for r in rows:
            if r.reservation_status not in (ReservationStatus.CONFIRMED.value, ReservationStatus.PRE_RESERVED.value):
                continue
            if r.reservation_status == ReservationStatus.PRE_RESERVED.value and r.expires_at:
                exp = r.expires_at
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < datetime.now(timezone.utc):
                    continue
            uid = f"{r.code}@acc{accommodation_id}"
            dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{dtstamp}",
                f"DTSTART;VALUE=DATE:{_format_dt(r.check_in)}",
                f"DTEND;VALUE=DATE:{_format_dt(r.check_out)}",
                f"SUMMARY:RESERVA {r.code}",
                "END:VEVENT",
            ])
        lines.append(ICS_FOOTER)
        return "\n".join(lines)

    async def import_events(self, accommodation_id: int, ical_text: str, source: str) -> int:
        # Parse muy simplificado: buscar bloques BEGIN:VEVENT ... END:VEVENT y extraer DTSTART/DTEND/UID
        events = ical_text.split("BEGIN:VEVENT")
        created = 0
        now = datetime.now(timezone.utc)
        # Cargar accommodation una vez para validar existencia y luego actualizar last_ical_sync_at
        acc_stmt = select(Accommodation).where(Accommodation.id == accommodation_id)
        acc_res = await self.db.execute(acc_stmt)
        acc = acc_res.scalar_one_or_none()
        if not acc:
            return 0
        for chunk in events[1:]:
            try:
                end_idx = chunk.index("END:VEVENT")
            except ValueError:
                continue
            block = chunk[:end_idx]
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            data = {}
            for line in lines:
                if line.startswith("UID:"):
                    data['uid'] = line[4:].strip()
                elif line.startswith("DTSTART"):
                    _, val = line.split(":",1)
                    data['start'] = datetime.strptime(val.strip(), "%Y%m%d").date()
                elif line.startswith("DTEND"):
                    _, val = line.split(":",1)
                    data['end'] = datetime.strptime(val.strip(), "%Y%m%d").date()
            if not data.get('uid') or not data.get('start') or not data.get('end'):
                continue
            uid = data['uid']
            check_in = data['start']
            check_out = data['end']
            # Dedupe por UID ya en internal_notes
            existing_stmt = select(Reservation).where(
                Reservation.accommodation_id==accommodation_id,
                Reservation.internal_notes.contains(uid)  # type: ignore
            )
            existing = await self.db.execute(existing_stmt)
            first = existing.scalar_one_or_none()
            if first:
                continue
            # Crear código determinístico
            code_hash = hashlib.sha1(uid.encode()).hexdigest()[:8].upper()
            code = f"BLK{code_hash}"
            reservation = Reservation(
                code=code,
                accommodation_id=accommodation_id,
                check_in=check_in,
                check_out=check_out,
                guest_name="ICAL",
                guest_phone="000",
                guests_count=1,
                nights=(check_out - check_in).days,
                base_price_per_night=0,
                total_price=0,
                deposit_percentage=0,
                deposit_amount=0,
                reservation_status=ReservationStatus.PRE_RESERVED.value,
                payment_status="pending",
                channel_source=source,
                expires_at=now + timedelta(days=365),  # mantener bloqueo largo
                internal_notes=f"UID:{uid}"
            )
            self.db.add(reservation)
            try:
                await self.db.commit()
                created += 1
            except Exception:
                await self.db.rollback()
                continue
        # Actualizar timestamp de última sync, independientemente de si se crearon eventos nuevos
        try:
            acc.last_ical_sync_at = now
            self.db.add(acc)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
        return created
