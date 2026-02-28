from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.framework.application.query_bus import Query, QueryHandler
from src.procurement_bc.vendor.application.ports import (
    IncidentByVendorReader,
    IncidentSummary,
    RiskByVendorReader,
    RiskSummary,
)
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError
from src.procurement_bc.vendor.domain.repository import (
    VendorContractRepositoryInterface,
    VendorDependencyRepositoryInterface,
    VendorRepositoryInterface,
    VendorRiskAssessmentRepositoryInterface,
)


@dataclass
class LatestAssessmentDto:
    id: str
    assessment_date: date
    next_review_date: Optional[date]
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    overall_risk_level: str
    justification: Optional[str]


@dataclass
class VendorRiskProfileDto:
    id: str
    name: str
    contact_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    website: Optional[str]
    category: Optional[str]
    is_critical_ict: bool
    risk_level: Optional[str]
    is_active: bool
    latest_assessment: Optional[LatestAssessmentDto]
    active_contracts_count: int
    total_contracts_count: int
    dependency_count: int
    critical_dependency_count: int
    incident_count: int
    risk_count: int
    incidents: list[IncidentSummary]
    risks: list[RiskSummary]


@dataclass
class GetVendorRiskProfileQuery(Query):
    vendor_id: str
    company_id: str


class GetVendorRiskProfileQueryHandler(
    QueryHandler[GetVendorRiskProfileQuery, VendorRiskProfileDto],
):
    def __init__(
        self,
        vendor_repo: VendorRepositoryInterface,
        contract_repo: VendorContractRepositoryInterface,
        assessment_repo: VendorRiskAssessmentRepositoryInterface,
        dependency_repo: VendorDependencyRepositoryInterface,
        incident_reader: IncidentByVendorReader,
        risk_reader: RiskByVendorReader,
    ):
        self.vendor_repo = vendor_repo
        self.contract_repo = contract_repo
        self.assessment_repo = assessment_repo
        self.dependency_repo = dependency_repo
        self.incident_reader = incident_reader
        self.risk_reader = risk_reader

    def handle(
        self, query: GetVendorRiskProfileQuery,
    ) -> VendorRiskProfileDto:
        vendor = self.vendor_repo.find_by_id(
            query.vendor_id, query.company_id,
        )
        if not vendor:
            raise VendorNotFoundError(
                f"Vendor {query.vendor_id} not found"
            )

        latest_assessment = self.assessment_repo.find_latest_by_vendor(
            query.vendor_id, query.company_id,
        )
        latest_dto = None
        if latest_assessment:
            latest_dto = LatestAssessmentDto(
                id=latest_assessment.id,
                assessment_date=latest_assessment.assessment_date,
                next_review_date=latest_assessment.next_review_date,
                data_handling_score=latest_assessment.data_handling_score,
                security_certs_score=latest_assessment.security_certs_score,
                incident_response_score=latest_assessment.incident_response_score,
                business_continuity_score=latest_assessment.business_continuity_score,
                subcontractor_score=latest_assessment.subcontractor_score,
                overall_risk_level=latest_assessment.overall_risk_level.value,
                justification=latest_assessment.justification,
            )

        # Active contracts (status=active, not deleted)
        from src.procurement_bc.vendor.domain.enums import ContractStatus
        active_contracts, active_count = self.contract_repo.find_all_by_vendor(
            query.vendor_id, query.company_id,
            page=1, page_size=1,
            status=ContractStatus.ACTIVE,
        )
        # Total contracts (all statuses)
        _, total_contracts = self.contract_repo.find_all_by_vendor(
            query.vendor_id, query.company_id,
            page=1, page_size=1,
        )

        # Dependencies
        deps, dep_count = self.dependency_repo.find_all_by_vendor(
            query.vendor_id, query.company_id,
            page=1, page_size=1000,
        )
        critical_dep_count = sum(1 for d in deps if d.is_critical)

        # Cross-BC: incidents
        incidents, incident_count = self.incident_reader.find_by_vendor(
            query.vendor_id, query.company_id,
        )

        # Cross-BC: risks
        risks = self.risk_reader.find_by_vendor(
            query.vendor_id, query.company_id,
        )

        return VendorRiskProfileDto(
            id=vendor.id,
            name=vendor.name,
            contact_email=vendor.contact_email,
            phone=vendor.phone,
            address=vendor.address,
            website=vendor.website,
            category=vendor.category.value if vendor.category else None,
            is_critical_ict=vendor.is_critical_ict,
            risk_level=vendor.risk_level.value if vendor.risk_level else None,
            is_active=vendor.is_active,
            latest_assessment=latest_dto,
            active_contracts_count=active_count,
            total_contracts_count=total_contracts,
            dependency_count=dep_count,
            critical_dependency_count=critical_dep_count,
            incident_count=incident_count,
            risk_count=len(risks),
            incidents=incidents,
            risks=risks,
        )
