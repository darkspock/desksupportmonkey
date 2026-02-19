"""Add priority_weight column to departments.

Revision ID: g2a0b0c0d0e0
Revises: g1a2b3c4d5e6
Create Date: 2026-02-18 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "g2a0b0c0d0e0"
down_revision = "g1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "departments",
        sa.Column("priority_weight", sa.Integer, nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("departments", "priority_weight")
