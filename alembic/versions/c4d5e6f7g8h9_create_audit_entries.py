"""create_audit_entries

Revision ID: c4d5e6f7g8h9
Revises: b5c6d7e8f9g0
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "c4d5e6f7g8h9"
down_revision: Union[str, None] = "b5c6d7e8f9g0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_entries",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=True),
        sa.Column("actor_id", sa.String(26), nullable=True),
        sa.Column(
            "actor_email",
            sa.String(255),
            nullable=False,
            server_default="",
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.String(26), nullable=True),
        sa.Column("http_method", sa.String(10), nullable=False),
        sa.Column("http_path", sa.String(500), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_data", JSON(), nullable=True),
        sa.Column("response_status", sa.Integer(), nullable=False),
        sa.Column("changes", JSON(), nullable=True),
        sa.Column("hash", sa.String(64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_audit_entries_company_created",
        "audit_entries",
        ["company_id", "created_at"],
    )
    op.create_index(
        "ix_audit_entries_company_actor_created",
        "audit_entries",
        ["company_id", "actor_id", "created_at"],
    )
    op.create_index(
        "ix_audit_entries_company_resource",
        "audit_entries",
        ["company_id", "resource_type", "resource_id"],
    )


def downgrade() -> None:
    op.drop_table("audit_entries")
