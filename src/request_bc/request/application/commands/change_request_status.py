from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import RequestStatus
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class ChangeRequestStatusCommand(Command):
    request_id: str
    company_id: str
    new_status: str
    performed_by: str


class ChangeRequestStatusCommandHandler(CommandHandler[ChangeRequestStatusCommand]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: ChangeRequestStatusCommand) -> None:
        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{command.request_id}' not found")

        old_status = request.status
        new_status = RequestStatus(command.new_status)

        request.change_status(new_status)

        # Track first response time for SLA measurement
        if old_status == RequestStatus.SUBMITTED and new_status not in (
            RequestStatus.REJECTED,
        ):
            request.record_first_response()

        # Auto-assign side effect: if moving to in_review and unassigned,
        # assign to the acting technician
        auto_assigned = False
        if new_status == RequestStatus.IN_REVIEW and request.assigned_to is None:
            request.assign(command.performed_by)
            auto_assigned = True

        self.request_repo.save(request)

        event = RequestEvent.create(
            request_id=request.id,
            event_type="status_changed",
            data={"old_status": old_status.value, "new_status": new_status.value},
            performed_by=command.performed_by,
        )
        self.request_repo.save_event(event)

        if auto_assigned:
            assign_event = RequestEvent.create(
                request_id=request.id,
                event_type="assigned",
                data={"assigned_to": command.performed_by, "reason": "auto_assign_on_review"},
                performed_by=command.performed_by,
            )
            self.request_repo.save_event(assign_event)
