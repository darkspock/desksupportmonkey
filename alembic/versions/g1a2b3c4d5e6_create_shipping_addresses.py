"""create shipping_addresses table

Revision ID: g1a2b3c4d5e6
Revises: f3c4d5e6f7a8
Create Date: 2026-02-18 18:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "g1a2b3c4d5e6"
down_revision = "f3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipping_addresses",
        sa.Column(
            "id", sa.String(26), primary_key=True,
        ),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "label", sa.String(100), nullable=False,
        ),
        sa.Column(
            "recipient_name",
            sa.String(200),
            nullable=True,
        ),
        sa.Column(
            "street_line_1",
            sa.String(300),
            nullable=False,
        ),
        sa.Column(
            "street_line_2",
            sa.String(300),
            nullable=True,
        ),
        sa.Column(
            "city", sa.String(100), nullable=False,
        ),
        sa.Column(
            "state", sa.String(100), nullable=False,
        ),
        sa.Column(
            "postal_code",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "country",
            sa.String(2),
            nullable=False,
            server_default=sa.text("'US'"),
        ),
        sa.Column(
            "phone", sa.String(30), nullable=True,
        ),
        sa.Column(
            "user_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "is_office",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at", sa.DateTime, nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("shipping_addresses")
