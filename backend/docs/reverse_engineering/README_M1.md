# Reverse Engineering — Módulo 1 (Code & Contracts)

Este índice resume los artefactos generados en el Módulo 1 y cómo usarlos.

## Artefactos

- INVENTARIO_CODIGO.csv — Inventario de modelos, routers, servicios y migraciones con sus campos/índices clave.
  - ./INVENTARIO_CODIGO.csv
- DB_CONSTRAINTS.md — Constraints e índices, incluyendo la columna generada `period` y el EXCLUDE gist anti-overlap.
  - ./DB_CONSTRAINTS.md
- CONFIG_MATRIX.md — Variables de configuración (env), defaults, validadores y notas de seguridad.
  - ./CONFIG_MATRIX.md
- MIGRATIONS_MAP.md — Línea de tiempo y contenido de migraciones Alembic con referencias de uso.
  - ./MIGRATIONS_MAP.md
- CONTRATOS_CORE.md — Contratos de API y webhooks (WhatsApp, Mercado Pago, iCal, Audio, NLU, Admin, Health).
  - ./CONTRATOS_CORE.md

## Cómo aprovechar estos artefactos

- QA/Seguridad: verificar firmas de webhooks y tokens HMAC usando CONTRATOS_CORE + CONFIG_MATRIX.
- DB Ops: confirmar que la instancia Postgres tenga `btree_gist` y que la migración 001 esté aplicada (ver DB_CONSTRAINTS + MIGRATIONS_MAP).
- Observabilidad: revisar health checks y métricas expuestas para SLOs (CONTRATOS_CORE: /healthz, /metrics en app/main.py).
- Integraciones: usar CONTRATOS_CORE para mocks de WhatsApp/MP en staging.

## Próximo paso sugerido

- Módulo 2 (Runtime): medir latencias p95 de endpoints críticos, validar locks Redis bajo concurrencia y monitorear jobs (expiración e iCal) con métricas.
