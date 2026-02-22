"""add budget enforcement and per-item budget fields

Revision ID: r5b6c7d8e9f0
Revises: q4a5b6c7d8e9
Create Date: 2026-02-21 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "r5b6c7d8e9f0"
down_revision = "q4a5b6c7d8e9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "departments",
        sa.Column(
            "budget_enforcement_enabled",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    op.add_column(
        "equipment_profile_items",
        sa.Column("budget_cents", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("equipment_profile_items", "budget_cents")
    op.drop_column("departments", "budget_enforcement_enabled")
