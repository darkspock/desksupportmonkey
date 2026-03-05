"""add reseller payouts table

Revision ID: e9f0g1h2i3j4
Revises: d8e9f0g1h2i3
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9f0g1h2i3j4"
down_revision = "d8e9f0g1h2i3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reseller_payouts",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("reseller_id", sa.String(26), sa.ForeignKey("resellers.id"), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="requested"),
        sa.Column("requested_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("processed_by", sa.String(26), nullable=True),
        sa.Column("payment_reference", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_reseller_payouts_reseller_id", "reseller_payouts", ["reseller_id"])
    op.create_index("ix_reseller_payouts_status", "reseller_payouts", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reseller_payouts_status", table_name="reseller_payouts")
    op.drop_index("ix_reseller_payouts_reseller_id", table_name="reseller_payouts")
    op.drop_table("reseller_payouts")
