"""add reseller password and pending status fields

Revision ID: 01kjxf5qgx9c
Revises: 540ee94fe733
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "01kjxf5qgx9c"
down_revision = "540ee94fe733"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resellers", sa.Column("password_hash", sa.String(255), nullable=True))
    op.add_column("resellers", sa.Column("reset_token", sa.String(255), nullable=True))
    op.add_column(
        "resellers",
        sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("resellers", "reset_token_expires_at")
    op.drop_column("resellers", "reset_token")
    op.drop_column("resellers", "password_hash")
