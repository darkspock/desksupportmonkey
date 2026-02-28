from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent
from src.change_bc.change_request.domain.enums import ChangeEventType, ChangeType
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    PIRRequiredForEmergencyCloseError,
    UnauthorizedApprovalError,
)
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class CloseChangeCommand(Command):
    change_id: str
    company_id: str
    performed_by: str
    performed_by_role: str


class CloseChangeCommandHandler(CommandHandler[CloseChangeCommand]):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: CloseChangeCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        if command.performed_by_role not in ("admin", "super_admin"):
            raise UnauthorizedApprovalError()

        if change.change_type == ChangeType.EMERGENCY:
            pir = self.change_repo.find_pir_by_change(change.id)
            if not pir:
                raise PIRRequiredForEmergencyCloseError()

        change.close()
        self.change_repo.save(change)

        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.CLOSED,
            description="Change closed",
            actor_id=command.performed_by,
        )
        self.change_repo.save_event(event)
