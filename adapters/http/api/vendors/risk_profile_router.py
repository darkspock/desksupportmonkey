import logging

from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.vendors.assessment_dependencies import (
    get_assessment_repo,
)
from adapters.http.api.vendors.contract_dependencies import (
    get_contract_repo,
)
from adapters.http.api.vendors.dependencies import get_vendor_repo
from adapters.http.api.vendors.dependency_dependencies import (
    get_dependency_repo,
)
from adapters.http.api.vendors.risk_profile_dependencies import (
    get_incident_reader,
    get_risk_reader,
)
from adapters.http.api.vendors.risk_profile_schemas import (
    LatestAssessmentResponse,
    VendorIncidentSummaryResponse,
    VendorRiskProfileResponse,
    VendorRiskSummaryResponse,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.queries.get_vendor_risk_profile import (  # noqa: E501
    GetVendorRiskProfileQuery,
    GetVendorRiskProfileQueryHandler,
)
from src.procurement_bc.vendor.domain.exceptions import VendorNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors/{vendor_id}/risk-profile",
    tags=["vendor-risk-profile"],
)


@router.get("")
def get_vendor_risk_profile(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    vendor_repo=Depends(get_vendor_repo),
    contract_repo=Depends(get_contract_repo),
    assessment_repo=Depends(get_assessment_repo),
    dependency_repo=Depends(get_dependency_repo),
    incident_reader=Depends(get_incident_reader),
    risk_reader=Depends(get_risk_reader),
):
    if not current_user.role.has_access(UserRole.TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician access required",
        )

    handler = GetVendorRiskProfileQueryHandler(
        vendor_repo=vendor_repo,
        contract_repo=contract_repo,
        assessment_repo=assessment_repo,
        dependency_repo=dependency_repo,
        incident_reader=incident_reader,
        risk_reader=risk_reader,
    )

    try:
        profile = handler.handle(
            GetVendorRiskProfileQuery(
                vendor_id=vendor_id,
                company_id=current_user.company_id,
            )
        )
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    latest_assessment = None
    if profile.latest_assessment:
        latest_assessment = LatestAssessmentResponse(
            id=profile.latest_assessment.id,
            assessment_date=profile.latest_assessment.assessment_date,
            next_review_date=profile.latest_assessment.next_review_date,
            data_handling_score=profile.latest_assessment.data_handling_score,
            security_certs_score=profile.latest_assessment.security_certs_score,
            incident_response_score=profile.latest_assessment.incident_response_score,
            business_continuity_score=profile.latest_assessment.business_continuity_score,
            subcontractor_score=profile.latest_assessment.subcontractor_score,
            overall_risk_level=profile.latest_assessment.overall_risk_level,
            justification=profile.latest_assessment.justification,
        )

    incidents = [
        VendorIncidentSummaryResponse(
            id=i.id,
            title=i.title,
            severity=i.severity,
            status=i.status,
            created_at=i.created_at,
        )
        for i in profile.incidents
    ]

    risks = [
        VendorRiskSummaryResponse(
            id=r.id,
            title=r.title,
            risk_level=r.risk_level,
            status=r.status,
        )
        for r in profile.risks
    ]

    response = VendorRiskProfileResponse(
        id=profile.id,
        name=profile.name,
        contact_email=profile.contact_email,
        phone=profile.phone,
        address=profile.address,
        website=profile.website,
        category=profile.category,
        is_critical_ict=profile.is_critical_ict,
        risk_level=profile.risk_level,
        is_active=profile.is_active,
        latest_assessment=latest_assessment,
        active_contracts_count=profile.active_contracts_count,
        total_contracts_count=profile.total_contracts_count,
        dependency_count=profile.dependency_count,
        critical_dependency_count=profile.critical_dependency_count,
        incident_count=profile.incident_count,
        risk_count=profile.risk_count,
        incidents=incidents,
        risks=risks,
    )

    return {"data": response.model_dump(mode="json")}
