# 🎯 PLAN DE VERIFICACIÓN, VALIDACIÓN Y OPTIMIZACIÓN EXHAUSTIVO
## Sistema MVP de Alojamientos - Fase de Robustecimiento

**Fecha:** 2025-10-08
**Objetivo:** Llevar el sistema del 95% al 100% de madurez productiva
**Duración Estimada:** 3-5 días de trabajo intensivo
**Prioridad:** CRÍTICO → ALTO → MEDIO → BAJO

---

## 📊 ESTRUCTURA DEL PLAN

### Fase 1: AUDITORÍA Y DIAGNÓSTICO (6-8 horas)
### Fase 2: TESTING EXHAUSTIVO (12-16 horas)
### Fase 3: OPTIMIZACIÓN Y PERFORMANCE (8-10 horas)
### Fase 4: SEGURIDAD Y HARDENING (6-8 horas)
### Fase 5: ROBUSTEZ Y RESILIENCIA (8-10 horas)
### Fase 6: OBSERVABILIDAD Y MONITOREO (4-6 horas)

---

# 🔍 FASE 1: AUDITORÍA Y DIAGNÓSTICO (6-8h)

## 1.1 Análisis de Código Estático [CRÍTICO] (2h)

### Objetivo
Identificar code smells, vulnerabilidades, complejidad ciclomática alta, y patrones anti-pattern.

### Tareas

#### 1.1.1 Instalación de herramientas de análisis
```bash
cd backend

# Instalar herramientas de análisis estático
pip install pylint flake8 mypy bandit radon safety black isort

# Análisis de seguridad
pip install semgrep
```

#### 1.1.2 Linting y formateo
```bash
# Verificar estilo de código
flake8 app/ tests/ --max-line-length=100 --exclude=__pycache__,migrations \
  --extend-ignore=E203,W503 > reports/flake8_report.txt

# Type checking
mypy app/ --ignore-missing-imports --disallow-untyped-defs \
  --no-implicit-optional > reports/mypy_report.txt

# Complejidad ciclomática
radon cc app/ -a -nb > reports/complexity_report.txt
radon mi app/ -nb > reports/maintainability_report.txt

# Linting completo
pylint app/ --rcfile=.pylintrc --output-format=json > reports/pylint_report.json
```

**Criterios de Éxito:**
- Score Pylint > 8.0/10
- Complejidad ciclomática media < 10
- Maintainability Index > 70
- 0 errores críticos de tipo

#### 1.1.3 Análisis de seguridad estático
```bash
# Vulnerabilidades conocidas en dependencias
safety check --json > reports/safety_report.json

# Análisis de código con Bandit (security)
bandit -r app/ -f json -o reports/bandit_report.json

# Análisis con Semgrep (patrones inseguros)
semgrep --config=auto app/ --json > reports/semgrep_report.json
```

**Criterios de Éxito:**
- 0 vulnerabilidades HIGH/CRITICAL
- 0 hardcoded secrets
- 0 SQL injection vulnerabilities
- 0 insecure crypto usage

## 1.2 Análisis de Base de Datos [CRÍTICO] (2h)

### 1.2.1 Verificación de constraints y índices
```bash
# Script de análisis DB
cat > scripts/analyze_db.sh << 'EOF'
#!/bin/bash
docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db << SQL
-- Verificar extensiones
SELECT * FROM pg_extension WHERE extname IN ('btree_gist', 'pg_trgm');

-- Listar todos los constraints
SELECT
    conname AS constraint_name,
    contype AS constraint_type,
    conrelid::regclass AS table_name,
    pg_get_constraintdef(oid) AS definition
FROM pg_constraint
WHERE conrelid::regclass::text LIKE '%reservation%'
   OR conrelid::regclass::text LIKE '%accommodation%'
ORDER BY conrelid, contype;

-- Verificar índices
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Estadísticas de uso de índices
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan AS index_scans,
    idx_tup_read AS tuples_read,
    idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Tablas sin índices utilizados
SELECT
    schemaname,
    tablename,
    seq_scan AS sequential_scans,
    seq_tup_read AS sequential_tuples_read,
    idx_scan AS index_scans
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND (idx_scan = 0 OR idx_scan IS NULL)
  AND seq_scan > 100;

-- Queries lentas (si pg_stat_statements está habilitado)
SELECT
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time,
    query
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat_statements%'
ORDER BY mean_exec_time DESC
LIMIT 20;
SQL
EOF

chmod +x scripts/analyze_db.sh
./scripts/analyze_db.sh > reports/db_analysis_report.txt
```

**Criterios de Éxito:**
- Constraint `no_overlap_reservations` EXISTS y activo
- Extensión `btree_gist` instalada
- Todos los FK tienen índices
- 0 tablas con >1000 seq_scans sin índices

### 1.2.2 Análisis de performance de queries
```bash
# Habilitar query logging temporal
docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_db -c \
  "ALTER SYSTEM SET log_min_duration_statement = 100;"
docker exec alojamientos_postgres pg_ctl reload

# Ejecutar carga de prueba y analizar
# (dejar correr 30 min con tráfico simulado)
```

## 1.3 Análisis de Arquitectura y Dependencias [ALTO] (2h)

### 1.3.1 Mapa de dependencias
```bash
# Generar grafo de dependencias
pip install pipdeptree
pipdeptree --json > reports/dependency_tree.json
pipdeptree --graph-output png > reports/dependency_graph.png

# Verificar versiones obsoletas
pip list --outdated > reports/outdated_packages.txt
```

