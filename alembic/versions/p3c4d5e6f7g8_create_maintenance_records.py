"""create maintenance records table

Revision ID: p3c4d5e6f7g8
Revises: p2b3c4d5e6f7
Create Date: 2026-02-18 20:12:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "p3c4d5e6f7g8"
down_revision = "p2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
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
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'SCHEDULED'"),
            index=True,
        ),
        sa.Column("priority", sa.String(20), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "technician_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "template_id",
            sa.String(26),
            sa.ForeignKey("maintenance_templates.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "plan_id",
            sa.String(26),
            sa.ForeignKey("maintenance_plans.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("checklist_items", sa.Text, nullable=True),
        sa.Column("scheduled_at", sa.DateTime, nullable=True, index=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("completion_notes", sa.Text, nullable=True),
        sa.Column("actual_findings", sa.Text, nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column("skip_reason", sa.Text, nullable=True),
        sa.Column(
            "reminder_48h_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "overdue_alert_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_index(
        "ix_maintenance_records_company_status",
        "maintenance_records",
        ["company_id", "status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_maintenance_records_company_status",
        table_name="maintenance_records",
    )
    op.drop_table("maintenance_records")
