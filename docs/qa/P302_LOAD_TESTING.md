# 🚀 P302: LOAD TESTING SUITE - Sistema MVP

**Fecha:** 14 Octubre 2025
**Herramienta:** Locust 2.x
**Alcance:** Validación de SLOs bajo carga concurrente

---

## 📋 RESUMEN EJECUTIVO

### Objetivo
Validar que el sistema cumple SLOs bajo carga realista con 100 usuarios concurrentes y 1000 req/min sostenido durante 5 minutos.

### SLOs a Validar
| Endpoint | Métrica | Target | Criticidad |
|----------|---------|--------|------------|
| Pre-reserva | P95 | < 3s | 🔴 CRÍTICO |
| Webhook WhatsApp (texto) | P95 | < 3s | 🔴 CRÍTICO |
| Webhook WhatsApp (audio) | P95 | < 15s | 🟡 ALTO |
| Health Check | P95 | < 500ms | 🟢 MEDIO |
| Error Rate | Total | < 1% | 🔴 CRÍTICO |

### Herramienta Creada
✅ **tools/load_test_suite.py** (300 líneas)
- 3 tipos de usuarios: Reservation, WhatsApp, Mercado Pago
- Validación automática de SLOs
- Event handlers para métricas personalizadas

---

## 🎯 ESCENARIOS DE PRUEBA

### Escenario 1: Tráfico Normal (Baseline)
**Perfil:** 10 usuarios, 1 minuto, ramp-up 2 users/s

**Objetivo:** Establecer baseline de performance sin stress

**Comando:**
```bash
locust -f tools/load_test_suite.py --headless \
  -u 10 -r 2 -t 1m \
  --host http://localhost:8000 \
  --html reports/loadtest_baseline.html
```

**Expected Results:**
- P95 < 2s (pre-reserva)
- P95 < 1.5s (webhook texto)
- Error rate < 0.5%
- No database connection errors
- No Redis connection errors

---

### Escenario 2: Tráfico Pico (Peak Load)
**Perfil:** 100 usuarios, 5 minutos, ramp-up 10 users/s

**Objetivo:** Validar SLOs bajo carga pico realista

**Comando:**
```bash
locust -f tools/load_test_suite.py --headless \
  -u 100 -r 10 -t 5m \
  --host http://localhost:8000 \
  --html reports/loadtest_peak.html \
  --csv reports/loadtest_peak
```

**Expected Results:**
- P95 < 3s (pre-reserva) ✅ SLO
- P95 < 3s (webhook texto) ✅ SLO
- P95 < 15s (webhook audio) ✅ SLO
- Error rate < 1% ✅ SLO
- Throughput > 200 req/s

**Métricas a Monitorear:**
```bash
# CPU usage
docker stats --no-stream

# Database connections
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Redis memory
docker exec -it sist-cabanas-redis redis-cli INFO memory | grep used_memory_human
```

---

### Escenario 3: Stress Test (Breaking Point)
**Perfil:** 200 usuarios, 10 minutos, ramp-up 20 users/s

**Objetivo:** Encontrar límite del sistema (breaking point)

**Comando:**
```bash
locust -f tools/load_test_suite.py --headless \
  -u 200 -r 20 -t 10m \
  --host http://localhost:8000 \
  --html reports/loadtest_stress.html \
  --csv reports/loadtest_stress
```

**Expected Results:**
- Identificar punto de fallo (P95 > 10s o error rate > 5%)
- Validar que sistema se degrada gracefully
- No memory leaks
- No database deadlocks
- Recovery automático después de carga

**Red Flags:**
- ❌ Error rate > 5%
- ❌ P95 > 10s
- ❌ Database connection exhaustion
- ❌ Redis OOM errors
- ❌ Memory leaks (heap growth continuo)

---

### Escenario 4: Spike Test (Súbito)
**Perfil:** 0→100 usuarios en 10s, mantener 2 min, bajar a 0

**Objetivo:** Validar comportamiento ante tráfico súbito (viral post, marketing campaign)

**Comando:**
```bash
# Locust no soporta spike directo, usar script custom
python tools/spike_test.py \
  --host http://localhost:8000 \
  --spike-users 100 \
  --spike-duration 120
```

