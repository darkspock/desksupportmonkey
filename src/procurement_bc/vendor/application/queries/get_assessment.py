from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.application.queries.list_assessments import (
    AssessmentDto,
)
from src.procurement_bc.vendor.domain.exceptions import AssessmentNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorRiskAssessmentRepositoryInterface,
)


@dataclass
class GetAssessmentQuery(Query):
    assessment_id: str
    vendor_id: str
    company_id: str


class GetAssessmentQueryHandler(
    QueryHandler[GetAssessmentQuery, AssessmentDto],
):
    def __init__(
        self,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
    ):
        self.assessment_repo = assessment_repo

    def handle(self, query: GetAssessmentQuery) -> AssessmentDto:
        assessment = self.assessment_repo.find_by_id(
            query.assessment_id,
            query.vendor_id,
            query.company_id,
        )
        if not assessment:
            raise AssessmentNotFoundError("Assessment not found")

        return AssessmentDto(
            id=assessment.id,
            vendor_id=assessment.vendor_id,
            company_id=assessment.company_id,
            assessed_by=assessment.assessed_by,
            assessment_date=assessment.assessment_date,
            next_review_date=assessment.next_review_date,
            data_handling_score=assessment.data_handling_score,
            security_certs_score=assessment.security_certs_score,
            incident_response_score=assessment.incident_response_score,
            business_continuity_score=assessment.business_continuity_score,
            subcontractor_score=assessment.subcontractor_score,
            overall_risk_level=assessment.overall_risk_level.value,
            justification=assessment.justification,
            created_at=assessment.created_at.isoformat() if assessment.created_at else None,
        )
