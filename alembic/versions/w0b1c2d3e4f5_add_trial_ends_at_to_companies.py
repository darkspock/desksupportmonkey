"""add_trial_ends_at_to_companies

Revision ID: w0b1c2d3e4f5
Revises: v9a0b1c2d3e4
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa

revision = 'w0b1c2d3e4f5'
down_revision = 'v9a0b1c2d3e4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'companies',
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('companies', 'trial_ends_at')
