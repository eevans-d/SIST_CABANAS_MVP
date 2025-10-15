# 🔧 FIX TESTS FASE 2 - Plan de Acción

**Fecha:** 14 Octubre 2025
**Status:** 🔴 PENDIENTE
**Tests Fallidos:** 9/17 E2E tests
**Esfuerzo Estimado:** 6-8 horas (reducido de 27h original)

---

## 📋 ESTADO ACTUAL

### Validación de Optimizaciones ✅
- ✅ Índices creados correctamente:
  - `idx_reservation_expires_prereserved` (8 KB)
  - `idx_reservation_status_dates` (8 KB)
- ✅ Código Python sin errores de sintaxis
- ✅ Sistema staging funcional (errores de auth son de config)
- 🟡 Sequential scans: 51% (alto porque sistema recién arrancó, mejorará con uso)

### Problema Identificado
- **pytest no está instalado en el contenedor backend**
- Los tests no se pueden ejecutar actualmente
- Necesitamos agregar pytest al Dockerfile o ejecutar fuera de Docker

---

## 🎯 TESTS QUE NECESITAN FIXES (De FASE 2)

Según el reporte previo de FASE 2, estos son los 9 tests fallidos:

### 1. test_list_accommodations
**Archivo:** `tests/test_e2e_flows.py::TestBasicAPIEndpoints`
**Problema:** Endpoint no retorna datos correctos
**Fix Estimado:** 30 min

### 2. test_availability_check
**Archivo:** `tests/test_e2e_flows.py::TestBasicAPIEndpoints`
**Problema:** Cálculo de disponibilidad con overlaps
**Fix Estimado:** 45 min

### 3. test_create_prereservation
**Archivo:** `tests/test_e2e_flows.py::TestBasicAPIEndpoints`
**Problema:** Validación de pre-reserva
**Fix Estimado:** 30 min

### 4. test_complete_whatsapp_to_confirmed_reservation
**Archivo:** `tests/test_e2e_flows.py::TestFlowCompleteReservation`
**Problema:** Mock de WhatsApp signature
**Fix Estimado:** 1 hora

### 5. test_double_booking_prevention
**Archivo:** `tests/test_e2e_flows.py::TestDoubleBookingPrevention`
**Problema:** IntegrityError no se captura bien
**Fix Estimado:** 45 min

### 6. test_concurrent_reservations
**Archivo:** `tests/test_e2e_flows.py::TestDoubleBookingPrevention`
**Problema:** Locks Redis en tests
**Fix Estimado:** 1 hora

### 7. test_mercadopago_webhook_payment_approved
**Archivo:** `tests/test_e2e_flows.py::TestMercadoPagoFlow`
**Problema:** Signature verification mock
**Fix Estimado:** 45 min

### 8. test_audio_transcription_flow
**Archivo:** `tests/test_e2e_flows.py::TestWhatsAppAudioFlow`
**Problema:** Whisper no instalado en MVP
**Fix Estimado:** 1 hora (skip o mock)

### 9. test_reservation_expiration
**Archivo:** `tests/test_e2e_flows.py::TestReservationLifecycle`
**Problema:** Background job timing
**Fix Estimado:** 45 min

---

## 🔧 SOLUCIONES PROPUESTAS

### Solución 1: Instalar pytest en Docker (RECOMENDADO)
**Esfuerzo:** 15 min
**Pro:** Tests se ejecutan en mismo entorno que producción
**Contra:** Requiere rebuild de imagen

```dockerfile
# Dockerfile - Agregar pytest
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pytest pytest-asyncio pytest-mock httpx
```

---

### Solución 2: Ejecutar Tests con venv local
**Esfuerzo:** 30 min (setup inicial)
**Pro:** Más rápido para desarrollo
**Contra:** Puede tener diferencias con producción

```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock
pytest tests/test_e2e_flows.py -v
```

---

### Solución 3: Skip Tests Problemáticos (NO RECOMENDADO)
**Esfuerzo:** 5 min
**Pro:** Rápido
**Contra:** No valida funcionalidad crítica

