"""create purchase_order_items table

Revision ID: k6l7m8n9o0p1
Revises: j5k6l7m8n9o0
Create Date: 2026-02-18 18:02:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "k6l7m8n9o0p1"
down_revision = "j5k6l7m8n9o0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "purchase_order_id",
            sa.String(26),
            sa.ForeignKey(
                "purchase_orders.id", ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "description", sa.String(500), nullable=False,
        ),
        sa.Column(
            "asset_type", sa.String(30), nullable=True,
        ),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "unit_cost_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "total_cost_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "received_quantity",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column("received_at", sa.DateTime, nullable=True),
        sa.Column(
            "linked_asset_id", sa.String(26), nullable=True,
        ),
        sa.Column("notes", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("purchase_order_items")
