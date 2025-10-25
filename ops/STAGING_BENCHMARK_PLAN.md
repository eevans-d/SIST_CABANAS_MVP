# Plan de Benchmark en Staging (Fly.io)

Objetivo: medir latencias p50/p95 y tasa de error por endpoint público clave y registrar resultados como evidencia.

## Entradas
- BASE_URL: `https://<app>.fly.dev`
- Concurrencia: 10
- Requests por endpoint: 100–200 (según costo)
- Endpoints:
  - GET `/api/v1/healthz`
  - GET `/api/v1/readyz`
  - GET `/metrics`
  - GET `/api/v1/accommodations` (o catálogo equivalente)

## Criterios de éxito (SLOs)
- p95 < 3s (warning > 4s, critical > 6s)
- Error-rate < 1%

## Procedimiento
1) Calentar 30–60s (pequeño tráfico inicial)
2) Ejecutar benchmark principal por endpoint con concurrencia 10
3) Recolectar métricas (avg/p50/p95, errores)
4) Registrar resultados en `backend/docs/reverse_engineering/RUNTIME_REPORT_YYYY-MM-DD.md` (o similar)

## Plantilla de resultados

```
Fecha: YYYY-MM-DD
Base URL: https://<app>.fly.dev

Endpoint                       avg (ms)   p50 (ms)   p95 (ms)   error-rate
GET /api/v1/healthz            xxx        xxx        xxx        x.x%
GET /api/v1/readyz             xxx        xxx        xxx        x.x%
GET /metrics                   xxx        xxx        xxx        x.x%
GET /api/v1/accommodations     xxx        xxx        xxx        x.x%

Observaciones:
-
Conclusión:
-
```

## Validación extra (concurrencia anti solape)
- Ejecutar prueba de concurrencia de pre-reservas (RUN_MUTATING=1)
- Esperado: 1 de N intentos falla con IntegrityError/409 por EXCLUDE gist + locks Redis
