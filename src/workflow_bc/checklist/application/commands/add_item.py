from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.workflow_bc.checklist.domain.entities import RequestChecklistItem
from src.workflow_bc.checklist.domain.repository import ChecklistItemRepositoryInterface


@dataclass
class AddChecklistItemCommand(Command):
    request_id: str
    title: str
    description: Optional[str] = None
    assignee_id: Optional[str] = None
    is_required: bool = False


class AddChecklistItemCommandHandler(CommandHandler[AddChecklistItemCommand]):
    def __init__(self, repo: ChecklistItemRepositoryInterface):
        self.repo = repo

    def handle(self, command: AddChecklistItemCommand) -> None:
        existing = self.repo.find_by_request(command.request_id)
        next_order = max((i.sort_order for i in existing), default=-1) + 1

        item = RequestChecklistItem.create(
            request_id=command.request_id,
            title=command.title,
            description=command.description,
            assignee_id=command.assignee_id,
            is_required=command.is_required,
            sort_order=next_order,
        )
        self.repo.save(item)
