"""create_resellers_table

Revision ID: a5d6e7f8g9h0
Revises: z4c5d6e7f8g9
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a5d6e7f8g9h0"
down_revision: Union[str, None] = "z4c5d6e7f8g9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "resellers",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("microsoft_id", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("tax_id", sa.String(100), nullable=True),
        sa.Column("commission_pct", sa.Integer, nullable=False, server_default="20"),
        sa.Column("min_payout_cents", sa.Integer, nullable=False, server_default="5000"),
        sa.Column("referral_code", sa.String(20), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )
    op.create_index("ix_resellers_email", "resellers", ["email"])
    op.create_index("ix_resellers_google_id", "resellers", ["google_id"])
    op.create_index("ix_resellers_microsoft_id", "resellers", ["microsoft_id"])
    op.create_index("ix_resellers_referral_code", "resellers", ["referral_code"])


def downgrade() -> None:
    op.drop_index("ix_resellers_referral_code", table_name="resellers")
    op.drop_index("ix_resellers_microsoft_id", table_name="resellers")
    op.drop_index("ix_resellers_google_id", table_name="resellers")
    op.drop_index("ix_resellers_email", table_name="resellers")
    op.drop_table("resellers")
