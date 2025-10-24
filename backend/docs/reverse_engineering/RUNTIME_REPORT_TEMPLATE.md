# Runtime Report — Módulo 2

Fecha: ________  Entorno: development|staging|production  Región: ________  Versión: commit ________

## 1) Latencias (benchmark)

Parámetros: BASE_URL=____  CONCURRENCY=__  REQUESTS_PER_ENDPOINT=__

Resultados (copiar JSON del script y/o resumir):

- GET /healthz → avg: __ ms | p50: __ ms | p95: __ ms | error_rate: __
- GET /readyz → avg: __ ms | p50: __ ms | p95: __ ms | error_rate: __
- GET /reservations/accommodations → avg: __ ms | p50: __ ms | p95: __ ms | error_rate: __
- GET /metrics → avg: __ ms | p50: __ ms | p95: __ ms | error_rate: __
- (opt) POST /nlu/analyze → avg: __ ms | p50: __ ms | p95: __ ms | error_rate: __

Conclusión p95: __ (OK/WARN/CRIT)

## 2) Concurrencia anti-overlap

Payload: accommodation_id=__, check_in=____, check_out=____

Resultados:
```
{ result1: {status_code: __, body: __},
  result2: {status_code: __, body: __},
  both_ok: true|false }
```

Diagnóstico:
- Si both_ok=true en Postgres real → revisar extensión `btree_gist`, constraint `no_overlap_reservations` y locks Redis.

## 3) Jobs y métricas

- Expiración pre-reservas: intervalo real observado: __ s  | errores: __
- iCal sync: ICAL_LAST_SYNC_AGE_MIN = __ min | last_ical_sync_at más reciente: __

## 4) Observaciones / acciones

- Hallazgos relevantes:
  - __
- Acciones propuestas:
  - __