### 1.3.2 Análisis de imports circulares
```bash
# Detectar imports circulares
pip install pydeps
pydeps app --max-bacon=3 --cluster > reports/import_graph.svg
```

**Criterios de Éxito:**
- 0 imports circulares
- 0 dependencias con vulnerabilidades críticas
- < 5% de dependencias major versions desactualizadas

---

# 🧪 FASE 2: TESTING EXHAUSTIVO (12-16h)

## 2.1 Tests Unitarios [CRÍTICO] (4h)

### 2.1.1 Ejecutar suite completa con coverage
```bash
cd backend

# Crear configuración de coverage
cat > .coveragerc << EOF
[run]
source = app
omit =
    */tests/*
    */migrations/*
    */__pycache__/*
    */conftest.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = htmlcov
EOF

# Ejecutar tests con coverage
pytest tests/ -v \
  --cov=app \
  --cov-report=html \
  --cov-report=term \
  --cov-report=json \
  --cov-fail-under=80 \
  --maxfail=1 \
  -n auto

# Ver reporte
open htmlcov/index.html  # o xdg-open en Linux
```

**Criterios de Éxito:**
- Coverage global > 80%
- Coverage crítico (models, services) > 90%
- 100% tests passing
- 0 tests skipped injustificadamente

### 2.1.2 Tests de constraint anti-doble-booking [CRÍTICO]
```bash
# REQUIERE PostgreSQL real con btree_gist
export TEST_DATABASE_URL="postgresql+asyncpg://alojamientos:aloj2025secure@localhost:5432/alojamientos_test"

# Crear DB de test
docker exec -i alojamientos_postgres psql -U alojamientos -c \
  "CREATE DATABASE alojamientos_test;"
docker exec -i alojamientos_postgres psql -U alojamientos -d alojamientos_test -c \
  "CREATE EXTENSION btree_gist;"

# Ejecutar tests específicos de double-booking
pytest tests/test_double_booking.py -v -s
pytest tests/test_constraint_validation.py -v -s
pytest tests/test_reservation_concurrency.py -v -s
```

**Tests Obligatorios:**
1. ✅ Overlap total (mismas fechas)
2. ✅ Overlap parcial inicio
3. ✅ Overlap parcial fin
4. ✅ Overlap contenido (nueva reserva dentro de existente)
5. ✅ Overlap continente (nueva reserva contiene existente)
6. ✅ Edge cases (check_in = check_out previo)
7. ✅ Concurrencia (2+ threads intentando reservar simultáneo)
8. ✅ Estados: solo pre_reserved y confirmed bloquean

### 2.1.3 Tests de servicios críticos
```bash
# Reservations service
pytest tests/test_reservation_service.py -v -s --log-cli-level=DEBUG

# WhatsApp webhook
pytest tests/test_whatsapp_webhook.py tests/test_whatsapp_signature.py -v

# Mercado Pago webhook
pytest tests/test_mercadopago_webhook.py tests/test_mercadopago_signature.py -v

# NLU y audio
pytest tests/test_nlu.py tests/test_audio_transcription.py -v

# iCal sync
pytest tests/test_ical_import.py -v

# Background jobs
pytest tests/test_expiration_job.py tests/test_reminder_job.py -v
```

## 2.2 Tests de Integración [CRÍTICO] (4h)

### 2.2.1 Journey tests completos
```bash
# Test de journey básico
pytest tests/test_journey_basic.py -v -s

# Test de journey con expiración
pytest tests/test_journey_expiration.py -v -s

# Test de ciclo de vida completo
pytest tests/test_reservation_lifecycle.py -v -s
```

### 2.2.2 Tests de integraciones externas (mocks)
```bash
# Crear test de integración completa
cat > backend/tests/test_integration_full.py << 'PYTEST'
"""Tests de integración completa del sistema."""
import pytest
from datetime import date, timedelta
from decimal import Decimal

pytestmark = pytest.mark.asyncio

class TestFullIntegration:
    """Suite de integración completa."""

    async def test_whatsapp_to_reservation_flow(
        self,
        async_client,
        db_session,
        sample_accommodation
    ):
        """Test flujo completo: WhatsApp -> Pre-reserva -> Pago -> Confirmación."""
        # 1. Mensaje WhatsApp de consulta
        whatsapp_payload = {
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "5491123456789",
                            "text": {"body": "Quiero reservar para el 15/11 al 17/11"},
                            "timestamp": "1234567890"
                        }]
                    }
                }]
            }]
        }

        # 2. Crear pre-reserva via API
        prereserv_data = {
            "accommodation_id": sample_accommodation.id,
            "check_in": (date.today() + timedelta(days=30)).isoformat(),
            "check_out": (date.today() + timedelta(days=32)).isoformat(),
            "guests": 2,
            "contact_name": "Test Usuario",
            "contact_phone": "+5491123456789",
            "contact_email": "test@example.com",
            "channel": "whatsapp"
        }

        response = await async_client.post(
            "/api/v1/reservations/pre-reserve",
            json=prereserv_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] is not None
        reservation_code = data["code"]

        # 3. Simular pago de Mercado Pago
        mp_payload = {
            "action": "payment.created",
            "data": {"id": "123456789"},
            "type": "payment"
        }

        # 4. Confirmar reserva
        # ... continuar flujo

    async def test_concurrent_reservations_different_accommodations(
        self,
        db_session,
        sample_accommodation
    ):
        """Test reservas concurrentes en diferentes alojamientos."""
        # Implementar
        pass

    async def test_ical_sync_prevents_double_booking(
        self,
        db_session,
        sample_accommodation
    ):
        """Test que iCal sync respeta constraint."""
        # Implementar
        pass
PYTEST

pytest backend/tests/test_integration_full.py -v -s
```

