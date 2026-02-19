"""Add manager_user_id to departments.

Revision ID: c4d5e6f7a8b9
Revises: b3f7a8c9d1e2
Create Date: 2026-02-17 18:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b3f7a8c9d1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "departments",
        sa.Column(
            "manager_user_id",
            sa.String(26),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("departments", "manager_user_id")
