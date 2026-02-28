"""create vendor_risk_assessments table

Revision ID: e25b1
Revises: e25a1_vendor_ext
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

revision = "e25b1"
down_revision = "e25a1_vendor_ext"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_risk_assessments",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "vendor_id",
            sa.String(26),
            sa.ForeignKey("vendors.id"),
            nullable=False,
        ),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column("assessed_by", sa.String(26), nullable=False),
        sa.Column("assessment_date", sa.Date, nullable=False),
        sa.Column("next_review_date", sa.Date, nullable=True),
        sa.Column("data_handling_score", sa.SmallInteger, nullable=False),
        sa.Column("security_certs_score", sa.SmallInteger, nullable=False),
        sa.Column("incident_response_score", sa.SmallInteger, nullable=False),
        sa.Column("business_continuity_score", sa.SmallInteger, nullable=False),
        sa.Column("subcontractor_score", sa.SmallInteger, nullable=False),
        sa.Column("overall_risk_level", sa.String(20), nullable=False),
        sa.Column("justification", sa.Text, nullable=True),
        sa.Column(
            "is_deleted",
            sa.Boolean,
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_vendor_risk_assessments_vendor_company",
        "vendor_risk_assessments",
        ["vendor_id", "company_id"],
    )
    op.create_index(
        "ix_vendor_risk_assessments_company_date",
        "vendor_risk_assessments",
        ["company_id", "assessment_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vendor_risk_assessments_company_date",
        table_name="vendor_risk_assessments",
    )
    op.drop_index(
        "ix_vendor_risk_assessments_vendor_company",
        table_name="vendor_risk_assessments",
    )
    op.drop_table("vendor_risk_assessments")
