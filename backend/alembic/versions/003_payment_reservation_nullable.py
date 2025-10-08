"""make payment.reservation_id nullable

Revision ID: 003_payment_reservation_nullable
Revises: 002_create_payments
Create Date: 2025-09-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "003_payment_reservation_nullable"
down_revision = "002_create_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # En algunos entornos ya podría ser nullable (si migración manual), uso batch alter para seguridad
    with op.batch_alter_table("payments") as batch_op:
        batch_op.alter_column(
            "reservation_id", existing_type=sa.Integer(), existing_nullable=False, nullable=True
        )


def downgrade() -> None:
    # Revertir a NOT NULL (si datos huérfanos existen fallará, decisión consciente)
    with op.batch_alter_table("payments") as batch_op:
        batch_op.alter_column(
            "reservation_id", existing_type=sa.Integer(), existing_nullable=True, nullable=False
        )
