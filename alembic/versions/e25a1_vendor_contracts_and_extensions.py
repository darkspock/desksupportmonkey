"""e25: vendor contracts and extensions

Revision ID: e25a1_vendor_ext
Revises: bed91f5969aa
Create Date: 2026-02-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e25a1_vendor_ext"
down_revision: Union[str, None] = "bed91f5969aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend vendors table
    op.add_column("vendors", sa.Column("is_critical_ict", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("vendors", sa.Column("risk_level", sa.String(20), nullable=True))
    op.add_column("vendors", sa.Column("website", sa.String(500), nullable=True))
    op.add_column("vendors", sa.Column("category", sa.String(30), nullable=True))

    # Create vendor_contracts table
    op.create_table(
        "vendor_contracts",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("vendor_id", sa.String(26), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("contract_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("auto_renewal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("annual_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("security_clauses", postgresql.JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="draft", nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_vendor_contracts_vendor_company", "vendor_contracts", ["vendor_id", "company_id"])
    op.create_index("ix_vendor_contracts_company_status", "vendor_contracts", ["company_id", "status"])

    # Create vendor_contract_documents table
    op.create_table(
        "vendor_contract_documents",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("contract_id", sa.String(26), sa.ForeignKey("vendor_contracts.id"), nullable=False),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("uploaded_by", sa.String(26), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_vendor_contract_docs_contract_company", "vendor_contract_documents", ["contract_id", "company_id"])


def downgrade() -> None:
    op.drop_table("vendor_contract_documents")
    op.drop_table("vendor_contracts")
    op.drop_column("vendors", "category")
    op.drop_column("vendors", "website")
    op.drop_column("vendors", "risk_level")
    op.drop_column("vendors", "is_critical_ict")