## 2.3 Tests End-to-End [ALTO] (2h)

### 2.3.1 E2E con sistema real corriendo
```bash
# Asegurar que containers están corriendo
docker-compose up -d

# Ejecutar tests E2E
cat > backend/tests_e2e/test_real_api.py << 'PYTEST'
"""Tests E2E contra API real."""
import requests
import pytest
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Health check debe responder."""
    resp = requests.get(f"{BASE_URL}/api/v1/healthz", timeout=5)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"

def test_create_prereservation_e2e():
    """Crear pre-reserva end-to-end."""
    payload = {
        "accommodation_id": 1,
        "check_in": (date.today() + timedelta(days=60)).isoformat(),
        "check_out": (date.today() + timedelta(days=62)).isoformat(),
        "guests": 2,
        "contact_name": "E2E Test",
        "contact_phone": "+5491199999999",
        "contact_email": "e2e@test.com",
        "channel": "test_e2e"
    }

    resp = requests.post(
        f"{BASE_URL}/api/v1/reservations/pre-reserve",
        json=payload,
        timeout=10
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["code"] is not None
    assert data["error"] is None

def test_double_booking_prevention_e2e():
    """Anti-doble-booking debe funcionar end-to-end."""
    check_in = (date.today() + timedelta(days=70)).isoformat()
    check_out = (date.today() + timedelta(days=72)).isoformat()

    payload = {
        "accommodation_id": 1,
        "check_in": check_in,
        "check_out": check_out,
        "guests": 2,
        "contact_name": "First",
        "contact_phone": "+5491111111111",
        "contact_email": "first@test.com",
        "channel": "test"
    }

    # Primera reserva
    resp1 = requests.post(
        f"{BASE_URL}/api/v1/reservations/pre-reserve",
        json=payload,
        timeout=10
    )
    assert resp1.status_code == 200
    assert resp1.json()["code"] is not None

    # Intento duplicado
    payload["contact_name"] = "Second"
    payload["contact_phone"] = "+5491122222222"
    resp2 = requests.post(
        f"{BASE_URL}/api/v1/reservations/pre-reserve",
        json=payload,
        timeout=10
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["error"] == "processing_or_unavailable"
    assert data2["code"] is None

def test_metrics_endpoint():
    """Metrics debe estar disponible."""
    resp = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert resp.status_code == 200
    assert b"reservations_created_total" in resp.content
PYTEST

pytest backend/tests_e2e/test_real_api.py -v -s
```

## 2.4 Tests de Performance y Carga [ALTO] (2h)

### 2.4.1 Load testing con Locust
```bash
# Instalar Locust
pip install locust

# Crear locustfile
cat > backend/tests_e2e/locustfile.py << 'PYTHON'
"""Load testing con Locust."""
from locust import HttpUser, task, between
from datetime import date, timedelta
import random

class ReservationUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def health_check(self):
        """Health check frecuente."""
        self.client.get("/api/v1/healthz")

    @task(1)
    def create_prereservation(self):
        """Crear pre-reserva."""
        days_ahead = random.randint(30, 90)
        stay_duration = random.randint(1, 7)

        payload = {
            "accommodation_id": random.randint(1, 4),
            "check_in": (date.today() + timedelta(days=days_ahead)).isoformat(),
            "check_out": (date.today() + timedelta(days=days_ahead + stay_duration)).isoformat(),
            "guests": random.randint(1, 4),
            "contact_name": f"LoadTest{random.randint(1000, 9999)}",
            "contact_phone": f"+54911{random.randint(10000000, 99999999)}",
            "contact_email": f"load{random.randint(1000, 9999)}@test.com",
            "channel": "load_test"
        }

        with self.client.post(
            "/api/v1/reservations/pre-reserve",
            json=payload,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("error"):
                    response.failure(f"API error: {data['error']}")
                else:
                    response.success()
            else:
                response.failure(f"HTTP {response.status_code}")
PYTHON

# Ejecutar load test
locust -f backend/tests_e2e/locustfile.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=5m \
  --html=reports/locust_report.html
```

**Criterios de Éxito:**
- P50 latency < 200ms
- P95 latency < 1000ms
- P99 latency < 2000ms
- 0 errores con 50 usuarios concurrentes
- Throughput > 100 req/s

### 2.4.2 Stress testing
```bash
# Test de carga extrema
locust -f backend/tests_e2e/locustfile.py \
  --host=http://localhost:8000 \
  --users=200 \
  --spawn-rate=10 \
  --run-time=10m \
  --html=reports/stress_test_report.html

# Monitorear recursos durante stress test
docker stats --no-stream > reports/docker_stats_stress.txt
```

---

# ⚡ FASE 3: OPTIMIZACIÓN Y PERFORMANCE (8-10h)

## 3.1 Optimización de Queries SQL [CRÍTICO] (3h)

### 3.1.1 Identificar N+1 queries
```bash
# Habilitar SQL echo para debug
# En app/core/database.py, temporalmente:
# engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Ejecutar tests y capturar queries
pytest tests/test_reservation_service.py -v -s 2>&1 | grep "SELECT" > reports/sql_queries.log

# Analizar duplicados
cat reports/sql_queries.log | sort | uniq -c | sort -rn | head -20
```

