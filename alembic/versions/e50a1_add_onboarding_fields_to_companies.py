"""add onboarding fields to companies

Revision ID: e50a1
Revises: 77fd61a8927e
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa

revision = "e50a1"
down_revision = "77fd61a8927e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("companies", sa.Column("sector", sa.String(50), nullable=True))
    op.add_column(
        "companies",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("companies", "onboarding_completed_at")
    op.drop_column("companies", "sector")
