from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.kb_bc.article.domain.exceptions import ArticleNotFoundError
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class ArticleDetailDto:
    id: str
    title: str
    slug: str
    content: str
    excerpt: Optional[str]
    category_id: Optional[str]
    category_name: Optional[str]
    status: str
    author_id: str
    author_name: Optional[str]
    view_count: int
    published_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class GetArticleDetailQuery(Query):
    article_id: str
    company_id: str
    increment_view: bool = False


class GetArticleDetailQueryHandler(
    QueryHandler[GetArticleDetailQuery, ArticleDetailDto]
):
    def __init__(
        self,
        article_repo: ArticleRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
        category_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.article_repo = article_repo
        self.user_name_resolver = user_name_resolver
        self.category_name_resolver = category_name_resolver

    def handle(self, query: GetArticleDetailQuery) -> ArticleDetailDto:
        article = self.article_repo.find_by_id(
            query.article_id, query.company_id
        )
        if not article:
            raise ArticleNotFoundError(query.article_id)

        if query.increment_view:
            article.increment_view_count()
            self.article_repo.save(article)

        author_name = None
        if self.user_name_resolver:
            names = self.user_name_resolver([article.author_id])
            author_name = names.get(article.author_id)

        category_name = None
        if self.category_name_resolver and article.category_id:
            cats = self.category_name_resolver([article.category_id])
            category_name = cats.get(article.category_id)

        return ArticleDetailDto(
            id=article.id,
            title=article.title,
            slug=article.slug,
            content=article.content,
            excerpt=article.excerpt,
            category_id=article.category_id,
            category_name=category_name,
            status=article.status.value,
            author_id=article.author_id,
            author_name=author_name,
            view_count=article.view_count,
            published_at=article.published_at,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
