from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.entities import Article, ArticleVersion
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class CreateArticleCommand(Command):
    article_id: str
    company_id: str
    title: str
    content: str
    author_id: str
    excerpt: Optional[str] = None
    category_id: Optional[str] = None


class CreateArticleCommandHandler(CommandHandler[CreateArticleCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: CreateArticleCommand) -> None:
        article = Article.create(
            company_id=command.company_id,
            title=command.title,
            content=command.content,
            author_id=command.author_id,
            excerpt=command.excerpt,
            category_id=command.category_id,
            id=command.article_id,
        )
        self.article_repo.save(article)

        version = ArticleVersion.create(
            article_id=article.id,
            version_number=1,
            title=article.title,
            content=article.content,
            edited_by=command.author_id,
        )
        self.article_repo.save_version(version)
