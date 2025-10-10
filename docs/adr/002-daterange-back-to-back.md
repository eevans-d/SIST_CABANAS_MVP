# ADR-0001: Rango de fechas half-open [) para reservas (Back-to-back)

Fecha: 2025-09-28

Estado: Aprobado

## Contexto

El MVP requiere prevenir doble-booking a nivel de base de datos usando PostgreSQL 16 con `btree_gist` y una restricción de exclusión por `daterange`.
La guía inicial sugería un rango cerrado `[]`, pero en hotelería es práctica estándar permitir reservas back-to-back (check-out el mismo día del check-in siguiente).

## Decisión

Se utiliza una columna generada `period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED` y una restricción:

```
CREATE EXTENSION IF NOT EXISTS btree_gist;
ALTER TABLE reservations
  ADD COLUMN period daterange GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED,
  ADD CONSTRAINT no_overlap_reservations
    EXCLUDE USING gist (accommodation_id WITH =, period WITH &&)
    WHERE (reservation_status IN ('pre_reserved','confirmed'));
```

Esto adopta el rango half-open `[)` (incluye check_in, excluye check_out), permitiendo back-to-back de forma segura.

## Consecuencias

- Dos reservas consecutivas donde A.check_out == B.check_in no se consideran solapadas.
- La lógica de negocio debe tratar `check_out` como no disponible para pernocte; la noche termina en `check_out`.
- Las pruebas de concurrencia y de borde deben reflejar este contrato. Los tests existentes ya contemplan este comportamiento.

## Alternativas consideradas

- `[]` (cerrado) bloquea el día de salida e impide back-to-back, reduciendo ocupación; descartado.
- Validación sólo en aplicación sin constraint: mayor riesgo en concurrencia; descartado.

## Estado de implementación

- Alembic `001_initial_schema.py` ya implementa `[)`.
- Tests validan casos edge (ver `tests/test_constraint_validation.py`).
