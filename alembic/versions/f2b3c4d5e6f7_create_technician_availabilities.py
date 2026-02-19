"""create technician availabilities table

Revision ID: f2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-18 12:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2b3c4d5e6f7"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "technician_availabilities",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "technician_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "day_of_week", sa.Integer, nullable=False,
        ),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("end_time", sa.Time, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint(
            "technician_id",
            "day_of_week",
            "start_time",
            name="uq_availability_tech_day_start",
        ),
    )

    op.create_index(
        "ix_tech_availabilities_technician",
        "technician_availabilities",
        ["technician_id"],
    )


def downgrade() -> None:
    op.drop_table("technician_availabilities")
