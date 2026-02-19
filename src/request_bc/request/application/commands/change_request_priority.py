from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import RequestPriority
from src.request_bc.request.domain.repository import RequestRepositoryInterface


class RequestNotFoundError(Exception):
    pass


@dataclass
class ChangeRequestPriorityCommand(Command):
    request_id: str
    company_id: str
    new_priority: str
    performed_by: str


class ChangeRequestPriorityCommandHandler(CommandHandler[ChangeRequestPriorityCommand]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: ChangeRequestPriorityCommand) -> None:
        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{command.request_id}' not found")

        old_priority = request.priority
        new_priority = RequestPriority(command.new_priority)

        request.change_priority(new_priority)

        self.request_repo.save(request)

        event = RequestEvent.create(
            request_id=request.id,
            event_type="priority_changed",
            data={"old_priority": old_priority.value, "new_priority": new_priority.value},
            performed_by=command.performed_by,
        )
        self.request_repo.save_event(event)
