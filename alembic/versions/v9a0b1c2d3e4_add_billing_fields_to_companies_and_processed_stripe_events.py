"""add billing fields to companies and processed stripe events

Revision ID: v9a0b1c2d3e4
Revises: u8e9f0g1h2i3
Create Date: 2026-02-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "v9a0b1c2d3e4"
down_revision = "u8e9f0g1h2i3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add billing columns to companies (all nullable or server-defaulted — non-breaking)
    op.add_column("companies", sa.Column("plan", sa.String(20), nullable=False, server_default="free"))
    op.add_column("companies", sa.Column("billing_status", sa.String(20), nullable=False, server_default="active"))
    op.add_column("companies", sa.Column("stripe_customer_id", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("stripe_subscription_id", sa.String(255), nullable=True))
    op.add_column("companies", sa.Column("grace_period_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("companies", sa.Column("pending_downgrade_plan", sa.String(20), nullable=True))
    op.add_column("companies", sa.Column("complimentary", sa.Boolean(), nullable=False, server_default="false"))

    op.create_index("ix_companies_stripe_customer_id", "companies", ["stripe_customer_id"], unique=False)

    # Create processed_stripe_events table (idempotency log)
    op.create_table(
        "processed_stripe_events",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("processed_stripe_events")
    op.drop_index("ix_companies_stripe_customer_id", table_name="companies")
    op.drop_column("companies", "complimentary")
    op.drop_column("companies", "pending_downgrade_plan")
    op.drop_column("companies", "current_period_end")
    op.drop_column("companies", "grace_period_started_at")
    op.drop_column("companies", "stripe_subscription_id")
    op.drop_column("companies", "stripe_customer_id")
    op.drop_column("companies", "billing_status")
    op.drop_column("companies", "plan")
