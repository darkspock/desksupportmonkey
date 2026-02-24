"""add_custom_fields_data

Revision ID: k2l3m4n5o6p7
Revises: j1k2l3m4n5o6
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "k2l3m4n5o6p7"
down_revision: Union[str, None] = "j1k2l3m4n5o6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "assets",
        sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False),
    )
    op.add_column(
        "service_requests",
        sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False),
    )
    op.add_column(
        "security_incidents",
        sa.Column("custom_fields_data", sa.JSON(), server_default="{}", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("security_incidents", "custom_fields_data")
    op.drop_column("service_requests", "custom_fields_data")
    op.drop_column("assets", "custom_fields_data")
