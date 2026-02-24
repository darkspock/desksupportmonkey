from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.exceptions import (
    CategoryHasArticlesError,
    CategoryNotFoundError,
)
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class DeleteCategoryCommand(Command):
    category_id: str
    company_id: str


class DeleteCategoryCommandHandler(CommandHandler[DeleteCategoryCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: DeleteCategoryCommand) -> None:
        category = self.article_repo.find_category_by_id(
            command.category_id, command.company_id
        )
        if not category:
            raise CategoryNotFoundError(command.category_id)

        count = self.article_repo.count_articles_in_category(
            command.category_id
        )
        if count > 0:
            raise CategoryHasArticlesError(command.category_id)

        self.article_repo.delete_category(
            command.category_id, command.company_id
        )
