from datetime import datetime
from typing import Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.audit.dependencies import get_audit_repo, get_user_repo
from adapters.http.api.audit.schemas import (
    AddAuditTagsRequest,
    AddEvidenceRequest,
    AssessControlRequest,
    AuditEntryDetailResponse,
    AuditEntryListResponse,
    AuditTagResponse,
    ComplianceControlResponse,
    ComplianceDashboardResponse,
    ComplianceEvidenceResponse,
    ControlAssessmentResponse,
    CreateControlRequest,
    ExportAuditRequest,
    ExportComplianceRequest,
    ExportStatusResponse,
    FrameworkSummaryResponse,
    GdprAnonymizeRequest,
    GdprExportRequest,
    GdprRequestDetailResponse,
    GdprRequestListResponse,
    RetentionPolicyResponse,
    UpdateControlRequest,
    UpdateRetentionRequest,
    VerifyIntegrityRequest,
    VerifyIntegrityResponse,
)
from adapters.http.api.auth.dependencies import (
    require_plan_feature,
    require_role,
)
from adapters.http.schemas.responses import PaginationMeta
from src.audit_bc.audit.application.commands.add_audit_tags import (
    AddAuditTagsCommand,
    AddAuditTagsHandler,
)
from src.audit_bc.audit.application.commands.create_compliance_control import (
    CreateComplianceControlCommand,
    CreateComplianceControlHandler,
)
from src.audit_bc.audit.application.commands \
        .deactivate_compliance_control import (
    DeactivateComplianceControlCommand,
    DeactivateComplianceControlHandler,
)
from src.audit_bc.audit.application.commands.remove_audit_tag import (
    RemoveAuditTagCommand,
    RemoveAuditTagHandler,
)
from src.audit_bc.audit.application.commands.update_compliance_control import (
    UpdateComplianceControlCommand,
    UpdateComplianceControlHandler,
)
from src.audit_bc.audit.application.queries.get_audit_entry import (
    GetAuditEntryQuery,
    GetAuditEntryQueryHandler,
)
from src.audit_bc.audit.application.queries.list_audit_entries import (
    ListAuditEntriesQuery,
    ListAuditEntriesQueryHandler,
)
from src.audit_bc.audit.application.queries.list_compliance_controls import (
    ListComplianceControlsQuery,
    ListComplianceControlsQueryHandler,
)
from src.audit_bc.audit.application.commands.update_retention_policy import (
    UpdateRetentionPolicyCommand,
    UpdateRetentionPolicyHandler,
)
from src.audit_bc.audit.application.queries.get_retention_policy import (
    GetRetentionPolicyQuery,
    GetRetentionPolicyQueryHandler,
)
from src.audit_bc.audit.application.commands.cancel_gdpr_request import (
    CancelGdprRequestCommand,
    CancelGdprRequestHandler,
)
from src.audit_bc.audit.application.commands.request_gdpr_anonymize import (
    RequestGdprAnonymizeCommand,
    RequestGdprAnonymizeHandler,
)
from src.audit_bc.audit.application.commands.request_gdpr_export import (
    RequestGdprExportCommand,
    RequestGdprExportHandler,
)
from src.audit_bc.audit.application.queries.get_gdpr_request import (
    GetGdprRequestQuery,
    GetGdprRequestQueryHandler,
)
from src.audit_bc.audit.application.queries.list_gdpr_requests import (
    ListGdprRequestsQuery,
    ListGdprRequestsQueryHandler,
)
from src.audit_bc.audit.domain.exceptions import (
    AuditEntryNotFoundError,
    CannotAnonymizeSelfError,
    CannotAnonymizeSuperAdminError,
    ControlCodeExistsError,
    ControlNotFoundError,
    EvidenceNotFoundError,
    GdprRequestNotFoundError,
    InvalidComplianceStatusError,
    InvalidGdprStatusTransitionError,
    InvalidRetentionPeriodError,
    PredefinedControlError,
    TargetUserNotFoundError,
    UserAlreadyAnonymizedError,
)
from src.audit_bc.audit.infrastructure.repository import AuditRepository
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def _user_name_resolver_factory(user_repo: UserRepository):
    def resolver(user_ids: list[str]) -> dict[str, str]:
        result: dict[str, str] = {}
        for uid in user_ids:
            user = user_repo.find_by_id(uid)
            if user:
                result[uid] = user.name or user.email
        return result

    return resolver


# ---------------------------------------------------------------------------
# Audit entry list
# ---------------------------------------------------------------------------


