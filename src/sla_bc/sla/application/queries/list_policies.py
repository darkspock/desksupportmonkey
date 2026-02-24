from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface


@dataclass
class SlaPolicyDto:
    id: str
    company_id: str
    name: str
    priority: str
    request_type: Optional[str]
    response_time_hours: float
    resolution_time_hours: float
    warning_threshold_pct: int
    escalate_on_breach: bool
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


@dataclass
class ListSlaPoliciesQuery(Query):
    company_id: str
    is_active: Optional[bool] = None


class ListSlaPoliciesQueryHandler(
    QueryHandler[ListSlaPoliciesQuery, list[SlaPolicyDto]]
):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, query: ListSlaPoliciesQuery) -> list[SlaPolicyDto]:
        policies = self.sla_repo.find_policies(
            company_id=query.company_id,
            is_active=query.is_active,
        )
        return [
            SlaPolicyDto(
                id=p.id,
                company_id=p.company_id,
                name=p.name,
                priority=p.priority,
                request_type=p.request_type,
                response_time_hours=p.response_time_hours,
                resolution_time_hours=p.resolution_time_hours,
                warning_threshold_pct=p.warning_threshold_pct,
                escalate_on_breach=p.escalate_on_breach,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in policies
        ]
