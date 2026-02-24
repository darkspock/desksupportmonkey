from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.exceptions import CategoryNotFoundError
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class UpdateCategoryCommand(Command):
    category_id: str
    company_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None


class UpdateCategoryCommandHandler(CommandHandler[UpdateCategoryCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: UpdateCategoryCommand) -> None:
        category = self.article_repo.find_category_by_id(
            command.category_id, command.company_id
        )
        if not category:
            raise CategoryNotFoundError(command.category_id)

        category.update(
            name=command.name,
            description=command.description,
            sort_order=command.sort_order,
        )
        self.article_repo.save_category(category)
