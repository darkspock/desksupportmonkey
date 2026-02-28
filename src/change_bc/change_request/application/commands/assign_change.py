from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent
from src.change_bc.change_request.domain.enums import ChangeEventType
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class AssignChangeCommand(Command):
    change_id: str
    company_id: str
    performed_by: str
    assigned_to: str


class AssignChangeCommandHandler(CommandHandler[AssignChangeCommand]):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: AssignChangeCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        change.assign(command.assigned_to)
        self.change_repo.save(change)

        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.ASSIGNED,
            description=f"Change assigned to {command.assigned_to}",
            actor_id=command.performed_by,
            metadata={"assigned_to": command.assigned_to},
        )
        self.change_repo.save_event(event)
