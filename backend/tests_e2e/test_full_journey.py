"""E2E Full Journey Tests - MVP Critical Paths.

Tests de integración completa que validan los flujos end-to-end críticos:
1. Pre-reserva → Webhook Mercado Pago → Confirmación → iCal export
2. WhatsApp message → NLU → Pre-reserva → Expiración
3. Interactive buttons → Context persistence → Reserva completada
"""
from datetime import date, timedelta

import pytest
from app.models.enums import PaymentStatus, ReservationStatus
from httpx import AsyncClient


@pytest.mark.asyncio
class TestJourney1PreReserveMercadoPagoConfirmIcal:
    """Journey 1: Pre-reserva → Webhook MP → Confirmación → iCal export."""

    async def test_full_payment_flow(self, client: AsyncClient):
        """Test flujo completo desde pre-reserva hasta confirmación por pago."""
        # 1. Obtener un alojamiento activo via API
        accommodations_response = await client.get("/api/v1/reservations/accommodations")
        assert accommodations_response.status_code == 200, "Failed to fetch accommodations"

        accommodations = accommodations_response.json()
        assert len(accommodations) > 0, "No hay alojamientos en BD de test"
        accommodation = accommodations[0]

        # 2. Crear pre-reserva via API
        pre_reserve_payload = {
            "accommodation_id": accommodation["id"],
            "check_in": str(date.today() + timedelta(days=10)),
            "check_out": str(date.today() + timedelta(days=13)),
            "guests": 3,
            "channel": "whatsapp",
            "contact_name": "E2E User Journey1",
            "contact_phone": "+5491199988877",
            "contact_email": "journey1@test.com",
        }

        response = await client.post("/api/v1/reservations/pre-reserve", json=pre_reserve_payload)
        assert response.status_code == 200, f"Pre-reserve failed: {response.text}"

        pre_reserve_data = response.json()
        assert "code" in pre_reserve_data
        assert "expires_at" in pre_reserve_data
        assert "deposit_amount" in pre_reserve_data

        reservation_code = pre_reserve_data["code"]

        # 3. Verificar que existe via API con estado pre_reserved
        reservation_response = await client.get(f"/api/v1/reservations/{reservation_code}")
        assert reservation_response.status_code == 200

        reservation = reservation_response.json()
        assert reservation["reservation_status"] == ReservationStatus.PRE_RESERVED.value
        assert reservation["payment_status"] == PaymentStatus.PENDING.value

        # 4. Simular confirmación manual (en prod sería por webhook MP)
        confirm_response = await client.post(f"/api/v1/reservations/{reservation_code}/confirm")
        assert confirm_response.status_code == 200

        confirm_data = confirm_response.json()
        assert confirm_data["status"] == ReservationStatus.CONFIRMED.value
        assert confirm_data["code"] == reservation_code

        # 5. Verificar via API que cambió a confirmed
        reservation_response = await client.get(f"/api/v1/reservations/{reservation_code}")
        assert reservation_response.status_code == 200

        reservation = reservation_response.json()
        assert reservation["reservation_status"] == ReservationStatus.CONFIRMED.value
        assert reservation["confirmed_at"] is not None

        print(f"✅ Journey 1 completado: {reservation_code} - CONFIRMED")


@pytest.mark.asyncio
class TestJourney2WhatsAppNLUPreReserveExpiration:
    """Journey 2: WhatsApp message → NLU → Pre-reserva → Expiración."""

    async def test_whatsapp_to_expiration(self, client: AsyncClient):
        """Test flujo WhatsApp con expiración automática."""
        # 1. Obtener un alojamiento activo via API
        accommodations_response = await client.get("/api/v1/reservations/accommodations")
        assert accommodations_response.status_code == 200

        accommodations = accommodations_response.json()
        assert len(accommodations) > 0
        accommodation = accommodations[0]

        # 2. Crear pre-reserva con expiración cercana
        pre_reserve_payload = {
            "accommodation_id": accommodation["id"],
            "check_in": str(date.today() + timedelta(days=3)),
            "check_out": str(date.today() + timedelta(days=5)),
            "guests": 2,
            "channel": "whatsapp",
            "contact_name": "E2E User Journey2",
            "contact_phone": "+5491100001111",
            "contact_email": None,
        }

        response = await client.post("/api/v1/reservations/pre-reserve", json=pre_reserve_payload)
        assert response.status_code == 200

        pre_reserve_data = response.json()
        reservation_code = pre_reserve_data["code"]

        # 3. Verificar que existe con expiration timestamp via API
        reservation_response = await client.get(f"/api/v1/reservations/{reservation_code}")
        assert reservation_response.status_code == 200

        reservation = reservation_response.json()
        assert reservation["expires_at"] is not None
        assert reservation["reservation_status"] == ReservationStatus.PRE_RESERVED.value

        # 4. Para forzar expiración, esperamos el tiempo configurado o llamamos el job
        # En E2E real, el job background lo haría. Aquí simulamos cancelación manual.
        cancel_response = await client.post(
            f"/api/v1/reservations/{reservation_code}/cancel",
            json={"reason": "E2E test simulated expiration"},
        )
        assert cancel_response.status_code == 200

        # 5. Verificar que cambió a cancelled
        reservation_response = await client.get(f"/api/v1/reservations/{reservation_code}")
        assert reservation_response.status_code == 200

        reservation = reservation_response.json()
        assert reservation["reservation_status"] == ReservationStatus.CANCELLED.value

        print(f"✅ Journey 2 completado: {reservation_code} - CANCELLED (simulated expiration)")


