import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import Optional

import ulid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from starlette.requests import Request

from adapters.http.api.auth.dependencies import get_current_user, require_role
from adapters.http.api.custom_fields.dependencies import (
    get_cf_definition_repo,
    get_cf_enrichment_service,
    get_cf_validation_service,
)
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.requests.dependencies import (
    get_asset_repo,
    get_classification_config_repo,
    get_config_repo,
    get_department_repo,
    get_profile_repo,
    get_request_repo,
    get_user_repo,
)
from adapters.http.api.requests.schemas import (
    AddCommentRequest,
    AssignRequestRequest,
    ChangePriorityRequest,
    ChangeStatusRequest,
    CommentResponse,
    CreateRequestRequest,
    NoteResponse,
    RejectRequestRequest,
    RequestEventResponse,
    RequestListItemResponse,
    RequestResponse,
    RequesterAssetResponse,
    SetAffectedAssetsRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.custom_field_bc.definition.application.services.enrichment_service import (
    CustomFieldEnrichmentService,
)
from src.custom_field_bc.definition.application.services.validation_service import (
    CustomFieldValidationService,
)
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.notification_bc.notification.application.services.event_bus import EventBus
from src.notification_bc.notification.application.services.event_factory import RequestEventFactory
from src.request_bc.request.application.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
    RequestNotFoundError as CommentRequestNotFoundError,
)
from src.request_bc.request.application.commands.add_note import (
    AddNoteCommand,
    AddNoteCommandHandler,
    RequestNotFoundError as NoteRequestNotFoundError,
)
from src.request_bc.request.application.commands.assign_request import (
    AssignRequestCommand,
    AssignRequestCommandHandler,
    RequestNotFoundError as AssignRequestNotFoundError,
    UserInactiveError,
    UserNotFoundError,
)
from src.request_bc.request.application.commands.change_request_priority import (
    ChangeRequestPriorityCommand,
    ChangeRequestPriorityCommandHandler,
    RequestNotFoundError as PriorityRequestNotFoundError,
)
from src.request_bc.request.application.commands.change_request_status import (
    ChangeRequestStatusCommand,
    ChangeRequestStatusCommandHandler,
    RequestNotFoundError as StatusRequestNotFoundError,
)
from src.request_bc.request.application.commands.approve_request import (
    ApproveRequestCommand,
    ApproveRequestCommandHandler,
    NotPendingApprovalError as ApproveNotPendingError,
    RequestNotFoundError as ApproveRequestNotFoundError,
    UnauthorizedApprovalError,
)
from src.request_bc.request.application.commands.create_request import (
    CreateRequestCommand,
    CreateRequestCommandHandler,
)
from src.request_bc.request.application.commands.reject_request import (
    NotPendingApprovalError as RejectNotPendingError,
    RejectRequestCommand,
    RejectRequestCommandHandler,
    RequestNotFoundError as RejectRequestNotFoundError,
    UnauthorizedRejectionError,
)
from src.request_bc.request.application.queries.get_request import (
    GetRequestQuery,
    GetRequestQueryHandler,
    RequestNotFoundError as GetRequestNotFoundError,
)
from src.request_bc.request.application.queries.list_comments import (
    ListCommentsQuery,
    ListCommentsQueryHandler,
    RequestNotFoundError as ListCommentsRequestNotFoundError,
)
from src.request_bc.request.application.queries.list_notes import (
    ListNotesQuery,
    ListNotesQueryHandler,
    RequestNotFoundError as ListNotesRequestNotFoundError,
)
from src.request_bc.request.application.queries.list_requests import (
    ListRequestsQuery,
    ListRequestsQueryHandler,
)
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.company_bc.assignment_config.infrastructure.repository import (  # noqa: E501
    AssignmentConfigRepository,
)
from src.company_bc.assignment_config.domain.enums import AIProvider
from src.company_bc.equipment_profile.application.services.auto_assign import (  # noqa: E501
    AutoAssignService,
)
from src.company_bc.equipment_profile.infrastructure.repository import (  # noqa: E501
    EquipmentProfileRepository,
)
from src.company_bc.classification_config.infrastructure.repository import (  # noqa: E501
    ClassificationConfigRepository,
)
from src.company_bc.classification_config.domain.entities import (
    CompanyClassificationConfig,
)
from src.company_bc.department.infrastructure.repository import DepartmentRepository
from src.request_bc.request.application.services.classification_service import (  # noqa: E501
    ClassificationService,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.workflow_bc.checklist.application.commands.generate_checklist import (
    GenerateChecklistCommand,
    GenerateChecklistCommandHandler,
)
from src.workflow_bc.checklist.infrastructure.repository import ChecklistItemRepository
from src.workflow_bc.template.infrastructure.repository import WorkflowTemplateRepository
from src.request_bc.request.domain.enums import (
    VALID_SUBTYPES,
    InvalidStatusTransitionError,
    RequestStatus,
)
from src.request_bc.request.infrastructure.repository import (
    RequestRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/requests", tags=["requests"])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _display_name(user: User | None) -> str | None:
    if not user:
        return None
    if user.name and user.name.strip():
        return user.name.strip()
    local = (
        user.email.split("@", 1)[0]
        .replace(".", " ")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )
    normalized = " ".join(part.capitalize() for part in local.split())
    return normalized or user.email


def _user_maps(
    user_repo: UserRepository, user_ids: list[str],
) -> tuple[dict[str, str], dict[str, str | None]]:
    users = user_repo.find_by_ids(user_ids)
    email_map = {uid: user.email for uid, user in users.items()}
    name_map = {uid: _display_name(user) for uid, user in users.items()}
    return email_map, name_map


def _user_email_map(user_repo: UserRepository, user_ids: list[str]) -> dict[str, str]:
    email_map, _ = _user_maps(user_repo, user_ids)
    return email_map


def _to_response(
    request: ServiceRequest,
    comment_count: int = 0,
    created_by_name: str | None = None,
    created_by_email: str | None = None,
    assigned_to_name: str | None = None,
    assigned_to_email: str | None = None,
    custom_fields: list | None = None,
    workflow_template_name: str | None = None,
    workflow_template_icon: str | None = None,
) -> RequestResponse:
    return RequestResponse(
        id=request.id,
        company_id=request.company_id,
        created_by=request.created_by,
        created_by_name=created_by_name,
        created_by_email=created_by_email,
        assigned_to=request.assigned_to,
        assigned_to_name=assigned_to_name,
        assigned_to_email=assigned_to_email,
        type=request.type,
        subtype=request.subtype,
        title=request.title,
        description=request.description,
        status=request.status.value,
        priority=request.priority.value,
        data=request.data,
        custom_fields=custom_fields,
        workflow_template_id=request.workflow_template_id,
        workflow_template_name=workflow_template_name,
        workflow_template_icon=workflow_template_icon,
        resolved_at=request.resolved_at,
        created_at=request.created_at,
        updated_at=request.updated_at,
        comment_count=comment_count,
    )


def _to_list_item(
    r: ServiceRequest,
    email_map: dict[str, str],
    name_map: dict[str, str | None],
    custom_fields: list | None = None,
    workflow_template_name: str | None = None,
    workflow_template_icon: str | None = None,
) -> dict:
    return RequestListItemResponse(
        id=r.id,
        type=r.type,
        subtype=r.subtype,
        title=r.title,
        status=r.status.value,
        priority=r.priority.value,
        assigned_to=r.assigned_to,
        assigned_to_name=name_map.get(r.assigned_to) if r.assigned_to else None,
        assigned_to_email=email_map.get(r.assigned_to) if r.assigned_to else None,
        created_by=r.created_by,
        created_by_name=name_map.get(r.created_by),
        created_by_email=email_map.get(r.created_by),
        custom_fields=custom_fields,
        workflow_template_name=workflow_template_name,
        workflow_template_icon=workflow_template_icon,
        created_at=r.created_at,
        updated_at=r.updated_at,
    ).model_dump(mode="json")


def _get_refreshed_request(
    request_repo: RequestRepository, request_id: str, company_id: str,
) -> ServiceRequest:
    """Re-fetch a request after mutation via GetRequestQueryHandler."""
    query_handler = GetRequestQueryHandler(request_repo=request_repo)
    detail = query_handler.handle(GetRequestQuery(request_id=request_id, company_id=company_id))
    return detail.request


def _verify_request_access(
    request_id: str,
    company_id: str,
    current_user: User,
    request_repo: RequestRepository,
) -> ServiceRequest:
    """Verify employee can access the request (owns it) or technician+ can access any."""
    request = request_repo.find_by_id(request_id, company_id)
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if not current_user.role.has_access(UserRole.TECHNICIAN):
        if request.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return request


def _build_comment_response(
    comment_id: str, request_id: str, author_id: str, author_email: str, body: str,
    author_name: str | None = None, author_role: str | None = None,
) -> dict:
    return CommentResponse(
        id=comment_id,
        request_id=request_id,
        author_id=author_id,
        author_email=author_email,
        author_name=author_name,
        author_role=author_role,
        body=body.strip(),
        created_at=datetime.now(timezone.utc),
    ).model_dump(mode="json")


def _build_note_response(
    note_id: str, request_id: str, author_id: str, author_email: str, body: str,
    author_name: str | None = None, author_role: str | None = None,
) -> dict:
    return NoteResponse(
        id=note_id,
        request_id=request_id,
        author_id=author_id,
        author_email=author_email,
        author_name=author_name,
        author_role=author_role,
        body=body.strip(),
        created_at=datetime.now(timezone.utc),
    ).model_dump(mode="json")


def _cancel_linked_appointments(
    request_id: str,
    new_status: str,
    performed_by: str,
    db: Session,
) -> None:
    """Cancel all pending/confirmed appointments when request is resolved/rejected."""
    try:
        from src.appointment_bc.appointment.infrastructure.repository import (
            AppointmentRepository,
        )
        appointment_repo = AppointmentRepository(db)
        linked = appointment_repo.find_pending_or_confirmed_by_request(
            request_id,
        )
        for appt in linked:
            appt.cancel(
                reason=f"Request {new_status}",
                cancelled_by=performed_by,
            )
            appointment_repo.save(appt)
    except Exception:
        logger.exception(
            "Failed to cancel linked appointments for request %s",
            request_id,
        )


def _find_existing_or_404(
    request_repo: RequestRepository, request_id: str, company_id: str,
) -> ServiceRequest:
    """Lookup an existing request; raise 404 if not found."""
    existing = request_repo.find_by_id(request_id, company_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return existing


def _attempt_auto_assign(
    request: ServiceRequest,
    current_user: User,
    request_repo: RequestRepository,
    profile_repo: EquipmentProfileRepository,
    config_repo: AssignmentConfigRepository,
    asset_repo: AssetRepository,
) -> None:
    """Try auto-assign and store metadata in request.data."""
    try:
        from core.config import settings
        svc = AutoAssignService(
            profile_repo=profile_repo,
            config_repo=config_repo,
            asset_lookup=asset_repo,
            ai_settings=settings.ai,
        )
        metadata = svc.attempt_assignment(
            company_id=current_user.company_id,
            department_id=current_user.department_id,
            employee_role_id=current_user.employee_role_id,
        )
        data = dict(request.data) if request.data else {}
        data["auto_assignment"] = metadata
        request.data = data
        request_repo.save(request)
    except Exception:
        logger.exception("Auto-assign failed for request %s", request.id)


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


@router.get("")
def list_requests(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    request_status: Optional[str] = Query(None, alias="status"),
    type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    subtype: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
    cf_def_repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    effective_assigned_to = current_user.id if assigned_to == "me" else assigned_to
    cf_filters = {
        k[3:]: v for k, v in request.query_params.items() if k.startswith("cf_")
    }
    cf_search_keys: list[str] | None = None
    if search:
        defs = cf_def_repo.find_active_by_entity_type(current_user.company_id, "request")
        cf_search_keys = [d.field_key for d in defs if d.field_type in ("text", "number")]
    handler = ListRequestsQueryHandler(request_repo=request_repo)
    requests, total = handler.handle(
        ListRequestsQuery(
            company_id=current_user.company_id,
            page=page, page_size=page_size, search=search,
            status=request_status, type=type, priority=priority,
            assigned_to=effective_assigned_to, subtype=subtype,
            custom_field_filters=cf_filters or None,
            custom_field_search_keys=cf_search_keys,
        )
    )
    user_ids = [r.created_by for r in requests]
    user_ids.extend([r.assigned_to for r in requests if r.assigned_to])
    email_map, name_map = _user_maps(user_repo, user_ids)
    cf_batch = cf_enricher.enrich_batch(
        current_user.company_id, "request", [r.custom_fields_data or {} for r in requests]
    )

    # Batch-fetch workflow templates for enrichment
    template_ids = list({r.workflow_template_id for r in requests if r.workflow_template_id})
    template_map: dict[str, tuple[str, str | None]] = {}
    if template_ids:
        wf_repo = WorkflowTemplateRepository(db)
        for tid in template_ids:
            tmpl = wf_repo.find_by_id(tid, current_user.company_id)
            if tmpl:
                template_map[tid] = (tmpl.name, tmpl.icon)

    return {
        "data": [
            _to_list_item(
                r, email_map, name_map, custom_fields=cf_batch[i],
                workflow_template_name=template_map.get(r.workflow_template_id, (None, None))[0] if r.workflow_template_id else None,
                workflow_template_icon=template_map.get(r.workflow_template_id, (None, None))[1] if r.workflow_template_id else None,
            )
            for i, r in enumerate(requests)
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def create_request(
    body: CreateRequestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    event_bus: EventBus = Depends(get_event_bus),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    profile_repo: EquipmentProfileRepository = Depends(get_profile_repo),
    config_repo: AssignmentConfigRepository = Depends(get_config_repo),
    dept_repo: DepartmentRepository = Depends(get_department_repo),
    classification_config_repo: ClassificationConfigRepository = Depends(
        get_classification_config_repo,
    ),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    # Validate subtype against type
    if body.subtype:
        from src.request_bc.request.domain.enums import RequestType
        try:
            req_type_enum = RequestType(body.type)
        except ValueError:
            req_type_enum = None
        if req_type_enum and req_type_enum in VALID_SUBTYPES:
            valid_subs = [s.value for s in VALID_SUBTYPES[req_type_enum]]
            if body.subtype not in valid_subs:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid subtype '{body.subtype}' for type '{body.type}'. "
                    f"Valid subtypes: {valid_subs}",
                )

    # Resolve effective user (on_behalf_of for technician/admin)
    effective_user = current_user
    effective_role = current_user.role.value
    if body.on_behalf_of and current_user.role.has_access(UserRole.TECHNICIAN):
        target_user = user_repo.find_by_id(body.on_behalf_of)
        if not target_user or target_user.company_id != current_user.company_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user not found")
        effective_user = target_user
        effective_role = "employee"

    # Look up department for scoring and approval routing
    dept_priority_weight = 0
    dept_has_manager = False
    dept_manager_id = None
    dept_id = effective_user.department_id
    if dept_id and current_user.company_id:
        dept = dept_repo.find_by_id(dept_id, current_user.company_id)
        if dept:
            dept_priority_weight = dept.priority_weight
            dept_has_manager = dept.manager_user_id is not None
            dept_manager_id = dept.manager_user_id

    # AI classification
    ai_priority_hint = 0
    ai_classification = None
    resolved_type = body.type
    resolved_subtype = body.subtype

    from core.config import settings
    config = classification_config_repo.find_by_company(current_user.company_id)
    groq_key_present = bool(settings.ai.GROQ_API_KEY)
    logger.warning(
        "AI_TRACE create_request classification check: "
        "company_id=%s has_config=%s groq_key_present=%s",
        current_user.company_id,
        bool(config),
        groq_key_present,
    )

    def _execute_ai(runtime_config: CompanyClassificationConfig) -> None:
        nonlocal ai_priority_hint, ai_classification, resolved_type, resolved_subtype
        classifier = ClassificationService.build_classifier(runtime_config, settings.ai)
        if not classifier:
            logger.warning(
                "AI_TRACE classification skipped: classifier unavailable "
                "company_id=%s provider=%s groq_key_present=%s",
                current_user.company_id,
                runtime_config.provider.value,
                groq_key_present,
            )
            return
        logger.warning(
            "AI_TRACE classifier ready: company_id=%s provider=%s model=%s",
            current_user.company_id,
            runtime_config.provider.value,
            runtime_config.model,
        )
        valid_types = {
            t.value: [s.value for s in subs]
            for t, subs in VALID_SUBTYPES.items()
        }
        svc = ClassificationService(classifier, runtime_config, valid_types)
        cls_result = svc.classify_request(
            body.title, body.description, body.type, body.subtype,
        )
        ai_priority_hint = cls_result.ai_priority_hint
        ai_classification = cls_result.ai_classification
        resolved_type = cls_result.resolved_type
        resolved_subtype = cls_result.resolved_subtype
        logger.warning(
            "AI_TRACE classification executed: company_id=%s provider=%s "
            "resolved_type=%s resolved_subtype=%s ai_hint=%s",
            current_user.company_id,
            runtime_config.provider.value,
            resolved_type,
            resolved_subtype,
            ai_priority_hint,
        )

    if config and config.is_enabled:
        runtime_config = config
        # Runtime preference requested by product: use Groq when available.
        if groq_key_present and config.provider != AIProvider.GROQ:
            runtime_config = replace(config, provider=AIProvider.GROQ)
            logger.warning(
                "AI_TRACE provider override applied: "
                "company_id=%s configured_provider=%s runtime_provider=%s",
                current_user.company_id,
                config.provider.value,
                runtime_config.provider.value,
            )
        else:
            logger.warning(
                "AI_TRACE provider selected: "
                "company_id=%s provider=%s groq_key_present=%s",
                current_user.company_id,
                runtime_config.provider.value,
                groq_key_present,
            )
        _execute_ai(runtime_config)
    elif config and not config.is_enabled:
        logger.warning(
            "AI_TRACE classification skipped: config disabled company_id=%s",
            current_user.company_id,
        )
    elif groq_key_present:
        runtime_config = CompanyClassificationConfig.create(
            company_id=current_user.company_id,
            is_enabled=True,
            provider=AIProvider.GROQ,
            model="llama-3.1-8b-instant",
            confidence_threshold=0.7,
            prompt_template=None,
            timeout_seconds=10,
        )
        logger.warning(
            "AI_TRACE no persisted config; using runtime Groq defaults: "
            "company_id=%s provider=%s model=%s",
            current_user.company_id,
            runtime_config.provider.value,
            runtime_config.model,
        )
        _execute_ai(runtime_config)
    else:
        logger.warning(
            "AI_TRACE classification skipped: no config company_id=%s",
            current_user.company_id,
        )

    cf_data: dict = {}
    if body.custom_fields_data:
        try:
            cf_data = cf_validator.validate_for_save(
                current_user.company_id, "request", body.custom_fields_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    # Resolve workflow template (if template_id provided)
    wf_template = None
    wf_template_id: str | None = None
    wf_subtype_id: str | None = None
    wf_template_repo: WorkflowTemplateRepository | None = None
    if body.template_id:
        wf_template_repo = WorkflowTemplateRepository(db)
        wf_template = wf_template_repo.find_by_id(body.template_id, current_user.company_id)
        if not wf_template or not wf_template.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Workflow template not found or inactive",
            )
        wf_template_id = wf_template.id
        # Resolve subtype against template's subtypes
        if body.subtype and wf_template.subtypes:
            matched = next(
                (s for s in wf_template.subtypes if s.name == body.subtype), None
            )
            if matched:
                wf_subtype_id = matched.id
                resolved_subtype = matched.name

    request_id = str(ulid.new())
    handler = CreateRequestCommandHandler(request_repo=request_repo)
    try:
        handler.handle(
            CreateRequestCommand(
                company_id=current_user.company_id, created_by=effective_user.id,
                type=resolved_type, title=body.title,
                description=body.description, data=body.data, id=request_id,
                subtype=resolved_subtype,
                department_priority_weight=dept_priority_weight,
                user_role=effective_role,
                department_has_manager=dept_has_manager,
                ai_priority_hint=ai_priority_hint,
                ai_classification=ai_classification,
                custom_fields_data=cf_data,
                workflow_template_id=wf_template_id,
                workflow_subtype_id=wf_subtype_id,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)

    # Auto-assign only for onboarding at creation; new_equipment auto-assigns post-approval
    if request.type == "onboarding":
        _attempt_auto_assign(
            request, effective_user, request_repo,
            profile_repo, config_repo, asset_repo,
        )

    event = RequestEventFactory.request_created(request, actor_id=current_user.id)
    event_bus.publish(event, db)

    # Notify manager if request needs approval
    if request.status == RequestStatus.PENDING_APPROVAL and dept_manager_id:
        approval_event = RequestEventFactory.approval_needed(
            request, actor_id=current_user.id,
            department_manager_id=dept_manager_id,
            department_id=dept_id,
        )
        event_bus.publish(approval_event, db)

    # Generate checklist from workflow template (if template_id provided)
    if wf_template_id:
        try:
            if not wf_template_repo:
                wf_template_repo = WorkflowTemplateRepository(db)
            wf_checklist_repo = ChecklistItemRepository(db)
            generate_handler = GenerateChecklistCommandHandler(
                template_repo=wf_template_repo, checklist_repo=wf_checklist_repo,
            )
            generate_handler.handle(GenerateChecklistCommand(
                request_id=request_id,
                template_id=wf_template_id,
                company_id=current_user.company_id,
            ))
        except Exception:
            logger.exception("Failed to generate checklist for request %s", request_id)

    custom_fields = cf_enricher.enrich(
        current_user.company_id, "request", request.custom_fields_data or {}
    )
    return {
        "data": _to_response(
            request,
            created_by_name=_display_name(effective_user),
            created_by_email=effective_user.email,
            custom_fields=custom_fields,
            workflow_template_name=wf_template.name if wf_template else None,
            workflow_template_icon=wf_template.icon if wf_template else None,
        ).model_dump(mode="json")
    }


@router.get("/{request_id}")
def get_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    handler = GetRequestQueryHandler(request_repo=request_repo)
    try:
        detail = handler.handle(
            GetRequestQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except GetRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if not current_user.role.has_access(UserRole.TECHNICIAN):
        if detail.request.created_by != current_user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    # Resolve workflow template info for response
    wf_name: str | None = None
    wf_icon: str | None = None
    if detail.request.workflow_template_id:
        wf_repo = WorkflowTemplateRepository(db)
        tmpl = wf_repo.find_by_id(detail.request.workflow_template_id, current_user.company_id)
        if tmpl:
            wf_name = tmpl.name
            wf_icon = tmpl.icon

    user_ids = [detail.request.created_by] + ([detail.request.assigned_to] if detail.request.assigned_to else [])
    email_map, name_map = _user_maps(user_repo, user_ids)
    custom_fields = cf_enricher.enrich(
        current_user.company_id, "request", detail.request.custom_fields_data or {}
    )
    return {
        "data": _to_response(
            detail.request, detail.comment_count,
            created_by_name=name_map.get(detail.request.created_by),
            created_by_email=email_map.get(detail.request.created_by),
            assigned_to_name=name_map.get(detail.request.assigned_to) if detail.request.assigned_to else None,
            assigned_to_email=email_map.get(detail.request.assigned_to) if detail.request.assigned_to else None,
            custom_fields=custom_fields,
            workflow_template_name=wf_name,
            workflow_template_icon=wf_icon,
        ).model_dump(mode="json")
    }


@router.get("/{request_id}/events")
def list_request_events(
    request_id: str,
    current_user: User = Depends(get_current_user),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    _verify_request_access(request_id, current_user.company_id, current_user, request_repo)
    events = request_repo.find_events(request_id=request_id, company_id=current_user.company_id)

    actor_ids = [e.performed_by for e in events if e.performed_by]
    email_map, name_map = _user_maps(user_repo, actor_ids)

    return {
        "data": [
            RequestEventResponse(
                id=e.id,
                request_id=e.request_id,
                event_type=e.event_type,
                data=e.data,
                performed_by=e.performed_by,
                performed_by_name=name_map.get(e.performed_by),
                performed_by_email=email_map.get(e.performed_by),
                created_at=e.created_at,
            ).model_dump(mode="json")
            for e in events
        ]
    }


@router.patch("/{request_id}/status")
def change_request_status(
    request_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    existing_request = _find_existing_or_404(request_repo, request_id, current_user.company_id)
    old_status = existing_request.status.value

    # Resolution guard: check if all required checklist items are complete
    if body.status == "resolved":
        wf_checklist_repo = ChecklistItemRepository(db)
        checklist_items = wf_checklist_repo.find_by_request(request_id)
        has_require_all = any(item.require_all_complete for item in checklist_items)
        if has_require_all:
            incomplete = [
                item for item in checklist_items
                if item.is_required and not item.is_completed
            ]
            if incomplete:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Complete all required checklist items before resolving",
                )

    handler = ChangeRequestStatusCommandHandler(request_repo=request_repo)
    try:
        handler.handle(ChangeRequestStatusCommand(
            request_id=request_id, company_id=current_user.company_id,
            new_status=body.status, performed_by=current_user.id,
        ))
    except StatusRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)
    event = RequestEventFactory.status_changed(
        request, old_status=old_status, new_status=request.status.value, actor_id=current_user.id,
        reason=body.reason,
    )
    event_bus.publish(event, db)

    # Auto-cancel linked appointments when request is resolved or rejected
    if request.status.value in ("resolved", "rejected"):
        _cancel_linked_appointments(
            request_id=request_id,
            new_status=request.status.value,
            performed_by=current_user.id,
            db=db,
        )

    return {"data": _to_response(request).model_dump(mode="json")}


@router.patch("/{request_id}/priority")
def change_request_priority(
    request_id: str,
    body: ChangePriorityRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    old_priority = _find_existing_or_404(request_repo, request_id, current_user.company_id).priority.value
    handler = ChangeRequestPriorityCommandHandler(request_repo=request_repo)
    try:
        handler.handle(ChangeRequestPriorityCommand(
            request_id=request_id, company_id=current_user.company_id,
            new_priority=body.priority, performed_by=current_user.id,
        ))
    except PriorityRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)
    event = RequestEventFactory.priority_changed(
        request, old_priority=old_priority, new_priority=request.priority.value, actor_id=current_user.id,
    )
    event_bus.publish(event, db)
    return {"data": _to_response(request).model_dump(mode="json")}


@router.patch("/{request_id}/assign")
def assign_request(
    request_id: str,
    body: AssignRequestRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = AssignRequestCommandHandler(request_repo=request_repo, user_repo=user_repo)
    try:
        handler.handle(
            AssignRequestCommand(
                request_id=request_id, company_id=current_user.company_id,
                user_id=body.user_id, performed_by=current_user.id,
            )
        )
    except AssignRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserInactiveError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is inactive")

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)
    event = RequestEventFactory.request_assigned(request, actor_id=current_user.id)
    event_bus.publish(event, db)
    return {"data": _to_response(request).model_dump(mode="json")}


@router.post("/{request_id}/approve")
def approve_request(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    dept_repo: DepartmentRepository = Depends(get_department_repo),
    event_bus: EventBus = Depends(get_event_bus),
    user_repo: UserRepository = Depends(get_user_repo),
    profile_repo: EquipmentProfileRepository = Depends(get_profile_repo),
    config_repo: AssignmentConfigRepository = Depends(get_config_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    # Find the request to get requester's department manager
    existing = _find_existing_or_404(request_repo, request_id, current_user.company_id)
    dept_manager_id = None
    requester = user_repo.find_by_id(existing.created_by)
    if requester and requester.department_id:
        dept = dept_repo.find_by_id(requester.department_id, current_user.company_id)
        if dept:
            dept_manager_id = dept.manager_user_id

    handler = ApproveRequestCommandHandler(request_repo=request_repo)
    try:
        handler.handle(
            ApproveRequestCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
                department_manager_id=dept_manager_id,
            )
        )
    except ApproveRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ApproveNotPendingError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)

    # Auto-assign new_equipment requests after approval (using requester's dept/role)
    if request.type == "new_equipment" and requester:
        _attempt_auto_assign(
            request, requester, request_repo,
            profile_repo, config_repo, asset_repo,
        )

    approved_event = RequestEventFactory.request_approved(request, actor_id=current_user.id)
    event_bus.publish(approved_event, db)
    status_event = RequestEventFactory.status_changed(
        request, old_status="pending_approval", new_status=request.status.value,
        actor_id=current_user.id,
    )
    event_bus.publish(status_event, db)
    email_map, name_map = _user_maps(user_repo, [request.created_by])
    return {"data": _to_response(
        request,
        created_by_name=name_map.get(request.created_by),
        created_by_email=email_map.get(request.created_by),
    ).model_dump(mode="json")}


@router.post("/{request_id}/reject")
def reject_request(
    request_id: str,
    body: RejectRequestRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    dept_repo: DepartmentRepository = Depends(get_department_repo),
    event_bus: EventBus = Depends(get_event_bus),
    user_repo: UserRepository = Depends(get_user_repo),
):
    existing = _find_existing_or_404(request_repo, request_id, current_user.company_id)
    dept_manager_id = None
    requester = user_repo.find_by_id(existing.created_by)
    if requester and requester.department_id:
        dept = dept_repo.find_by_id(requester.department_id, current_user.company_id)
        if dept:
            dept_manager_id = dept.manager_user_id

    handler = RejectRequestCommandHandler(request_repo=request_repo)
    try:
        handler.handle(
            RejectRequestCommand(
                request_id=request_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
                reason=body.reason,
                department_manager_id=dept_manager_id,
            )
        )
    except RejectRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except RejectNotPendingError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UnauthorizedRejectionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    request = _get_refreshed_request(request_repo, request_id, current_user.company_id)
    status_event = RequestEventFactory.status_changed(
        request, old_status="pending_approval", new_status=request.status.value,
        actor_id=current_user.id,
    )
    event_bus.publish(status_event, db)
    email_map, name_map = _user_maps(user_repo, [request.created_by])
    return {"data": _to_response(
        request,
        created_by_name=name_map.get(request.created_by),
        created_by_email=email_map.get(request.created_by),
    ).model_dump(mode="json")}


@router.post("/{request_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(
    request_id: str,
    body: AddCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    sr = _verify_request_access(request_id, current_user.company_id, current_user, request_repo)
    old_status = sr.status.value  # capture before command for auto-transition detection
    comment_id = str(ulid.new())
    handler = AddCommentCommandHandler(request_repo=request_repo)
    try:
        handler.handle(
            AddCommentCommand(
                request_id=request_id, company_id=current_user.company_id,
                author_id=current_user.id, body=body.body, id=comment_id,
            )
        )
    except CommentRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    event = RequestEventFactory.comment_added(sr, actor_id=current_user.id, comment_body=body.body)
    event_bus.publish(event, db)

    # Check for auto-transition (waiting_for_employee → in_progress) and publish event
    sr_after = request_repo.find_by_id(request_id, current_user.company_id)
    if sr_after and sr_after.status.value != old_status:
        auto_event = RequestEventFactory.status_changed(
            sr_after, old_status=old_status, new_status=sr_after.status.value,
            actor_id=current_user.id,
        )
        event_bus.publish(auto_event, db)

    return {"data": _build_comment_response(
        comment_id, request_id, current_user.id, current_user.email, body.body,
        author_name=_display_name(current_user), author_role=current_user.role.value,
    )}


@router.get("/{request_id}/comments")
def list_comments(
    request_id: str,
    current_user: User = Depends(get_current_user),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    _verify_request_access(request_id, current_user.company_id, current_user, request_repo)
    handler = ListCommentsQueryHandler(request_repo=request_repo)
    try:
        comments = handler.handle(
            ListCommentsQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except ListCommentsRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    users = user_repo.find_by_ids([c.author_id for c in comments])
    return {
        "data": [
            CommentResponse(
                id=c.id, request_id=c.request_id, author_id=c.author_id,
                author_email=users[c.author_id].email if c.author_id in users else None,
                author_name=_display_name(users[c.author_id]) if c.author_id in users else None,
                author_role=users[c.author_id].role.value if c.author_id in users else None,
                body=c.body, created_at=c.created_at,
            ).model_dump(mode="json")
            for c in comments
        ]
    }


@router.post("/{request_id}/notes", status_code=status.HTTP_201_CREATED)
def add_note(
    request_id: str,
    body: AddCommentRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
    request_repo: RequestRepository = Depends(get_request_repo),
    event_bus: EventBus = Depends(get_event_bus),
):
    note_id = str(ulid.new())
    handler = AddNoteCommandHandler(request_repo=request_repo)
    try:
        handler.handle(
            AddNoteCommand(
                request_id=request_id, company_id=current_user.company_id,
                author_id=current_user.id, body=body.body, id=note_id,
            )
        )
    except NoteRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    sr = request_repo.find_by_id(request_id, current_user.company_id)
    if sr:
        event = RequestEventFactory.note_added(sr, actor_id=current_user.id)
        event_bus.publish(event, db)
    return {"data": _build_note_response(
        note_id, request_id, current_user.id, current_user.email, body.body,
        author_name=_display_name(current_user), author_role=current_user.role.value,
    )}


@router.get("/{request_id}/notes")
def list_notes(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    request_repo: RequestRepository = Depends(get_request_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = ListNotesQueryHandler(request_repo=request_repo)
    try:
        notes = handler.handle(
            ListNotesQuery(request_id=request_id, company_id=current_user.company_id)
        )
    except ListNotesRequestNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    users = user_repo.find_by_ids([n.author_id for n in notes])
    return {
        "data": [
            NoteResponse(
                id=n.id, request_id=n.request_id, author_id=n.author_id,
                author_email=users[n.author_id].email if n.author_id in users else None,
                author_name=_display_name(users[n.author_id]) if n.author_id in users else None,
                author_role=users[n.author_id].role.value if n.author_id in users else None,
                body=n.body, created_at=n.created_at,
            ).model_dump(mode="json")
            for n in notes
        ]
    }


# ---- Affected Assets ----


@router.patch("/{request_id}/affected-assets")
def set_affected_assets(
    request_id: str,
    body: SetAffectedAssetsRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    request_repo: RequestRepository = Depends(get_request_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    from src.request_bc.request.application.commands.set_affected_assets import (
        AssetNotFoundError,
        RequestNotFoundError as AffectedRequestNotFoundError,
        SetAffectedAssetsCommand,
        SetAffectedAssetsCommandHandler,
    )

    handler = SetAffectedAssetsCommandHandler(
        request_repo=request_repo,
        asset_repo=asset_repo,
    )
    try:
        handler.handle(SetAffectedAssetsCommand(
            request_id=request_id,
            company_id=current_user.company_id,
            asset_ids=body.asset_ids,
            performed_by=current_user.id,
        ))
    except AffectedRequestNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    except AssetNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    request = _get_refreshed_request(
        request_repo, request_id, current_user.company_id,
    )
    return {"data": _to_response(request).model_dump(mode="json")}


@router.get("/{request_id}/requester-assets")
def get_requester_assets(
    request_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    request_repo: RequestRepository = Depends(get_request_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    from src.request_bc.request.application.queries.get_requester_assets import (
        GetRequesterAssetsQuery,
        GetRequesterAssetsQueryHandler,
    )

    handler = GetRequesterAssetsQueryHandler(
        request_repo=request_repo,
        asset_repo=asset_repo,
    )
    dtos = handler.handle(GetRequesterAssetsQuery(
        request_id=request_id,
        company_id=current_user.company_id,
    ))
    return {
        "data": [
            RequesterAssetResponse(
                id=d.id,
                brand=d.brand,
                model=d.model,
                serial_number=d.serial_number,
                type=d.type,
                criticality=d.criticality,
                status=d.status,
                is_affected=d.is_affected,
            ).model_dump(mode="json")
            for d in dtos
        ]
    }
