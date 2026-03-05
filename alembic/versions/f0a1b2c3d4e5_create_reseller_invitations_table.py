"""create_reseller_invitations_table

Revision ID: f0a1b2c3d4e5
Revises: 01kjxf5qgx9c
Create Date: 2026-03-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f0a1b2c3d4e5"
down_revision: Union[str, None] = "01kjxf5qgx9c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reseller_invitations",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("reseller_id", sa.String(26), sa.ForeignKey("resellers.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_reseller_invitations_reseller_id", "reseller_invitations", ["reseller_id"])
    op.create_index("ix_reseller_invitations_email_status", "reseller_invitations", ["email", "status"])
    op.execute(
        "CREATE UNIQUE INDEX uq_reseller_invitation_pending "
        "ON reseller_invitations (reseller_id, email) "
        "WHERE status = 'pending'"
    )


def downgrade() -> None:
    op.drop_index("uq_reseller_invitation_pending", table_name="reseller_invitations")
    op.drop_index("ix_reseller_invitations_email_status", table_name="reseller_invitations")
    op.drop_index("ix_reseller_invitations_reseller_id", table_name="reseller_invitations")
    op.drop_table("reseller_invitations")
