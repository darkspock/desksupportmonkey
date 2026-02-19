"""create shipments table

Revision ID: g2b3c4d5e6f7
Revises: o0p1q2r3s4t5
Create Date: 2026-02-18 18:01:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "g2b3c4d5e6f7"
down_revision = "o0p1q2r3s4t5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "shipments",
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
            "direction",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "destination_type",
            sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column(
            "origin_address_id",
            sa.String(26),
            sa.ForeignKey("shipping_addresses.id"),
            nullable=True,
        ),
        sa.Column(
            "destination_address_id",
            sa.String(26),
            sa.ForeignKey("shipping_addresses.id"),
            nullable=False,
        ),
        sa.Column(
            "recipient_name",
            sa.String(200),
            nullable=True,
        ),
        sa.Column(
            "recipient_user_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "carrier",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "tracking_number",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "tracking_url",
            sa.String(500),
            nullable=True,
        ),
        sa.Column(
            "request_id",
            sa.String(26),
            sa.ForeignKey("service_requests.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "po_id",
            sa.String(26),
            sa.ForeignKey("purchase_orders.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "return_for_shipment_id",
            sa.String(26),
            sa.ForeignKey("shipments.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "notes", sa.Text, nullable=True,
        ),
        sa.Column(
            "failure_reason", sa.Text, nullable=True,
        ),
        sa.Column(
            "cancellation_reason",
            sa.Text,
            nullable=True,
        ),
        sa.Column(
            "created_by",
            sa.String(26),
            nullable=False,
        ),
        sa.Column(
            "dispatched_at",
            sa.DateTime,
            nullable=True,
        ),
        sa.Column(
            "delivered_at",
            sa.DateTime,
            nullable=True,
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
        "ix_shipments_status",
        "shipments",
        ["status"],
    )
    op.create_index(
        "ix_shipments_direction",
        "shipments",
        ["direction"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_shipments_direction",
        table_name="shipments",
    )
    op.drop_index(
        "ix_shipments_status",
        table_name="shipments",
    )
    op.drop_table("shipments")
