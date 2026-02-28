from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent
from src.change_bc.change_request.domain.enums import ChangeEventType
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class ImplementChangeCommand(Command):
    change_id: str
    company_id: str
    performed_by: str
    notes: Optional[str] = None


class ImplementChangeCommandHandler(
    CommandHandler[ImplementChangeCommand]
):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: ImplementChangeCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        change.implement(notes=command.notes)
        self.change_repo.save(change)

        metadata = {"notes": command.notes} if command.notes else None
        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.IMPLEMENTED,
            description="Change implemented",
            actor_id=command.performed_by,
            metadata=metadata,
        )
        self.change_repo.save_event(event)
