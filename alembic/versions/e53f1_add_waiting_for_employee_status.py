"""add_waiting_for_employee_sla_fields

Revision ID: e53f1a001
Revises: 3b819e174e0c
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e53f1a001"
down_revision: Union[str, None] = "3b819e174e0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("sla_paused_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "service_requests",
        sa.Column("sla_paused_total_seconds", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("service_requests", "sla_paused_total_seconds")
    op.drop_column("service_requests", "sla_paused_at")
