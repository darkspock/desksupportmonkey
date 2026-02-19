"""create maintenance plans table

Revision ID: p2b3c4d5e6f7
Revises: p1a2b3c4d5e6
Create Date: 2026-02-18 20:11:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "p2b3c4d5e6f7"
down_revision = "p1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_plans",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "template_id",
            sa.String(26),
            sa.ForeignKey("maintenance_templates.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "asset_id",
            sa.String(26),
            sa.ForeignKey("assets.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("next_due_at", sa.DateTime, nullable=False, index=True),
        sa.Column("last_generated_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_index(
        "ix_maintenance_plans_template_asset_active",
        "maintenance_plans",
        ["template_id", "asset_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_plans_template_asset_active",
        table_name="maintenance_plans",
    )
    op.drop_table("maintenance_plans")
