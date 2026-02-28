"""create sla_escalation_config table

Revision ID: e38c1
Revises: e38b1
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e38c1"
down_revision: Union[str, None] = "e38b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_sla_escalation_configs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("company_id", name="uq_sla_escalation_config_company"),
    )
    op.create_index(
        "ix_sla_escalation_config_company",
        "company_sla_escalation_configs",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sla_escalation_config_company", table_name="company_sla_escalation_configs")
    op.drop_table("company_sla_escalation_configs")
