"""create purchase_order_requests table

Revision ID: l7m8n9o0p1q2
Revises: k6l7m8n9o0p1
Create Date: 2026-02-18 18:03:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "l7m8n9o0p1q2"
down_revision = "k6l7m8n9o0p1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_order_requests",
        sa.Column(
            "purchase_order_id",
            sa.String(26),
            sa.ForeignKey(
                "purchase_orders.id", ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            sa.String(26),
            sa.ForeignKey("service_requests.id"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "purchase_order_id", "request_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("purchase_order_requests")
