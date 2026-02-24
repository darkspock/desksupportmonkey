"""create asset_type_definitions table

Revision ID: b2c3d4e5f6g7
Revises: 96dd3418e4ad
Create Date: 2026-02-24

Creates the asset_type_definitions table for company-configurable asset types.
Migrates existing companies to have the 8 default types from the old enum.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from datetime import datetime, timezone

import ulid


# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6g7"
down_revision: Union[str, None] = "96dd3418e4ad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_TYPES = [
    ("laptop", "Laptop", "laptop", 0),
    ("monitor", "Monitor", "monitor", 1),
    ("keyboard", "Keyboard", "keyboard", 2),
    ("mouse", "Mouse", "mouse", 3),
    ("headset", "Headset", "headset", 4),
    ("phone", "Phone", "phone", 5),
    ("docking_station", "Docking Station", "dock", 6),
    ("other", "Other", None, 7),
]


def upgrade() -> None:
    op.create_table(
        "asset_type_definitions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("icon", sa.String(100), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean,
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "sort_order",
            sa.Integer,
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "company_id", "code", name="uq_atd_company_code"
        ),
        sa.Index(
            "ix_atd_company_active", "company_id", "is_active"
        ),
    )

    # Data migration: insert default types for every existing company
    conn = op.get_bind()
    companies = conn.execute(
        text("SELECT id FROM companies")
    ).fetchall()

    now = datetime.now(timezone.utc)
    for (company_id,) in companies:
        for code, name, icon, sort_order in DEFAULT_TYPES:
            conn.execute(
                text(
                    "INSERT INTO asset_type_definitions "
                    "(id, company_id, code, name, icon, is_active, sort_order, created_at, updated_at) "
                    "VALUES (:id, :company_id, :code, :name, :icon, true, :sort_order, :now, :now)"
                ),
                {
                    "id": str(ulid.new()),
                    "company_id": company_id,
                    "code": code,
                    "name": name,
                    "icon": icon,
                    "sort_order": sort_order,
                    "now": now,
                },
            )


def downgrade() -> None:
    op.drop_table("asset_type_definitions")
