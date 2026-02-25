from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.checklist.domain.exceptions import ChecklistItemNotFoundError
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface


@dataclass
class AssignChecklistItemCommand(Command):
    item_id: str
    assignee_id: Optional[str]


class AssignChecklistItemCommandHandler(CommandHandler[AssignChecklistItemCommand]):
    def __init__(self, repo: ChecklistItemRepositoryInterface):
        self.repo = repo

    def handle(self, command: AssignChecklistItemCommand) -> None:
        item = self.repo.find_by_id(command.item_id)
        if not item:
            raise ChecklistItemNotFoundError(command.item_id)

        item.assign(command.assignee_id)
        self.repo.save(item)
