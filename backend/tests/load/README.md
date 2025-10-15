# k6 Load Testing Suite

Suite de pruebas de carga para el sistema de reservas MVP.

## FASE 2 - P106: Load Testing

### Scripts Disponibles

#### 1. Normal Load Test (`normal-load.js`)
**Perfil:** 50 usuarios concurrentes durante 10 minutos
**Objetivo:** Validar comportamiento bajo carga normal esperada

```bash
k6 run backend/tests/load/normal-load.js
```

**SLOs validados:**
- P95 < 3s para endpoints de texto
- P99 < 6s para endpoints de texto
- Error rate < 1%
- Disponibilidad > 99%

#### 2. Spike Test (`spike-test.js`)
**Perfil:** Spike de 50→200 usuarios (4x) durante 3 minutos
**Objetivo:** Validar resiliencia ante picos súbitos de tráfico

```bash
k6 run backend/tests/load/spike-test.js
```

**Métricas clave:**
- Error rate < 5% durante spike
- Lock contention < 30%
- P95 < 5s (más laxo durante spike)
- Recuperación rápida post-spike

#### 3. Soak Test (`soak-test.js`)
**Perfil:** 30 usuarios concurrentes durante 2 horas
**Objetivo:** Detectar memory leaks y degradación gradual

```bash
k6 run backend/tests/load/soak-test.js
```

**Validaciones:**
- Performance degradation < 15% vs baseline
- Memory usage estable
- DB connections no crecen indefinidamente
- Error rate < 1% sostenido

### Configuración del Entorno

#### Variables de Entorno

```bash
# BASE_URL del sistema bajo test
export BASE_URL=http://localhost:8000/api/v1

# O para staging/producción
export BASE_URL=https://staging.example.com/api/v1
```

#### Pre-requisitos Sistema

1. **Sistema corriendo:**
   ```bash
   cd /home/eevan/ProyectosIA/SIST_CABAÑAS
   docker-compose up -d
   ```

2. **Alojamientos de test creados:**
   ```bash
   # IDs 1, 2, 3 deben existir en DB
   # O modificar arrays `accommodations` en los scripts
   ```

3. **k6 instalado:**
   ```bash
   # Ubuntu/Debian
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6

   # macOS
   brew install k6

   # Docker (alternativa)
   docker run --rm -i grafana/k6 run - <backend/tests/load/normal-load.js
   ```

### Ejecución Secuencial Completa

```bash
#!/bin/bash
# run-all-load-tests.sh

set -e

echo "=== INICIANDO SUITE COMPLETA DE LOAD TESTS ==="
echo ""

# 1. Normal Load
echo "1/3 - Normal Load Test (10 min)..."
k6 run backend/tests/load/normal-load.js
echo ""
sleep 30  # Cooldown

# 2. Spike Test
echo "2/3 - Spike Test (8 min)..."
k6 run backend/tests/load/spike-test.js
echo ""
sleep 60  # Cooldown más largo

# 3. Soak Test
echo "3/3 - Soak Test (2 horas)..."
k6 run backend/tests/load/soak-test.js
echo ""

echo "=== SUITE COMPLETA FINALIZADA ==="
echo "Revisar archivos JSON de resultados:"
ls -lh *-results.json
```

### Análisis de Resultados

#### Métricas Clave a Revisar

1. **Request Duration:**
   - P50, P95, P99 vs SLOs
   - Max duration (outliers)

2. **Error Rate:**
   - http_req_failed rate
   - Tipos de errores (5xx vs 4xx vs timeouts)

3. **Throughput:**
   - Requests/second sostenido
   - Peak throughput durante spike

4. **Resource Utilization:**
   - Memory usage (gauge)
   - Active DB connections
   - Cache hit rate

5. **Custom Metrics:**
   - Lock contention rate (spike test)
   - Performance degradation (soak test)
   - Pre-reservation success rate

#### Interpretación de Resultados

**✓ PASS - Sistema Production-Ready:**
```
✓ Normal Load: P95 < 3s, error rate < 1%
✓ Spike Test: P95 < 5s, error rate < 5%, recovery < 1min
✓ Soak Test: degradation < 15%, no memory leaks
```

