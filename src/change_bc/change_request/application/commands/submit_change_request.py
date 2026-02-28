from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
)
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class SubmitChangeRequestCommand(Command):
    change_id: str
    company_id: str
    performed_by: str


class SubmitChangeRequestCommandHandler(
    CommandHandler[SubmitChangeRequestCommand]
):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: SubmitChangeRequestCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        change.submit()
        self.change_repo.save(change)

        auto_approved = change.status == ChangeStatus.SCHEDULED
        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.SUBMITTED,
            description=f"Change submitted ({change.change_type.value})",
            actor_id=command.performed_by,
            metadata={"auto_approved": auto_approved},
        )
        self.change_repo.save_event(event)
