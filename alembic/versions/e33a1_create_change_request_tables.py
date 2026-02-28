"""create change_requests and change_events tables

Revision ID: e33a1
Revises: e40b1
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "e33a1"
down_revision: Union[str, None] = "e40b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "change_requests",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(20), nullable=False),
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="draft"
        ),
        sa.Column("business_justification", sa.Text(), nullable=True),
        sa.Column("risk_assessment", sa.Text(), nullable=True),
        sa.Column("rollback_plan", sa.Text(), nullable=True),
        sa.Column(
            "planned_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("requested_by", sa.String(26), nullable=False),
        sa.Column("assigned_to", sa.String(26), nullable=True),
        sa.Column("approved_by", sa.String(26), nullable=True),
        sa.Column(
            "approved_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("rejected_by", sa.String(26), nullable=True),
        sa.Column(
            "rejected_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "started_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "implemented_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("implementation_notes", sa.Text(), nullable=True),
        sa.Column(
            "rolled_back_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("rollback_reason", sa.Text(), nullable=True),
        sa.Column(
            "closed_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_change_requests_company_id",
        "change_requests",
        ["company_id"],
    )
    op.create_index(
        "ix_change_requests_company_status",
        "change_requests",
        ["company_id", "status"],
    )
    op.create_index(
        "ix_change_requests_company_type",
        "change_requests",
        ["company_id", "change_type"],
    )
    op.create_index(
        "ix_change_requests_planned_date",
        "change_requests",
        ["planned_date"],
    )

    op.create_table(
        "change_events",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "change_request_id",
            sa.String(26),
            sa.ForeignKey("change_requests.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column("metadata_json", JSON, nullable=True),
    )
    op.create_index(
        "ix_change_events_change_request_id",
        "change_events",
        ["change_request_id"],
    )


def downgrade() -> None:
    op.drop_table("change_events")
    op.drop_table("change_requests")
