from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.kb_bc.article.domain.exceptions import ArticleNotFoundError
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class ArticleVersionDto:
    id: str
    version_number: int
    title: str
    content: str
    edited_by: str
    editor_name: Optional[str]
    created_at: Optional[datetime]


@dataclass
class GetArticleVersionsQuery(Query):
    article_id: str
    company_id: str


class GetArticleVersionsQueryHandler(
    QueryHandler[GetArticleVersionsQuery, list[ArticleVersionDto]]
):
    def __init__(
        self,
        article_repo: ArticleRepositoryInterface,
        user_name_resolver: Optional[Callable[[list[str]], dict[str, str]]] = None,
    ):
        self.article_repo = article_repo
        self.user_name_resolver = user_name_resolver

    def handle(
        self, query: GetArticleVersionsQuery
    ) -> list[ArticleVersionDto]:
        article = self.article_repo.find_by_id(
            query.article_id, query.company_id
        )
        if not article:
            raise ArticleNotFoundError(query.article_id)

        versions = self.article_repo.get_versions(query.article_id)

        name_map: dict[str, str] = {}
        if self.user_name_resolver:
            user_ids = {v.edited_by for v in versions}
            if user_ids:
                name_map = self.user_name_resolver(list(user_ids))

        return [
            ArticleVersionDto(
                id=v.id,
                version_number=v.version_number,
                title=v.title,
                content=v.content,
                edited_by=v.edited_by,
                editor_name=name_map.get(v.edited_by),
                created_at=v.created_at,
            )
            for v in versions
        ]
