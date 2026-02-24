"""add asset_locations table and location_id to assets

Revision ID: c6d7e8f9g0h1
Revises: b5c6d7e8f9g0
Create Date: 2026-02-23 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c6d7e8f9g0h1"
down_revision: Union[str, None] = "b5c6d7e8f9g0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SYSTEM_LOCATIONS = [
    ("employee", "Empleado"),
    ("in_transit", "En Tránsito"),
    ("main_warehouse", "Almacén Principal"),
]


def upgrade() -> None:
    op.create_table(
        "asset_locations",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), sa.ForeignKey("companies.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_system", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("system_key", sa.String(50), nullable=True),
        sa.Column("in_use", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("company_id", "name", name="uq_location_company_name"),
    )

    op.add_column(
        "assets",
        sa.Column("location_id", sa.String(26), sa.ForeignKey("asset_locations.id"), nullable=True, index=True),
    )

    # Data migration: seed 3 system locations per existing company
    # and set existing assets' location_id
    conn = op.get_bind()

    companies = conn.execute(sa.text("SELECT id FROM companies")).fetchall()

    import ulid as _ulid

    for (company_id,) in companies:
        loc_ids = {}
        for system_key, name in SYSTEM_LOCATIONS:
            loc_id = str(_ulid.new())
            conn.execute(
                sa.text(
                    "INSERT INTO asset_locations (id, company_id, name, is_system, system_key, in_use) "
                    "VALUES (:id, :company_id, :name, true, :system_key, true)"
                ),
                {"id": loc_id, "company_id": company_id, "name": name, "system_key": system_key},
            )
            loc_ids[system_key] = loc_id

        # Assigned assets -> Empleado
        conn.execute(
            sa.text(
                "UPDATE assets SET location_id = :loc_id "
                "WHERE company_id = :company_id AND status = 'assigned'"
            ),
            {"loc_id": loc_ids["employee"], "company_id": company_id},
        )

        # In-stock assets -> Almacén Principal
        conn.execute(
            sa.text(
                "UPDATE assets SET location_id = :loc_id "
                "WHERE company_id = :company_id AND status = 'in_stock'"
            ),
            {"loc_id": loc_ids["main_warehouse"], "company_id": company_id},
        )

        # In-repair assets -> Almacén Principal
        conn.execute(
            sa.text(
                "UPDATE assets SET location_id = :loc_id "
                "WHERE company_id = :company_id AND status = 'in_repair'"
            ),
            {"loc_id": loc_ids["main_warehouse"], "company_id": company_id},
        )


def downgrade() -> None:
    op.drop_column("assets", "location_id")
    op.drop_table("asset_locations")
