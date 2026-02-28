from dataclasses import dataclass

from src.company_bc.sla_escalation_config.domain.repository import (
    SlaEscalationConfigRepositoryInterface,
)
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class SlaEscalationConfigDto:
    enabled: bool


@dataclass
class GetSlaEscalationConfigQuery(Query):
    company_id: str


class GetSlaEscalationConfigQueryHandler(
    QueryHandler[GetSlaEscalationConfigQuery, SlaEscalationConfigDto],
):
    def __init__(
        self,
        config_repo: SlaEscalationConfigRepositoryInterface,
    ):
        self.config_repo = config_repo

    def handle(
        self, query: GetSlaEscalationConfigQuery,
    ) -> SlaEscalationConfigDto:
        config = self.config_repo.find_by_company(query.company_id)
        if config:
            return SlaEscalationConfigDto(enabled=config.enabled)
        return SlaEscalationConfigDto(enabled=True)
