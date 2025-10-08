from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "004_add_last_ical_sync_at"
down_revision = "003_payment_reservation_nullable"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "accommodations", sa.Column("last_ical_sync_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("accommodations", "last_ical_sync_at")
