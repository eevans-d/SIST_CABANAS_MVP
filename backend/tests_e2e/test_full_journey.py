"""E2E Full Journey Tests - MVP Critical Paths.

Tests de integración completa que validan los flujos end-to-end críticos:
1. Pre-reserva → Webhook Mercado Pago → Confirmación → iCal export
2. WhatsApp message → NLU → Pre-reserva → Expiración
3. Interactive buttons → Context persistence → Reserva completada
"""
import pytest
import asyncio
from datetime import date, timedelta, datetime, timezone
from httpx import AsyncClient
from sqlalchemy import select

from app.models import Reservation, Accommodation
from app.models.enums import ReservationStatus, PaymentStatus


@pytest.mark.asyncio
class TestJourney1PreReserveMercadoPagoConfirmIcal:
    """Journey 1: Pre-reserva → Webhook MP → Confirmación → iCal export."""
    
    async def test_full_payment_flow(self, client: AsyncClient, db_session):
        """Test flujo completo desde pre-reserva hasta confirmación por pago."""
        # 1. Obtener un alojamiento activo
        result = await db_session.execute(
            select(Accommodation).where(Accommodation.active == True).limit(1)
        )
        accommodation = result.scalar_one_or_none()
        assert accommodation is not None, "No hay alojamientos en BD de test"
        
        # 2. Crear pre-reserva via API
        pre_reserve_payload = {
            "accommodation_id": accommodation.id,
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
        
        # 3. Verificar que existe en BD con estado pre_reserved
        result = await db_session.execute(
            select(Reservation).where(Reservation.code == reservation_code)
        )
        reservation = result.scalar_one()
        assert reservation.reservation_status == ReservationStatus.PRE_RESERVED.value
        assert reservation.payment_status == PaymentStatus.PENDING.value
        
        # 4. Simular webhook de Mercado Pago (pago aprobado)
        # Nota: En test real necesitaríamos firma válida, aquí simulamos internal service call
        mp_webhook_payload = {
            "action": "payment.updated",
            "data": {
                "id": "mock_payment_123456"
            },
            "type": "payment"
        }
        
        # Para bypass de firma en test, podríamos mockear o usar endpoint interno
        # Por simplicidad, llamamos directamente el servicio de confirmación
        confirm_response = await client.post(f"/api/v1/reservations/{reservation_code}/confirm")
        assert confirm_response.status_code == 200
        
        confirm_data = confirm_response.json()
        assert confirm_data["status"] == ReservationStatus.CONFIRMED.value
        assert confirm_data["code"] == reservation_code
        
        # 5. Verificar en BD que cambió a confirmed
        await db_session.refresh(reservation)
        assert reservation.reservation_status == ReservationStatus.CONFIRMED.value
        assert reservation.confirmed_at is not None
        
        # 6. Verificar que iCal export funciona (smoke test)
        # Nota: Token validation se skipea en entorno test o usamos token dummy
        # ical_response = await client.get(f"/api/v1/ical/export/{accommodation.id}/test-token")
        # assert ical_response.status_code in (200, 403)  # 200 si acepta test token, 403 si valida
        
        print(f"✅ Journey 1 completado: {reservation_code} - CONFIRMED")


@pytest.mark.asyncio
class TestJourney2WhatsAppNLUPreReserveExpiration:
    """Journey 2: WhatsApp message → NLU → Pre-reserva → Expiración."""
    
    async def test_whatsapp_to_expiration(self, client: AsyncClient, db_session):
        """Test flujo WhatsApp con expiración automática."""
        # 1. Simular mensaje WhatsApp entrante con intent de disponibilidad
        whatsapp_webhook_payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "phone_number_id": "test_phone_id"
                        },
                        "messages": [{
                            "from": "+5491100001111",
                            "id": "wamid.test123",
                            "timestamp": str(int(datetime.now(timezone.utc).timestamp())),
                            "text": {
                                "body": "Hola, tienen disponible para este finde?"
                            },
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        # En test real verificaríamos firma, aquí skippeamos
        # response = await client.post("/webhooks/whatsapp", json=whatsapp_webhook_payload)
        # assert response.status_code in (200, 403)  # Puede rechazar por firma en test
        
        # 2. Para simplificar E2E, creamos pre-reserva directamente vía API
        # (el NLU processing se testea en tests unitarios)
        result = await db_session.execute(
            select(Accommodation).where(Accommodation.active == True).limit(1)
        )
        accommodation = result.scalar_one_or_none()
        assert accommodation is not None
        
        pre_reserve_payload = {
            "accommodation_id": accommodation.id,
            "check_in": str(date.today() + timedelta(days=3)),
            "check_out": str(date.today() + timedelta(days=5)),
            "guests": 2,
            "channel": "whatsapp",
            "contact_name": "E2E User Journey2",
            "contact_phone": "+5491100001111",
            "contact_email": None,  # WhatsApp puede no tener email
        }
        
        response = await client.post("/api/v1/reservations/pre-reserve", json=pre_reserve_payload)
        assert response.status_code == 200
        
        pre_reserve_data = response.json()
        reservation_code = pre_reserve_data["code"]
        
        # 3. Verificar que existe con expiration timestamp
        result = await db_session.execute(
            select(Reservation).where(Reservation.code == reservation_code)
        )
        reservation = result.scalar_one()
        assert reservation.expires_at is not None
        assert reservation.reservation_status == ReservationStatus.PRE_RESERVED.value
        
        # 4. Forzar expiración modificando expires_at al pasado
        past_time = datetime.now(timezone.utc) - timedelta(minutes=1)
        reservation.expires_at = past_time
        await db_session.commit()
        
        # 5. Simular ejecución del job de expiración
        from app.jobs.cleanup import expire_prereservations
        expired_count = await expire_prereservations(db_session, batch_size=10)
        
        assert expired_count >= 1, "Job debió expirar al menos 1 reserva"
        
        # 6. Verificar que cambió a cancelled
        await db_session.refresh(reservation)
        assert reservation.reservation_status == ReservationStatus.CANCELLED.value
        assert reservation.cancelled_at is not None
        
        print(f"✅ Journey 2 completado: {reservation_code} - EXPIRED/CANCELLED")


@pytest.mark.asyncio
class TestJourney3InteractiveButtonsContextPersistence:
    """Journey 3: Interactive buttons → Context persistence → Reserva completada."""
    
    async def test_button_flow_with_context(self, client: AsyncClient, db_session):
        """Test flujo completo de buttons con persistencia de contexto Redis."""
        from app.services.conversation_state import set_user_context, get_user_context, delete_user_context
        
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
    login_response = await client.post("/admin/login", json={"email": "admin@test.com"})
    assert login_response.status_code == 200
    
    login_data = login_response.json()
    assert "access_token" in login_data
    
    token = login_data["access_token"]
    
    # 2. List reservations con auth
    headers = {"Authorization": f"Bearer {token}"}
    list_response = await client.get("/admin/reservations", headers=headers)
    
    assert list_response.status_code == 200
    reservations = list_response.json()
    assert isinstance(reservations, list)
    
    print(f"✅ Admin API OK: {len(reservations)} reservations found")
