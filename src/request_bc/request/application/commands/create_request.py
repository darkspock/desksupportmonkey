from dataclasses import dataclass
from typing import Optional

from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import RequestType
from src.request_bc.request.domain.repository import RequestRepositoryInterface


@dataclass
class CreateRequestCommand:
    company_id: str
    created_by: str
    type: str
    title: str
    description: str
    data: Optional[dict] = None


class CreateRequestCommandHandler:
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: CreateRequestCommand) -> ServiceRequest:
        request_type = RequestType(command.type)

        request = ServiceRequest.create(
            company_id=command.company_id,
            created_by=command.created_by,
            type=request_type,
            title=command.title,
            description=command.description,
            data=command.data,
        )

        request = self.request_repo.save(request)

        event = RequestEvent.create(
            request_id=request.id,
            event_type="created",
            data={
                "type": request.type.value,
                "title": request.title,
                "priority": request.priority.value,
            },
            performed_by=command.created_by,
        )
        self.request_repo.save_event(event)

        return request
