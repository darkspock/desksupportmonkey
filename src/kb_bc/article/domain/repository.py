from abc import ABC, abstractmethod
from typing import Optional

from src.kb_bc.article.domain.entities import (
    Article,
    ArticleCategory,
    ArticleVersion,
)


class ArticleRepositoryInterface(ABC):
    # --- Articles ---

    @abstractmethod
    def save(self, article: Article) -> None: ...

    @abstractmethod
    def find_by_id(
        self, article_id: str, company_id: str
    ) -> Optional[Article]: ...

    @abstractmethod
    def find_by_slug(
        self, slug: str, company_id: str
    ) -> Optional[Article]: ...

    @abstractmethod
    def find_all(
        self, company_id: str, filters: dict
    ) -> tuple[list[Article], int]: ...

    @abstractmethod
    def find_published(
        self, company_id: str, filters: dict
    ) -> tuple[list[Article], int]: ...

    @abstractmethod
    def delete(self, article_id: str, company_id: str) -> None: ...

    @abstractmethod
    def search(
        self, company_id: str, query: str, limit: int = 20
    ) -> list[Article]: ...

    @abstractmethod
    def suggest(
        self, company_id: str, text: str, limit: int = 5
    ) -> list[Article]: ...

    # --- Versions ---

    @abstractmethod
    def save_version(self, version: ArticleVersion) -> None: ...

    @abstractmethod
    def get_versions(self, article_id: str) -> list[ArticleVersion]: ...

    @abstractmethod
    def get_latest_version_number(self, article_id: str) -> int: ...

    # --- Categories ---

    @abstractmethod
    def save_category(self, category: ArticleCategory) -> None: ...

    @abstractmethod
    def find_category_by_id(
        self, category_id: str, company_id: str
    ) -> Optional[ArticleCategory]: ...

    @abstractmethod
    def find_all_categories(
        self, company_id: str
    ) -> list[ArticleCategory]: ...

    @abstractmethod
    def delete_category(
        self, category_id: str, company_id: str
    ) -> None: ...

    @abstractmethod
    def count_articles_in_category(self, category_id: str) -> int: ...
