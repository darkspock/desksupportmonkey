from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.exceptions import ArticleNotFoundError
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class RestoreArticleCommand(Command):
    article_id: str
    company_id: str


class RestoreArticleCommandHandler(CommandHandler[RestoreArticleCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: RestoreArticleCommand) -> None:
        article = self.article_repo.find_by_id(
            command.article_id, command.company_id
        )
        if not article:
            raise ArticleNotFoundError(command.article_id)

        article.restore()
        self.article_repo.save(article)
