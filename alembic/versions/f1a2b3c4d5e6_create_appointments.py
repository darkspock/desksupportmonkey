"""create appointments table

Revision ID: f1a2b3c4d5e6
Revises: f1a0b0c0d0e0
Create Date: 2026-02-18 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "f1a0b0c0d0e0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "appointments",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "company_id",
            sa.String(26),
            sa.ForeignKey("companies.id"),
            nullable=False,
        ),
        sa.Column(
            "request_id",
            sa.String(26),
            sa.ForeignKey("service_requests.id"),
            nullable=False,
        ),
        sa.Column(
            "technician_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column(
            "scheduled_start",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "scheduled_end",
            sa.DateTime,
            nullable=False,
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer,
            nullable=False,
            server_default="60",
        ),
        sa.Column("location", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "cancellation_reason", sa.Text, nullable=True,
        ),
        sa.Column(
            "cancelled_by", sa.String(26), nullable=True,
        ),
        sa.Column(
            "rescheduled_from_id",
            sa.String(26),
            sa.ForeignKey("appointments.id"),
            nullable=True,
        ),
        sa.Column(
            "reminder_24h_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "reminder_1h_sent",
            sa.Boolean,
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "completed_at", sa.DateTime, nullable=True,
        ),
        sa.Column(
            "created_by", sa.String(26), nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime, nullable=True),
    )

    op.create_index(
        "ix_appointments_company_id",
        "appointments",
        ["company_id"],
    )
    op.create_index(
        "ix_appointments_technician_id",
        "appointments",
        ["technician_id"],
    )
    op.create_index(
        "ix_appointments_employee_id",
        "appointments",
        ["employee_id"],
    )
    op.create_index(
        "ix_appointments_request_id",
        "appointments",
        ["request_id"],
    )
    op.create_index(
        "ix_appointments_status",
        "appointments",
        ["status"],
    )
    op.create_index(
        "ix_appointments_scheduled_start",
        "appointments",
        ["scheduled_start"],
    )


def downgrade() -> None:
    op.drop_table("appointments")
