"""create ci_relationships table

Revision ID: e38b1
Revises: e38a1
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e38b1"
down_revision: Union[str, None] = "e38a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ci_relationships",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("source_asset_id", sa.String(26), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("target_asset_id", sa.String(26), sa.ForeignKey("assets.id"), nullable=False),
        sa.Column("relationship_type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_by", sa.String(26), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "source_asset_id", "target_asset_id", "relationship_type",
            name="uq_ci_rel_source_target_type",
        ),
    )
    op.create_index("ix_ci_relationships_company_id", "ci_relationships", ["company_id"])
    op.create_index("ix_ci_relationships_source", "ci_relationships", ["source_asset_id"])
    op.create_index("ix_ci_relationships_target", "ci_relationships", ["target_asset_id"])


def downgrade() -> None:
    op.drop_index("ix_ci_relationships_target", table_name="ci_relationships")
    op.drop_index("ix_ci_relationships_source", table_name="ci_relationships")
    op.drop_index("ix_ci_relationships_company_id", table_name="ci_relationships")
    op.drop_table("ci_relationships")
