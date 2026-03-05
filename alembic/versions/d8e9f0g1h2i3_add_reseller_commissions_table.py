"""add_reseller_commissions_table

Revision ID: d8e9f0g1h2i3
Revises: c7f8g9h0i1j2
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d8e9f0g1h2i3"
down_revision: Union[str, None] = "c7f8g9h0i1j2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reseller_commissions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("reseller_id", sa.String(26), sa.ForeignKey("resellers.id"), nullable=False),
        sa.Column("reseller_client_id", sa.String(26), sa.ForeignKey("reseller_clients.id"), nullable=False),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("payment_amount_cents", sa.Integer, nullable=False),
        sa.Column("commission_pct", sa.Integer, nullable=False),
        sa.Column("commission_amount_cents", sa.Integer, nullable=False),
        sa.Column("stripe_invoice_id", sa.String(255), nullable=False),
        sa.Column("period_start", sa.DateTime, nullable=True),
        sa.Column("period_end", sa.DateTime, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reseller_commissions_reseller_id", "reseller_commissions", ["reseller_id"])
    op.create_index("ix_reseller_commissions_company_id", "reseller_commissions", ["company_id"])
    op.create_index("ix_reseller_commissions_stripe_invoice_id", "reseller_commissions", ["stripe_invoice_id"])
    op.create_index("ix_reseller_commissions_status", "reseller_commissions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reseller_commissions_status", table_name="reseller_commissions")
    op.drop_index("ix_reseller_commissions_stripe_invoice_id", table_name="reseller_commissions")
    op.drop_index("ix_reseller_commissions_company_id", table_name="reseller_commissions")
    op.drop_index("ix_reseller_commissions_reseller_id", table_name="reseller_commissions")
    op.drop_table("reseller_commissions")
