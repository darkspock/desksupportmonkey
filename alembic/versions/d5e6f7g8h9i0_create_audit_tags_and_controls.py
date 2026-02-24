"""create_audit_tags_and_controls

Revision ID: d5e6f7g8h9i0
Revises: c4d5e6f7g8h9
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

import ulid

# revision identifiers, used by Alembic.
revision: str = "d5e6f7g8h9i0"
down_revision: Union[str, None] = "c4d5e6f7g8h9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PREDEFINED_CONTROLS = [
    # NIS2 Article 21(2) — key measures
    ("NIS2-ART21-2A", "Risk analysis and information security policies", "NIS2",
     "Policies on risk analysis and information system security"),
    ("NIS2-ART21-2B", "Incident handling", "NIS2",
     "Incident handling procedures and response capabilities"),
    ("NIS2-ART21-2E", "Security in network and information systems", "NIS2",
     "Security in network and information systems acquisition, development and maintenance"),
    ("NIS2-ART21-2I", "Human resources security and access control", "NIS2",
     "Human resources security, access control policies and asset management"),
    ("NIS2-ART21-2J", "Multi-factor authentication", "NIS2",
     "Use of multi-factor authentication or continuous authentication solutions"),
    # DORA — key chapters
    ("DORA-CH2-ART5", "ICT risk management framework", "DORA",
     "ICT risk management framework governance and organization"),
    ("DORA-CH2-ART9", "Protection and prevention", "DORA",
     "Implement ICT security policies, procedures, protocols and tools for protection and prevention"),
    ("DORA-CH3-ART17", "ICT-related incident management process", "DORA",
     "Establish and implement an ICT-related incident management process"),
    ("DORA-CH3-ART19", "Reporting of major ICT incidents", "DORA",
     "Reporting major ICT-related incidents to competent authorities"),
    # ISO 27001:2022 Annex A — selected controls
    ("ISO27001-A5.1", "Policies for information security", "ISO27001",
     "Information security policy and topic-specific policies shall be defined and approved"),
    ("ISO27001-A5.23", "Information security for use of cloud services", "ISO27001",
     "Processes for acquisition, use, management and exit from cloud services"),
    ("ISO27001-A6.1", "Screening", "ISO27001",
     "Background verification checks on all candidates shall be carried out"),
    ("ISO27001-A8.2", "Privileged access rights", "ISO27001",
     "The allocation and use of privileged access rights shall be restricted and managed"),
    ("ISO27001-A8.15", "Logging", "ISO27001",
     "Logs that record activities, exceptions, faults and other relevant events shall be produced and stored"),
    ("ISO27001-A8.16", "Monitoring activities", "ISO27001",
     "Networks, systems and applications shall be monitored for anomalous behaviour"),
]


def upgrade() -> None:
    # compliance_controls table
    op.create_table(
        "compliance_controls",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=True),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("framework", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_predefined", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("company_id", "code", name="uq_compliance_controls_company_code"),
    )
    op.create_index("ix_compliance_controls_company", "compliance_controls", ["company_id"])
    op.create_index("ix_compliance_controls_framework", "compliance_controls", ["framework"])

    # audit_entry_tags table
    op.create_table(
        "audit_entry_tags",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("audit_entry_id", sa.String(26), sa.ForeignKey("audit_entries.id"), nullable=False),
        sa.Column("control_id", sa.String(26), sa.ForeignKey("compliance_controls.id"), nullable=False),
        sa.Column("tagged_by", sa.String(26), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tagged_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("audit_entry_id", "control_id", name="uq_audit_entry_tags_entry_control"),
    )
    op.create_index("ix_audit_entry_tags_entry", "audit_entry_tags", ["audit_entry_id"])
    op.create_index("ix_audit_entry_tags_control", "audit_entry_tags", ["control_id"])

    # Seed predefined compliance controls
    now = datetime.now(timezone.utc)
    controls_table = sa.table(
        "compliance_controls",
        sa.column("id", sa.String),
        sa.column("company_id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("framework", sa.String),
        sa.column("description", sa.Text),
        sa.column("is_predefined", sa.Boolean),
        sa.column("is_active", sa.Boolean),
        sa.column("created_at", sa.DateTime),
    )
    op.bulk_insert(
        controls_table,
        [
            {
                "id": str(ulid.new()),
                "company_id": None,
                "code": code,
                "name": name,
                "framework": framework,
                "description": description,
                "is_predefined": True,
                "is_active": True,
                "created_at": now,
            }
            for code, name, framework, description in PREDEFINED_CONTROLS
        ],
    )


def downgrade() -> None:
    op.drop_table("audit_entry_tags")
    op.drop_table("compliance_controls")
