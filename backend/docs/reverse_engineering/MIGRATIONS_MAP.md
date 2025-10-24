# Mapa de Migraciones (Alembic)

Ubicación: `backend/alembic/versions`

1) 001_initial_schema.py (2025-09-24)
   - Tablas: accommodations, reservations
   - Índices: accommodations (name, type, active), reservations (accommodation_id+fechas, expires, guest_phone, code)
   - Checks: ck_reservation_dates, ck_guests_positive, ck_total_price_positive
   - Extensiones (Postgres): btree_gist, uuid-ossp
   - Columna generada: reservations.period (daterange)
   - Constraint EXCLUDE USING gist: no_overlap_reservations (filtrado por status pre_reserved/confirmed)

2) 002_create_payments_table.py (2025-09-25)
   - Tabla: payments
   - Índices: idx_payment_reservation, idx_payment_external_ref
   - Unique: uq_payment_external_id (external_payment_id)

3) 003_payment_reservation_nullable.py (2025-09-26)
   - Alter: payments.reservation_id -> nullable (batch_alter)

4) 004_add_last_ical_sync_at.py
   - Columna: accommodations.last_ical_sync_at (DateTime tz)

5) 005_idempotency_keys.py (2025-01-10)
   - Tabla: idempotency_keys
   - Índices: idx_idempotency_key_endpoint, idx_idempotency_expires, ix_idempotency_keys_endpoint, ix_idempotency_keys_key (unique)

6) 002_perf_indexes.py (2025-10-14)
   - Índices concurrentes:
     - idx_reservation_expires_prereserved (partial WHERE reservation_status='pre_reserved')
     - idx_reservation_status_dates (reservation_status, check_in, check_out)

Notas:
- Orden lógico respeta `down_revision` en cada archivo (ver cabeceras).
- Para entornos SQLite, extensiones/EXCLUDE se omiten automáticamente.
