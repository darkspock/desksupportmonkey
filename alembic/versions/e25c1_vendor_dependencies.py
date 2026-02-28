"""create vendor_dependencies table

Revision ID: e25c1
Revises: e25b1
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

revision = "e25c1"
down_revision = "e25b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_dependencies",
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
        sa.Column("service_description", sa.String(500), nullable=False),
        sa.Column("business_function", sa.String(30), nullable=False),
        sa.Column(
            "is_critical",
            sa.Boolean,
            server_default="false",
            nullable=False,
        ),
        sa.Column("notes", sa.Text, nullable=True),
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
        "ix_vendor_dependencies_vendor_company",
        "vendor_dependencies",
        ["vendor_id", "company_id"],
    )
    op.create_index(
        "ix_vendor_dependencies_company_critical",
        "vendor_dependencies",
        ["company_id", "is_critical"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_vendor_dependencies_company_critical",
        table_name="vendor_dependencies",
    )
    op.drop_index(
        "ix_vendor_dependencies_vendor_company",
        table_name="vendor_dependencies",
    )
    op.drop_table("vendor_dependencies")
