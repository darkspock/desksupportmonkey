import logging
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user, require_role
from adapters.http.api.custom_fields.dependencies import (
    get_cf_definition_repo,
    get_cf_enrichment_service,
    get_cf_validation_service,
)
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)
from src.custom_field_bc.definition.application.services.enrichment_service import (
    CustomFieldEnrichmentService,
)
from src.custom_field_bc.definition.application.services.validation_service import (
    CustomFieldValidationService,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.incidents.dependencies import (
    get_asset_repo,
    get_incident_repo,
    get_user_repo,
    get_vendor_repo,
)
from adapters.http.api.incidents.schemas import (
    AssignIncidentRequest,
    ChangeIncidentSeverityRequest,
    ChangeIncidentStatusRequest,
    CreateIncidentRequest,
    CreatePostMortemRequest,
    DashboardResponse,
    IncidentAssetResponse,
    IncidentDetailResponse,
    IncidentListItemResponse,
    IncidentVendorResponse,
    LinkAssetRequest,
    LinkVendorRequest,
    PostMortemResponse,
    RecentIncidentResponse,
    ReportResponse,
    TimelineEntryResponse,
    UpdateIncidentRequest,
    UpdatePostMortemRequest,
    UpcomingDeadlineResponse,
)
from starlette.requests import Request
from starlette.responses import JSONResponse
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.incident_bc.incident.application.commands.assign_incident import (
    AssignIncidentCommand,
    AssignIncidentCommandHandler,
)
from src.incident_bc.incident.application.commands.change_severity import (
    ChangeIncidentSeverityCommand,
    ChangeIncidentSeverityCommandHandler,
)
from src.incident_bc.incident.application.commands.change_status import (
    ChangeIncidentStatusCommand,
    ChangeIncidentStatusCommandHandler,
)
from src.incident_bc.incident.application.commands.create_incident import (
    CreateIncidentCommand,
    CreateIncidentCommandHandler,
)
from src.incident_bc.incident.application.commands.update_incident import (
    UpdateIncidentCommand,
    UpdateIncidentCommandHandler,
)
from src.incident_bc.incident.application.queries.get_incident_detail import (
    GetIncidentDetailQuery,
    GetIncidentDetailQueryHandler,
)
from src.incident_bc.incident.application.queries.list_incidents import (
    ListIncidentsQuery,
    ListIncidentsQueryHandler,
)
from src.incident_bc.incident.application.commands.generate_report import (
    GenerateReportCommand,
    GenerateReportCommandHandler,
)
from src.incident_bc.incident.application.commands.submit_report import (
    SubmitReportCommand,
    SubmitReportCommandHandler,
)
from src.incident_bc.incident.application.queries.list_reports import (
    ListReportsQuery,
    ListReportsQueryHandler,
)
from src.incident_bc.incident.application.commands.link_asset import (
    LinkAssetCommand,
    LinkAssetCommandHandler,
)
from src.incident_bc.incident.application.commands.unlink_asset import (
    UnlinkAssetCommand,
    UnlinkAssetCommandHandler,
)
from src.incident_bc.incident.application.commands.link_vendor import (
    LinkVendorCommand,
    LinkVendorCommandHandler,
)
from src.incident_bc.incident.application.commands.unlink_vendor import (
    UnlinkVendorCommand,
    UnlinkVendorCommandHandler,
)
from src.incident_bc.incident.application.commands.create_postmortem import (
    CreatePostMortemCommand,
    CreatePostMortemCommandHandler,
)
from src.incident_bc.incident.application.commands.update_postmortem import (
    UpdatePostMortemCommand,
    UpdatePostMortemCommandHandler,
)
from src.incident_bc.incident.application.queries.get_dashboard import (
    GetDashboardQuery,
    GetDashboardQueryHandler,
)
from src.incident_bc.incident.application.queries.get_postmortem import (
    GetPostMortemQuery,
    GetPostMortemQueryHandler,
)
from src.incident_bc.incident.domain.exceptions import (
    AssetAlreadyLinkedError,
    CloseReasonRequiredError,
    IncidentClosedError,
    IncidentNotClosableForPostMortemError,
    IncidentNotFoundError,
    InvalidStatusTransitionError,
    PostMortemAlreadyExistsError,
    PostMortemNotFoundError,
    ReportNotFoundError,
    ReportNotGeneratedError,
    VendorAlreadyLinkedError,
)
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.incident_bc.incident.infrastructure.repository import IncidentRepository
from src.notification_bc.notification.application.services.event_bus import EventBus
from src.procurement_bc.vendor.infrastructure.repository import VendorRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _make_detail_handler(
    incident_repo: IncidentRepository,
    user_repo: UserRepository,
    asset_repo: AssetRepository = None,
    vendor_repo: VendorRepository = None,
) -> GetIncidentDetailQueryHandler:
    return GetIncidentDetailQueryHandler(
        incident_repo=incident_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        asset_reader=asset_repo,
        vendor_reader=vendor_repo,
    )


def _user_name_resolver_factory(user_repo: UserRepository):
    def resolver(user_ids: list[str]) -> dict[str, str]:
        users = user_repo.find_by_ids(user_ids)
        result: dict[str, str] = {}
        for uid, user in users.items():
            if user.name and user.name.strip():
                result[uid] = user.name.strip()
            else:
                local = (
                    user.email.split("@", 1)[0]
                    .replace(".", " ")
                    .replace("_", " ")
                    .replace("-", " ")
                    .strip()
                )
                result[uid] = " ".join(
                    part.capitalize() for part in local.split()
                ) or user.email
        return result

    return resolver


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("")
def list_incidents(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    incident_status: Optional[str] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None, alias="type"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
    cf_def_repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    cf_filters = {
        k[3:]: v for k, v in request.query_params.items() if k.startswith("cf_")
    }
    cf_search_keys: list[str] | None = None
    if search:
        defs = cf_def_repo.find_active_by_entity_type(current_user.company_id, "incident")
        cf_search_keys = [d.field_key for d in defs if d.field_type in ("text", "number")]
    handler = ListIncidentsQueryHandler(
        incident_repo=incident_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    items, total = handler.handle(
        ListIncidentsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=incident_status,
            severity=severity,
            incident_type=incident_type,
            search=search,
            custom_field_filters=cf_filters or None,
            custom_field_search_keys=cf_search_keys,
        )
    )
    cf_batch = cf_enricher.enrich_batch(
        current_user.company_id, "incident", [i.custom_fields_data or {} for i in items]
    )
    return {
        "data": [
            IncidentListItemResponse(
                id=i.id,
                title=i.title,
                incident_type=i.incident_type,
                severity=i.severity,
                status=i.status,
                assigned_to=i.assigned_to,
                assigned_to_name=i.assigned_to_name,
                custom_fields=cf_batch[idx],
                detected_at=i.detected_at,
                created_at=i.created_at,
                updated_at=i.updated_at,
            ).model_dump(mode="json")
            for idx, i in enumerate(items)
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    handler = GetDashboardQueryHandler(incident_repo=incident_repo)
    dto = handler.handle(
        GetDashboardQuery(company_id=current_user.company_id)
    )
    return DashboardResponse(
        total_active=dto.total_active,
        total_closed=dto.total_closed,
        active_by_severity=dto.active_by_severity,
        by_type=dto.by_type,
        mttc_hours=dto.mttc_hours,
        mttr_hours=dto.mttr_hours,
        upcoming_deadlines=[
            UpcomingDeadlineResponse(
                incident_id=d.incident_id,
                incident_title=d.incident_title,
                report_type=d.report_type,
                deadline_at=d.deadline_at,
                time_remaining_seconds=d.time_remaining_seconds,
            )
            for d in dto.upcoming_deadlines
        ],
        recent_incidents=[
            RecentIncidentResponse(
                id=r.id,
                title=r.title,
                incident_type=r.incident_type,
                severity=r.severity,
                status=r.status,
                detected_at=r.detected_at,
                created_at=r.created_at,
            )
            for r in dto.recent_incidents
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_incident(
    body: CreateIncidentRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    event_bus: EventBus = Depends(get_event_bus),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    cf_data: dict = {}
    if body.custom_fields_data:
        try:
            cf_data = cf_validator.validate_for_save(
                current_user.company_id, "incident", body.custom_fields_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )

    incident_id = str(ulid.new())
    handler = CreateIncidentCommandHandler(
        incident_repo=incident_repo, event_bus=event_bus, db=db
    )
    try:
        handler.handle(
            CreateIncidentCommand(
                company_id=current_user.company_id,
                title=body.title,
                description=body.description,
                incident_type=body.incident_type,
                severity=body.severity,
                detected_at=body.detected_at,
                reported_by=current_user.id,
                attack_vector=body.attack_vector,
                data_breach_scope=body.data_breach_scope,
                id=incident_id,
                custom_fields_data=cf_data,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id, company_id=current_user.company_id
        )
    )
    custom_fields = cf_enricher.enrich(
        current_user.company_id, "incident", detail.custom_fields_data or {}
    )
    return {"data": _detail_to_response(detail, custom_fields=custom_fields).model_dump(mode="json")}


@router.get("/{incident_id}")
def get_incident(
    incident_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    try:
        detail = handler.handle(
            GetIncidentDetailQuery(
                incident_id=incident_id,
                company_id=current_user.company_id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    custom_fields = cf_enricher.enrich(
        current_user.company_id, "incident", detail.custom_fields_data or {}
    )
    return {"data": _detail_to_response(detail, custom_fields=custom_fields).model_dump(mode="json")}


@router.put("/{incident_id}")
def update_incident(
    incident_id: str,
    body: UpdateIncidentRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    cf_data = None
    if body.custom_fields_data is not None:
        try:
            cf_data = cf_validator.validate_for_save(
                current_user.company_id, "incident", body.custom_fields_data
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
            )

    handler = UpdateIncidentCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            UpdateIncidentCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                title=body.title,
                description=body.description,
                attack_vector=body.attack_vector,
                data_breach_scope=body.data_breach_scope,
                custom_fields_data=cf_data,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    custom_fields = cf_enricher.enrich(
        current_user.company_id, "incident", detail.custom_fields_data or {}
    )
    return {"data": _detail_to_response(detail, custom_fields=custom_fields).model_dump(mode="json")}


@router.post("/{incident_id}/status")
def change_incident_status(
    incident_id: str,
    body: ChangeIncidentStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = ChangeIncidentStatusCommandHandler(
        incident_repo=incident_repo, event_bus=event_bus, db=db
    )
    try:
        handler.handle(
            ChangeIncidentStatusCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                new_status=body.status,
                actor_id=current_user.id,
                close_reason=body.close_reason,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except CloseReasonRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


@router.post("/{incident_id}/severity")
def change_incident_severity(
    incident_id: str,
    body: ChangeIncidentSeverityRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = ChangeIncidentSeverityCommandHandler(
        incident_repo=incident_repo, event_bus=event_bus, db=db
    )
    try:
        handler.handle(
            ChangeIncidentSeverityCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                new_severity=body.severity,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


@router.post("/{incident_id}/assign")
def assign_incident(
    incident_id: str,
    body: AssignIncidentRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = AssignIncidentCommandHandler(
        incident_repo=incident_repo, event_bus=event_bus, db=db
    )
    try:
        handler.handle(
            AssignIncidentCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                assigned_to=body.user_id,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


# ---------------------------------------------------------------------------
# F1: Regulatory Report endpoints
# ---------------------------------------------------------------------------


@router.get("/{incident_id}/reports")
def list_reports(
    incident_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    handler = ListReportsQueryHandler(incident_repo=incident_repo)
    try:
        reports = handler.handle(
            ListReportsQuery(
                incident_id=incident_id,
                company_id=current_user.company_id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return {
        "data": [
            ReportResponse(
                id=r.id,
                report_type=r.report_type,
                status=r.status,
                deadline_at=r.deadline_at,
                generated_at=r.generated_at,
                submitted_at=r.submitted_at,
                time_remaining_seconds=r.time_remaining_seconds,
                elapsed_percentage=r.elapsed_percentage,
            ).model_dump(mode="json")
            for r in reports
        ]
    }


@router.post("/{incident_id}/reports/{report_id}/generate")
def generate_report(
    incident_id: str,
    report_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    handler = GenerateReportCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            GenerateReportCommand(
                incident_id=incident_id,
                report_id=report_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return {"data": {"status": "generating"}}


@router.post("/{incident_id}/reports/{report_id}/submit")
def submit_report(
    incident_id: str,
    report_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    handler = SubmitReportCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            SubmitReportCommand(
                incident_id=incident_id,
                report_id=report_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    except ReportNotGeneratedError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Report has not been generated yet",
        )
    return {"data": {"status": "submitted"}}


@router.get("/{incident_id}/reports/{report_id}/download")
def download_report(
    incident_id: str,
    report_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    incident = incident_repo.find_by_id(incident_id, current_user.company_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    report = incident_repo.find_report_by_id(report_id, incident_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    if not report.file_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Report has not been generated yet",
        )

    from core.storage import S3StorageService

    storage = S3StorageService()
    signed_url = storage.get_signed_url(report.file_path)
    return {"data": {"download_url": signed_url}}


# ---------------------------------------------------------------------------
# F2: Asset & Vendor Linking endpoints
# ---------------------------------------------------------------------------


@router.post("/{incident_id}/assets", status_code=status.HTTP_200_OK)
def link_asset(
    incident_id: str,
    body: LinkAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    handler = LinkAssetCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            LinkAssetCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                asset_id=body.asset_id,
                actor_id=current_user.id,
                impact_description=body.impact_description,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except AssetAlreadyLinkedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


@router.delete("/{incident_id}/assets/{asset_id}")
def unlink_asset(
    incident_id: str,
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    handler = UnlinkAssetCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            UnlinkAssetCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                asset_id=asset_id,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


@router.post("/{incident_id}/vendors", status_code=status.HTTP_200_OK)
def link_vendor(
    incident_id: str,
    body: LinkVendorRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    handler = LinkVendorCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            LinkVendorCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                vendor_id=body.vendor_id,
                actor_id=current_user.id,
                involvement_description=body.involvement_description,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except VendorAlreadyLinkedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


@router.delete("/{incident_id}/vendors/{vendor_id}")
def unlink_vendor(
    incident_id: str,
    vendor_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    handler = UnlinkVendorCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            UnlinkVendorCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                vendor_id=vendor_id,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentClosedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    detail_handler = _make_detail_handler(
        incident_repo, user_repo, asset_repo, vendor_repo,
    )
    detail = detail_handler.handle(
        GetIncidentDetailQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _detail_to_response(detail).model_dump(mode="json")}


# ---------------------------------------------------------------------------
# F3: Post-Mortem endpoints
# ---------------------------------------------------------------------------


@router.post("/{incident_id}/post-mortem", status_code=status.HTTP_201_CREATED)
def create_postmortem(
    incident_id: str,
    body: CreatePostMortemRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
):
    handler = CreatePostMortemCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            CreatePostMortemCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                root_cause=body.root_cause,
                lessons_learned=body.lessons_learned,
                corrective_actions=body.corrective_actions,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except IncidentNotClosableForPostMortemError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except PostMortemAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )

    pm_handler = GetPostMortemQueryHandler(
        incident_repo=incident_repo,
        user_name_resolver=_user_name_resolver_factory(
            UserRepository(incident_repo.session)
        ),
    )
    pm = pm_handler.handle(
        GetPostMortemQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _postmortem_to_response(pm).model_dump(mode="json") if pm else None}


@router.get("/{incident_id}/post-mortem")
def get_postmortem(
    incident_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    pm_handler = GetPostMortemQueryHandler(
        incident_repo=incident_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    try:
        pm = pm_handler.handle(
            GetPostMortemQuery(
                incident_id=incident_id,
                company_id=current_user.company_id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    if not pm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post-mortem not found",
        )
    return {"data": _postmortem_to_response(pm).model_dump(mode="json")}


@router.put("/{incident_id}/post-mortem")
def update_postmortem(
    incident_id: str,
    body: UpdatePostMortemRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    incident_repo: IncidentRepository = Depends(get_incident_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = UpdatePostMortemCommandHandler(incident_repo=incident_repo)
    try:
        handler.handle(
            UpdatePostMortemCommand(
                incident_id=incident_id,
                company_id=current_user.company_id,
                root_cause=body.root_cause,
                lessons_learned=body.lessons_learned,
                corrective_actions=body.corrective_actions,
                actor_id=current_user.id,
            )
        )
    except IncidentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    except PostMortemNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post-mortem not found",
        )

    pm_handler = GetPostMortemQueryHandler(
        incident_repo=incident_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    pm = pm_handler.handle(
        GetPostMortemQuery(
            incident_id=incident_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _postmortem_to_response(pm).model_dump(mode="json") if pm else None}


# ---------------------------------------------------------------------------
# Response builder
# ---------------------------------------------------------------------------


def _postmortem_to_response(pm) -> PostMortemResponse:
    return PostMortemResponse(
        id=pm.id,
        root_cause=pm.root_cause,
        lessons_learned=pm.lessons_learned,
        corrective_actions=pm.corrective_actions,
        created_by_name=pm.created_by_name,
        created_at=pm.created_at,
        updated_at=pm.updated_at,
    )


def _detail_to_response(detail, custom_fields: list | None = None) -> IncidentDetailResponse:
    from datetime import datetime as dt
    from datetime import timezone as tz

    now = dt.now(tz.utc)

    def _compute_report_countdown(r, detected_at):
        deadline = r.deadline_at
        if not deadline or not detected_at:
            return None, None
        remaining = deadline - now
        time_remaining = max(int(remaining.total_seconds()), 0)
        total_duration = (deadline - detected_at).total_seconds()
        elapsed = (now - detected_at).total_seconds()
        pct = min(round((elapsed / total_duration) * 100, 1), 100.0) if total_duration > 0 else 100.0
        return time_remaining, pct

    report_responses = []
    for r in detail.reports:
        remaining, pct = _compute_report_countdown(r, detail.detected_at)
        report_responses.append(
            ReportResponse(
                id=r.id,
                report_type=r.report_type,
                status=r.status,
                deadline_at=r.deadline_at,
                generated_at=r.generated_at,
                submitted_at=r.submitted_at,
                time_remaining_seconds=remaining,
                elapsed_percentage=pct,
            )
        )

    return IncidentDetailResponse(
        id=detail.id,
        title=detail.title,
        description=detail.description,
        incident_type=detail.incident_type,
        severity=detail.severity,
        status=detail.status,
        attack_vector=detail.attack_vector,
        data_breach_scope=detail.data_breach_scope,
        reported_by=detail.reported_by,
        reported_by_name=detail.reported_by_name,
        assigned_to=detail.assigned_to,
        assigned_to_name=detail.assigned_to_name,
        detected_at=detail.detected_at,
        close_reason=detail.close_reason,
        closed_at=detail.closed_at,
        custom_fields=custom_fields,
        created_at=detail.created_at,
        updated_at=detail.updated_at,
        timeline=[
            TimelineEntryResponse(
                id=e.id,
                event_type=e.event_type,
                description=e.description,
                actor_id=e.actor_id,
                actor_name=e.actor_name,
                created_at=e.created_at,
                metadata=e.metadata,
            )
            for e in detail.timeline
        ],
        reports=report_responses,
        assets=[
            IncidentAssetResponse(
                asset_id=a.asset_id,
                asset_name=a.asset_name,
                asset_type=a.asset_type,
                impact_description=a.impact_description,
            )
            for a in detail.assets
        ],
        vendors=[
            IncidentVendorResponse(
                vendor_id=v.vendor_id,
                vendor_name=v.vendor_name,
                involvement_description=v.involvement_description,
            )
            for v in detail.vendors
        ],
        postmortem=_postmortem_to_response(detail.postmortem) if detail.postmortem else None,
    )
