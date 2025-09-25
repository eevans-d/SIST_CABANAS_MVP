"""create payments table

Revision ID: 002_create_payments
Revises: 001_initial_schema
Create Date: 2025-09-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_create_payments'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reservation_id', sa.Integer(), sa.ForeignKey('reservations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False, server_default='mercadopago'),
        sa.Column('external_payment_id', sa.String(length=80), nullable=False),
        sa.Column('external_reference', sa.String(length=80), nullable=True),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='pending'),
        sa.Column('amount', sa.Numeric(12,2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='ARS'),
        sa.Column('event_first_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_last_received_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('events_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('idx_payment_reservation', 'payments', ['reservation_id'])
    op.create_index('idx_payment_external_ref', 'payments', ['external_reference'])
    op.create_unique_constraint('uq_payment_external_id', 'payments', ['external_payment_id'])


def downgrade() -> None:
    op.drop_constraint('uq_payment_external_id', 'payments', type_='unique')
    op.drop_index('idx_payment_external_ref', table_name='payments')
    op.drop_index('idx_payment_reservation', table_name='payments')
    op.drop_table('payments')