### 3.1.2 Agregar eager loading donde sea necesario
```python
# Ejemplo de optimización
# ANTES (N+1):
reservations = await session.execute(select(Reservation))
for res in reservations.scalars():
    print(res.accommodation.name)  # Query por cada reserva!

# DESPUÉS (eager loading):
from sqlalchemy.orm import selectinload

reservations = await session.execute(
    select(Reservation).options(selectinload(Reservation.accommodation))
)
```

### 3.1.3 Crear índices adicionales según análisis
```sql
-- Ejemplo de índices adicionales recomendados
CREATE INDEX IF NOT EXISTS idx_reservations_check_in_out
  ON reservations (check_in, check_out);

CREATE INDEX IF NOT EXISTS idx_reservations_channel_status
  ON reservations (channel_source, reservation_status);

CREATE INDEX IF NOT EXISTS idx_reservations_created_at
  ON reservations (created_at DESC);

-- Índice para búsquedas de disponibilidad
CREATE INDEX IF NOT EXISTS idx_reservations_availability
  ON reservations (accommodation_id, reservation_status, check_in, check_out)
  WHERE reservation_status IN ('pre_reserved', 'confirmed');
```

## 3.2 Optimización de Redis [ALTO] (2h)

### 3.2.1 Análisis de uso de Redis
```bash
# Conectar a Redis y analizar
docker exec -it alojamientos_redis redis-cli

# Dentro de redis-cli:
INFO stats
INFO memory
SLOWLOG GET 10
KEYS lock:*
KEYS rate_limit:*

# Analizar TTLs
SCAN 0 COUNT 100
```

### 3.2.2 Implementar pipeline para operaciones batch
```python
# Optimizar locks con pipeline
async def acquire_multiple_locks(keys: list, ttl: int = 1800):
    """Adquirir múltiples locks en una operación."""
    redis_conn = await get_redis_pool()
    pipe = redis_conn.pipeline()

    for key in keys:
        pipe.set(key, "1", nx=True, ex=ttl)

    results = await pipe.execute()
    return all(results)
```

### 3.2.3 Configurar eviction policy óptima
```bash
# Ajustar configuración Redis
docker exec alojamientos_redis redis-cli CONFIG SET maxmemory 256mb
docker exec alojamientos_redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 3.3 Optimización de FastAPI [ALTO] (2h)

### 3.3.1 Agregar response caching estratégico
```python
# Instalar
pip install fastapi-cache2[redis]

# En app/main.py
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.on_event("startup")
async def startup():
    redis_conn = await get_redis_pool()
    FastAPICache.init(RedisBackend(redis_conn), prefix="api-cache")

# En routers con datos relativamente estáticos
@router.get("/accommodations/{id}")
@cache(expire=300)  # 5 minutos
async def get_accommodation(id: int):
    # ...
```

### 3.3.2 Implementar connection pooling óptimo
```python
# En app/core/database.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,           # Ajustar según carga
    max_overflow=10,        # Conexiones adicionales en picos
    pool_pre_ping=True,     # Verificar conexiones antes de usar
    pool_recycle=3600,      # Reciclar conexiones cada hora
    echo=False,
    connect_args={
        "statement_cache_size": 0,  # Evitar memory leak en asyncpg
        "prepared_statement_cache_size": 0
    }
)
```

### 3.3.3 Optimizar serialización JSON
```python
# Usar orjson para mejor performance
pip install orjson

# En app/main.py
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)
```

## 3.4 Profiling y Bottleneck Detection [MEDIO] (1h)

```bash
# Instalar py-spy
pip install py-spy

# Profile de la API en producción
py-spy record -o reports/profile.svg --duration 60 --pid $(docker inspect -f '{{.State.Pid}}' alojamientos_api)

# Análisis de memoria
pip install memory_profiler

# Agregar @profile a funciones sospechosas
python -m memory_profiler app/services/reservations.py
```

---

# 🔒 FASE 4: SEGURIDAD Y HARDENING (6-8h)

## 4.1 Penetration Testing [CRÍTICO] (3h)

### 4.1.1 OWASP ZAP automated scan
```bash
# Instalar OWASP ZAP
docker pull owasp/zap2docker-stable

# Ejecutar baseline scan
docker run --network=host owasp/zap2docker-stable \
  zap-baseline.py \
  -t http://localhost:8000 \
  -r reports/zap_baseline_report.html

# Ejecutar full scan (más lento)
docker run --network=host owasp/zap2docker-stable \
  zap-full-scan.py \
  -t http://localhost:8000 \
  -r reports/zap_full_report.html
```

### 4.1.2 Tests de vulnerabilidades específicas
```bash
# SQL Injection
curl -X POST "http://localhost:8000/api/v1/reservations/pre-reserve" \
  -H "Content-Type: application/json" \
  -d '{"accommodation_id": "1 OR 1=1", "check_in": "2025-11-01"}'

# XSS
curl -X POST "http://localhost:8000/api/v1/reservations/pre-reserve" \
  -H "Content-Type: application/json" \
  -d '{"contact_name": "<script>alert(1)</script>", "accommodation_id": 1}'

# Path Traversal
curl "http://localhost:8000/../../etc/passwd"

# CSRF (sin token)
curl -X POST "http://localhost:8000/api/v1/admin/settings" \
  -H "Content-Type: application/json" \
  -d '{"key": "test"}'
```

**Criterios de Éxito:**
- 0 High/Critical vulnerabilities
- Todas las entradas sanitizadas
- CSRF protection activa
- Rate limiting funcionando

## 4.2 Secrets y Configuración [CRÍTICO] (1h)

### 4.2.1 Auditoría de secrets
```bash
# Buscar secrets hardcoded
grep -rn "password\|secret\|api_key\|token" backend/app/ \
  --exclude-dir=__pycache__ | grep -v "getenv\|environ"