**Script a crear:**
```python
# tools/spike_test.py
import asyncio
import aiohttp
import time

async def spike_test(host: str, spike_users: int, duration: int):
    """Simular spike de tráfico súbito"""
    start = time.monotonic()

    async with aiohttp.ClientSession() as session:
        # Crear 100 requests simultáneas
        tasks = [
            session.post(f"{host}/api/v1/reservations/prereserve", json={...})
            for _ in range(spike_users)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Analizar resultados
    successful = sum(1 for r in results if not isinstance(r, Exception))
    print(f"Spike test: {successful}/{spike_users} successful")
```

---

### Escenario 5: Endurance Test (Soak)
**Perfil:** 50 usuarios, 1 hora, ramp-up 5 users/s

**Objetivo:** Detectar memory leaks y degradación de performance a largo plazo

**Comando:**
```bash
locust -f tools/load_test_suite.py --headless \
  -u 50 -r 5 -t 1h \
  --host http://localhost:8000 \
  --html reports/loadtest_endurance.html \
  --csv reports/loadtest_endurance
```

**Métricas Críticas:**
```bash
# Memory growth (cada 10 min)
docker stats --no-stream | grep sist-cabanas

# Database cache hit ratio (debe mantenerse > 95%)
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 AS cache_hit_ratio FROM pg_statio_user_tables;"

# Redis fragmentation (debe mantenerse < 1.5)
docker exec -it sist-cabanas-redis redis-cli INFO memory | grep mem_fragmentation_ratio
```

**Red Flags:**
- ❌ Heap memory growth > 20% en 1h
- ❌ P95 latency degradation > 30%
- ❌ Cache hit ratio drop < 90%
- ❌ Redis fragmentation > 2.0

---

## 📊 MÉTRICAS Y UMBRALES

### Request-Level Metrics

| Métrica | Formula | Target | Critical |
|---------|---------|--------|----------|
| **Success Rate** | (successful / total) * 100 | > 99% | < 95% |
| **P50 Latency** | 50th percentile | < 1s | > 5s |
| **P95 Latency** | 95th percentile | < 3s | > 10s |
| **P99 Latency** | 99th percentile | < 5s | > 15s |
| **Max Latency** | Maximum observed | < 10s | > 30s |

### System-Level Metrics

| Métrica | Command | Target | Critical |
|---------|---------|--------|----------|
| **CPU Usage** | `docker stats` | < 70% | > 90% |
| **Memory Usage** | `docker stats` | < 80% | > 95% |
| **DB Connections** | `SELECT count(*) FROM pg_stat_activity` | < 15 | > 25 |
| **Redis Memory** | `redis-cli INFO memory` | < 100MB | > 500MB |
| **Disk I/O** | `iostat -x 1` | < 50% util | > 80% |

### Business-Level Metrics

| Métrica | Description | Target | Critical |
|---------|-------------|--------|----------|
| **Booking Success Rate** | Pre-reservas creadas / intentos | > 95% | < 80% |
| **Lock Acquisition Rate** | Locks acquired / attempts | > 98% | < 90% |
| **Webhook Processing Rate** | Webhooks procesados / recibidos | > 99% | < 95% |
| **Constraint Violations** | IntegrityError por overlaps | < 1% | > 5% |

---

## 🧪 DISTRIBUCIÓN DE CARGA POR TIPO DE USUARIO

### Perfil Realista de Tráfico

**ReservationUser (70%)**
- View accommodations: 50% de sus acciones
- Check availability: 30% de sus acciones
- Create prereservation: 20% de sus acciones

**WhatsAppWebhookUser (20%)**
- Text messages: 90% de webhooks
- Audio messages: 10% de webhooks (future)

**MercadoPagoWebhookUser (10%)**
- Payment webhooks: 100%

### Comando con Distribución Custom
```bash
locust -f tools/load_test_suite.py --headless \
  -u 100 -r 10 -t 5m \
  --host http://localhost:8000 \
  --user-classes ReservationUser:70,WhatsAppWebhookUser:20,MercadoPagoWebhookUser:10 \
  --html reports/loadtest_realistic.html
```

---

## 🔧 CONFIGURACIÓN DE LOCUST

### Instalación
```bash
cd /home/eevan/ProyectosIA/SIST_CABAÑAS
source backend/.venv/bin/activate
pip install locust aiohttp
```

### Estructura del Load Test Suite

