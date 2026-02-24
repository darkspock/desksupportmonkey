from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.sla_bc.sla.domain.exceptions import SlaPolicyNotFoundError
from src.sla_bc.sla.domain.repository import SlaRepositoryInterface
from src.sla_bc.sla.application.queries.list_policies import SlaPolicyDto


@dataclass
class GetSlaPolicyQuery(Query):
    policy_id: str
    company_id: str


class GetSlaPolicyQueryHandler(QueryHandler[GetSlaPolicyQuery, SlaPolicyDto]):
    def __init__(self, sla_repo: SlaRepositoryInterface):
        self.sla_repo = sla_repo

    def handle(self, query: GetSlaPolicyQuery) -> SlaPolicyDto:
        policy = self.sla_repo.find_policy_by_id(
            query.policy_id, query.company_id
        )
        if not policy:
            raise SlaPolicyNotFoundError(query.policy_id)

        return SlaPolicyDto(
            id=policy.id,
            company_id=policy.company_id,
            name=policy.name,
            priority=policy.priority,
            request_type=policy.request_type,
            response_time_hours=policy.response_time_hours,
            resolution_time_hours=policy.resolution_time_hours,
            warning_threshold_pct=policy.warning_threshold_pct,
            escalate_on_breach=policy.escalate_on_breach,
            is_active=policy.is_active,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        )