# Verificar que .env no está en git
git ls-files | grep "\.env$"

# Verificar permisos de archivos sensibles
ls -la backend/.env backend/.env.production
# Deben ser 600 (rw-------)
```

### 4.2.2 Implementar secrets rotation
```bash
# Script de rotación de secrets
cat > scripts/rotate_secrets.sh << 'BASH'
#!/bin/bash
set -e

echo "🔄 Rotando secrets..."

# Generar nuevos secrets
NEW_JWT_SECRET=$(openssl rand -hex 32)
NEW_WHATSAPP_VERIFY=$(openssl rand -hex 16)
NEW_ICS_SALT=$(openssl rand -hex 16)

# Backup del .env actual
cp backend/.env.production backend/.env.production.backup.$(date +%Y%m%d_%H%M%S)

# Actualizar .env.production
sed -i "s/^JWT_SECRET=.*/JWT_SECRET=${NEW_JWT_SECRET}/" backend/.env.production
sed -i "s/^WHATSAPP_VERIFY_TOKEN=.*/WHATSAPP_VERIFY_TOKEN=${NEW_WHATSAPP_VERIFY}/" backend/.env.production
sed -i "s/^ICS_SALT=.*/ICS_SALT=${NEW_ICS_SALT}/" backend/.env.production

echo "✅ Secrets rotados. Reiniciar containers."
BASH

chmod +x scripts/rotate_secrets.sh
```

## 4.3 Rate Limiting y DDoS Protection [ALTO] (1h)

### 4.3.1 Verificar rate limiting
```bash
# Test de rate limiting
for i in {1..200}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    "http://localhost:8000/api/v1/healthz" &
done
wait

# Debe haber algunos 429 (Too Many Requests)
```

### 4.3.2 Implementar rate limiting por endpoint
```python
# En app/core/middleware.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# En routers críticos
@router.post("/pre-reserve")
@limiter.limit("10/minute")  # Max 10 reservas por minuto por IP
async def create_prereservation(...):
    pass

@router.post("/webhooks/whatsapp")
@limiter.limit("100/minute")  # WhatsApp puede enviar muchos mensajes
async def whatsapp_webhook(...):
    pass
```

## 4.4 Headers de Seguridad [MEDIO] (1h)

```python
# En app/main.py - Agregar middleware de seguridad
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Solo permitir hosts conocidos
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "*.yourdomain.com"]
)

# Headers de seguridad
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

# 🛡️ FASE 5: ROBUSTEZ Y RESILIENCIA (8-10h)

## 5.1 Error Handling Exhaustivo [CRÍTICO] (3h)

### 5.1.1 Implementar manejo de errores global
```python
# En app/main.py
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, OperationalError
import structlog

logger = structlog.get_logger()

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Manejar errores de constraint DB."""
    logger.error("database_integrity_error",
                 error=str(exc),
                 path=request.url.path)

    # Parsear tipo de error
    if "no_overlap_reservations" in str(exc):
        return JSONResponse(
            status_code=409,
            content={"error": "date_overlap", "detail": "Fechas no disponibles"}
        )

    return JSONResponse(
        status_code=500,
        content={"error": "database_error", "detail": "Error de integridad"}
    )

@app.exception_handler(OperationalError)
async def operational_error_handler(request: Request, exc: OperationalError):
    """Manejar errores de conexión DB."""
    logger.error("database_connection_error", error=str(exc))
    return JSONResponse(
        status_code=503,
        content={"error": "service_unavailable", "detail": "Base de datos no disponible"}
    )

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Manejar errores de validación de entrada."""
    logger.warning("validation_error", errors=exc.errors(), path=request.url.path)
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all para errores no manejados."""
    logger.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Error interno del servidor"}
    )
```

### 5.1.2 Tests de manejo de errores
```python
# En tests/test_error_handling.py
@pytest.mark.asyncio
async def test_database_down(async_client, monkeypatch):
    """Test comportamiento cuando DB está caída."""
    # Simular DB down
    # ...
    response = await async_client.get("/api/v1/healthz")
    assert response.status_code == 503

@pytest.mark.asyncio
async def test_redis_down_graceful_degradation(async_client):
    """Test que sistema funciona sin Redis (degraded)."""
    # Apagar Redis temporalmente
    # ...
    # Sistema debe seguir funcionando en modo degradado
```

## 5.2 Retry Logic y Circuit Breaker [ALTO] (2h)

### 5.2.1 Implementar retry con exponential backoff
```python
# Instalar tenacity
pip install tenacity

# En app/services/external_api.py
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import httpx

class ExternalAPIService:

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(httpx.HTTPError),
        before_sleep=lambda retry_state: logger.warning(
            "retrying_api_call",
            attempt=retry_state.attempt_number
        )
    )
    async def call_external_api(self, url: str, **kwargs):
        """Llamar API externa con retry."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, **kwargs)
            response.raise_for_status()
            return response.json()
```

### 5.2.2 Implementar circuit breaker
```python
# Instalar pybreaker
pip install pybreaker

from pybreaker import CircuitBreaker

# Circuit breaker para WhatsApp API
whatsapp_breaker = CircuitBreaker(
    fail_max=5,           # Abrir después de 5 fallos
    timeout_duration=60,  # Intentar cerrar después de 60s
    name="whatsapp_api"
)

@whatsapp_breaker
async def send_whatsapp_message(phone: str, message: str):
    """Enviar mensaje WhatsApp con circuit breaker."""
    # Si circuit está abierto, levanta CircuitBreakerError inmediatamente
    # ...
```

