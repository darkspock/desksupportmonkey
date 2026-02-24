"""merge_custom_fields_branch

Revision ID: 2853b6e6873f
Revises: 6873afcf07f7, k2l3m4n5o6p7
Create Date: 2026-02-24 15:40:43.952433

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2853b6e6873f'
down_revision: Union[str, None] = ('6873afcf07f7', 'k2l3m4n5o6p7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
