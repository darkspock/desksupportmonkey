from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.domain.repository import (
    VendorRiskAssessmentRepositoryInterface,
)


@dataclass
class AssessmentDto:
    id: str
    vendor_id: str
    company_id: str
    assessed_by: str
    assessment_date: date
    next_review_date: Optional[date]
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    overall_risk_level: str
    justification: Optional[str]
    created_at: Optional[str]


@dataclass
class ListAssessmentsQuery(Query):
    vendor_id: str
    company_id: str
    page: int = 1
    page_size: int = 20


class ListAssessmentsQueryHandler(
    QueryHandler[ListAssessmentsQuery, tuple[list[AssessmentDto], int]],
):
    def __init__(
        self,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
    ):
        self.assessment_repo = assessment_repo

    def handle(
        self, query: ListAssessmentsQuery,
    ) -> tuple[list[AssessmentDto], int]:
        assessments, total = self.assessment_repo.find_all_by_vendor(
            query.vendor_id,
            query.company_id,
            query.page,
            query.page_size,
        )
        dtos = [
            AssessmentDto(
                id=a.id,
                vendor_id=a.vendor_id,
                company_id=a.company_id,
                assessed_by=a.assessed_by,
                assessment_date=a.assessment_date,
                next_review_date=a.next_review_date,
                data_handling_score=a.data_handling_score,
                security_certs_score=a.security_certs_score,
                incident_response_score=a.incident_response_score,
                business_continuity_score=a.business_continuity_score,
                subcontractor_score=a.subcontractor_score,
                overall_risk_level=a.overall_risk_level.value,
                justification=a.justification,
                created_at=a.created_at.isoformat() if a.created_at else None,
            )
            for a in assessments
        ]
        return dtos, total
