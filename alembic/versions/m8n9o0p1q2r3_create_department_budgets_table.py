"""create department_budgets table

Revision ID: m8n9o0p1q2r3
Revises: l7m8n9o0p1q2
Create Date: 2026-02-18 18:04:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "m8n9o0p1q2r3"
down_revision = "l7m8n9o0p1q2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department_budgets",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "department_id",
            sa.String(26),
            sa.ForeignKey("departments.id"),
            nullable=False,
        ),
        sa.Column(
            "fiscal_year", sa.Integer, nullable=False,
        ),
        sa.Column(
            "allocated_amount_cents",
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
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "department_id",
            "fiscal_year",
            name="uq_budget_department_year",
        ),
    )


def downgrade() -> None:
    op.drop_table("department_budgets")
