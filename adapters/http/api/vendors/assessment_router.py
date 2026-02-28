import logging

import ulid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.vendors.assessment_dependencies import (
    get_assessment_repo,
)
from adapters.http.api.vendors.assessment_schemas import (
    AssessmentResponse,
    CreateAssessmentRequest,
)
from adapters.http.api.vendors.contract_dependencies import (
    get_contract_repo,
)
from adapters.http.api.vendors.dependencies import get_vendor_repo
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.commands.create_assessment import (
    CreateAssessmentCommand,
    CreateAssessmentCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_assessment import (  # noqa: E501
    SoftDeleteAssessmentCommand,
    SoftDeleteAssessmentCommandHandler,
)
from src.procurement_bc.vendor.application.queries.get_assessment import (
    GetAssessmentQuery,
    GetAssessmentQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_assessments import (
    AssessmentDto,
    ListAssessmentsQuery,
    ListAssessmentsQueryHandler,
)
from src.procurement_bc.vendor.domain.exceptions import (
    AssessmentNotFoundError,
    InvalidAssessmentScoreError,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorContractRepository,
    VendorRiskAssessmentRepository,
    VendorRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors/{vendor_id}/assessments",
    tags=["vendor-assessments"],
)


def _to_response(dto: AssessmentDto) -> AssessmentResponse:
    return AssessmentResponse(
        id=dto.id,
        vendor_id=dto.vendor_id,
        company_id=dto.company_id,
        assessed_by=dto.assessed_by,
        assessment_date=dto.assessment_date,
        next_review_date=dto.next_review_date,
        data_handling_score=dto.data_handling_score,
        security_certs_score=dto.security_certs_score,
        incident_response_score=dto.incident_response_score,
        business_continuity_score=dto.business_continuity_score,
        subcontractor_score=dto.subcontractor_score,
        overall_risk_level=dto.overall_risk_level,
        justification=dto.justification,
        created_at=dto.created_at,
    )


def _require_technician(user: User) -> None:
    if not user.role.has_access(UserRole.TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician access required",
        )


def _require_admin(user: User) -> None:
    if not user.role.has_access(UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_assessment(
    vendor_id: str,
    body: CreateAssessmentRequest,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    assessment_repo: VendorRiskAssessmentRepository = Depends(
        get_assessment_repo,
    ),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    assessment_id = str(ulid.new())
    handler = CreateAssessmentCommandHandler(
        vendor_repo=vendor_repo,
        assessment_repo=assessment_repo,
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            CreateAssessmentCommand(
                id=assessment_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                assessed_by=current_user.id,
                assessment_date=body.assessment_date,
                next_review_date=body.next_review_date,
                data_handling_score=body.data_handling_score,
                security_certs_score=body.security_certs_score,
                incident_response_score=body.incident_response_score,
                business_continuity_score=body.business_continuity_score,
                subcontractor_score=body.subcontractor_score,
                justification=body.justification,
                performed_by=current_user.id,
            )
        )
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    except InvalidAssessmentScoreError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    query_handler = GetAssessmentQueryHandler(
        assessment_repo=assessment_repo,
    )
    dto = query_handler.handle(
        GetAssessmentQuery(
            assessment_id=assessment_id,
            vendor_id=vendor_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(dto).model_dump(mode="json"),
    }


@router.get("")
def list_assessments(
    vendor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    assessment_repo: VendorRiskAssessmentRepository = Depends(
        get_assessment_repo,
    ),
):
    _require_technician(current_user)

    handler = ListAssessmentsQueryHandler(
        assessment_repo=assessment_repo,
    )
    dtos, total = handler.handle(
        ListAssessmentsQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [
            _to_response(d).model_dump(mode="json") for d in dtos
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/{assessment_id}")
def get_assessment(
    vendor_id: str,
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    assessment_repo: VendorRiskAssessmentRepository = Depends(
        get_assessment_repo,
    ),
):
    _require_technician(current_user)

    handler = GetAssessmentQueryHandler(
        assessment_repo=assessment_repo,
    )
    try:
        dto = handler.handle(
            GetAssessmentQuery(
                assessment_id=assessment_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
            )
        )
    except AssessmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    return {
        "data": _to_response(dto).model_dump(mode="json"),
    }


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_assessment(
    vendor_id: str,
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    assessment_repo: VendorRiskAssessmentRepository = Depends(
        get_assessment_repo,
    ),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    handler = SoftDeleteAssessmentCommandHandler(
        vendor_repo=vendor_repo,
        assessment_repo=assessment_repo,
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            SoftDeleteAssessmentCommand(
                assessment_id=assessment_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except AssessmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
