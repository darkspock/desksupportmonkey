import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import ulid

from src.kb_bc.article.domain.enums import (
    ArticleStatus,
    VALID_ARTICLE_STATUS_TRANSITIONS,
)
from src.kb_bc.article.domain.exceptions import (
    ArticleDraftOnlyDeleteError,
    InvalidArticleStatusTransitionError,
)


def generate_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug[:120]


@dataclass
class Article:
    id: str
    company_id: str
    title: str
    slug: str
    content: str
    status: ArticleStatus
    author_id: str
    view_count: int
    excerpt: Optional[str] = None
    category_id: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        title: str,
        content: str,
        author_id: str,
        excerpt: Optional[str] = None,
        category_id: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "Article":
        if not title or not title.strip():
            raise ValueError("Title is required")
        if not content or not content.strip():
            raise ValueError("Content is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            title=title.strip(),
            slug=generate_slug(title),
            content=content.strip(),
            status=ArticleStatus.DRAFT,
            author_id=author_id,
            view_count=0,
            excerpt=excerpt.strip() if excerpt else None,
            category_id=category_id,
        )

    def publish(self) -> None:
        self._change_status(ArticleStatus.PUBLISHED)
        if not self.published_at:
            self.published_at = datetime.now(timezone.utc)

    def unpublish(self) -> None:
        self._change_status(ArticleStatus.DRAFT)

    def archive(self) -> None:
        self._change_status(ArticleStatus.ARCHIVED)

    def restore(self) -> None:
        self._change_status(ArticleStatus.DRAFT)

    def update_content(
        self,
        title: Optional[str] = None,
        content: Optional[str] = None,
        excerpt: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> None:
        if title is not None:
            if not title.strip():
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
            self.slug = generate_slug(title)
        if content is not None:
            if not content.strip():
                raise ValueError("Content cannot be empty")
            self.content = content.strip()
        if excerpt is not None:
            self.excerpt = excerpt.strip() if excerpt else None
        if category_id is not None:
            self.category_id = category_id if category_id else None

    def increment_view_count(self) -> None:
        self.view_count += 1

    def validate_can_delete(self) -> None:
        if self.status != ArticleStatus.DRAFT:
            raise ArticleDraftOnlyDeleteError()

    def _change_status(self, new_status: ArticleStatus) -> None:
        valid_targets = VALID_ARTICLE_STATUS_TRANSITIONS.get(self.status, [])
        if new_status not in valid_targets:
            raise InvalidArticleStatusTransitionError(
                self.status.value, new_status.value
            )
        self.status = new_status


@dataclass
class ArticleCategory:
    id: str
    company_id: str
    name: str
    slug: str
    sort_order: int
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        name: str,
        sort_order: int = 0,
        description: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "ArticleCategory":
        if not name or not name.strip():
            raise ValueError("Category name is required")
        return cls(
            id=id or str(ulid.new()),
            company_id=company_id,
            name=name.strip(),
            slug=generate_slug(name),
            sort_order=sort_order,
            description=description.strip() if description else None,
        )

    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: Optional[int] = None,
    ) -> None:
        if name is not None:
            if not name.strip():
                raise ValueError("Category name cannot be empty")
            self.name = name.strip()
            self.slug = generate_slug(name)
        if description is not None:
            self.description = description.strip() if description else None
        if sort_order is not None:
            self.sort_order = sort_order


@dataclass
class ArticleVersion:
    id: str
    article_id: str
    version_number: int
    title: str
    content: str
    edited_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        article_id: str,
        version_number: int,
        title: str,
        content: str,
        edited_by: str,
    ) -> "ArticleVersion":
        return cls(
            id=str(ulid.new()),
            article_id=article_id,
            version_number=version_number,
            title=title,
            content=content,
            edited_by=edited_by,
        )
