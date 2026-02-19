"""create company_classification_configs table

Revision ID: h3c4d5e6f7a8
Revises: g2a0b0c0d0e0
Create Date: 2026-02-18 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "h3c4d5e6f7a8"
down_revision = "g2a0b0c0d0e0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "company_classification_configs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column(
            "confidence_threshold", sa.Float, nullable=False, server_default="0.7"
        ),
        sa.Column("prompt_template", sa.Text, nullable=True),
        sa.Column(
            "timeout_seconds", sa.Integer, nullable=False, server_default="10"
        ),
        sa.Column(
            "created_at", sa.DateTime, server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "company_id", name="uq_classification_config_company",
        ),
    )


def downgrade() -> None:
    op.drop_table("company_classification_configs")
