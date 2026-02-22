"""add email_verified_at to users

Revision ID: t7d8e9f0g1h2
Revises: s6c7d8e9f0g1
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "t7d8e9f0g1h2"
down_revision = "s6c7d8e9f0g1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "email_verified_at")