**⚠️ WARNING - Optimización Recomendada:**
```
⚠️ P95: 3-4s (cerca del límite)
⚠️ Error rate: 1-3% (por encima de SLO)
⚠️ Degradation: 15-20% en soak test
```

**✗ FAIL - Requiere Fixes:**
```
✗ P95 > 4s consistently
✗ Error rate > 5%
✗ Memory leak evidente (crecimiento continuo)
✗ DB connection pool agotado
✗ Degradation > 20%
```

### Troubleshooting Común

#### 1. Connection Refused
```bash
# Verificar que sistema esté corriendo
curl http://localhost:8000/api/v1/healthz

# Si falla, iniciar sistema
docker-compose up -d
docker-compose logs -f backend
```

#### 2. High Error Rate (409 Conflicts)
```
Esperado: 409 (date overlap) bajo carga concurrente es NORMAL
Acción: Verificar que no sean todos 409, mix con 200 OK es saludable
```

#### 3. Timeouts Frecuentes
```bash
# Aumentar workers Gunicorn
# En docker-compose.yml o .env:
GUNICORN_WORKERS=4
GUNICORN_THREADS=2

# Restart
docker-compose restart backend
```

#### 4. DB Connection Pool Exhausted
```bash
# Aumentar pool size
# En backend/app/core/database.py:
pool_size=20
max_overflow=10

# Verificar conexiones activas
docker-compose exec postgres psql -U user -d dbname -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"
```

#### 5. Redis Out of Memory
```bash
# Verificar uso de memoria
docker-compose exec redis redis-cli INFO memory

# Ajustar maxmemory en docker-compose.yml
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### Integración con CI/CD

```yaml
# .github/workflows/load-test.yml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * 0'  # Domingo 2am
  workflow_dispatch:      # Manual

jobs:
  load-test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Start system
        run: |
          docker-compose up -d
          sleep 30  # Wait for readiness

      - name: Install k6
        run: |
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run normal load test
        run: k6 run backend/tests/load/normal-load.js

      - name: Run spike test
        run: k6 run backend/tests/load/spike-test.js

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: '*-results.json'

      - name: Check SLO compliance
        run: |
          # Parse JSON y validar thresholds
          python tools/validate_load_test_results.py
```

### Baseline Performance (Referencia)

**Hardware de referencia:** 2 CPU, 4GB RAM
**Database:** PostgreSQL 16
**Cache:** Redis 7

#### Expected Baseline (sin optimizaciones):
- Normal Load P95: ~2.5s
- Spike Test P95: ~4.5s
- Soak Test degradation: ~8%
- Error rate: < 0.5%

#### After Optimizations (7 quick wins implementadas):
- Normal Load P95: ~1.2s (50% mejora)
- Spike Test P95: ~3.5s (22% mejora)
- Soak Test degradation: ~5%
- Cache hit rate: ~70%

### Referencias

- [k6 Documentation](https://k6.io/docs/)
- [Load Testing Best Practices](https://k6.io/docs/test-types/introduction/)
- [k6 Thresholds](https://k6.io/docs/using-k6/thresholds/)
- [k6 Metrics](https://k6.io/docs/using-k6/metrics/)

### Checklist de Ejecución

Antes de load tests en producción/staging:

- [ ] Backup de base de datos reciente
- [ ] Notificar a stakeholders (test generará tráfico artificial)
- [ ] Verificar que monitoring (Prometheus/Grafana) esté activo
- [ ] Establecer baseline pre-optimizaciones
- [ ] Preparar rollback plan si sistema se degrada
- [ ] Post-test: revisar logs de errores y warnings
- [ ] Post-test: comparar métricas vs baseline
- [ ] Documentar hallazgos y próximos pasos

---

**Última actualización:** 2025-10-14
**Autor:** Sistema QA - FASE 2 P106
**Tiempo estimado ejecución completa:** ~2h 30min (excl. soak test de 2h)
