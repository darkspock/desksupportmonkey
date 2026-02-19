"""add purchase_cost_cents to assets

Revision ID: o0p1q2r3s4t5
Revises: n9o0p1q2r3s4
Create Date: 2026-02-18 18:06:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "o0p1q2r3s4t5"
down_revision = "n9o0p1q2r3s4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column(
            "purchase_cost_cents",
            sa.Integer,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("assets", "purchase_cost_cents")
