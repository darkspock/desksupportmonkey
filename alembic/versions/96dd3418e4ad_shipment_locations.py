"""shipment_locations: unify addresses and locations

Revision ID: 96dd3418e4ad
Revises: 2853b6e6873f
Create Date: 2026-02-24

Adds address fields to asset_locations and users tables.
Adds origin_location_id / destination_location_id FK columns to shipments.
Migrates existing shipping_address data into asset_locations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "96dd3418e4ad"
down_revision: Union[str, None] = "2853b6e6873f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1a. Add address columns to asset_locations
    op.add_column(
        "asset_locations",
        sa.Column("street_line_1", sa.String(255), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("street_line_2", sa.String(255), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("city", sa.String(100), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("state", sa.String(100), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("postal_code", sa.String(20), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("country", sa.String(100), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column("phone", sa.String(50), nullable=True),
    )
    op.add_column(
        "asset_locations",
        sa.Column(
            "is_personal",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.add_column(
        "asset_locations",
        sa.Column("user_id", sa.String(26), nullable=True),
    )
    op.create_foreign_key(
        "fk_asset_locations_user_id",
        "asset_locations",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index(
        "ix_asset_locations_user_id",
        "asset_locations",
        ["user_id"],
    )

    # 1b. Add address columns to users
    op.add_column(
        "users",
        sa.Column("street_line_1", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("street_line_2", sa.String(255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("city", sa.String(100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("state", sa.String(100), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("postal_code", sa.String(20), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("country", sa.String(100), nullable=True),
    )

    # 1c. Add location FK columns to shipments
    op.add_column(
        "shipments",
        sa.Column("origin_location_id", sa.String(26), nullable=True),
    )
    op.add_column(
        "shipments",
        sa.Column("destination_location_id", sa.String(26), nullable=True),
    )
    op.create_foreign_key(
        "fk_shipments_origin_location_id",
        "shipments",
        "asset_locations",
        ["origin_location_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_shipments_destination_location_id",
        "shipments",
        "asset_locations",
        ["destination_location_id"],
        ["id"],
    )
    op.create_index(
        "ix_shipments_origin_location_id",
        "shipments",
        ["origin_location_id"],
    )
    op.create_index(
        "ix_shipments_destination_location_id",
        "shipments",
        ["destination_location_id"],
    )

    # Make old address FK columns nullable (they already are, but ensure)
    op.alter_column(
        "shipments",
        "destination_address_id",
        existing_type=sa.String(26),
        nullable=True,
    )
    op.alter_column(
        "shipments",
        "origin_address_id",
        existing_type=sa.String(26),
        nullable=True,
    )

    # 1d. Data migration: copy shipping_addresses → asset_locations
    # and map shipment FKs
    op.execute("""
        INSERT INTO asset_locations (
            id, company_id, name,
            street_line_1, street_line_2, city, state, postal_code, country, phone,
            is_personal, user_id,
            is_system, in_use, created_at
        )
        SELECT
            id, company_id, label,
            street_line_1, street_line_2, city, state, postal_code, country, phone,
            CASE WHEN is_office = false AND user_id IS NOT NULL THEN true ELSE false END,
            user_id,
            false, true, created_at
        FROM shipping_addresses
        ON CONFLICT (company_id, name) DO NOTHING
    """)

    # Map shipment origin_address_id → origin_location_id
    op.execute("""
        UPDATE shipments
        SET origin_location_id = origin_address_id
        WHERE origin_address_id IS NOT NULL
          AND origin_location_id IS NULL
    """)

    # Map shipment destination_address_id → destination_location_id
    op.execute("""
        UPDATE shipments
        SET destination_location_id = destination_address_id
        WHERE destination_address_id IS NOT NULL
          AND destination_location_id IS NULL
    """)


def downgrade() -> None:
    # Reverse the FK mapping
    op.execute("""
        UPDATE shipments
        SET origin_address_id = origin_location_id
        WHERE origin_location_id IS NOT NULL
          AND origin_address_id IS NULL
    """)
    op.execute("""
        UPDATE shipments
        SET destination_address_id = destination_location_id
        WHERE destination_location_id IS NOT NULL
          AND destination_address_id IS NULL
    """)

    # Drop shipment location FK columns
    op.drop_index("ix_shipments_destination_location_id", "shipments")
    op.drop_index("ix_shipments_origin_location_id", "shipments")
    op.drop_constraint(
        "fk_shipments_destination_location_id", "shipments", type_="foreignkey",
    )
    op.drop_constraint(
        "fk_shipments_origin_location_id", "shipments", type_="foreignkey",
    )
    op.drop_column("shipments", "destination_location_id")
    op.drop_column("shipments", "origin_location_id")

    # Drop user address columns
    op.drop_column("users", "country")
    op.drop_column("users", "postal_code")
    op.drop_column("users", "state")
    op.drop_column("users", "city")
    op.drop_column("users", "street_line_2")
    op.drop_column("users", "street_line_1")

    # Drop asset_locations new columns
    op.drop_index("ix_asset_locations_user_id", "asset_locations")
    op.drop_constraint(
        "fk_asset_locations_user_id", "asset_locations", type_="foreignkey",
    )
    op.drop_column("asset_locations", "user_id")
    op.drop_column("asset_locations", "is_personal")
    op.drop_column("asset_locations", "phone")
    op.drop_column("asset_locations", "country")
    op.drop_column("asset_locations", "postal_code")
    op.drop_column("asset_locations", "state")
    op.drop_column("asset_locations", "city")
    op.drop_column("asset_locations", "street_line_2")
    op.drop_column("asset_locations", "street_line_1")