```python
# tools/load_test_suite.py

class ReservationUser(HttpUser):
    wait_time = between(1, 3)  # Esperar 1-3s entre requests

    @task(5)  # Peso 5 (más común)
    def view_accommodations(self):
        # GET /api/v1/accommodations

    @task(3)  # Peso 3
    def check_availability(self):
        # GET /api/v1/accommodations/{id}/availability

    @task(2)  # Peso 2 (menos común pero crítico)
    def create_prereservation(self):
        # POST /api/v1/reservations/prereserve
        # Validar SLO: P95 < 3s

    @task(1)  # Peso 1 (bajo pero importante)
    def healthcheck(self):
        # GET /api/v1/healthz


class WhatsAppWebhookUser(HttpUser):
    wait_time = between(2, 5)

    @task(3)
    def text_message_webhook(self):
        # POST /api/v1/webhooks/whatsapp (text)
        # Validar SLO: P95 < 3s


class MercadoPagoWebhookUser(HttpUser):
    wait_time = between(3, 7)

    @task
    def payment_webhook(self):
        # POST /api/v1/webhooks/mercadopago
```

### Event Handlers para Validación de SLOs

```python
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Validar SLOs al finalizar test"""
    stats = environment.stats

    slo_endpoints = {
        "/reservations/prereserve [POST]": {"p95_max_ms": 3000},
        "/webhooks/whatsapp [TEXT]": {"p95_max_ms": 3000},
    }

    slo_passed = True
    for endpoint, slo in slo_endpoints.items():
        stat = stats.get(endpoint)
        p95_ms = stat.get_response_time_percentile(0.95)

        if p95_ms > slo["p95_max_ms"]:
            logger.error(f"❌ SLO FAILED: {endpoint} P95={p95_ms}ms > {slo['p95_max_ms']}ms")
            slo_passed = False
        else:
            logger.info(f"✅ SLO PASSED: {endpoint} P95={p95_ms}ms")

    return slo_passed
```

---

## 📈 ANÁLISIS DE RESULTADOS

### Locust HTML Report
Al ejecutar con `--html reports/loadtest_peak.html`, se genera reporte con:
- **Charts:** Request rate, response times, number of users
- **Statistics Table:** Total requests, failures, median, P95, P99, avg size
- **Failures Table:** Tipos de errores y frecuencia
- **Exceptions Table:** Stack traces de excepciones

### CSV Export para Análisis Avanzado
```bash
# Genera 3 archivos CSV
locust ... --csv reports/loadtest_peak

# loadtest_peak_stats.csv - estadísticas por endpoint
# loadtest_peak_stats_history.csv - historial temporal
# loadtest_peak_failures.csv - detalles de fallos
```

### Análisis con Python
```python
import pandas as pd
import matplotlib.pyplot as plt

# Leer stats history
df = pd.read_csv("reports/loadtest_peak_stats_history.csv")

# Plot P95 latency over time
plt.figure(figsize=(12, 6))
plt.plot(df["Timestamp"], df["95%"], label="P95 Latency")
plt.axhline(y=3000, color='r', linestyle='--', label="SLO (3s)")
plt.xlabel("Time")
plt.ylabel("Latency (ms)")
plt.legend()
plt.savefig("reports/p95_latency_timeline.png")
```

---

## 🚨 TROUBLESHOOTING DURANTE LOAD TEST

### Problema 1: Error Rate > 5%
**Diagnóstico:**
```bash
# Ver logs de errors
docker-compose logs api --tail=100 | grep ERROR

# Verificar DB connections
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT state, count(*) FROM pg_stat_activity GROUP BY state;"
```

**Soluciones:**
- Aumentar `pool_size` en database engine
- Aumentar `max_connections` en Redis
- Verificar rate limiting no está bloqueando tráfico legítimo

---

### Problema 2: P95 > 10s (Degradación Severa)
**Diagnóstico:**
```bash
# Ver queries lentas
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT query, mean_exec_time, calls FROM pg_stat_statements WHERE mean_exec_time > 1000 ORDER BY mean_exec_time DESC LIMIT 5;"

# Verificar CPU usage
docker stats --no-stream
```

**Soluciones:**
- Identificar queries N+1 y optimizar con selectinload
- Verificar índices están siendo usados (EXPLAIN ANALYZE)
- Reducir load para evitar cascading failures

---

### Problema 3: Memory Leak (Heap Growth)
**Diagnóstico:**
```bash
# Monitorear memory growth
watch -n 10 'docker stats --no-stream | grep sist-cabanas-api'

# Verificar Redis memory
docker exec -it sist-cabanas-redis redis-cli INFO memory
```

