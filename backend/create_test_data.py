#!/usr/bin/env python3
"""
Crear datos de prueba para el sistema de alojamientos
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.models.accommodation import Accommodation
from app.models.reservation import Reservation, ReservationStatus
from app.models.enums import PaymentStatus
from app.core.config import get_settings

settings = get_settings()

async def create_test_data():
    """Crear datos de prueba en la base de datos"""
    
    # Crear engine y sesión
    database_url = settings.DATABASE_URL
    if not database_url:
        raise ValueError("DATABASE_URL no está configurada")
    
    engine = create_async_engine(database_url)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    
    async with SessionLocal() as session:
        print("🏨 Creando alojamientos de prueba...")
        
        # Alojamiento 1: Cabaña Familiar
        cabana_familiar = Accommodation(
            uuid=str(uuid.uuid4()),
            name="Cabaña Familiar Los Pinos",
            type="cabana",
            capacity=6,
            base_price=15000.00,
            weekend_multiplier=1.3,
            description="Hermosa cabaña familiar con vista al lago, ideal para familias. Incluye cocina completa, chimenea y parrilla.",
            amenities={
                "wifi": True,
                "aire_acondicionado": True,
                "calefaccion": True,
                "cocina": True,
                "heladera": True,
                "microondas": True,
                "parrilla": True,
                "chimenea": True,
                "tv": True,
                "estacionamiento": True,
                "mascotas": False,
                "piscina": False
            },
            photos={
                "principal": "https://example.com/cabana1/principal.jpg",
                "interior": ["https://example.com/cabana1/living.jpg", "https://example.com/cabana1/cocina.jpg"],
                "exterior": ["https://example.com/cabana1/exterior1.jpg", "https://example.com/cabana1/exterior2.jpg"]
            },
            location={
                "direccion": "Av. del Lago 123, Villa La Angostura",
                "coordenadas": {"lat": -40.7608, "lng": -71.6429},
                "descripcion": "A 200 metros del lago, zona tranquila"
            },
            policies={
                "check_in": "15:00",
                "check_out": "11:00",
                "cancelacion": "Cancelación gratuita hasta 7 días antes",
                "deposito": 30,
                "reglas": ["No fumar en interiores", "Máximo 6 personas", "Respetar horarios de silencio 22:00-08:00"]
            },
            ical_export_token=str(uuid.uuid4()),
            ical_import_urls=[],
            active=True
        )
        
        # Alojamiento 2: Departamento Céntrico
        depto_centrico = Accommodation(
            uuid=str(uuid.uuid4()),
            name="Departamento Céntrico Vista Montaña",
            type="departamento",
            capacity=4,
            base_price=8500.00,
            weekend_multiplier=1.2,
            description="Moderno departamento en el centro de la ciudad con hermosa vista a las montañas. Ideal para parejas o familias pequeñas.",
            amenities={
                "wifi": True,
                "aire_acondicionado": True,
                "calefaccion": True,
                "cocina": True,
                "heladera": True,
                "microondas": True,
                "parrilla": False,
                "chimenea": False,
                "tv": True,
                "estacionamiento": True,
                "mascotas": True,
                "piscina": False
            },
            photos={
                "principal": "https://example.com/depto1/principal.jpg",
                "interior": ["https://example.com/depto1/living.jpg", "https://example.com/depto1/dormitorio.jpg"],
                "exterior": ["https://example.com/depto1/balcon.jpg"]
            },
            location={
                "direccion": "San Martin 456, Bariloche Centro",
                "coordenadas": {"lat": -41.1335, "lng": -71.3103},
                "descripcion": "Centro de Bariloche, a 3 cuadras del Civic"
            },
            policies={
                "check_in": "14:00",
                "check_out": "10:00",
                "cancelacion": "Cancelación gratuita hasta 5 días antes",
                "deposito": 25,
                "reglas": ["Mascotas permitidas con depósito adicional", "No fiestas", "Máximo 4 personas"]
            },
            ical_export_token=str(uuid.uuid4()),
            ical_import_urls=[],
            active=True
        )
        
        # Alojamiento 3: Casa Completa
        casa_completa = Accommodation(
            uuid=str(uuid.uuid4()),
            name="Casa Completa El Refugio",
            type="casa",
            capacity=8,
            base_price=22000.00,
            weekend_multiplier=1.4,
            description="Casa completa con gran jardín y quincho. Perfecta para grupos grandes y celebraciones familiares.",
            amenities={
                "wifi": True,
                "aire_acondicionado": False,
                "calefaccion": True,
                "cocina": True,
                "heladera": True,
                "microondas": True,
                "parrilla": True,
                "chimenea": True,
                "tv": True,
                "estacionamiento": True,
                "mascotas": True,
                "piscina": True
            },
            photos={
                "principal": "https://example.com/casa1/principal.jpg",
                "interior": ["https://example.com/casa1/living.jpg", "https://example.com/casa1/cocina.jpg", "https://example.com/casa1/dormitorio1.jpg"],
                "exterior": ["https://example.com/casa1/jardin.jpg", "https://example.com/casa1/piscina.jpg", "https://example.com/casa1/quincho.jpg"]
            },
            location={
                "direccion": "Los Arrayanes 789, El Bolsón",
                "coordenadas": {"lat": -41.9630, "lng": -71.5339},
                "descripcion": "Zona residencial tranquila, a 10 min del centro"
            },
            policies={
                "check_in": "16:00",
                "check_out": "12:00",
                "cancelacion": "Cancelación gratuita hasta 10 días antes",
                "deposito": 35,
                "reglas": ["Eventos permitidos previo acuerdo", "Mascotas bienvenidas", "Máximo 8 personas", "Cuidar la piscina y jardín"]
            },
            ical_export_token=str(uuid.uuid4()),
            ical_import_urls=[],
            active=True
        )
        
        # Agregar alojamientos a la sesión
        session.add_all([cabana_familiar, depto_centrico, casa_completa])
        await session.commit()
        
        print("✅ Alojamientos creados:")
        print(f"   - {cabana_familiar.name} (ID: {cabana_familiar.id})")
        print(f"   - {depto_centrico.name} (ID: {depto_centrico.id})")
        print(f"   - {casa_completa.name} (ID: {casa_completa.id})")
        
        # Crear algunas reservas de prueba
        print("\n📋 Creando reservas de prueba...")
        
        today = datetime.now().date()
        
        # Reserva confirmada (pasada)
        check_in_past = today - timedelta(days=10)
        check_out_past = today - timedelta(days=7)
        nights_past = (check_out_past - check_in_past).days
        
        reserva_pasada = Reservation(
            code="RES" + datetime.now().strftime("%y%m%d") + "001",
            accommodation_id=cabana_familiar.id,
            guest_name="Juan Pérez",
            guest_phone="+5491123456789",
            guest_email="juan.perez@example.com",
            check_in=check_in_past,
            check_out=check_out_past,
            guests_count=4,
            nights=nights_past,
            base_price_per_night=15000.00,
            total_price=45000.00,
            deposit_percentage=30,
            deposit_amount=13500.00,
            payment_status=PaymentStatus.PAID.value,
            reservation_status=ReservationStatus.CONFIRMED.value,
            channel_source="whatsapp",
            special_requests="Familia con niños, solicitan cuna adicional"
        )
        
        # Reserva confirmada (futura)
        check_in_future = today + timedelta(days=5)
        check_out_future = today + timedelta(days=8)
        nights_future = (check_out_future - check_in_future).days
        
        reserva_futura = Reservation(
            code="RES" + datetime.now().strftime("%y%m%d") + "002",
            accommodation_id=depto_centrico.id,
            guest_name="María González",
            guest_phone="+5491198765432",
            guest_email="maria.gonzalez@example.com",
            check_in=check_in_future,
            check_out=check_out_future,
            guests_count=2,
            nights=nights_future,
            base_price_per_night=8500.00,
            total_price=25500.00,
            deposit_percentage=25,
            deposit_amount=6375.00,
            payment_status=PaymentStatus.PAID.value,
            reservation_status=ReservationStatus.CONFIRMED.value,
            channel_source="email",
            special_requests="Luna de miel, solicitan decoración especial"
        )
        
        # Pre-reserva (pendiente de pago)
        check_in_pre = today + timedelta(days=15)
        check_out_pre = today + timedelta(days=18)
        nights_pre = (check_out_pre - check_in_pre).days
        
        pre_reserva = Reservation(
            code="RES" + datetime.now().strftime("%y%m%d") + "003",
            accommodation_id=casa_completa.id,
            guest_name="Carlos Rodriguez",
            guest_phone="+5491134567890",
            guest_email="carlos.rodriguez@example.com",
            check_in=check_in_pre,
            check_out=check_out_pre,
            guests_count=6,
            nights=nights_pre,
            base_price_per_night=22000.00,
            total_price=66000.00,
            deposit_percentage=35,
            deposit_amount=23100.00,
            payment_status=PaymentStatus.PENDING.value,
            reservation_status=ReservationStatus.PRE_RESERVED.value,
            channel_source="whatsapp",
            expires_at=datetime.now() + timedelta(minutes=30),
            special_requests="Reunión familiar, requieren acceso temprano"
        )
        
        # Agregar reservas a la sesión
        session.add_all([reserva_pasada, reserva_futura, pre_reserva])
        await session.commit()
        
        print("✅ Reservas creadas:")
        print(f"   - {reserva_pasada.code} - {reserva_pasada.guest_name} (Confirmada - Pasada)")
        print(f"   - {reserva_futura.code} - {reserva_futura.guest_name} (Confirmada - Futura)")
        print(f"   - {pre_reserva.code} - {pre_reserva.guest_name} (Pre-reserva)")
        
        print("\n🎉 Datos de prueba creados exitosamente!")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_test_data())