from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.entities import ArticleVersion
from src.kb_bc.article.domain.exceptions import ArticleNotFoundError
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class UpdateArticleCommand(Command):
    article_id: str
    company_id: str
    edited_by: str
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    category_id: Optional[str] = None


class UpdateArticleCommandHandler(CommandHandler[UpdateArticleCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: UpdateArticleCommand) -> None:
        article = self.article_repo.find_by_id(
            command.article_id, command.company_id
        )
        if not article:
            raise ArticleNotFoundError(command.article_id)

        article.update_content(
            title=command.title,
            content=command.content,
            excerpt=command.excerpt,
            category_id=command.category_id,
        )
        self.article_repo.save(article)

        # Create new version snapshot
        version_number = self.article_repo.get_latest_version_number(
            article.id
        ) + 1
        version = ArticleVersion.create(
            article_id=article.id,
            version_number=version_number,
            title=article.title,
            content=article.content,
            edited_by=command.edited_by,
        )
        self.article_repo.save_version(version)
