"""create sla tables

Revision ID: a4c5d6e7f8g9
Revises: z3b4c5d6e7f8
Create Date: 2026-02-23 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a4c5d6e7f8g9"
down_revision: Union[str, None] = "z3b4c5d6e7f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sla_policies",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("request_type", sa.String(30), nullable=True),
        sa.Column("response_time_hours", sa.Float, nullable=False),
        sa.Column("resolution_time_hours", sa.Float, nullable=False),
        sa.Column(
            "warning_threshold_pct",
            sa.Integer,
            nullable=False,
            server_default="75",
        ),
        sa.Column(
            "escalate_on_breach",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_sla_policies_company_active",
        "sla_policies",
        ["company_id", "is_active"],
    )
    op.create_index(
        "ix_sla_policies_company_priority_type_active",
        "sla_policies",
        ["company_id", "priority", "request_type", "is_active"],
    )
    op.create_unique_constraint(
        "uq_sla_policies_company_priority_type",
        "sla_policies",
        ["company_id", "priority", "request_type"],
    )

    op.create_table(
        "sla_breach_records",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("request_id", sa.String(26), nullable=False),
        sa.Column("policy_id", sa.String(26), nullable=False),
        sa.Column("breach_type", sa.String(30), nullable=False),
        sa.Column("target_hours", sa.Float, nullable=False),
        sa.Column("actual_hours", sa.Float, nullable=False),
        sa.Column(
            "escalated",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_sla_breaches_company_created",
        "sla_breach_records",
        ["company_id", "created_at"],
    )
    op.create_index(
        "ix_sla_breaches_request",
        "sla_breach_records",
        ["request_id"],
    )
    op.create_unique_constraint(
        "uq_sla_breaches_request_type",
        "sla_breach_records",
        ["request_id", "breach_type"],
    )


def downgrade() -> None:
    op.drop_table("sla_breach_records")
    op.drop_table("sla_policies")
