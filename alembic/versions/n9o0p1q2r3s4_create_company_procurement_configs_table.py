"""create company_procurement_configs table

Revision ID: n9o0p1q2r3s4
Revises: m8n9o0p1q2r3
Create Date: 2026-02-18 18:05:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "n9o0p1q2r3s4"
down_revision = "m8n9o0p1q2r3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_procurement_configs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "enforcement_mode",
            sa.String(10),
            nullable=False,
            server_default="warn",
        ),
        sa.Column(
            "approval_threshold_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "po_number_prefix",
            sa.String(10),
            nullable=False,
            server_default="PO",
        ),
        sa.Column(
            "fiscal_year_start_month",
            sa.Integer,
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="USD",
        ),
        sa.Column(
            "auto_create_assets",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("company_procurement_configs")
