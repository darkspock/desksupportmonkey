from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import ChangeEvent, ChangeRequest
from src.change_bc.change_request.domain.enums import ChangeEventType, ChangeType
from src.change_bc.change_request.domain.exceptions import ChangeNotFoundError
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class UpdateChangeRequestCommand(Command):
    change_id: str
    company_id: str
    performed_by: str
    title: Optional[str] = None
    description: Optional[str] = None
    change_type: Optional[str] = None
    business_justification: Optional[str] = None
    risk_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None
    planned_date: Optional[datetime] = None


class UpdateChangeRequestCommandHandler(
    CommandHandler[UpdateChangeRequestCommand]
):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: UpdateChangeRequestCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        change.update_details(
            title=command.title,
            description=command.description,
            change_type=ChangeType(command.change_type) if command.change_type else None,
            business_justification=command.business_justification,
            risk_assessment=command.risk_assessment,
            rollback_plan=command.rollback_plan,
            planned_date=command.planned_date,
        )
        self.change_repo.save(change)

        event = ChangeEvent.create(
            change_request_id=change.id,
            event_type=ChangeEventType.UPDATED,
            description="Change request updated",
            actor_id=command.performed_by,
        )
        self.change_repo.save_event(event)
