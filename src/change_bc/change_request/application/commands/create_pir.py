from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.change_bc.change_request.domain.entities import (
    ChangeEvent,
    PostImplementationReview,
)
from src.change_bc.change_request.domain.enums import (
    ChangeEventType,
    ChangeStatus,
    InvalidStatusTransitionError,
    PIROutcome,
)
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotFoundError,
    PIRAlreadyExistsError,
    UnauthorizedApprovalError,
)
from src.change_bc.change_request.domain.repository import (
    ChangeRequestRepositoryInterface,
)


@dataclass
class CreatePIRCommand(Command):
    change_id: str
    company_id: str
    outcome: str
    issues_found: Optional[str]
    lessons_learned: Optional[str]
    follow_up_actions: Optional[str]
    performed_by: str
    performed_by_role: str


class CreatePIRCommandHandler(CommandHandler[CreatePIRCommand]):
    def __init__(
        self, change_repo: ChangeRequestRepositoryInterface
    ):
        self.change_repo = change_repo

    def handle(self, command: CreatePIRCommand) -> None:
        change = self.change_repo.find_by_id(
            command.change_id, command.company_id
        )
        if not change:
            raise ChangeNotFoundError(command.change_id)

        if command.performed_by_role not in ("admin", "super_admin"):
            raise UnauthorizedApprovalError()

        if change.status != ChangeStatus.IMPLEMENTED:
            raise InvalidStatusTransitionError(
                change.status, ChangeStatus.IMPLEMENTED
            )

        existing = self.change_repo.find_pir_by_change(command.change_id)
        if existing:
            raise PIRAlreadyExistsError(command.change_id)

        pir = PostImplementationReview.create(
            change_request_id=command.change_id,
            outcome=PIROutcome(command.outcome),
            created_by=command.performed_by,
            issues_found=command.issues_found,
            lessons_learned=command.lessons_learned,
            follow_up_actions=command.follow_up_actions,
        )
        self.change_repo.save_pir(pir)

        event = ChangeEvent.create(
            change_request_id=command.change_id,
            event_type=ChangeEventType.PIR_ADDED,
            description="Post-implementation review added",
            actor_id=command.performed_by,
        )
        self.change_repo.save_event(event)
