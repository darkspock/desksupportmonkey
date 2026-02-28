"""create post_implementation_reviews table

Revision ID: e33c1
Revises: e33b1
Create Date: 2026-02-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "e33c1"
down_revision: Union[str, None] = "e33b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "post_implementation_reviews",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column(
            "change_request_id",
            sa.String(26),
            sa.ForeignKey("change_requests.id"),
            nullable=False,
        ),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("issues_found", sa.Text, nullable=True),
        sa.Column("lessons_learned", sa.Text, nullable=True),
        sa.Column("follow_up_actions", sa.Text, nullable=True),
        sa.Column("created_by", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "change_request_id",
            name="uq_pir_change_request",
        ),
    )
    op.create_index(
        "ix_pir_change_request_id",
        "post_implementation_reviews",
        ["change_request_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_pir_change_request_id",
        table_name="post_implementation_reviews",
    )
    op.drop_table("post_implementation_reviews")
