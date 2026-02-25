from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.checklist.domain.exceptions import ChecklistItemNotFoundError
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface


@dataclass
class RemoveChecklistItemCommand(Command):
    item_id: str


class RemoveChecklistItemCommandHandler(CommandHandler[RemoveChecklistItemCommand]):
    def __init__(self, repo: ChecklistItemRepositoryInterface):
        self.repo = repo

    def handle(self, command: RemoveChecklistItemCommand) -> None:
        item = self.repo.find_by_id(command.item_id)
        if not item:
            raise ChecklistItemNotFoundError(command.item_id)

        self.repo.delete(command.item_id)
