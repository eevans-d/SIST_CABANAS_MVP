# Sistema MVP Reservas Alojamientos [![CI](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml/badge.svg)](https://github.com/eevans-d/SIST_CABANAS_MVP/actions/workflows/ci.yml)

> Filosofía: SHIPPING > PERFECCIÓN. Código mínimo viable para orquestar pre-reservas con anti doble-booking, canal WhatsApp y pagos (WIP).

## Repo oficial único (fuente de verdad)
- Código e issues: https://github.com/eevans-d/SIST_CABANAS_MVP

Política de consolidación:
- Este es el único repositorio oficial del proyecto.
- Cualquier otro repositorio con contenido duplicado (p. ej. `SIST_CABANAS`, `SIST_CABANAS_DOCS`) será archivado para evitar confusiones.
- La documentación vive dentro de este mismo repo (carpetas `README.md`, `backend/docs`, `backend/docs/adr`).

Estado de consolidación: ver `docs/CONSOLIDATION_STATUS.md`.

## Estado Actual (2025-09-24)
- Esquema base: `accommodations`, `reservations` + constraint `no_overlap_reservations` (PostgreSQL, daterange + EXCLUDE gist) implementado en migración `001_initial_schema.py`.
- Tests anti solapamiento listos (`test_double_booking.py`, `test_constraint_validation.py`).
- ADR-001: No integrar PMS externo en MVP.
- Fixtures avanzadas de test con fallback a SQLite (los tests críticos se saltan si no hay Postgres real).
- Daily log: `docs/DAILY_LOG_2025-09-24.md`.

## Próximos Hitos (orden sugerido)
1. ReservationService (locks Redis + creación pre-reserva + pricing simple).
2. Job expiración pre-reservas.
3. Webhook WhatsApp (firma HMAC + normalización mensaje unificado).
4. Integración Mercado Pago mínima (preferencia + webhook idempotente).
5. Métricas Prometheus y enriquecimiento `/healthz`.
6. Migración siguiente: tabla de pagos / mensajes / audio procesado.
7. Pipeline audio (FFmpeg + faster-whisper) + NLU básico (regex + dateparser).

## Requisitos Técnicos Clave
- Python 3.11+
- PostgreSQL 16 con extensión `btree_gist`.
- Redis 7.
- Docker + Docker Compose (flujo recomendado).

## Puesta en Marcha Rápida (Docker)
```bash
cp .env.template .env  # Completar secretos mínimos
make up                # Levanta Postgres, Redis, API, Nginx
make migrate           # Aplica migraciones
```
API local: http://localhost:8000 (o vía Nginx según config).

## Ejecutar Tests
Para validar constraint (requiere Postgres real):
```bash
make test
```
Si falta Postgres accesible en `TEST_DATABASE_URL`, los tests críticos se marcarán como `skipped`.

## Migraciones
Crear nueva migración (ejemplo):
```bash
docker-compose exec api alembic revision -m "add payments table"
make migrate
```

## Estructura Relevante
```
backend/
  app/
    models/            # ORM
    core/              # config, db, redis, seguridad, logging
    routers/           # endpoints (solo health por ahora)
  alembic/             # migraciones
  tests/               # tests y fixtures
docs/adr               # ADRs
```

## Convenciones Anti Doble-Booking
- Redis lock previo a insertar pre-reserva: `lock:acc:{id}:{checkin}:{checkout}` TTL 1800s.
- Constraint Postgres aplica a estados `pre_reserved` y `confirmed`.
- Fechas half-open: [check_in, check_out) → checkout mismo día = permitido.

## Estándares de Observabilidad (Target)
- Latencia P95 texto < 3s, audio < 15s.
- Error rate < 1%.
- `/healthz` incluirá (WIP): DB, Redis, edad sync iCal, reachability WA/MP.

## ADRs
- Ver índice en `docs/adr/README.md`.

## Principios
- SIN feature creep.
- TODO test crítico (locks, overlap, firmas) antes de ampliar superficie.
- Refactors sólo tras cubrir funcionalidad prioritaria.

---
_Archivo generado automáticamente para consolidar el estado inicial._
