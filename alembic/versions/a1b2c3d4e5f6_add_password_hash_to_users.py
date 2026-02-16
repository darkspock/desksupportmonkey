"""add_password_hash_to_users

Revision ID: a1b2c3d4e5f6
Revises: dfae9268fd2d
Create Date: 2026-02-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'dfae9268fd2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