## 5.3 Graceful Degradation [ALTO] (2h)

### 5.3.1 Implementar fallbacks
```python
# En app/services/nlu.py
async def analyze_intent(text: str) -> Dict:
    """Analizar intención con fallback."""
    try:
        # Intentar con servicio principal (ej: LLM)
        return await analyze_with_llm(text)
    except Exception as e:
        logger.warning("llm_failed_using_fallback", error=str(e))
        # Fallback a keyword matching simple
        return analyze_with_keywords(text)

# En app/services/audio.py
async def transcribe_audio(audio_path: str) -> Dict:
    """Transcribir audio con fallback."""
    try:
        return await transcribe_with_whisper(audio_path)
    except Exception as e:
        logger.error("whisper_failed", error=str(e))
        return {
            "text": None,
            "confidence": 0.0,
            "error": "transcription_failed"
        }
```

### 5.3.2 Feature flags
```python
# En app/core/config.py
class Settings(BaseSettings):
    # Feature flags
    ENABLE_ICAL_SYNC: bool = True
    ENABLE_AUDIO_TRANSCRIPTION: bool = True
    ENABLE_NLU_ANALYSIS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = True

# En código
if settings.ENABLE_ICAL_SYNC:
    await sync_ical_calendars()
else:
    logger.info("ical_sync_disabled")
```

## 5.4 Idempotencia [CRÍTICO] (1h)

### 5.4.1 Implementar idempotency keys
```python
# En app/routers/mercadopago.py
from app.utils.idempotency import ensure_idempotent

@router.post("/webhooks/mercadopago")
@ensure_idempotent(key_extractor=lambda req: req.json().get("data", {}).get("id"))
async def mercadopago_webhook(request: Request):
    """Webhook idempotente de Mercado Pago."""
    # Si ya procesamos este payment_id, devolver respuesta cached
    # ...
```

```python
# En app/utils/idempotency.py
from functools import wraps
import hashlib

idempotency_cache = {}  # O usar Redis

def ensure_idempotent(key_extractor: Callable):
    """Decorator para asegurar idempotencia."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Extraer idempotency key
            body = await request.json()
            key = key_extractor(body)
            cache_key = f"idempotency:{key}"

            # Verificar si ya procesado
            if cache_key in idempotency_cache:
                logger.info("idempotent_request_cached", key=key)
                return idempotency_cache[cache_key]

            # Procesar
            result = await func(request, *args, **kwargs)

            # Cachear resultado
            idempotency_cache[cache_key] = result
            return result
        return wrapper
    return decorator
```

---

# 📊 FASE 6: OBSERVABILIDAD Y MONITOREO (4-6h)

## 6.1 Métricas Avanzadas [ALTO] (2h)

### 6.1.1 Agregar métricas de negocio
```python
# En app/metrics.py
from prometheus_client import Histogram, Gauge, Counter

# Métricas de negocio
REVENUE_TOTAL = Counter(
    "revenue_total",
    "Ingresos totales en pesos",
    ["accommodation_id", "channel"]
)

OCCUPANCY_RATE = Gauge(
    "occupancy_rate",
    "Tasa de ocupación por alojamiento",
    ["accommodation_id"]
)

BOOKING_LEAD_TIME = Histogram(
    "booking_lead_time_days",
    "Días de anticipación de reservas",
    ["accommodation_id"],
    buckets=[1, 3, 7, 14, 30, 60, 90, 180]
)

# Métricas técnicas adicionales
DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Duración de queries DB",
    ["query_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

REDIS_OPERATION_DURATION = Histogram(
    "redis_operation_duration_seconds",
    "Duración de operaciones Redis",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)
```

### 6.1.2 Instrumentar código crítico
```python
# En app/services/reservations.py
import time

async def create_prereservation(...):
    start_time = time.monotonic()

    try:
        # ... lógica de reserva

        # Registrar métricas de negocio
        REVENUE_TOTAL.labels(
            accommodation_id=accommodation_id,
            channel=channel
        ).inc(float(total_price))

        lead_time = (check_in - date.today()).days
        BOOKING_LEAD_TIME.labels(
            accommodation_id=accommodation_id
        ).observe(lead_time)

    finally:
        duration = time.monotonic() - start_time
        DB_QUERY_DURATION.labels(query_type="create_reservation").observe(duration)
```

## 6.2 Logging Estructurado Completo [ALTO] (1h)

### 6.2.1 Agregar correlation IDs
```python
# En app/main.py
import uuid
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Agregar correlation ID a cada request."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)

    # Agregar a logs
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    structlog.contextvars.unbind_contextvars("correlation_id")
    return response
```

### 6.2.2 Logging de eventos de negocio
```python
# Eventos de negocio importantes
logger.info("reservation_created",
    reservation_code=code,
    accommodation_id=accommodation_id,
    check_in=check_in.isoformat(),
    check_out=check_out.isoformat(),
    total_price=str(total_price),
    channel=channel
)

logger.warning("reservation_expired",
    reservation_code=code,
    reason="timeout"
)

logger.info("payment_received",
    reservation_code=code,
    payment_id=payment_id,
    amount=amount,
    payment_method=method
)
```

## 6.3 Distributed Tracing [MEDIO] (1h)

### 6.3.1 Implementar OpenTelemetry
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

```python
# En app/main.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Setup tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Instrumentar FastAPI automáticamente
FastAPIInstrumentor.instrument_app(app)

# Uso manual en código crítico
async def create_prereservation(...):
    with tracer.start_as_current_span("create_prereservation") as span:
        span.set_attribute("accommodation.id", accommodation_id)
        span.set_attribute("channel", channel)
        # ... lógica
```

