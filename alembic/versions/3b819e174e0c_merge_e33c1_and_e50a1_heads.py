"""merge_e33c1_and_e50a1_heads

Revision ID: 3b819e174e0c
Revises: e33c1, e50a1
Create Date: 2026-02-28 17:04:27.729915

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b819e174e0c'
down_revision: Union[str, None] = ('e33c1', 'e50a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
