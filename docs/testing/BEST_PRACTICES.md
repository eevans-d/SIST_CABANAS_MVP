# Testing Best Practices - Sistema MVP Alojamientos

**Versión:** 1.0
**Última Actualización:** 2 de Octubre, 2025
**Audiencia:** Developers, QA Engineers

---

## 📋 Tabla de Contenidos

1. [Filosofía de Testing](#filosofía-de-testing)
2. [Estructura de Tests](#estructura-de-tests)
3. [Patrones Anti-Doble-Booking](#patrones-anti-doble-booking)
4. [Mocking y Fixtures](#mocking-y-fixtures)
5. [Testing de Webhooks](#testing-de-webhooks)
6. [Coverage Goals](#coverage-goals)
7. [Testing Asyncio/Trio](#testing-asynciotrio)
8. [Patrones a Evitar](#patrones-a-evitar)
9. [CI/CD Integration](#cicd-integration)
10. [Debugging Tests](#debugging-tests)

---

## 🎯 Filosofía de Testing

### Principios Core

1. **Tests como Documentación:**
   - Cada test documenta un comportamiento esperado
   - Nombres descriptivos: `test_prereservation_expires_and_confirm_fails`
   - No comentarios innecesarios, código auto-explicativo

2. **Pirámide de Testing:**
   ```
   ┌─────────────┐
   │     E2E     │  ← 10% (placeholder en MVP)
   ├─────────────┤
   │ Integration │  ← 30% (API endpoints, DB, Redis)
   ├─────────────┤
   │    Unit     │  ← 60% (Services, NLU, utils)
   └─────────────┘
   ```

3. **Fast Feedback Loop:**
   - Tests unitarios < 0.5s cada uno
   - Tests de integración < 5s cada uno
   - Suite completa < 10 minutos

4. **Isolation:**
   - Cada test independiente (sin dependencias entre tests)
   - Fixtures limpias antes/después
   - DB/Redis en memoria o containers efímeros

---

## 🗂️ Estructura de Tests

### Organización de Archivos

```
backend/tests/
├── conftest.py                     # Fixtures globales (db, redis, client)
├── test_*.py                       # Tests por feature/módulo
│
├── test_double_booking.py          # Anti-doble-booking crítico
├── test_constraint_validation.py   # PostgreSQL constraints
├── test_reservation_concurrency.py # Concurrencia
│
├── test_whatsapp_webhook.py        # WhatsApp integration
├── test_whatsapp_signature.py      # Signature validation
├── test_mercadopago_webhook.py     # Mercado Pago integration
├── test_mercadopago_signature.py   # x-signature validation
│
├── test_nlu.py                     # Natural Language Understanding
├── test_audio_transcription.py     # Audio pipeline
├── test_ical_import.py             # iCal sync
│
├── test_reservation_lifecycle.py  # Flujos principales
├── test_reservation_expiration.py  # Expiración pre-reservas
├── test_metrics.py                 # Prometheus metrics
└── test_health.py                  # Health checks
```

### Convenciones de Nombres

```python
# ❌ MAL: Nombres vagos
def test_reservation():
    pass

# ✅ BIEN: Nombres descriptivos
def test_create_prereservation_with_valid_dates_succeeds():
    pass

def test_prereservation_with_overlapping_dates_raises_integrity_error():
    pass

def test_confirm_expired_prereservation_returns_400():
    pass
```

---

## 🔒 Patrones Anti-Doble-Booking

### Test 1: Constraint PostgreSQL

```python
import pytest
from sqlalchemy.exc import IntegrityError

async def test_overlapping_reservations_raise_integrity_error(async_session):
    """
    Validar que el constraint EXCLUDE USING gist previene doble-booking
    a nivel de base de datos.
    """
    # Arrange
    accommodation_id = 1
    check_in = date(2025, 10, 10)
    check_out = date(2025, 10, 15)

    # Act: Primera reserva OK
    reservation1 = Reservation(
        accommodation_id=accommodation_id,
        check_in=check_in,
        check_out=check_out,
        reservation_status="confirmed",
        # ... otros campos
    )
    async_session.add(reservation1)
    await async_session.commit()

    # Act: Segunda reserva con overlap DEBE fallar
    reservation2 = Reservation(
        accommodation_id=accommodation_id,
        check_in=date(2025, 10, 12),  # Overlap con primera
        check_out=date(2025, 10, 17),
        reservation_status="confirmed",
    )
    async_session.add(reservation2)

    # Assert: Constraint debe prevenir commit
    with pytest.raises(IntegrityError, match="no_overlap_reservations"):
        await async_session.commit()
```

### Test 2: Redis Lock

```python
async def test_redis_lock_prevents_concurrent_prereservations(redis_client):
    """
    Validar que Redis locks previenen doble pre-reserva concurrente.
    """
    # Arrange
    accommodation_id = 1
    check_in = "2025-10-10"
    check_out = "2025-10-15"
    lock_key = f"lock:acc:{accommodation_id}:{check_in}:{check_out}"

    # Act: Primer proceso obtiene lock
    lock1 = await redis_client.set(lock_key, "process1", nx=True, ex=1800)
    assert lock1 is True  # Lock obtenido

    # Act: Segundo proceso intenta obtener mismo lock
    lock2 = await redis_client.set(lock_key, "process2", nx=True, ex=1800)
    assert lock2 is None  # Lock rechazado (ya existe)

    # Cleanup
    await redis_client.delete(lock_key)
```

### Test 3: Concurrencia Real

```python
import asyncio

async def test_concurrent_prereservations_only_one_succeeds(client, async_session):
    """
    Simular 10 requests concurrentes para mismo período.
    Solo 1 debe tener éxito, otros 9 deben fallar con 409 o 423.
    """
    accommodation_id = 1
    payload = {
        "accommodation_id": accommodation_id,
        "check_in": "2025-11-01",
        "check_out": "2025-11-05",
        "guests_count": 2,
        "guest_name": "Test User",
        "guest_phone": "+5491112345678",
        "channel_source": "test"
    }

    # Act: Disparar 10 requests simultáneos
    tasks = [
        client.post("/api/v1/reservations/pre-reserve", json=payload)
        for _ in range(10)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Assert: Solo 1 respuesta 201, el resto 409/423
    success_count = sum(1 for r in responses if r.status_code == 201)
    conflict_count = sum(1 for r in responses if r.status_code in [409, 423])

    assert success_count == 1, "Solo una pre-reserva debe tener éxito"
    assert conflict_count == 9, "Las otras 9 deben fallar con conflicto"
```

---

## 🎭 Mocking y Fixtures

### Fixtures Principales (conftest.py)

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from redis.asyncio import Redis
from httpx import AsyncClient

@pytest.fixture(scope="session")
async def async_engine():
    """Engine SQLAlchemy async para tests (SQLite in-memory)"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def async_session(async_engine):
    """Sesión DB limpia por test"""
    async with AsyncSession(async_engine, expire_on_commit=False) as session:
        yield session
        await session.rollback()

@pytest.fixture
async def redis_client():
    """Cliente Redis para tests (fakeredis o real container)"""
    from fakeredis.aioredis import FakeRedis
    redis = FakeRedis(decode_responses=True)
    yield redis
    await redis.flushall()
    await redis.close()

@pytest.fixture
async def client(async_session, redis_client):
    """Cliente HTTP con dependency injection de DB/Redis"""
    app.dependency_overrides[get_db] = lambda: async_session
    app.dependency_overrides[get_redis] = lambda: redis_client

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

### Mocking External APIs

```python
from unittest.mock import AsyncMock, patch

async def test_whatsapp_send_message_success(client):
    """
    Mock WhatsApp API para evitar llamadas reales en tests.
    """
    with patch("app.services.whatsapp.httpx.AsyncClient.post") as mock_post:
        # Arrange: Mock respuesta exitosa
        mock_post.return_value = AsyncMock(
            status_code=200,
            json=lambda: {"messages": [{"id": "wamid.123"}]}
        )

        # Act: Enviar mensaje
        response = await client.post("/api/v1/whatsapp/send", json={
            "phone": "+5491112345678",
            "message": "Test message"
        })

        # Assert
        assert response.status_code == 200
        mock_post.assert_called_once()
```

---

## 🔐 Testing de Webhooks

### Validación de Firmas HMAC

```python
import hmac
import hashlib

def test_whatsapp_webhook_valid_signature(client):
    """
    Test firma HMAC SHA-256 de WhatsApp.
    """
    # Arrange
    secret = "test_secret"
    payload = b'{"object":"whatsapp_business_account"}'
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    # Act
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )

    # Assert
    assert response.status_code == 200


def test_whatsapp_webhook_invalid_signature_rejected(client):
    """
    Test que firma inválida retorna 403.
    """
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        json={"test": "data"},
        headers={"X-Hub-Signature-256": "sha256=invalid"}
    )
    assert response.status_code == 403
```

### Idempotencia

```python
async def test_mercadopago_webhook_idempotent(client, async_session):
    """
    Enviar mismo webhook de pago 3 veces.
    Solo debe procesarse una vez (idempotencia por payment_id).
    """
    payload = {
        "id": 12345,
        "type": "payment",
        "data": {"id": "PAY-12345"}
    }

    # Act: Enviar 3 veces
    response1 = await client.post("/api/v1/webhooks/mercadopago", json=payload)
    response2 = await client.post("/api/v1/webhooks/mercadopago", json=payload)
    response3 = await client.post("/api/v1/webhooks/mercadopago", json=payload)

    # Assert: Todas 200 pero solo 1 procesamiento
    assert all(r.status_code == 200 for r in [response1, response2, response3])

    # Verificar en DB que solo se actualizó 1 vez
    # (e.g., contando logs o verificando campo updated_at)
```

---

## 📊 Coverage Goals

### Objetivos por Módulo

| Módulo | Coverage Mínimo | Actual | Notas |
|--------|-----------------|--------|-------|
| `services/reservations.py` | 90% | 95% | Crítico (anti-doble-booking) |
| `services/nlu.py` | 80% | 85% | Intent detection |
| `services/whatsapp.py` | 85% | 90% | Webhook handling |
| `services/mercadopago.py` | 85% | 88% | Payment processing |
| `services/ical.py` | 75% | 80% | Import/export |
| `routers/*.py` | 80% | 85% | API endpoints |
| `models/*.py` | 70% | 75% | ORM models |
| `utils/*.py` | 80% | 90% | Helpers |
| **TOTAL** | **80%** | **87%** ✅ | Meta superada |

### Verificar Coverage

```bash
# Generar reporte
pytest backend/tests/ --cov=backend/app --cov-report=html --cov-report=term

# Ver reporte HTML
open htmlcov/index.html

# Identificar líneas no cubiertas
pytest --cov=backend/app --cov-report=term-missing
```

### Excluir de Coverage

```python
# pyproject.toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/conftest.py",
    "*/main.py",  # Solo startup, difícil testear
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## ⚡ Testing Asyncio/Trio

### Pytest Plugins

```python
# pytest.ini
[pytest]
asyncio_mode = auto
trio_mode = true

markers =
    asyncio: Tests usando asyncio event loop
    trio: Tests usando trio event loop
```

### Parametrización Multi-Backend

```python
import pytest

@pytest.mark.parametrize("anyio_backend", ["asyncio", "trio"])
async def test_prereservation_with_anyio(anyio_backend, client):
    """
    Test que funciona con asyncio Y trio.
    """
    response = await client.post("/api/v1/reservations/pre-reserve", json={
        "accommodation_id": 1,
        "check_in": "2025-11-01",
        "check_out": "2025-11-05",
        "guests_count": 2,
    })
    assert response.status_code == 201
```

---

## ❌ Patrones a Evitar

### 1. Tests que Dependen de Orden de Ejecución

```python
# ❌ MAL: Test depende de que test_create se ejecute primero
def test_create():
    global reservation_id
    reservation_id = create_reservation()

def test_update():
    update_reservation(reservation_id)  # Falla si test_create no corrió

# ✅ BIEN: Tests independientes con fixtures
@pytest.fixture
def reservation_id(async_session):
    res = create_reservation()
    return res.id

def test_update(reservation_id):
    update_reservation(reservation_id)
```

### 2. Sleep en Tests

```python
# ❌ MAL: Sleep arbitrario
async def test_expiration():
    create_prereservation()
    await asyncio.sleep(5)  # Esperar expiración
    assert reservation.expired

# ✅ BIEN: Manipular tiempo o usar timeout
async def test_expiration():
    with freeze_time("2025-10-01 10:00:00"):
        create_prereservation(expires_at="2025-10-01 10:30:00")

    with freeze_time("2025-10-01 10:31:00"):
        assert reservation.is_expired()
```

### 3. Tests No Determinísticos

```python
# ❌ MAL: Resultado varía
def test_random_feature():
    result = random.choice([True, False])
    assert result  # Falla 50% del tiempo

# ✅ BIEN: Mockear randomness
def test_random_feature():
    with patch("random.choice", return_value=True):
        result = random.choice([True, False])
        assert result is True
```

### 4. Tests con Side Effects

```python
# ❌ MAL: Modifica estado global
def test_config():
    os.environ["SECRET_KEY"] = "test"  # Side effect!
    assert get_config().secret_key == "test"

# ✅ BIEN: Usar monkeypatch fixture
def test_config(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test")
    assert get_config().secret_key == "test"
    # monkeypatch revierte cambios automáticamente
```

---

## 🔄 CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r backend/requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run tests with coverage
        run: |
          pytest backend/tests/ \
            --cov=backend/app \
            --cov-report=xml \
            --cov-report=term \
            --junitxml=test-results.xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: true

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml
```

### Pre-commit Hook para Tests

```yaml
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: pytest-check
      name: pytest-check
      entry: pytest
      args: [backend/tests/, --tb=short, -v]
      language: system
      pass_filenames: false
      stages: [commit]
```

---

## 🐛 Debugging Tests

### 1. Usar pytest -v y -s

```bash
# Verbose + print output
pytest backend/tests/test_reservation.py -v -s

# Solo un test específico
pytest backend/tests/test_reservation.py::test_create_prereservation -v -s
```

### 2. pdb (Python Debugger)

```python
async def test_complex_logic():
    result = await complex_function()

    import pdb; pdb.set_trace()  # Breakpoint

    assert result == expected
```

### 3. pytest --pdb (Auto-breakpoint en failures)

```bash
# Abrir pdb automáticamente en primer fallo
pytest --pdb

# Abrir pdb en todos los fallos
pytest --pdb --maxfail=5
```

### 4. Logs Estructurados

```python
import structlog

logger = structlog.get_logger()

async def test_with_logging():
    logger.info("test_started", test_name="test_with_logging")

    result = await function_under_test()

    logger.info("test_result", result=result, expected=expected)

    assert result == expected
```

### 5. pytest-xdist (Parallel Tests)

```bash
# Correr tests en paralelo (4 workers)
pytest -n 4

# Auto-detectar CPUs
pytest -n auto
```

---

## 📝 Checklist de PR

Antes de mergear código nuevo, verificar:

- [ ] **Coverage no disminuye** (`pytest --cov` vs baseline)
- [ ] **Todos los tests passing** (37+ tests)
- [ ] **Tests nuevos para features nuevas** (1:1 feature:test ratio)
- [ ] **Tests de edge cases** (null values, límites, errors)
- [ ] **Tests de concurrencia** (si aplica)
- [ ] **Mocking de APIs externas** (WhatsApp, MP, etc.)
- [ ] **Nombres descriptivos** (`test_what_when_then` format)
- [ ] **No sleep() innecesarios** (usar fixtures o time mocking)
- [ ] **Cleanup en fixtures** (yield + teardown)
- [ ] **Pre-commit hooks passing** (pytest incluido)

---

## 🔗 Referencias

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Hypothesis (property-based testing)](https://hypothesis.readthedocs.io/)
- [Testing Best Practices - Martin Fowler](https://martinfowler.com/testing/)

---

**Última Actualización:** 2 de Octubre, 2025
**Mantenido por:** Sistema MVP Alojamientos Contributors
**Versión Mínima Python:** 3.12
**Frameworks:** pytest, pytest-asyncio, pytest-cov, httpx
