"""create purchase_orders table

Revision ID: j5k6l7m8n9o0
Revises: i4j5k6l7m8n9
Create Date: 2026-02-18 18:01:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "j5k6l7m8n9o0"
down_revision = "i4j5k6l7m8n9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("po_number", sa.String(30), nullable=False),
        sa.Column(
            "vendor_id",
            sa.String(26),
            sa.ForeignKey("vendors.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("vendor_name", sa.String(200), nullable=False),
        sa.Column(
            "department_id",
            sa.String(26),
            sa.ForeignKey("departments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "status",
            sa.String(30),
            nullable=False,
            server_default="DRAFT",
            index=True,
        ),
        sa.Column(
            "total_amount_cents",
            sa.Integer,
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="USD",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("approved_by", sa.String(26), nullable=True),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("ordered_at", sa.DateTime, nullable=True),
        sa.Column("cancellation_reason", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "company_id",
            "po_number",
            name="uq_purchase_order_company_number",
        ),
    )


def downgrade() -> None:
    op.drop_table("purchase_orders")
