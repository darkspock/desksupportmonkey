"""add shipment logistics fields

Revision ID: q4a5b6c7d8e9
Revises: p3c4d5e6f7g8
Create Date: 2026-02-20 10:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "q4a5b6c7d8e9"
down_revision = "p3c4d5e6f7g8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "shipments",
        sa.Column("service_level", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "shipments",
        sa.Column("items_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "shipments",
        sa.Column("internal_notes", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("shipments", "internal_notes")
    op.drop_column("shipments", "items_description")
    op.drop_column("shipments", "service_level")
