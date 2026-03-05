"""merge resellers and e53f1 heads

Revision ID: b6e7f8g9h0i1
Revises: a5d6e7f8g9h0, e53f1a001
Create Date: 2026-03-03

"""
from typing import Sequence, Union

revision: str = "b6e7f8g9h0i1"
down_revision: Union[str, tuple[str, ...], None] = ("a5d6e7f8g9h0", "e53f1a001")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