**Soluciones:**
- Verificar no hay locks Redis sin TTL
- Verificar conexiones DB se cierran correctamente
- Revisar asyncio tasks no están leaking

---

### Problema 4: Database Connection Exhaustion
**Diagnóstico:**
```bash
# Ver conexiones activas
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Max connections configuradas
docker exec -it sist-cabanas-postgres psql -U alojamientos_user -d alojamientos \
  -c "SHOW max_connections;"
```

**Soluciones:**
```python
# Aumentar pool_size y max_overflow
engine = create_async_engine(
    DATABASE_URL,
    pool_size=30,  # De 10 a 30
    max_overflow=20,  # De 5 a 20
    pool_pre_ping=True,
)
```

---

## ✅ CHECKLIST DE EJECUCIÓN

### Pre-Test
- [ ] Sistema en staging levantado (`docker-compose up -d`)
- [ ] Database con datos de prueba (al menos 10 accommodations)
- [ ] Redis limpio (`redis-cli FLUSHALL`)
- [ ] Locust instalado (`pip install locust`)
- [ ] Crear directorio de reportes (`mkdir -p reports`)
- [ ] Verificar health check (`curl http://localhost:8000/api/v1/healthz`)

### Durante Test
- [ ] Monitorear logs en real-time (`docker-compose logs -f api`)
- [ ] Monitorear métricas de sistema (`docker stats`)
- [ ] Verificar Locust Web UI (si no es headless)
- [ ] Tomar snapshots de métricas cada minuto

### Post-Test
- [ ] Generar HTML report
- [ ] Exportar CSV stats
- [ ] Validar SLOs cumplidos
- [ ] Documentar bottlenecks encontrados
- [ ] Crear tickets para optimizaciones
- [ ] Limpiar datos de prueba

---

## 📋 PLAN DE EJECUCIÓN RECOMENDADO

### Semana 1: Baseline y Peak Load
```bash
# Día 1: Baseline (establecer métricas sin stress)
locust -f tools/load_test_suite.py --headless -u 10 -r 2 -t 1m \
  --host http://localhost:8000 --html reports/baseline.html

# Día 2: Peak Load (validar SLOs)
locust -f tools/load_test_suite.py --headless -u 100 -r 10 -t 5m \
  --host http://localhost:8000 --html reports/peak.html

# Día 3: Analizar resultados y documentar
```

### Semana 2: Stress y Endurance
```bash
# Día 1: Stress Test (encontrar breaking point)
locust -f tools/load_test_suite.py --headless -u 200 -r 20 -t 10m \
  --host http://localhost:8000 --html reports/stress.html

# Día 2-3: Endurance Test (detectar memory leaks)
locust -f tools/load_test_suite.py --headless -u 50 -r 5 -t 1h \
  --host http://localhost:8000 --html reports/endurance.html

# Día 4: Analizar y crear roadmap de optimización
```

---

## 🎯 CRITERIOS DE ACEPTACIÓN

### ✅ Test Exitoso SI:
1. P95 < 3s para pre-reserva bajo 100 users
2. P95 < 3s para webhook texto bajo 100 users
3. Error rate < 1% durante todo el test
4. No memory leaks en endurance test (1h)
5. Sistema se recupera automáticamente después de stress
6. No database deadlocks o connection exhaustion
7. Cache hit ratio DB > 95% durante todo el test

### ❌ Test Fallido SI:
1. P95 > 5s en cualquier endpoint crítico
2. Error rate > 5% en cualquier momento
3. Memory growth > 30% en endurance test
4. Database connection exhaustion
5. Redis OOM errors
6. Cascading failures (un error causa múltiples fallos)
7. Sistema no se recupera después de stress en < 5 min

---

## 📚 REFERENCIAS

- [Locust Documentation](https://docs.locust.io/)
- [Performance Testing Best Practices](https://martinfowler.com/articles/performance-testing.html)
- [PERFORMANCE_BENCHMARKS_v1.0.0.md](../../PERFORMANCE_BENCHMARKS_v1.0.0.md)

---

**Próximo paso:** P303 - Database Query Optimization (EXPLAIN ANALYZE, N+1 queries, índices)

**Documento creado:** 14 Octubre 2025
**Autor:** Performance Team
**Status:** ✅ DOCUMENTADO (suite creada, ejecución pendiente)
