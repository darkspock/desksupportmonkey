"""create_risk_tables

Revision ID: y2a3b4c5d6e7
Revises: x1c2d3e4f5g6
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "y2a3b4c5d6e7"
down_revision: Union[str, None] = "x1c2d3e4f5g6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. risks
    op.create_table(
        "risks",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("likelihood", sa.Integer(), nullable=True),
        sa.Column("impact", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(10), nullable=True),
        sa.Column("treatment", sa.String(20), nullable=True),
        sa.Column("review_cadence", sa.String(20), nullable=True),
        sa.Column(
            "next_review_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("owner_id", sa.String(26), nullable=True),
        sa.Column("created_by", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_risks_company_status", "risks", ["company_id", "status"]
    )
    op.create_index(
        "ix_risks_company_level", "risks", ["company_id", "risk_level"]
    )
    op.create_index(
        "ix_risks_company_category", "risks", ["company_id", "category"]
    )
    op.create_index("ix_risks_next_review", "risks", ["next_review_at"])

    # 2. mitigation_plans
    op.create_table(
        "mitigation_plans",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("risk_id", sa.String(26), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("owner_id", sa.String(26), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_mitigation_plans_risk_id", "mitigation_plans", ["risk_id"]
    )

    # 3. risk_links
    op.create_table(
        "risk_links",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("risk_id", sa.String(26), nullable=False),
        sa.Column("link_type", sa.String(20), nullable=False),
        sa.Column("link_id", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index("ix_risk_links_risk_id", "risk_links", ["risk_id"])
    op.create_unique_constraint(
        "uq_risk_links_risk_type_entity",
        "risk_links",
        ["risk_id", "link_type", "link_id"],
    )

    # 4. risk_history
    op.create_table(
        "risk_history",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("risk_id", sa.String(26), nullable=False),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(26), nullable=False),
        sa.Column("metadata_json", JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index("ix_risk_history_risk_id", "risk_history", ["risk_id"])


def downgrade() -> None:
    op.drop_table("risk_history")
    op.drop_table("risk_links")
    op.drop_table("mitigation_plans")
    op.drop_table("risks")
