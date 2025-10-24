# DB Constraints y Reglas de Integridad

Este documento resume constraints, índices y reglas anti doble-booking implementadas en la base de datos (PostgreSQL 16; SQLite para tests unitarios).

## Tablas principales

### accommodations
- Primary Key: id
- Unique: uuid, ical_export_token
- Índices:
  - ix_accommodations_name (automático por `index=True` en ORM)
  - idx_accommodation_type (migración 001)
  - idx_accommodation_active (migración 001)

### reservations
- Primary Key: id
- Unique: uuid, code
- Foreign Keys:
  - accommodation_id → accommodations.id ON DELETE CASCADE
- Check constraints (migración 001 / ORM):
  - ck_reservation_dates: check_in < check_out
  - ck_guests_positive: guests_count > 0
  - ck_total_price_positive: total_price >= 0
- Índices (migración 001 y ORM):
  - idx_reservation_dates (accommodation_id, check_in, check_out)
  - idx_reservation_expires (expires_at)
  - idx_reservation_guest_phone (guest_phone)
  - ix_reservations_code (code)

#### Columna generada + Exclusion Constraint anti-overlap (CRÍTICO)
- Columna generada:
  - period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED
- Exclusion constraint (filtrado por estado):
```
ALTER TABLE reservations
ADD CONSTRAINT no_overlap_reservations
EXCLUDE USING gist (
    accommodation_id WITH =,
    period WITH &&
) WHERE (reservation_status IN ('pre_reserved','confirmed'));
```
- Requisitos previos: `CREATE EXTENSION IF NOT EXISTS btree_gist` (migración 001)
- Efecto: evita solapamientos en el mismo alojamiento para reservas activas (pre_reserved/confirmed). Insert/UPDATE concurrentes conflictivos generan IntegrityError.

### payments
- Primary Key: id
- Unique: uuid, external_payment_id (uq_payment_external_id)
- Foreign Keys:
  - reservation_id → reservations.id ON DELETE CASCADE (nullable desde migración 003)
- Índices:
  - idx_payment_reservation
  - idx_payment_external_ref

### idempotency_keys
- Primary Key: id (UUID)
- Unique: key
- Índices:
  - idx_idempotency_key_endpoint (key, endpoint)
  - idx_idempotency_expires (expires_at)
  - ix_idempotency_keys_endpoint
  - ix_idempotency_keys_key (unique)

## Índices de Performance (002_perf_indexes)
- idx_reservation_expires_prereserved (partial):
  - Columnas: expires_at
  - WHERE reservation_status = 'pre_reserved'
  - Concurrente: TRUE
  - Uso: job de limpieza de pre-reservas expiradas
- idx_reservation_status_dates (composite):
  - Columnas: reservation_status, check_in, check_out
  - Concurrente: TRUE
  - Uso: filtros frecuentes del dashboard admin

## Notas de compatibilidad SQLite (tests)
- Las extensiones y exclusion constraints se omiten en SQLite.
- La lógica anti-overlap sigue cubierta por el constraint en Postgres y por locks Redis a nivel aplicación.
- Tests de overlap que requieren Postgres real están marcados en `backend/tests/test_double_booking.py` y `test_constraint_validation.py` (ver guía QA).
