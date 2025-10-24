# Runtime Report — Módulo 2

Fecha: 2025-10-24  Entorno: local-dev  Región: n/a  Versión: commit: pending

## 1) Latencias (benchmark)

Parámetros: BASE_URL=http://localhost:8000/api/v1  CONCURRENCY=2  REQUESTS_PER_ENDPOINT=4

Resultados (crudos):

```
{"base_url": "http://localhost:8000/api/v1", "root_url": "http://localhost:8000", "concurrency": 2, "requests_per_endpoint": 4, "mutating": false}
{
  "results": [
    {
      "endpoint": "http://localhost:8000/api/v1/healthz",
      "method": "GET",
      "requests": 4,
      "errors": 4,
      "error_rate": 1.0,
      "avg_ms": null,
      "p50_ms": null,
      "p95_ms": null
    },
    {
      "endpoint": "http://localhost:8000/api/v1/readyz",
      "method": "GET",
      "requests": 4,
      "errors": 4,
      "error_rate": 1.0,
      "avg_ms": null,
      "p50_ms": null,
      "p95_ms": null
    },
    {
      "endpoint": "http://localhost:8000/api/v1/reservations/accommodations",
      "method": "GET",
      "requests": 4,
      "errors": 4,
      "error_rate": 1.0,
      "avg_ms": null,
      "p50_ms": null,
      "p95_ms": null
    },
    {
      "endpoint": "http://localhost:8000/metrics",
      "method": "GET",
      "requests": 4,
      "errors": 4,
      "error_rate": 1.0,
      "avg_ms": null,
      "p50_ms": null,
      "p95_ms": null
    }
  ]
}
```

Interpretación: No hay servidor escuchando en http://localhost:8000, por eso 100% errores.

## 2) Concurrencia anti-overlap

No ejecutado (RUN_MUTATING=1 requerido y entorno no disponible).

## 3) Jobs y métricas

No ejecutado; /metrics no accesible.

## 4) Observaciones / acciones

- Hallazgos:
  - No hay servidor activo en localhost:8000 al momento de la medición.
- Acciones propuestas (elige una):
  1) Proveer BASE_URL de staging/producción (e.g. https://app.tu-dominio/api/v1) y reejecuto los scripts.
  2) Levantar localmente y medir:
     - Opcional (Docker): `docker compose up -d` en `backend/` y esperar readiness; luego reejecutar benchmark.
     - Opcional (poetry/venv): iniciar app con uvicorn y repetir mediciones.
