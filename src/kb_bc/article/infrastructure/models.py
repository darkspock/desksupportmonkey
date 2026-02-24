from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base
from core.mixins import TimestampMixin, ULIDMixin


class ArticleCategoryModel(ULIDMixin, Base):
    __tablename__ = "article_categories"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    __table_args__ = (
        Index("ix_article_categories_company", "company_id"),
        UniqueConstraint(
            "company_id", "slug", name="uq_article_categories_company_slug"
        ),
    )


class ArticleModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "articles"

    company_id: Mapped[str] = mapped_column(String(26), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(350), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    category_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="draft"
    )
    author_id: Mapped[str] = mapped_column(String(26), nullable=False)
    view_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("ix_articles_company_status", "company_id", "status"),
        Index("ix_articles_company_category", "company_id", "category_id"),
        UniqueConstraint("company_id", "slug", name="uq_articles_company_slug"),
    )


class ArticleVersionModel(ULIDMixin, Base):
    __tablename__ = "article_versions"

    article_id: Mapped[str] = mapped_column(String(26), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    edited_by: Mapped[str] = mapped_column(String(26), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    __table_args__ = (
        Index("ix_article_versions_article", "article_id"),
    )
