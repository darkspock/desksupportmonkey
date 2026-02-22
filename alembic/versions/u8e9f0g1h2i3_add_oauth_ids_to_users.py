"""add google_id and microsoft_id to users

Revision ID: u8e9f0g1h2i3
Revises: t7d8e9f0g1h2
Create Date: 2026-02-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "u8e9f0g1h2i3"
down_revision = "t7d8e9f0g1h2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_id", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("microsoft_id", sa.String(255), nullable=True))
    op.create_unique_constraint("uq_users_google_id", "users", ["google_id"])
    op.create_unique_constraint("uq_users_microsoft_id", "users", ["microsoft_id"])
    op.create_index("ix_users_google_id", "users", ["google_id"])
    op.create_index("ix_users_microsoft_id", "users", ["microsoft_id"])


def downgrade() -> None:
    op.drop_index("ix_users_microsoft_id", table_name="users")
    op.drop_index("ix_users_google_id", table_name="users")
    op.drop_constraint("uq_users_microsoft_id", "users", type_="unique")
    op.drop_constraint("uq_users_google_id", "users", type_="unique")
    op.drop_column("users", "microsoft_id")
    op.drop_column("users", "google_id")
