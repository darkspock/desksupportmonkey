"""add asset criticality and BIA columns

Revision ID: e38a1
Revises: e25c1
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa

revision = "e38a1"
down_revision = "e25c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("assets", sa.Column("criticality", sa.String(20), nullable=True))
    op.add_column("assets", sa.Column("impact_score", sa.Integer(), nullable=True))
    op.add_column("assets", sa.Column("rto_minutes", sa.Integer(), nullable=True))
    op.add_column("assets", sa.Column("rpo_minutes", sa.Integer(), nullable=True))
    op.add_column("assets", sa.Column("bia_justification", sa.Text(), nullable=True))
    op.add_column("assets", sa.Column("bia_reviewed_at", sa.DateTime(), nullable=True))
    op.add_column(
        "assets",
        sa.Column(
            "bia_reviewed_by",
            sa.String(26),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_assets_criticality",
        "assets",
        ["criticality"],
        postgresql_where=sa.text("criticality IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_assets_criticality", table_name="assets")
    op.drop_column("assets", "bia_reviewed_by")
    op.drop_column("assets", "bia_reviewed_at")
    op.drop_column("assets", "bia_justification")
    op.drop_column("assets", "rpo_minutes")
    op.drop_column("assets", "rto_minutes")
    op.drop_column("assets", "impact_score")
    op.drop_column("assets", "criticality")
