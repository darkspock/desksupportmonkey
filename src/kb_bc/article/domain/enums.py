from enum import Enum


class ArticleStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


VALID_ARTICLE_STATUS_TRANSITIONS: dict[ArticleStatus, list[ArticleStatus]] = {
    ArticleStatus.DRAFT: [ArticleStatus.PUBLISHED],
    ArticleStatus.PUBLISHED: [ArticleStatus.DRAFT, ArticleStatus.ARCHIVED],
    ArticleStatus.ARCHIVED: [ArticleStatus.DRAFT],
}
