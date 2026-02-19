"""create maintenance templates and checklist items

Revision ID: p1a2b3c4d5e6
Revises: g3c4d5e6f7a8
Create Date: 2026-02-18 20:10:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "p1a2b3c4d5e6"
down_revision = "g3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_templates",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("default_priority", sa.String(20), nullable=False),
        sa.Column("recurrence_frequency", sa.String(20), nullable=True),
        sa.Column(
            "recurrence_interval",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("asset_type_filter", sa.String(50), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "maintenance_checklist_items",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "template_id",
            sa.String(26),
            sa.ForeignKey("maintenance_templates.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "is_required",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "sort_order",
            sa.Integer,
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_index(
        "ix_maintenance_templates_company_active",
        "maintenance_templates",
        ["company_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_templates_company_active",
        table_name="maintenance_templates",
    )
    op.drop_table("maintenance_checklist_items")
    op.drop_table("maintenance_templates")
