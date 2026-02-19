from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import RequestStatus
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


class NotPendingApprovalError(Exception):
    pass


class UnauthorizedRejectionError(Exception):
    pass


@dataclass
class RejectRequestCommand(Command):
    request_id: str
    company_id: str
    performed_by: str
    performed_by_role: str
    reason: str
    department_manager_id: str | None = None


class RejectRequestCommandHandler(CommandHandler[RejectRequestCommand]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: RejectRequestCommand) -> None:
        if not command.reason or not command.reason.strip():
            raise ValueError("Rejection reason is required")

        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError("Request not found")

        if request.status != RequestStatus.PENDING_APPROVAL:
            raise NotPendingApprovalError(
                f"Request is not pending approval (current status: {request.status.value})"
            )

        is_admin = command.performed_by_role in ("admin", "super_admin")
        is_manager = (
            command.department_manager_id is not None
            and command.performed_by == command.department_manager_id
        )
        if not is_admin and not is_manager:
            raise UnauthorizedRejectionError(
                "Only the department manager or an admin can reject this request"
            )

        request.change_status(RequestStatus.REJECTED)
        self.request_repo.save(request)

        event = RequestEvent.create(
            request_id=request.id,
            event_type="rejected",
            data={
                "rejected_by": command.performed_by,
                "reason": command.reason.strip(),
            },
            performed_by=command.performed_by,
        )
        self.request_repo.save_event(event)
