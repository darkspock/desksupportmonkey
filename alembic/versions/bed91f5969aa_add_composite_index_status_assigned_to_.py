"""add composite index status+assigned_to on service_requests

Revision ID: bed91f5969aa
Revises: z4c5d6e7f8g9
Create Date: 2026-02-25 16:01:51.028918

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'bed91f5969aa'
down_revision: Union[str, None] = 'z4c5d6e7f8g9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_service_requests_company_status_assigned",
        "service_requests",
        ["company_id", "status", "assigned_to"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_requests_company_status_assigned", table_name="service_requests")
