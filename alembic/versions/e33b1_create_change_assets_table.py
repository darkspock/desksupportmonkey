"""create change_assets table

Revision ID: e33b1
Revises: e33a1
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e33b1"
down_revision: Union[str, None] = "e33a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "change_assets",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "change_request_id",
            sa.String(26),
            sa.ForeignKey("change_requests.id"),
            nullable=False,
        ),
        sa.Column("asset_id", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "change_request_id",
            "asset_id",
            name="uq_change_assets_change_asset",
        ),
    )
    op.create_index(
        "ix_change_assets_change_request_id",
        "change_assets",
        ["change_request_id"],
    )
    op.create_index(
        "ix_change_assets_asset_id",
        "change_assets",
        ["asset_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_change_assets_asset_id", table_name="change_assets")
    op.drop_index(
        "ix_change_assets_change_request_id", table_name="change_assets"
    )
    op.drop_table("change_assets")
