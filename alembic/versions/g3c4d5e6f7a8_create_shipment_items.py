"""create shipment_items table

Revision ID: g3c4d5e6f7a8
Revises: g2b3c4d5e6f7
Create Date: 2026-02-18 18:02:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "g3c4d5e6f7a8"
down_revision = "g2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipment_items",
        sa.Column(
            "id", sa.String(26), primary_key=True,
        ),
        sa.Column(
            "shipment_id",
            sa.String(26),
            sa.ForeignKey(
                "shipments.id", ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "asset_id",
            sa.String(26),
            sa.ForeignKey("assets.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "notes", sa.Text, nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("shipment_items")
