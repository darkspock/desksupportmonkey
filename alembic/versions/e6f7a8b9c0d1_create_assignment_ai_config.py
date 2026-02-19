"""create company_assignment_ai_configs table

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-02-17 23:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_assignment_ai_configs",
        sa.Column(
            "id", sa.String(26), primary_key=True,
        ),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "provider", sa.String(20), nullable=False,
        ),
        sa.Column(
            "prompt_template", sa.Text, nullable=False,
        ),
        sa.Column(
            "model", sa.String(100), nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=True,
        ),
        sa.UniqueConstraint(
            "company_id",
            name="uq_assignment_ai_config_company",
        ),
    )


def downgrade() -> None:
    op.drop_table("company_assignment_ai_configs")
