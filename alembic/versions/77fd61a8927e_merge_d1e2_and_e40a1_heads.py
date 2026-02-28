"""merge d1e2 and e40a1 heads

Revision ID: 77fd61a8927e
Revises: d1e2f3a4b5c6, e40a1
Create Date: 2026-02-26 23:57:53.830669

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77fd61a8927e'
down_revision: Union[str, None] = ('d1e2f3a4b5c6', 'e40a1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
