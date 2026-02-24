"""merge_compliance_and_locations_heads

Revision ID: 6873afcf07f7
Revises: c6d7e8f9g0h1, e6f7g8h9i0j1
Create Date: 2026-02-24 11:03:32.137512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6873afcf07f7'
down_revision: Union[str, None] = ('c6d7e8f9g0h1', 'e6f7g8h9i0j1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
