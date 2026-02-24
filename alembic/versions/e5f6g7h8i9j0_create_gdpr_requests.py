"""create_gdpr_requests

Revision ID: e5f6g7h8i9j0
Revises: d5e6f7g8h9i0
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e5f6g7h8i9j0"
down_revision: Union[str, None] = "d5e6f7g8h9i0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gdpr_requests",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("target_user_id", sa.String(26), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("target_user_email", sa.String(255), nullable=False),
        sa.Column("requested_by", sa.String(26), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.String(500), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_gdpr_requests_company", "gdpr_requests", ["company_id"])
    op.create_index("ix_gdpr_requests_company_status", "gdpr_requests", ["company_id", "status"])
    op.create_index("ix_gdpr_requests_target", "gdpr_requests", ["target_user_id"])


def downgrade() -> None:
    op.drop_table("gdpr_requests")
