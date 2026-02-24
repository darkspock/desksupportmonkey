from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class ArticleListDto:
    id: str
    title: str
    slug: str
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
class ListArticlesQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    category_id: Optional[str] = None
    search: Optional[str] = None


class ListArticlesQueryHandler(
    QueryHandler[ListArticlesQuery, tuple[list[ArticleListDto], int]]
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

    def handle(
        self, query: ListArticlesQuery
    ) -> tuple[list[ArticleListDto], int]:
        filters = {
            "page": query.page,
            "page_size": query.page_size,
            "status": query.status,
            "category_id": query.category_id,
            "search": query.search,
        }
        articles, total = self.article_repo.find_all(
            query.company_id, filters
        )

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {a.author_id for a in articles}
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        cat_map: dict[str, str] = {}
        if self.category_name_resolver:
            cat_ids = {a.category_id for a in articles if a.category_id}
            if cat_ids:
                cat_map = self.category_name_resolver(list(cat_ids))

        dtos = [
            ArticleListDto(
                id=a.id,
                title=a.title,
                slug=a.slug,
                excerpt=a.excerpt,
                category_id=a.category_id,
                category_name=(
                    cat_map.get(a.category_id) if a.category_id else None
                ),
                status=a.status.value,
                author_id=a.author_id,
                author_name=name_map.get(a.author_id),
                view_count=a.view_count,
                published_at=a.published_at,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
            for a in articles
        ]
        return dtos, total