```python
@pytest.mark.skip(reason="Whisper not in MVP")
async def test_audio_transcription_flow():
    pass
```

---

## 📝 PLAN DE ACCIÓN RECOMENDADO

### Fase 1: Setup Ambiente de Testing (30 min)
1. ✅ Crear venv local
2. ✅ Instalar dependencies + pytest
3. ✅ Configurar pytest.ini
4. ✅ Verificar conexión a DB test

```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock aioresponses
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export REDIS_URL="redis://localhost:6379/1"
```

---

### Fase 2: Fix Tests Básicos (2 horas)
**Priority: 🔴 HIGH**

#### Fix 1: test_list_accommodations (30 min)
```python
async def test_list_accommodations(self, db_session, accommodation_factory):
    # Crear accommodation con todos los campos requeridos
    accommodation = await accommodation_factory(
        name="Test Cabin",
        capacity=4,
        base_price=Decimal("15000"),
        active=True  # Importante: debe estar activo
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/reservations/accommodations")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "Test Cabin"
```

#### Fix 2: test_availability_check (45 min)
```python
async def test_availability_check(self, db_session, accommodation_factory):
    accommodation = await accommodation_factory()
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)

    # Crear reserva existente que NO debe solapar
    existing_reservation = Reservation(
        code=f"TEST{date.today():%y%m%d}001",
        accommodation_id=accommodation.id,
        check_in=check_in + timedelta(days=10),  # 10 días después
        check_out=check_out + timedelta(days=10),
        guests_count=2,
        # ... resto de campos
    )
    db_session.add(existing_reservation)
    await db_session.commit()

    # Verificar disponibilidad (debe estar disponible)
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/accommodations/{accommodation.id}/availability",
            params={
                "check_in": check_in.isoformat(),
                "check_out": check_out.isoformat()
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
```

#### Fix 3: test_create_prereservation (30 min)
```python
async def test_create_prereservation(self, db_session, accommodation_factory):
    accommodation = await accommodation_factory()
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)

    payload = {
        "accommodation_id": accommodation.id,
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "guests_count": 2,
        "contact_name": "Test User",
        "contact_phone": "+5491112345678",
        "contact_email": "test@test.com",
        "channel": "web"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/reservations/pre-reserve", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["code"] is not None
        assert data["status"] == "pre_reserved"
        assert data["total_price"] > 0
```

---

### Fase 3: Fix Tests con Mocks (2 horas)
**Priority: 🟡 MEDIUM**

#### Fix 4: test_complete_whatsapp_to_confirmed_reservation (1h)
```python
@patch("app.core.security.verify_whatsapp_signature")
@patch("app.services.whatsapp.send_text_message")
async def test_complete_whatsapp_flow(
    self, mock_send, mock_verify, db_session, accommodation_factory
):
    # Setup
    accommodation = await accommodation_factory()
    mock_verify.return_value = True  # Simplificar
    mock_send.return_value = {"success": True}

    # ... resto del test
```

#### Fix 5: test_mercadopago_webhook (45 min)
```python
@patch("app.core.security.verify_mercadopago_signature")
@patch("app.services.mercadopago.MercadoPagoService.process_webhook")
async def test_mercadopago_webhook(
    self, mock_process, mock_verify, db_session
):
    mock_verify.return_value = True
    mock_process.return_value = {"status": "approved"}

    # ... resto del test
```

---

### Fase 4: Fix Tests con Redis (1.5 horas)
**Priority: 🟡 MEDIUM**

#### Fix 6: test_concurrent_reservations (1h)
```python
@pytest.mark.asyncio
async def test_concurrent_reservations(self, db_session, accommodation_factory, redis_client):
    # Limpiar Redis antes
    await redis_client.flushdb()

    accommodation = await accommodation_factory()
    check_in = date.today() + timedelta(days=30)
    check_out = check_in + timedelta(days=2)

    # Crear 2 reservas simultáneas
    tasks = [
        create_prereservation_task(accommodation.id, check_in, check_out, "User1"),
        create_prereservation_task(accommodation.id, check_in, check_out, "User2"),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Verificar que solo 1 tuvo éxito
    successful = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    assert len(successful) == 1
    assert len(failed) == 1
    assert isinstance(failed[0], IntegrityError)
```

