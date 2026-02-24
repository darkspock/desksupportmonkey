from dataclasses import dataclass
from typing import Optional

from src.audit_bc.audit.application.dtos import ControlAssessmentDto
from src.audit_bc.audit.domain.enums import ComplianceStatus
from src.audit_bc.audit.domain.repository import AuditRepositoryInterface
from src.framework.application.query_bus import Query, QueryHandler


@dataclass
class GetComplianceAssessmentsQuery(Query):
    company_id: str
    framework: Optional[str] = None


class GetComplianceAssessmentsQueryHandler(
    QueryHandler[
        GetComplianceAssessmentsQuery, list[ControlAssessmentDto]
    ]
):
    def __init__(self, repo: AuditRepositoryInterface):
        self.repo = repo

    def handle(
        self, query: GetComplianceAssessmentsQuery
    ) -> list[ControlAssessmentDto]:
        controls = self.repo.find_controls(query.company_id)
        assessments = self.repo.find_assessments_by_company(
            query.company_id
        )
        evidence_counts = self.repo.count_evidence_by_control(
            query.company_id
        )

        assessment_map = {a.control_id: a for a in assessments}

        result: list[ControlAssessmentDto] = []
        for c in controls:
            if query.framework and c.framework != query.framework:
                continue

            a = assessment_map.get(c.id)
            result.append(
                ControlAssessmentDto(
                    control_id=c.id,
                    control_code=c.code,
                    control_name=c.name,
                    framework=c.framework,
                    description=c.description,
                    is_predefined=c.is_predefined,
                    status=(
                        a.status.value
                        if a
                        else ComplianceStatus.NOT_ASSESSED.value
                    ),
                    notes=a.notes if a else None,
                    assessed_by=a.assessed_by if a else None,
                    assessed_at=a.assessed_at if a else None,
                    evidence_count=evidence_counts.get(c.id, 0),
                )
            )

        return result
