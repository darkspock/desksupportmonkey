"""Add subtype column to service_requests.

Revision ID: f1a0b0c0d0e0
Revises: e6f7a8b9c0d1
Create Date: 2026-02-18 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "f1a0b0c0d0e0"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("subtype", sa.String(50), nullable=True),
    )
    op.create_index(
        "ix_service_requests_company_subtype",
        "service_requests",
        ["company_id", "subtype"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_requests_company_subtype", table_name="service_requests")
    op.drop_column("service_requests", "subtype")
