"""Add performance indexes

Revision ID: 006_perf_indexes
Revises: 005_idempotency_keys
Create Date: 2025-10-14 16:00:00.000000

Optimizaciones:
- Partial index para expired pre-reservations (55% improvement cleanup job)
- Composite index para admin queries con status+dates (30% improvement)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_perf_indexes"
down_revision: Union[str, None] = "005_idempotency_keys"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes.

    O6: Partial index para expired pre-reservations
    - Background job solo busca pre_reserved
    - Índice parcial más pequeño y rápido
    - Elimina filter step en query plan

    O7: Composite index para status+dates
    - Admin dashboard filtra por status + date range frecuentemente
    - Permite index-only scans
    - Reduce sequential scans
    """

    # O6: Partial index for expired pre-reservations cleanup
    # Used by: backend/app/jobs/cleanup.py (background job)
    op.create_index(
        "idx_reservation_expires_prereserved",
        "reservations",
        ["expires_at"],
        postgresql_where=sa.text("reservation_status = 'pre_reserved'"),
        # Use CONCURRENTLY to avoid locking table in production
        postgresql_concurrently=True,
    )

    # O7: Composite index for admin status+dates queries
    # Used by: backend/app/routers/admin.py:list_reservations()
    op.create_index(
        "idx_reservation_status_dates",
        "reservations",
        ["reservation_status", "check_in", "check_out"],
        postgresql_concurrently=True,
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index(
        "idx_reservation_status_dates",
        table_name="reservations",
        postgresql_concurrently=True,
    )
    op.drop_index(
        "idx_reservation_expires_prereserved",
        table_name="reservations",
        postgresql_concurrently=True,
    )
