"""create_custom_field_definitions

Revision ID: j1k2l3m4n5o6
Revises: g7h8i9j0k1l2
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = "j1k2l3m4n5o6"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "custom_field_definitions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("field_key", sa.String(50), nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("field_type", sa.String(20), nullable=False),
        sa.Column("options", JSON(), nullable=True),
        sa.Column(
            "required", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="true"
        ),
        sa.Column(
            "visible_to_employees",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_cfd_company_entity",
        "custom_field_definitions",
        ["company_id", "entity_type"],
    )
    op.create_unique_constraint(
        "uq_cfd_company_entity_key",
        "custom_field_definitions",
        ["company_id", "entity_type", "field_key"],
    )


def downgrade() -> None:
    op.drop_table("custom_field_definitions")
