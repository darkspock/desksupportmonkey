"""create_incident_tables

Revision ID: x1c2d3e4f5g6
Revises: w0b1c2d3e4f5
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "x1c2d3e4f5g6"
down_revision: Union[str, None] = "w0b1c2d3e4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # security_incidents
    op.create_table(
        "security_incidents",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("incident_type", sa.String(30), nullable=False),
        sa.Column("severity", sa.String(5), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="detected",
        ),
        sa.Column("attack_vector", sa.String(500), nullable=True),
        sa.Column("data_breach_scope", sa.Text(), nullable=True),
        sa.Column("reported_by", sa.String(26), nullable=False),
        sa.Column("assigned_to", sa.String(26), nullable=True),
        sa.Column(
            "detected_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("close_reason", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_security_incidents_company_id",
        "security_incidents",
        ["company_id"],
    )
    op.create_index(
        "ix_security_incidents_company_status",
        "security_incidents",
        ["company_id", "status"],
    )
    op.create_index(
        "ix_security_incidents_company_severity",
        "security_incidents",
        ["company_id", "severity"],
    )
    op.create_index(
        "ix_security_incidents_company_type",
        "security_incidents",
        ["company_id", "incident_type"],
    )
    op.create_index(
        "ix_security_incidents_detected_at",
        "security_incidents",
        ["detected_at"],
    )

    # incident_timeline
    op.create_table(
        "incident_timeline",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(26),
            sa.ForeignKey("security_incidents.id"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
    )
    op.create_index(
        "ix_incident_timeline_incident_id",
        "incident_timeline",
        ["incident_id"],
    )

    # incident_assets
    op.create_table(
        "incident_assets",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(26),
            sa.ForeignKey("security_incidents.id"),
            nullable=False,
        ),
        sa.Column("asset_id", sa.String(26), nullable=False),
        sa.Column("impact_description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "incident_id", "asset_id", name="uq_incident_asset"
        ),
    )
    op.create_index(
        "ix_incident_assets_incident_id",
        "incident_assets",
        ["incident_id"],
    )

    # incident_vendors
    op.create_table(
        "incident_vendors",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(26),
            sa.ForeignKey("security_incidents.id"),
            nullable=False,
        ),
        sa.Column("vendor_id", sa.String(26), nullable=False),
        sa.Column("involvement_description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "incident_id", "vendor_id", name="uq_incident_vendor"
        ),
    )
    op.create_index(
        "ix_incident_vendors_incident_id",
        "incident_vendors",
        ["incident_id"],
    )

    # regulatory_reports
    op.create_table(
        "regulatory_reports",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(26),
            sa.ForeignKey("security_incidents.id"),
            nullable=False,
        ),
        sa.Column("report_type", sa.String(20), nullable=False),
        sa.Column(
            "status",
            sa.String(15),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "deadline_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column("file_path", sa.String(500), nullable=True),
    )
    op.create_index(
        "ix_regulatory_reports_incident_id",
        "regulatory_reports",
        ["incident_id"],
    )
    op.create_index(
        "ix_regulatory_reports_deadline",
        "regulatory_reports",
        ["deadline_at"],
    )
    op.create_index(
        "ix_regulatory_reports_status",
        "regulatory_reports",
        ["status"],
    )

    # post_mortems
    op.create_table(
        "post_mortems",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "incident_id",
            sa.String(26),
            sa.ForeignKey("security_incidents.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("lessons_learned", sa.Text(), nullable=False),
        sa.Column("corrective_actions", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("post_mortems")
    op.drop_table("regulatory_reports")
    op.drop_table("incident_vendors")
    op.drop_table("incident_assets")
    op.drop_table("incident_timeline")
    op.drop_table("security_incidents")
