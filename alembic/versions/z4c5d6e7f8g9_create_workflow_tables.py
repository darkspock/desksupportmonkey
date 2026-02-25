"""create_workflow_tables

Revision ID: z4c5d6e7f8g9
Revises: b2c3d4e5f6g7
Create Date: 2026-02-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "z4c5d6e7f8g9"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Workflow templates
    op.create_table(
        "workflow_templates",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.Column("require_all_complete", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("company_id", "name", name="uq_workflow_templates_company_name"),
    )
    op.create_index("ix_workflow_templates_company", "workflow_templates", ["company_id"])

    # Workflow subtypes
    op.create_table(
        "workflow_subtypes",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("template_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default="true", nullable=False),
        sa.UniqueConstraint("template_id", "name", name="uq_workflow_subtypes_template_name"),
    )
    op.create_index("ix_workflow_subtypes_template", "workflow_subtypes", ["template_id"])

    # Checklist item definitions (template-level)
    op.create_table(
        "checklist_item_definitions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("template_id", sa.String(26), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assignee_role", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("is_required", sa.Boolean, server_default="true", nullable=False),
    )
    op.create_index(
        "ix_checklist_item_definitions_template", "checklist_item_definitions", ["template_id"]
    )

    # Request checklist items (runtime, per request)
    op.create_table(
        "request_checklist_items",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("request_id", sa.String(26), nullable=False),
        sa.Column("require_all_complete", sa.Boolean, server_default="false", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("assignee_id", sa.String(26), nullable=True),
        sa.Column("is_required", sa.Boolean, server_default="true", nullable=False),
        sa.Column("is_completed", sa.Boolean, server_default="false", nullable=False),
        sa.Column("completed_by", sa.String(26), nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_request_checklist_items_request", "request_checklist_items", ["request_id"]
    )
    op.create_index(
        "ix_request_checklist_items_assignee",
        "request_checklist_items",
        ["assignee_id", "is_completed"],
    )

    # Add workflow_template_id to service_requests (nullable for now)
    op.add_column(
        "service_requests",
        sa.Column("workflow_template_id", sa.String(26), nullable=True),
    )
    op.add_column(
        "service_requests",
        sa.Column("workflow_subtype_id", sa.String(26), nullable=True),
    )
    op.create_index(
        "ix_service_requests_workflow_template",
        "service_requests",
        ["workflow_template_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_requests_workflow_template", table_name="service_requests")
    op.drop_column("service_requests", "workflow_subtype_id")
    op.drop_column("service_requests", "workflow_template_id")
    op.drop_table("request_checklist_items")
    op.drop_table("checklist_item_definitions")
    op.drop_table("workflow_subtypes")
    op.drop_table("workflow_templates")
