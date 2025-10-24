# Módulo 2 — Runtime & Observabilidad

Objetivo: validar desempeño real (latencias p50/p95), comportamiento bajo concurrencia (locks + EXCLUDE), y salud de jobs, con artefactos reproducibles.

## KPIs a medir
- Latencias p50/p95 y error rate de endpoints:
  - GET /api/v1/healthz
  - GET /api/v1/readyz
  - GET /api/v1/reservations/accommodations
  - GET /metrics (raíz)
  - (opt-in) POST /api/v1/nlu/analyze — cuidado: puede crear pre-reservas
- Concurrencia anti-overlap:
  - Dos pre-reservas simultáneas para mismo alojamiento/rango → una debe fallar (date_overlap) en Postgres.
- Jobs
  - Expiración de pre-reservas: que corra en el intervalo configurado y afecte /healthz si hay degradaciones.
  - Sync iCal: métrica `ICAL_LAST_SYNC_AGE_MIN` y campo `last_ical_sync_at` actualizándose.

## Artefactos incluidos
- scripts/runtime_benchmark.py — benchmark simple (async) con httpx para latencias y error rate.
- scripts/concurrency_overlap_test.py — test de carrera anti-overlap (opt-in).
- RUNTIME_REPORT_TEMPLATE.md — plantilla para documentar resultados.

## Cómo ejecutar
1) Benchmark (read-only por defecto):

```bash
BASE_URL=http://localhost:8000/api/v1 \
CONCURRENCY=5 REQUESTS_PER_ENDPOINT=20 \
python backend/scripts/runtime_benchmark.py
```

2) Concurrencia anti-overlap (mutante: crea pre-reservas):

```bash
BASE_URL=http://localhost:8000/api/v1 RUN_MUTATING=1 \
python backend/scripts/concurrency_overlap_test.py
```

3) (Opcional) Activar pruebas mutantes en benchmark:

```bash
BASE_URL=http://localhost:8000/api/v1 RUN_MUTATING=1 \
python backend/scripts/runtime_benchmark.py
```

## Observaciones y criterios
- SLOs (del proyecto):
  - Texto p95 < 3s (warning > 4s, critical > 6s)
  - Audio p95 < 15s (no medido aquí)
  - iCal sync age < 20min (warning > 30min)
  - Error rate < 1% (critical > 5%)
- Entornos SQLite pueden permitir doble éxito en overlap; validar en Postgres con extensión `btree_gist` y constraint activo.
- /metrics suele estar fuera del prefijo /api/v1.