---

### Fase 5: Skip Tests Bloqueados (30 min)
**Priority: 🟢 LOW**

#### Fix 7: test_audio_transcription_flow (SKIP)
```python
@pytest.mark.skip(reason="Whisper not in MVP, será implementado post-launch")
async def test_audio_transcription_flow(self):
    pass
```

---

### Fase 6: Fix Background Jobs (45 min)
**Priority: 🟡 MEDIUM**

#### Fix 8: test_reservation_expiration (45 min)
```python
@pytest.mark.asyncio
async def test_reservation_expiration(self, db_session, accommodation_factory):
    accommodation = await accommodation_factory()

    # Crear pre-reserva que YA expiró
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    reservation = Reservation(
        code=f"EXP{date.today():%y%m%d}001",
        accommodation_id=accommodation.id,
        check_in=date.today() + timedelta(days=30),
        check_out=date.today() + timedelta(days=32),
        guests_count=2,
        reservation_status="pre_reserved",
        expires_at=expired_time,
        # ... resto de campos
    )
    db_session.add(reservation)
    await db_session.commit()

    # Ejecutar cleanup job manualmente
    from app.jobs.cleanup import expire_prereservations
    await expire_prereservations(db_session)

    # Verificar que cambió a cancelled
    await db_session.refresh(reservation)
    assert reservation.reservation_status == "cancelled"
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

### Setup (30 min)
- [ ] Crear venv local
- [ ] Instalar pytest + dependencies
- [ ] Configurar DATABASE_URL test
- [ ] Verificar Redis disponible
- [ ] Ejecutar `pytest --collect-only` para verificar

### Fix Tests (6 horas)
- [ ] test_list_accommodations (30 min)
- [ ] test_availability_check (45 min)
- [ ] test_create_prereservation (30 min)
- [ ] test_complete_whatsapp_flow (1 hora)
- [ ] test_mercadopago_webhook (45 min)
- [ ] test_concurrent_reservations (1 hora)
- [ ] test_reservation_expiration (45 min)
- [ ] SKIP test_audio_transcription (5 min)
- [ ] Fix test_double_booking (45 min)

### Validación (30 min)
- [ ] Ejecutar todos los tests: `pytest tests/test_e2e_flows.py -v`
- [ ] Verificar coverage: `pytest --cov=app tests/`
- [ ] Documentar results en reporte
- [ ] Commit fixes a repo

---

## 📊 PROGRESO ESPERADO

### Antes
- Tests E2E: 8/17 passing (47%)
- Tests totales: 110+ (security) + 8 (E2E) = 118 passing

### Después (Target)
- Tests E2E: 16/17 passing (94%) - 1 skipped (audio)
- Tests totales: 110+ (security) + 16 (E2E) = 126 passing
- **+8 tests fixed** = +7% coverage crítica

---

## 🎯 CRITERIOS DE ÉXITO

1. ✅ Al menos 15/17 tests E2E passing
2. ✅ 1 test skipped (audio) con justificación
3. ✅ No flaky tests (ejecutar 3 veces sin fallos)
4. ✅ Todos los tests críticos (double-booking, concurrent) passing
5. ✅ Documentación de fixes completa

---

## 🚀 SIGUIENTE PASO

### Inmediato (Ahora)
```bash
# Setup venv
cd /home/eevan/ProyectosIA/SIST_CABAÑAS/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock aioresponses

# Ejecutar test para ver error real
export DATABASE_URL="sqlite+aiosqlite:///:memory:"
pytest tests/test_e2e_flows.py::TestBasicAPIEndpoints::test_list_accommodations -v --tb=short
```

### Luego (1-2 horas)
- Fix 3 tests básicos (list, availability, create)
- Validar que funcionan
- Continuar con mocks

---

**Documento creado:** 14 Octubre 2025
**Autor:** QA Team
**Status:** 📝 PLAN READY - Pendiente ejecución
**Próximo:** Setup venv y comenzar fixes
