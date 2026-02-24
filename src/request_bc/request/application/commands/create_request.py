from dataclasses import dataclass
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.request_bc.request.application.services.priority_scorer import PriorityScorer
from src.request_bc.request.domain.entities import RequestEvent, ServiceRequest
from src.request_bc.request.domain.enums import RequestType
from src.request_bc.request.domain.repository import RequestRepositoryInterface


@dataclass
class CreateRequestCommand(Command):
    company_id: str
    created_by: str
    type: str
    title: str
    description: str
    data: Optional[dict] = None
    id: Optional[str] = None
    subtype: Optional[str] = None
    department_priority_weight: int = 0
    user_role: str = "employee"
    department_has_manager: bool = False
    ai_priority_hint: int = 0
    ai_classification: Optional[dict] = None
    custom_fields_data: Optional[dict] = None


class CreateRequestCommandHandler(CommandHandler[CreateRequestCommand]):
    def __init__(self, request_repo: RequestRepositoryInterface):
        self.request_repo = request_repo

    def handle(self, command: CreateRequestCommand) -> None:
        request_type = RequestType(command.type)

        scorer = PriorityScorer()
        priority, scoring_breakdown = scorer.compute(
            request_type=request_type,
            subtype=command.subtype,
            department_priority_weight=command.department_priority_weight,
            user_role=command.user_role,
            ai_priority_hint=command.ai_priority_hint,
        )

        data = dict(command.data) if command.data else {}
        data["priority_scoring"] = scoring_breakdown
        if command.ai_classification is not None:
            data["ai_classification"] = command.ai_classification

        requires_approval = (
            request_type == RequestType.NEW_EQUIPMENT and command.department_has_manager
        )

        request = ServiceRequest.create(
            company_id=command.company_id,
            created_by=command.created_by,
            type=request_type,
            title=command.title,
            description=command.description,
            data=data,
            id=command.id,
            subtype=command.subtype,
            requires_approval=requires_approval,
            custom_fields_data=command.custom_fields_data,
        )
        request.priority = priority

        self.request_repo.save(request)

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
