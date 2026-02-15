from dataclasses import dataclass

from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.repository import RequestRepositoryInterface
from src.auth_bc.user.domain.repository import UserRepositoryInterface


class RequestNotFoundError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserInactiveError(Exception):
    pass


@dataclass
class AssignRequestCommand:
    request_id: str
    company_id: str
    user_id: str
    performed_by: str


class AssignRequestCommandHandler:
    def __init__(
        self,
        request_repo: RequestRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.request_repo = request_repo
        self.user_repo = user_repo

    def handle(self, command: AssignRequestCommand) -> ServiceRequest:
        request = self.request_repo.find_by_id(command.request_id, command.company_id)
        if not request:
            raise RequestNotFoundError(f"Request '{command.request_id}' not found")

        user = self.user_repo.find_by_id_and_company(command.user_id, command.company_id)
        if not user:
            raise UserNotFoundError(f"User '{command.user_id}' not found")

        if not user.is_active:
            raise UserInactiveError(f"User '{command.user_id}' is inactive")

        request.assign(command.user_id)
        request = self.request_repo.save(request)

        event = RequestEvent.create(
            request_id=request.id,
            event_type="assigned",
            data={
                "assigned_to": command.user_id,
                "assigned_by": command.performed_by,
            },
            performed_by=command.performed_by,
        )
        self.request_repo.save_event(event)

        return request
