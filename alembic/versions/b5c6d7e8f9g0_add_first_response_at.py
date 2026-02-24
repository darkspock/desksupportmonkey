"""add first_response_at to service_requests

Revision ID: b5c6d7e8f9g0
Revises: a4c5d6e7f8g9
Create Date: 2026-02-23 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "b5c6d7e8f9g0"
down_revision: Union[str, None] = "a4c5d6e7f8g9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("first_response_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_requests", "first_response_at")
