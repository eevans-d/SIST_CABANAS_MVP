"""Initial schema with anti double-booking constraint

Revision ID: 001
Revises:
Create Date: 2025-09-24
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Skip extensions for SQLite (tests)
    if op.get_bind().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.create_table(
        "accommodations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "uuid",
            (
                postgresql.UUID(as_uuid=True)
                if op.get_bind().dialect.name == "postgresql"
                else sa.String(36)
            ),
            nullable=False,
            unique=True,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("weekend_multiplier", sa.Numeric(4, 2), server_default="1.2", nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("amenities", postgresql.JSON(astext_type=sa.Text()), server_default="{}"),
        sa.Column("photos", postgresql.JSON(astext_type=sa.Text()), server_default="[]"),
        sa.Column("location", postgresql.JSON(astext_type=sa.Text()), server_default="{}"),
        sa.Column("policies", postgresql.JSON(astext_type=sa.Text()), server_default="{}"),
        sa.Column("ical_export_token", sa.String(length=64), nullable=False, unique=True),
        sa.Column("ical_import_urls", postgresql.JSON(astext_type=sa.Text()), server_default="{}"),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_accommodation_active", "accommodations", ["active"])
    op.create_index("idx_accommodation_type", "accommodations", ["type"])
    op.create_index("ix_accommodations_name", "accommodations", ["name"])

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("uuid", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("code", sa.String(length=20), nullable=False, unique=True),
        sa.Column(
            "accommodation_id",
            sa.Integer(),
            sa.ForeignKey("accommodations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("check_in", sa.Date(), nullable=False),
        sa.Column("check_out", sa.Date(), nullable=False),
        sa.Column("guest_name", sa.String(length=100), nullable=False),
        sa.Column("guest_phone", sa.String(length=20), nullable=False),
        sa.Column("guest_email", sa.String(length=100)),
        sa.Column("guest_document", sa.String(length=20)),
        sa.Column("guests_count", sa.Integer(), nullable=False),
        sa.Column("nights", sa.Integer(), nullable=False),
        sa.Column("base_price_per_night", sa.Numeric(12, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("deposit_percentage", sa.Integer(), server_default="30", nullable=False),
        sa.Column("deposit_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(12, 2), server_default="0", nullable=False),
        sa.Column(
            "reservation_status",
            sa.String(length=20),
            server_default="pre_reserved",
            nullable=False,
        ),
        sa.Column("payment_status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("channel_source", sa.String(length=50)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("extended_once", sa.Boolean(), server_default="false"),
        sa.Column("lock_value", sa.String(length=36)),
        sa.Column("confirmed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("internal_notes", sa.Text()),
        sa.Column("special_requests", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("check_in < check_out", name="ck_reservation_dates"),
        sa.CheckConstraint("guests_count > 0", name="ck_guests_positive"),
        sa.CheckConstraint("total_price >= 0", name="ck_total_price_positive"),
    )
    op.create_index(
        "idx_reservation_dates", "reservations", ["accommodation_id", "check_in", "check_out"]
    )
    op.create_index("idx_reservation_expires", "reservations", ["expires_at"])
    op.create_index("idx_reservation_guest_phone", "reservations", ["guest_phone"])
    op.create_index("ix_reservations_code", "reservations", ["code"])

    op.execute(
        """
        ALTER TABLE reservations
        ADD COLUMN period daterange
        GENERATED ALWAYS AS (daterange(check_in, check_out, '[)')) STORED
    """
    )
    op.execute(
        """
        ALTER TABLE reservations
        ADD CONSTRAINT no_overlap_reservations
        EXCLUDE USING gist (
            accommodation_id WITH =,
            period WITH &&
        ) WHERE (reservation_status IN ('pre_reserved','confirmed'))
    """
    )


def downgrade() -> None:
    op.drop_constraint("no_overlap_reservations", "reservations", type_="exclusion")
    op.drop_table("reservations")
    op.drop_table("accommodations")
