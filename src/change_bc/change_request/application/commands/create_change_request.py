from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent, ChangeRequest
from src.change_bc.change_request.domain.enums import ChangeEventType, ChangeType
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class CreateChangeRequestCommand(Command):
    change_id: str
    company_id: str
    requested_by: str
    title: str
    change_type: str = "standard"
    planned_date: Optional[datetime] = None
    rollback_plan: Optional[str] = None


class CreateChangeRequestCommandHandler(
    CommandHandler[CreateChangeRequestCommand]
):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: CreateChangeRequestCommand) -> None:
        change = ChangeRequest.create(
            id=command.change_id,
            company_id=command.company_id,
            requested_by=command.requested_by,
            title=command.title,
            change_type=ChangeType(command.change_type),
            planned_date=command.planned_date,
            rollback_plan=command.rollback_plan,
        )
        self.change_repo.save(change)

        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.CREATED,
            description="Change request created",
            actor_id=command.requested_by,
        )
        self.change_repo.save_event(event)
