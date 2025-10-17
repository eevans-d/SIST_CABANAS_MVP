"""
Tests para endpoint /admin/dashboard/stats.

Valida que las estadísticas del dashboard se calculen correctamente.
"""
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_stats_success(test_client: AsyncClient, db_session):
    """Test exitoso de obtención de estadísticas del dashboard."""
    from app.core.config import get_settings
    from app.core.security import create_access_token
    from app.models.accommodation import Accommodation
    from app.models.reservation import Reservation

    settings = get_settings()

    # Crear alojamiento de prueba
    acc = Accommodation(
        name="Test Cabin",
        type="cabin",
        capacity=4,
        base_price=Decimal("100.00"),
        active=True,
    )
    db_session.add(acc)
    await db_session.flush()

    # Crear reservas de prueba
    now = datetime.utcnow()

    # 2 pre-reservas activas
    for i in range(2):
        res = Reservation(
            code=f"PRE{i:03d}",
            accommodation_id=acc.id,
            guest_name=f"Guest {i}",
            guest_phone=f"+549111222{i:04d}",
            check_in=now.date() + timedelta(days=i + 1),
            check_out=now.date() + timedelta(days=i + 3),
            guests_count=2,
            total_price=Decimal("200.00"),
            reservation_status="pre_reserved",
            channel_source="whatsapp",
        )
        db_session.add(res)

    # 1 reserva confirmada este mes
    res_confirmed = Reservation(
        code="CONF001",
        accommodation_id=acc.id,
        guest_name="Confirmed Guest",
        guest_phone="+5491112223333",
        check_in=now.date() + timedelta(days=5),
        check_out=now.date() + timedelta(days=7),
        guests_count=3,
        total_price=Decimal("300.00"),
        reservation_status="confirmed",
        channel_source="email",
        created_at=now,
    )
    db_session.add(res_confirmed)

    # 1 reserva cancelada (no debe contar)
    res_cancelled = Reservation(
        code="CANC001",
        accommodation_id=acc.id,
        guest_name="Cancelled Guest",
        guest_phone="+5491112224444",
        check_in=now.date() + timedelta(days=10),
        check_out=now.date() + timedelta(days=12),
        guests_count=2,
        total_price=Decimal("200.00"),
        reservation_status="cancelled",
        channel_source="whatsapp",
    )
    db_session.add(res_cancelled)

    await db_session.commit()

    # Crear token admin válido
    admin_email = settings.ADMIN_ALLOWED_EMAILS.split(",")[0].strip()
    token = create_access_token({"email": admin_email})

    # Hacer request al endpoint con autenticación
    response = await test_client.get(
        "/admin/dashboard/stats", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # Validar estructura de respuesta
    assert "total_reservations" in data
    assert "total_guests" in data
    assert "monthly_revenue" in data
    assert "pending_confirmations" in data
    assert "avg_occupancy_rate" in data
    assert "last_updated" in data

    # Validar valores esperados
    assert data["total_reservations"] == 3  # 2 pre-reserved + 1 confirmed
    assert data["total_guests"] == 7  # 2+2+3
    assert data["monthly_revenue"] == 300.0  # Solo la confirmada
    assert data["pending_confirmations"] == 2  # Solo pre-reservas
    assert data["avg_occupancy_rate"] >= 0.0
    assert data["avg_occupancy_rate"] <= 100.0


@pytest.mark.asyncio
async def test_dashboard_stats_empty_db(test_client: AsyncClient):
    """Test con base de datos vacía - debe retornar ceros."""
    from app.core.config import get_settings
    from app.core.security import create_access_token

    settings = get_settings()
    admin_email = settings.ADMIN_ALLOWED_EMAILS.split(",")[0].strip()
    token = create_access_token({"email": admin_email})

    response = await test_client.get(
        "/admin/dashboard/stats", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_reservations"] == 0
    assert data["total_guests"] == 0
    assert data["monthly_revenue"] == 0.0
    assert data["pending_confirmations"] == 0
    assert data["avg_occupancy_rate"] == 0.0


@pytest.mark.asyncio
async def test_dashboard_stats_unauthorized(test_client: AsyncClient):
    """Test sin autenticación - debe retornar 401."""
    response = await test_client.get("/admin/dashboard/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_stats_invalid_token(test_client: AsyncClient):
    """Test con token inválido - debe retornar 401."""
    response = await test_client.get(
        "/admin/dashboard/stats", headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code in [401, 403]
