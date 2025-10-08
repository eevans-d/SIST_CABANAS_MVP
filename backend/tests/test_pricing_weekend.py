import pytest
from datetime import date


@pytest.mark.asyncio
async def test_weekend_multiplier_applied(db_session, accommodation_factory):  # type: ignore
    from app.services.reservations import ReservationService
    from app.models.reservation import Reservation

    acc = await accommodation_factory(weekend_multiplier=1.5, base_price=12000)
    service = ReservationService(db_session)
    # Rango que incluye viernes->lunes (3 noches: vie->sab, sab->dom, dom->lun) => 2 noches weekend (sab, dom)
    check_in = date(2025, 1, 3)  # Asumir que es viernes (ver calendario 2025: 3 Jan 2025 es Friday)
    check_out = date(2025, 1, 6)
    result = await service.create_prereservation(
        accommodation_id=acc.id,
        check_in=check_in,
        check_out=check_out,
        guests=2,
        channel="test",
        contact_name="Tester",
        contact_phone="+5491100000000",
        contact_email=None,
    )
    assert "error" not in result, result
    # Precio esperado: 1 noche normal + 2 noches con multiplicador 1.5
    base = 12000
    expected = base * 1 + base * 1.5 * 2
    assert float(result["total_price"]) == pytest.approx(expected, rel=1e-6)