@router.get("")
def list_audit_entries(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    control_id: Optional[str] = None,
    search: Optional[str] = None,
):
    handler = ListAuditEntriesQueryHandler(
        repo=audit_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    entries, total = handler.handle(
        ListAuditEntriesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            date_from=date_from,
            date_to=date_to,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            control_id=control_id,
            search=search,
        )
    )
    return {
        "data": [
            AuditEntryListResponse.model_validate(
                e.__dict__
            ).model_dump(mode="json")
            for e in entries
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


# ---------------------------------------------------------------------------
# Compliance controls (static routes before /{id})
# ---------------------------------------------------------------------------


@router.get("/controls")
def list_controls(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = ListComplianceControlsQueryHandler(repo=audit_repo)
    controls = handler.handle(
        ListComplianceControlsQuery(company_id=current_user.company_id)
    )
    return {
        "data": [
            ComplianceControlResponse.model_validate(
                c.__dict__
            ).model_dump(mode="json")
            for c in controls
        ]
    }


@router.post("/controls", status_code=status.HTTP_201_CREATED)
def create_control(
    body: CreateControlRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = CreateComplianceControlHandler(repo=audit_repo)
    try:
        handler.handle(
            CreateComplianceControlCommand(
                company_id=current_user.company_id,
                code=body.code,
                name=body.name,
                framework=body.framework,
                description=body.description,
            )
        )
    except ControlCodeExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Control created"}


@router.put("/controls/{control_id}")
def update_control(
    control_id: str,
    body: UpdateControlRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = UpdateComplianceControlHandler(repo=audit_repo)
    try:
        handler.handle(
            UpdateComplianceControlCommand(
                control_id=control_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
            )
        )
    except ControlNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PredefinedControlError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Control updated"}


@router.delete("/controls/{control_id}")
def deactivate_control(
    control_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = DeactivateComplianceControlHandler(repo=audit_repo)
    try:
        handler.handle(
            DeactivateComplianceControlCommand(
                control_id=control_id,
                company_id=current_user.company_id,
            )
        )
    except ControlNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PredefinedControlError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Control deactivated"}


# ---------------------------------------------------------------------------
# Export (static routes before /{id})
# ---------------------------------------------------------------------------


@router.post("/export", status_code=status.HTTP_202_ACCEPTED)
def request_export(
    body: ExportAuditRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    from core.tasks.audit import export_audit_log

    filters = {}
    if body.date_from:
        filters["date_from"] = body.date_from.isoformat()
    if body.date_to:
        filters["date_to"] = body.date_to.isoformat()
    if body.actor_id:
        filters["actor_id"] = body.actor_id
    if body.action:
        filters["action"] = body.action
    if body.resource_type:
        filters["resource_type"] = body.resource_type
    if body.control_id:
        filters["control_id"] = body.control_id

    result = export_audit_log.delay(
        company_id=current_user.company_id,
        requested_by=current_user.id,
        export_format=body.format,
        filters=filters,
    )
    return {"task_id": result.id}


@router.get("/export/{task_id}/download")
def get_export_download(
    task_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    from core.storage import S3StorageService

    result = AsyncResult(task_id)
    if result.state == "PENDING":
        return ExportStatusResponse(
            task_id=task_id, status="pending"
        ).model_dump()
    if result.state == "STARTED":
        return ExportStatusResponse(
            task_id=task_id, status="processing"
        ).model_dump()
    if result.state == "FAILURE":
        return ExportStatusResponse(
            task_id=task_id, status="failed"
        ).model_dump()

    # SUCCESS — build download URL
    storage = S3StorageService()
    # Try CSV and PDF keys
    for ext in ("csv", "pdf"):
        key = f"audit-exports/{current_user.company_id}/{task_id}.{ext}"
        try:
            url = storage.get_signed_url(key, expiration=3600)
            return ExportStatusResponse(
                task_id=task_id, status="completed", download_url=url
            ).model_dump()
        except Exception:
            continue

    return ExportStatusResponse(
        task_id=task_id, status="completed"
    ).model_dump()


# ---------------------------------------------------------------------------
# Retention (static routes before /{id})
# ---------------------------------------------------------------------------


@router.get("/retention")
def get_retention_policy(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = GetRetentionPolicyQueryHandler(repo=audit_repo)
    dto = handler.handle(
        GetRetentionPolicyQuery(company_id=current_user.company_id)
    )
    return RetentionPolicyResponse(
        retention_months=dto.retention_months,
        updated_at=dto.updated_at,
        updated_by=dto.updated_by,
    ).model_dump(mode="json")


@router.put("/retention")
def update_retention_policy(
    body: UpdateRetentionRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = UpdateRetentionPolicyHandler(repo=audit_repo)
    try:
        handler.handle(
            UpdateRetentionPolicyCommand(
                company_id=current_user.company_id,
                retention_months=body.retention_months,
                updated_by=current_user.id,
            )
        )
    except InvalidRetentionPeriodError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Retention policy updated"}


# ---------------------------------------------------------------------------
# Integrity verification (static routes before /{id})
# ---------------------------------------------------------------------------


@router.post("/verify", status_code=status.HTTP_202_ACCEPTED)
def request_verify_integrity(
    body: VerifyIntegrityRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    from core.tasks.audit import verify_audit_integrity

    kwargs: dict = {"company_id": current_user.company_id}
    if body.date_from:
        kwargs["date_from"] = body.date_from.isoformat()
    if body.date_to:
        kwargs["date_to"] = body.date_to.isoformat()

    result = verify_audit_integrity.delay(**kwargs)
    return {"task_id": result.id}


@router.get("/verify/{task_id}")
def get_verify_status(
    task_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    result = AsyncResult(task_id)
    if result.state == "PENDING":
        return VerifyIntegrityResponse(
            task_id=task_id, status="pending"
        ).model_dump()
    if result.state == "STARTED":
        return VerifyIntegrityResponse(
            task_id=task_id, status="processing"
        ).model_dump()
    if result.state == "FAILURE":
        return VerifyIntegrityResponse(
            task_id=task_id, status="failed"
        ).model_dump()

    # SUCCESS
    data = result.result or {}
    return VerifyIntegrityResponse(
        task_id=task_id,
        status="completed",
        total_checked=data.get("total_checked", 0),
        valid_count=data.get("valid_count", 0),
        invalid_count=data.get("invalid_count", 0),
        first_invalid_entry_id=data.get("first_invalid_entry_id"),
    ).model_dump()


# ---------------------------------------------------------------------------
# GDPR (static routes before /{id})
# ---------------------------------------------------------------------------


@router.get("/gdpr")
def list_gdpr_requests(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    request_type: Optional[str] = None,
    search: Optional[str] = None,
):
    handler = ListGdprRequestsQueryHandler(repo=audit_repo)
    requests, total = handler.handle(
        ListGdprRequestsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=status_filter,
            request_type=request_type,
            search=search,
        )
    )
    return {
        "data": [
            GdprRequestListResponse.model_validate(
                r.__dict__
            ).model_dump(mode="json")
            for r in requests
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


@router.post("/gdpr/export", status_code=status.HTTP_202_ACCEPTED)
def request_gdpr_export(
    body: GdprExportRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    from core.tasks.gdpr import gdpr_data_export

    handler = RequestGdprExportHandler(
        audit_repo=audit_repo, user_repo=user_repo
    )
    command = RequestGdprExportCommand(
        company_id=current_user.company_id,
        target_user_email=body.target_user_email,
        requested_by=current_user.id,
    )
    try:
        handler.handle(command)
    except TargetUserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    gdpr_data_export.delay(command.request_id)
    return {"id": command.request_id}


@router.post("/gdpr/anonymize", status_code=status.HTTP_202_ACCEPTED)
def request_gdpr_anonymize(
    body: GdprAnonymizeRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    from core.tasks.gdpr import gdpr_anonymize_user

    handler = RequestGdprAnonymizeHandler(
        audit_repo=audit_repo, user_repo=user_repo
    )
    command = RequestGdprAnonymizeCommand(
        company_id=current_user.company_id,
        target_user_email=body.target_user_email,
        requested_by=current_user.id,
        reason=body.reason,
    )
    try:
        handler.handle(command)
    except TargetUserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except CannotAnonymizeSuperAdminError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except CannotAnonymizeSelfError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except UserAlreadyAnonymizedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    gdpr_anonymize_user.delay(command.request_id)
    return {"id": command.request_id}


@router.get("/gdpr/{request_id}")
def get_gdpr_request(
    request_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    from core.storage import S3StorageService

    handler = GetGdprRequestQueryHandler(repo=audit_repo)
    try:
        dto = handler.handle(
            GetGdprRequestQuery(
                request_id=request_id,
                company_id=current_user.company_id,
            )
        )
    except GdprRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    download_url = None
    if dto.storage_key and dto.status == "completed":
        try:
            storage = S3StorageService()
            download_url = storage.get_signed_url(
                dto.storage_key, expiration=3600
            )
        except Exception:
            pass

    resp = GdprRequestDetailResponse(
        id=dto.id,
        target_user_email=dto.target_user_email,
        request_type=dto.request_type,
        status=dto.status,
        reason=dto.reason,
        error_message=dto.error_message,
        started_at=dto.started_at,
        completed_at=dto.completed_at,
        created_at=dto.created_at,
        download_url=download_url,
    )
    return resp.model_dump(mode="json")


@router.post("/gdpr/{request_id}/cancel")
def cancel_gdpr_request(
    request_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = CancelGdprRequestHandler(repo=audit_repo)
    try:
        handler.handle(
            CancelGdprRequestCommand(
                request_id=request_id,
                company_id=current_user.company_id,
            )
        )
    except GdprRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidGdprStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return {"message": "Request cancelled"}


# ---------------------------------------------------------------------------
# Compliance assessment & evidence (static routes before /{id})
# ---------------------------------------------------------------------------


@router.get("/compliance/assessments")
def list_compliance_assessments(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    framework: Optional[str] = None,
):
    from src.audit_bc.audit.application.queries \
            .get_compliance_assessments import (
        GetComplianceAssessmentsQuery,
        GetComplianceAssessmentsQueryHandler,
    )

    handler = GetComplianceAssessmentsQueryHandler(repo=audit_repo)
    items = handler.handle(
        GetComplianceAssessmentsQuery(
            company_id=current_user.company_id,
            framework=framework,
        )
    )
    return {
        "data": [
            ControlAssessmentResponse.model_validate(
                i.__dict__
            ).model_dump(mode="json")
            for i in items
        ]
    }


@router.put("/compliance/controls/{control_id}/assessment")
def assess_control(
    control_id: str,
    body: AssessControlRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    from src.audit_bc.audit.application.commands \
            .assess_compliance_control import (
        AssessComplianceControlCommand,
        AssessComplianceControlHandler,
    )

    handler = AssessComplianceControlHandler(repo=audit_repo)
    try:
        handler.handle(
            AssessComplianceControlCommand(
                company_id=current_user.company_id,
                control_id=control_id,
                status=body.status,
                assessed_by=current_user.id,
                notes=body.notes,
            )
        )
    except ControlNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except InvalidComplianceStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return {"message": "Assessment updated"}


@router.get("/compliance/controls/{control_id}/evidence")
def list_control_evidence(
    control_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    from src.audit_bc.audit.application.queries \
            .list_compliance_evidence import (
        ListComplianceEvidenceQuery,
        ListComplianceEvidenceQueryHandler,
    )

    handler = ListComplianceEvidenceQueryHandler(repo=audit_repo)
    items = handler.handle(
        ListComplianceEvidenceQuery(
            company_id=current_user.company_id,
            control_id=control_id,
        )
    )
    return {
        "data": [
            ComplianceEvidenceResponse.model_validate(
                e.__dict__
            ).model_dump(mode="json")
            for e in items
        ]
    }


@router.post(
    "/compliance/controls/{control_id}/evidence",
    status_code=status.HTTP_201_CREATED,
)
def add_control_evidence(
    control_id: str,
    body: AddEvidenceRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    from src.audit_bc.audit.application.commands \
            .add_compliance_evidence import (
        AddComplianceEvidenceCommand,
        AddComplianceEvidenceHandler,
    )

    handler = AddComplianceEvidenceHandler(repo=audit_repo)
    try:
        handler.handle(
            AddComplianceEvidenceCommand(
                company_id=current_user.company_id,
                control_id=control_id,
                evidence_type=body.evidence_type,
                title=body.title,
                added_by=current_user.id,
                reference_id=body.reference_id,
                description=body.description,
                url=body.url,
            )
        )
    except ControlNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return {"message": "Evidence added"}


@router.delete("/compliance/evidence/{evidence_id}")
def remove_evidence(
    evidence_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    from src.audit_bc.audit.application.commands \
            .remove_compliance_evidence import (
        RemoveComplianceEvidenceCommand,
        RemoveComplianceEvidenceHandler,
    )

    handler = RemoveComplianceEvidenceHandler(repo=audit_repo)
    try:
        handler.handle(
            RemoveComplianceEvidenceCommand(
                evidence_id=evidence_id,
                company_id=current_user.company_id,
            )
        )
    except EvidenceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return {"message": "Evidence removed"}


@router.get("/compliance/dashboard")
def get_compliance_dashboard(
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    framework: Optional[str] = None,
):
    from src.audit_bc.audit.application.queries \
            .get_compliance_dashboard import (
        GetComplianceDashboardQuery,
        GetComplianceDashboardQueryHandler,
    )

    handler = GetComplianceDashboardQueryHandler(repo=audit_repo)
    dto = handler.handle(
        GetComplianceDashboardQuery(
            company_id=current_user.company_id,
            framework=framework,
        )
    )
    return ComplianceDashboardResponse(
        overall_compliance_pct=dto.overall_compliance_pct,
        total_controls=dto.total_controls,
        compliant=dto.compliant,
        partial=dto.partial,
        non_compliant=dto.non_compliant,
        not_assessed=dto.not_assessed,
        controls_with_evidence=dto.controls_with_evidence,
        controls_without_evidence=dto.controls_without_evidence,
        frameworks=[
            FrameworkSummaryResponse(**f.__dict__)
            for f in dto.frameworks
        ],
        gap_controls=[
            ControlAssessmentResponse.model_validate(g.__dict__)
            for g in dto.gap_controls
        ],
    ).model_dump(mode="json")


@router.post(
    "/compliance/export", status_code=status.HTTP_202_ACCEPTED
)
def request_compliance_export(
    body: ExportComplianceRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    from core.tasks.compliance import generate_compliance_report

    result = generate_compliance_report.delay(
        company_id=current_user.company_id,
        requested_by=current_user.id,
        framework=body.framework,
    )
    return {"task_id": result.id}


@router.get("/compliance/export/{task_id}/download")
def get_compliance_export_download(
    task_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
):
    from core.storage import S3StorageService

    result = AsyncResult(task_id)
    if result.state == "PENDING":
        return ExportStatusResponse(
            task_id=task_id, status="pending"
        ).model_dump()
    if result.state == "STARTED":
        return ExportStatusResponse(
            task_id=task_id, status="processing"
        ).model_dump()
    if result.state == "FAILURE":
        return ExportStatusResponse(
            task_id=task_id, status="failed"
        ).model_dump()

    storage = S3StorageService()
    key = (
        f"compliance-reports/{current_user.company_id}/{task_id}.pdf"
    )
    try:
        url = storage.get_signed_url(key, expiration=3600)
        return ExportStatusResponse(
            task_id=task_id, status="completed", download_url=url
        ).model_dump()
    except Exception:
        return ExportStatusResponse(
            task_id=task_id, status="completed"
        ).model_dump()


# ---------------------------------------------------------------------------
# Audit entry detail (parameterized — after static routes)
# ---------------------------------------------------------------------------


@router.get("/{entry_id}")
def get_audit_entry(
    entry_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = GetAuditEntryQueryHandler(
        repo=audit_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    try:
        detail = handler.handle(
            GetAuditEntryQuery(
                entry_id=entry_id,
                company_id=current_user.company_id,
            )
        )
    except AuditEntryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    tag_responses = [
        AuditTagResponse.model_validate(t.__dict__).model_dump(mode="json")
        for t in detail.tags
    ]
    resp = AuditEntryDetailResponse.model_validate(detail.__dict__)
    resp_dict = resp.model_dump(mode="json")
    resp_dict["tags"] = tag_responses
    return resp_dict


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.post("/{entry_id}/tags", status_code=status.HTTP_201_CREATED)
def add_tags(
    entry_id: str,
    body: AddAuditTagsRequest,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = AddAuditTagsHandler(repo=audit_repo)
    try:
        handler.handle(
            AddAuditTagsCommand(
                entry_id=entry_id,
                company_id=current_user.company_id,
                control_ids=body.control_ids,
                tagged_by=current_user.id,
            )
        )
    except AuditEntryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ControlNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return {"message": "Tags added"}


@router.delete("/{entry_id}/tags/{tag_id}")
def remove_tag(
    entry_id: str,
    tag_id: str,
    current_user=Depends(require_plan_feature("audit_trail")),
    _admin=Depends(require_role(UserRole.ADMIN)),
    audit_repo: AuditRepository = Depends(get_audit_repo),
):
    handler = RemoveAuditTagHandler(repo=audit_repo)
    try:
        handler.handle(
            RemoveAuditTagCommand(
                tag_id=tag_id,
                entry_id=entry_id,
                company_id=current_user.company_id,
            )
        )
    except AuditEntryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return {"message": "Tag removed"}
