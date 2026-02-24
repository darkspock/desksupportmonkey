"""create_kb_tables

Revision ID: z3b4c5d6e7f8
Revises: y2a3b4c5d6e7
Create Date: 2026-02-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "z3b4c5d6e7f8"
down_revision: Union[str, None] = "y2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. article_categories
    op.create_table(
        "article_categories",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("description", sa.String(300), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_article_categories_company", "article_categories", ["company_id"]
    )
    op.create_unique_constraint(
        "uq_article_categories_company_slug",
        "article_categories",
        ["company_id", "slug"],
    )

    # 2. articles
    op.create_table(
        "articles",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("company_id", sa.String(26), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("slug", sa.String(350), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.String(500), nullable=True),
        sa.Column("category_id", sa.String(26), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("author_id", sa.String(26), nullable=False),
        sa.Column("view_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_articles_company_status", "articles", ["company_id", "status"]
    )
    op.create_index(
        "ix_articles_company_category", "articles", ["company_id", "category_id"]
    )
    op.create_unique_constraint(
        "uq_articles_company_slug", "articles", ["company_id", "slug"]
    )

    # 3. article_versions
    op.create_table(
        "article_versions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("article_id", sa.String(26), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("edited_by", sa.String(26), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_article_versions_article", "article_versions", ["article_id"]
    )


def downgrade() -> None:
    op.drop_table("article_versions")
    op.drop_table("articles")
    op.drop_table("article_categories")