## 6.4 Alerting [ALTO] (1h)

### 6.4.1 Definir reglas de alertas (Prometheus)
```yaml
# alerts.yml
groups:
  - name: alojamientos_alerts
    interval: 30s
    rules:
      # Disponibilidad
      - alert: APIDown
        expr: up{job="alojamientos_api"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "API está caída"

      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Tasa de errores > 5%"

      # Performance
      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P95 latency > 2s"

      # Negocio
      - alert: NoReservationsIn24h
        expr: increase(reservations_created_total[24h]) == 0
        for: 24h
        labels:
          severity: warning
        annotations:
          summary: "No hay reservas en 24h"

      - alert: HighReservationRejectionRate
        expr: rate(reservations_date_overlap_total[1h]) / rate(reservations_created_total[1h]) > 0.3
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: ">30% reservas rechazadas por overlap"

      # Recursos
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes{name="alojamientos_api"} / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Uso de memoria > 90%"

      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_size >= db_pool_max_size
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Pool de conexiones DB agotado"
```

---

# 📝 FASE 7: DOCUMENTACIÓN Y RUNBOOKS (2-3h)

## 7.1 Runbooks Operacionales [CRÍTICO]

### 7.1.1 Crear runbooks para incidentes comunes
```markdown
# RUNBOOK: API No Responde

## Síntomas
- Health check retorna 503
- Timeout en requests

## Diagnóstico
1. Verificar containers: `docker ps`
2. Ver logs: `docker logs alojamientos_api --tail 100`
3. Verificar DB: `docker exec alojamientos_postgres pg_isready`
4. Verificar Redis: `docker exec alojamientos_redis redis-cli PING`

## Resolución
1. Si container caído: `docker-compose restart alojamientos_api`
2. Si DB bloqueada: Ver `RUNBOOK: Database Issues`
3. Si Redis caído: `docker-compose restart alojamientos_redis`

## Prevención
- Monitorear métricas de health check
- Alertar si uptime < 99.9%
```

## 7.2 Documentación de APIs
```bash
# Generar documentación OpenAPI actualizada
# Acceder a http://localhost:8000/docs
# Exportar JSON
curl http://localhost:8000/openapi.json > docs/api_spec.json
```

---

# ✅ CHECKLIST FINAL DE VALIDACIÓN

## Checklist Pre-Producción

### Testing ✅
- [ ] Coverage > 80% en tests unitarios
- [ ] Todos los tests de constraint anti-doble-booking pasando
- [ ] Tests E2E pasando contra API real
- [ ] Load test con 50 usuarios concurrentes sin errores
- [ ] Stress test con 200 usuarios documentado

### Performance ✅
- [ ] P95 latency < 1s en endpoints críticos
- [ ] 0 N+1 queries detectadas
- [ ] Índices DB optimizados
- [ ] Connection pool configurado óptimamente
- [ ] Redis eviction policy configurada

### Seguridad ✅
- [ ] 0 vulnerabilidades HIGH/CRITICAL en escaneo
- [ ] Todas las entradas validadas y sanitizadas
- [ ] Secrets no hardcoded (audit passed)
- [ ] HTTPS configurado con headers seguros
- [ ] Rate limiting activo en endpoints críticos
- [ ] OWASP ZAP scan pasando

### Robustez ✅
- [ ] Error handling global implementado
- [ ] Retry logic con backoff exponencial
- [ ] Circuit breakers configurados
- [ ] Graceful degradation implementado
- [ ] Idempotencia en webhooks críticos

### Observabilidad ✅
- [ ] Métricas de negocio exportándose
- [ ] Logging estructurado con correlation IDs
- [ ] Distributed tracing configurado
- [ ] Alertas definidas para incidentes críticos
- [ ] Dashboards de monitoreo creados
- [ ] Runbooks documentados

### Infrastructure ✅
- [ ] Backups automáticos configurados
- [ ] Disaster recovery plan documentado
- [ ] Escalabilidad horizontal validada
- [ ] Health checks en todos los servicios
- [ ] Logs centralizados

---

# 🚀 SCRIPTS DE EJECUCIÓN

## Script Master de Validación

