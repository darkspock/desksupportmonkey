"""create_compliance_tables

Revision ID: e6f7g8h9i0j1
Revises: g7h8i9j0k1l2
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e6f7g8h9i0j1"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "compliance_assessments",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "control_id",
            sa.String(26),
            sa.ForeignKey("compliance_controls.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="not_assessed",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "assessed_by",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "assessed_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.UniqueConstraint(
            "company_id",
            "control_id",
            name="uq_compliance_assessments_company_control",
        ),
    )
    op.create_index(
        "ix_compliance_assessments_company",
        "compliance_assessments",
        ["company_id"],
    )
    op.create_index(
        "ix_compliance_assessments_control",
        "compliance_assessments",
        ["control_id"],
    )
    op.create_index(
        "ix_compliance_assessments_company_status",
        "compliance_assessments",
        ["company_id", "status"],
    )

    op.create_table(
        "compliance_evidence",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "control_id",
            sa.String(26),
            sa.ForeignKey("compliance_controls.id"),
            nullable=False,
        ),
        sa.Column("evidence_type", sa.String(20), nullable=False),
        sa.Column("reference_id", sa.String(255), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("url", sa.String(1000), nullable=True),
        sa.Column(
            "added_by",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False
        ),
    )
    op.create_index(
        "ix_compliance_evidence_control",
        "compliance_evidence",
        ["control_id"],
    )
    op.create_index(
        "ix_compliance_evidence_company",
        "compliance_evidence",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_table("compliance_evidence")
    op.drop_table("compliance_assessments")