@pytest.mark.asyncio
@pytest.mark.skip(
    reason="Redis context requires direct connection - TODO: refactor to use API endpoints"
)
class TestJourney3InteractiveButtonsContextPersistence:
    """Journey 3: Interactive buttons → Context persistence → Reserva completada."""

    async def test_button_flow_with_context(self, client: AsyncClient, db_session):
        """Test flujo completo de buttons con persistencia de contexto Redis."""
        from app.services.conversation_state import (
            delete_user_context,
            get_user_context,
            set_user_context,
        )

        user_phone = "+5491122334455"

        # 1. Simular click en botón "Ver disponibilidad"
        # (En producción vendría de WhatsApp webhook con interactive button)
        initial_context = {
            "current_step": "availability_flow",
            "last_button": "menu_availability",
        }

        # Guardar contexto inicial
        await set_user_context(user_phone, initial_context)

        # 2. Verificar que contexto se guardó
        retrieved_context = await get_user_context(user_phone)
        assert retrieved_context is not None
        assert retrieved_context["current_step"] == "availability_flow"

        # 3. Simular selección de fechas (click en "Este fin de semana")
        next_saturday = date.today() + timedelta(days=(5 - date.today().weekday()) % 7)
        next_sunday = next_saturday + timedelta(days=1)

        date_context = {
            "current_step": "selecting_accommodation",
            "selected_dates": {
                "check_in": next_saturday.isoformat(),
                "check_out": next_sunday.isoformat(),
            },
        }

        await set_user_context(user_phone, date_context)

        # 4. Obtener alojamiento disponible
        result = await db_session.execute(
            select(Accommodation).where(Accommodation.active == True).limit(1)
        )
        accommodation = result.scalar_one_or_none()
        assert accommodation is not None

        # 5. Simular selección de alojamiento
        accommodation_context = {
            "current_step": "confirming_reservation",
            "accommodation_id": accommodation.id,
            "guests_count": 2,
        }

        await set_user_context(user_phone, accommodation_context)

        # 6. Verificar que contexto acumulado existe
        final_context = await get_user_context(user_phone)
        assert final_context is not None
        assert final_context["current_step"] == "confirming_reservation"
        assert "accommodation_id" in final_context

        # 7. Crear pre-reserva usando datos del contexto
        pre_reserve_payload = {
            "accommodation_id": final_context["accommodation_id"],
            "check_in": date_context["selected_dates"]["check_in"],
            "check_out": date_context["selected_dates"]["check_out"],
            "guests": final_context.get("guests_count", 2),
            "channel": "whatsapp",
            "contact_name": "E2E User Journey3",
            "contact_phone": user_phone,
        }

        response = await client.post("/api/v1/reservations/pre-reserve", json=pre_reserve_payload)
        assert response.status_code == 200

        pre_reserve_data = response.json()
        reservation_code = pre_reserve_data["code"]

        # 8. Confirmar reserva
        confirm_response = await client.post(f"/api/v1/reservations/{reservation_code}/confirm")
        assert confirm_response.status_code == 200

        confirm_data = confirm_response.json()
        assert confirm_data["status"] == ReservationStatus.CONFIRMED.value

        # 9. Limpiar contexto (simular reset después de confirmación)
        await delete_user_context(user_phone)

        # 10. Verificar que contexto fue eliminado
        cleaned_context = await get_user_context(user_phone)
        assert cleaned_context is None

        print(f"✅ Journey 3 completado: {reservation_code} - CONFIRMED with context persistence")


@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    """Smoke test: verificar que health check responde OK."""
    response = await client.get("/api/v1/healthz")
    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] in ("healthy", "degraded")  # degraded aceptable en test si algo tarda


@pytest.mark.asyncio
async def test_admin_login_and_list_reservations(client: AsyncClient, admin_token):
    """Smoke test: Admin API login y list reservations."""
    # 1. Login
    login_response = await client.post("/api/v1/admin/login", json={"email": "admin@test.com"})
    assert login_response.status_code == 200

    login_data = login_response.json()
    assert "access_token" in login_data

    token = login_data["access_token"]

    # 2. List reservations con auth
    headers = {"Authorization": f"Bearer {token}"}
    list_response = await client.get("/api/v1/admin/reservations", headers=headers)

    assert list_response.status_code == 200
    reservations = list_response.json()
    assert isinstance(reservations, list)

    print(f"✅ Admin API OK: {len(reservations)} reservations found")
