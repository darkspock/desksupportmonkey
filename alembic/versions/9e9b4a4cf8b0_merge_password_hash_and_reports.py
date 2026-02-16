"""merge_password_hash_and_reports

Revision ID: 9e9b4a4cf8b0
Revises: 4780252b7cdd, a1b2c3d4e5f6
Create Date: 2026-02-16 13:22:02.464903

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9e9b4a4cf8b0'
down_revision: Union[str, None] = ('4780252b7cdd', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
