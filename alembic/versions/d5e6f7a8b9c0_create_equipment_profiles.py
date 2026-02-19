"""create equipment_profiles and items tables

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-02-17 23:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "equipment_profiles",
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
            "department_id",
            sa.String(26),
            sa.ForeignKey("departments.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "role", sa.String(20), nullable=False,
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

    op.create_index(
        "ix_equipment_profile_active_unique",
        "equipment_profiles",
        ["company_id", "department_id", "role"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "equipment_profile_items",
        sa.Column(
            "id", sa.String(26), primary_key=True,
        ),
        sa.Column(
            "profile_id",
            sa.String(26),
            sa.ForeignKey(
                "equipment_profiles.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "asset_type", sa.String(30), nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer,
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "preferred_brand",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "preferred_model",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "min_ram_gb", sa.Integer, nullable=True,
        ),
        sa.Column(
            "min_storage_gb", sa.Integer, nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("equipment_profile_items")
    op.drop_index(
        "ix_equipment_profile_active_unique",
        table_name="equipment_profiles",
    )
    op.drop_table("equipment_profiles")
