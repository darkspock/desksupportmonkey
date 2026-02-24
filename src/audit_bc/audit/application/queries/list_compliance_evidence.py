from dataclasses import dataclass

from src.audit_bc.audit.application.dtos import ComplianceEvidenceDto
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class ListComplianceEvidenceQuery(Query):
    company_id: str
    control_id: str


class ListComplianceEvidenceQueryHandler(
    QueryHandler[
        ListComplianceEvidenceQuery, list[ComplianceEvidenceDto]
    ]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: ListComplianceEvidenceQuery
    ) -> list[ComplianceEvidenceDto]:
        evidence_list = self.repo.find_evidence_by_control(
            query.control_id, query.company_id
        )
        return [
            ComplianceEvidenceDto(
                id=e.id,
                control_id=e.control_id,
                evidence_type=e.evidence_type.value,
                reference_id=e.reference_id,
                title=e.title,
                description=e.description,
                url=e.url,
                added_by=e.added_by,
                created_at=e.created_at,
            )
            for e in evidence_list
        ]
