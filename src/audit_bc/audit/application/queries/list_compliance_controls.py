from dataclasses import dataclass

from src.audit_bc.audit.application.dtos import ComplianceControlDto
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListComplianceControlsQuery(Query):
    company_id: str


class ListComplianceControlsQueryHandler(
    QueryHandler[ListComplianceControlsQuery, list[ComplianceControlDto]]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: ListComplianceControlsQuery
    ) -> list[ComplianceControlDto]:
        controls = self.repo.find_controls(query.company_id)
        return [
            ComplianceControlDto(
                id=c.id,
                code=c.code,
                name=c.name,
                framework=c.framework,
                description=c.description,
                is_predefined=c.is_predefined,
                is_active=c.is_active,
                created_at=c.created_at,
            )
            for c in controls
        ]
