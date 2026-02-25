"""create company_nav_configs table

Revision ID: c7d8e9f0a1b2
Revises: bed91f5969aa
Create Date: 2026-02-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, None] = "bed91f5969aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_nav_configs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "hidden_nav_items",
            JSONB,
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "company_id",
            name="uq_nav_config_company",
        ),
    )
    op.create_index(
        "ix_company_nav_configs_company_id",
        "company_nav_configs",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_company_nav_configs_company_id",
        table_name="company_nav_configs",
    )
    op.drop_table("company_nav_configs")
