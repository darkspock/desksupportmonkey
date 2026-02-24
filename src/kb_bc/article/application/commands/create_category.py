from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.kb_bc.article.domain.entities import ArticleCategory
from src.kb_bc.article.domain.repository import ArticleRepositoryInterface


@dataclass
class CreateCategoryCommand(Command):
    category_id: str
    company_id: str
    name: str
    sort_order: int = 0
    description: Optional[str] = None


class CreateCategoryCommandHandler(CommandHandler[CreateCategoryCommand]):
    def __init__(self, article_repo: ArticleRepositoryInterface):
        self.article_repo = article_repo

    def handle(self, command: CreateCategoryCommand) -> None:
        category = ArticleCategory.create(
            company_id=command.company_id,
            name=command.name,
            sort_order=command.sort_order,
            description=command.description,
            id=command.category_id,
        )
        self.article_repo.save_category(category)