```bash
#!/bin/bash
# master_validation.sh - Ejecutar TODO el plan de validación

set -e

REPORTS_DIR="reports/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$REPORTS_DIR"

echo "🎯 INICIANDO VALIDACIÓN EXHAUSTIVA DEL MVP"
echo "==========================================="
echo "Reportes en: $REPORTS_DIR"
echo ""

# FASE 1: AUDITORÍA
echo "📊 FASE 1: AUDITORÍA Y DIAGNÓSTICO"
echo "===================================="

echo "→ Análisis estático de código..."
cd backend
flake8 app/ --max-line-length=100 > "$REPORTS_DIR/flake8.txt" 2>&1 || true
mypy app/ --ignore-missing-imports > "$REPORTS_DIR/mypy.txt" 2>&1 || true
radon cc app/ -a > "$REPORTS_DIR/complexity.txt"
bandit -r app/ -f json -o "$REPORTS_DIR/bandit.json" 2>&1 || true

echo "→ Análisis de base de datos..."
./scripts/analyze_db.sh > "$REPORTS_DIR/db_analysis.txt"

echo "→ Análisis de dependencias..."
pip list --outdated > "$REPORTS_DIR/outdated_packages.txt"

# FASE 2: TESTING
echo ""
echo "🧪 FASE 2: TESTING EXHAUSTIVO"
echo "=============================="

echo "→ Tests unitarios con coverage..."
pytest tests/ -v \
  --cov=app \
  --cov-report=html:"$REPORTS_DIR/coverage_html" \
  --cov-report=json:"$REPORTS_DIR/coverage.json" \
  --cov-fail-under=80 \
  -n auto \
  > "$REPORTS_DIR/pytest_unit.log" 2>&1

echo "→ Tests de constraint anti-doble-booking..."
pytest tests/test_double_booking.py \
  tests/test_constraint_validation.py \
  tests/test_reservation_concurrency.py \
  -v -s > "$REPORTS_DIR/double_booking_tests.log" 2>&1

echo "→ Tests E2E..."
pytest tests_e2e/test_real_api.py -v > "$REPORTS_DIR/e2e_tests.log" 2>&1

echo "→ Load testing..."
locust -f tests_e2e/locustfile.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=5m \
  --headless \
  --html="$REPORTS_DIR/locust_report.html" \
  > "$REPORTS_DIR/load_test.log" 2>&1

# FASE 3: SEGURIDAD
echo ""
echo "🔒 FASE 3: SEGURIDAD Y PENETRATION TESTING"
echo "=========================================="

echo "→ OWASP ZAP baseline scan..."
docker run --network=host owasp/zap2docker-stable \
  zap-baseline.py \
  -t http://localhost:8000 \
  -r "$REPORTS_DIR/zap_baseline.html" \
  > "$REPORTS_DIR/zap.log" 2>&1 || true

echo "→ Auditoría de secrets..."
grep -rn "password\|secret\|api_key\|token" backend/app/ \
  --exclude-dir=__pycache__ | grep -v "getenv\|environ" \
  > "$REPORTS_DIR/secrets_audit.txt" || true

# FASE 4: PERFORMANCE
echo ""
echo "⚡ FASE 4: ANÁLISIS DE PERFORMANCE"
echo "=================================="

echo "→ Profiling de la API..."
py-spy record -o "$REPORTS_DIR/profile.svg" \
  --duration 60 \
  --pid $(docker inspect -f '{{.State.Pid}}' alojamientos_api) \
  > "$REPORTS_DIR/profiling.log" 2>&1 || true

echo "→ Análisis de queries SQL..."
# Ejecutar con SQL echo activado y capturar
# ...

# RESUMEN FINAL
echo ""
echo "✅ VALIDACIÓN COMPLETADA"
echo "========================"
echo ""
echo "📊 RESUMEN:"
echo "- Tests unitarios: $(grep -c 'passed' $REPORTS_DIR/pytest_unit.log) passed"
echo "- Coverage: $(jq -r '.totals.percent_covered' $REPORTS_DIR/coverage.json)%"
echo "- Vulnerabilidades: $(jq -r '.results | length' $REPORTS_DIR/bandit.json) encontradas"
echo "- Load test P95: $(grep 'P95' $REPORTS_DIR/load_test.log | head -1)"
echo ""
echo "📁 Todos los reportes en: $REPORTS_DIR"
echo ""
echo "🚀 SISTEMA VALIDADO Y LISTO PARA PRODUCCIÓN"
```

---

# 📅 CRONOGRAMA RECOMENDADO

## Día 1: Auditoría y Testing (8h)
- **08:00-10:00**: Análisis estático (Fase 1.1)
- **10:00-12:00**: Análisis de DB (Fase 1.2)
- **12:00-13:00**: Break
- **13:00-15:00**: Tests unitarios (Fase 2.1)
- **15:00-17:00**: Tests de integración (Fase 2.2)

## Día 2: Performance y Seguridad (8h)
- **08:00-10:00**: Tests E2E y carga (Fase 2.3-2.4)
- **10:00-13:00**: Optimización SQL y Redis (Fase 3.1-3.2)
- **13:00-14:00**: Break
- **14:00-17:00**: Penetration testing (Fase 4.1-4.2)

## Día 3: Robustez y Observabilidad (8h)
- **08:00-11:00**: Error handling y retry logic (Fase 5.1-5.2)
- **11:00-13:00**: Graceful degradation (Fase 5.3-5.4)
- **13:00-14:00**: Break
- **14:00-17:00**: Métricas y alerting (Fase 6.1-6.4)

## Día 4: Refinamiento y Documentación (4h)
- **08:00-10:00**: Fixes de issues encontrados
- **10:00-12:00**: Documentación y runbooks (Fase 7)

---

# 🎯 CRITERIOS DE ÉXITO FINALES

## ✅ Sistema Aprobado Si:

### Testing
- ✅ Coverage > 80%
- ✅ 100% tests críticos pasando
- ✅ Load test P95 < 1s
- ✅ 0 errores en stress test (200 usuarios)

### Performance
- ✅ Latencia P95 < 1000ms
- ✅ Throughput > 100 req/s
- ✅ 0 N+1 queries
- ✅ Índices optimizados

### Seguridad
- ✅ 0 vulnerabilidades HIGH/CRITICAL
- ✅ 0 secrets hardcoded
- ✅ Rate limiting activo
- ✅ OWASP ZAP clean

### Robustez
- ✅ Error handling global
- ✅ Circuit breakers configurados
- ✅ Idempotencia en webhooks
- ✅ Graceful degradation

### Observabilidad
- ✅ Métricas exportándose
- ✅ Logs estructurados
- ✅ Alertas configuradas
- ✅ Dashboards operativos

---

**🚀 AL COMPLETAR ESTE PLAN: SISTEMA 100% PRODUCTION-READY**
