"""add_reseller_clients_table

Revision ID: c7f8g9h0i1j2
Revises: b6e7f8g9h0i1
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c7f8g9h0i1j2"
down_revision: Union[str, None] = "b6e7f8g9h0i1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reseller_clients",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("reseller_id", sa.String(26), sa.ForeignKey("resellers.id"), nullable=False),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False, unique=True),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("is_demo", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("demo_expires_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reseller_clients_reseller_id", "reseller_clients", ["reseller_id"])
    op.create_index(
        "ix_reseller_clients_demo_expires",
        "reseller_clients",
        ["demo_expires_at"],
        postgresql_where=sa.text("is_demo = true"),
    )


def downgrade() -> None:
    op.drop_index("ix_reseller_clients_demo_expires", table_name="reseller_clients")
    op.drop_index("ix_reseller_clients_reseller_id", table_name="reseller_clients")
    op.drop_table("reseller_clients")
