from dataclasses import dataclass
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class CategoryDto:
    id: str
    name: str
    slug: str
    description: Optional[str]
    sort_order: int
    article_count: int


@dataclass
class ListCategoriesQuery(Query):
    company_id: str


class ListCategoriesQueryHandler(
    QueryHandler[ListCategoriesQuery, list[CategoryDto]]
):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, query: ListCategoriesQuery) -> list[CategoryDto]:
        categories = self.article_repo.find_all_categories(query.company_id)
        return [
            CategoryDto(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                sort_order=c.sort_order,
                article_count=self.article_repo.count_articles_in_category(
                    c.id
                ),
            )
            for c in categories
        ]
