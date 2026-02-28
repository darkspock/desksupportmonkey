from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user, require_role
from adapters.http.api.changes.dependencies import (
    get_asset_repo,
    get_change_repo,
    get_user_repo,
)
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.changes.schemas import (
    ApproveChangeRequestSchema,
    AssignChangeSchema,
    ChangeAssetResponse,
    ChangeDashboardResponse,
    ChangeEventResponse,
    ChangeRequestDetailResponse,
    ChangeRequestListItemResponse,
    CreateChangeRequestSchema,
    CreatePIRRequest,
    ImplementChangeSchema,
    LinkAssetsRequest,
    PIRResponse,
    RecentImplementedResponse,
    RejectChangeRequestSchema,
    RollbackChangeSchema,
    UpcomingChangeResponse,
    UpdateChangeRequestSchema,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.change_bc.change_request.application.commands.approve_change_request import (
    ApproveChangeRequestCommand,
    ApproveChangeRequestCommandHandler,
)
from src.change_bc.change_request.application.commands.assign_change import (
    AssignChangeCommand,
    AssignChangeCommandHandler,
)
from src.change_bc.change_request.application.commands.close_change import (
    CloseChangeCommand,
    CloseChangeCommandHandler,
)
from src.change_bc.change_request.application.commands.create_pir import (
    CreatePIRCommand,
    CreatePIRCommandHandler,
)
from src.change_bc.change_request.application.commands.create_change_request import (
    CreateChangeRequestCommand,
    CreateChangeRequestCommandHandler,
)
from src.change_bc.change_request.application.commands.implement_change import (
    ImplementChangeCommand,
    ImplementChangeCommandHandler,
)
from src.change_bc.change_request.application.commands.reject_change_request import (
    RejectChangeRequestCommand,
    RejectChangeRequestCommandHandler,
)
from src.change_bc.change_request.application.commands.rollback_change import (
    RollbackChangeCommand,
    RollbackChangeCommandHandler,
)
from src.change_bc.change_request.application.commands.start_change import (
    StartChangeCommand,
    StartChangeCommandHandler,
)
from src.change_bc.change_request.application.commands.submit_change_request import (
    SubmitChangeRequestCommand,
    SubmitChangeRequestCommandHandler,
)
from src.change_bc.change_request.application.commands.update_change_request import (
    UpdateChangeRequestCommand,
    UpdateChangeRequestCommandHandler,
)
from src.change_bc.change_request.application.queries.get_change_request_detail import (
    GetChangeRequestDetailQuery,
    GetChangeRequestDetailQueryHandler,
)
from src.change_bc.change_request.application.queries.change_dashboard import (
    ChangeDashboardQuery,
    ChangeDashboardQueryHandler,
)
from src.change_bc.change_request.application.queries.list_change_requests import (
    ListChangeRequestsQuery,
    ListChangeRequestsQueryHandler,
)
from src.change_bc.change_request.application.services.event_factory import (
    ChangeEventFactory,
)
from src.change_bc.change_request.application.commands.link_assets import (
    LinkAssetsCommand,
    LinkAssetsCommandHandler,
)
from src.change_bc.change_request.application.commands.unlink_asset import (
    UnlinkAssetCommand,
    UnlinkAssetCommandHandler,
)
from src.change_bc.change_request.domain.enums import InvalidStatusTransitionError
from src.change_bc.change_request.domain.exceptions import (
    ChangeNotEditableError,
    ChangeNotFoundError,
    ChangeNotUnlinkableError,
    PIRAlreadyExistsError,
    PIRRequiredForEmergencyCloseError,
    RejectionReasonRequiredError,
    RollbackPlanRequiredError,
    RollbackReasonRequiredError,
    UnauthorizedApprovalError,
)
from src.change_bc.change_request.infrastructure.repository import (
    ChangeRequestRepository,
)
from src.notification_bc.notification.application.services.event_bus import EventBus

router = APIRouter(prefix="/api/v1/changes", tags=["changes"])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


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


def _get_detail(
    change_id: str,
    company_id: str,
    change_repo: ChangeRequestRepository,
    user_repo: UserRepository,
    asset_repo=None,
) -> ChangeRequestDetailResponse:
    handler = GetChangeRequestDetailQueryHandler(
        change_repo=change_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
        asset_repo=asset_repo,
    )
    detail = handler.handle(
        GetChangeRequestDetailQuery(
            change_id=change_id, company_id=company_id
        )
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Change request not found")
    detail_dict: dict = {}
    for k, v in detail.__dict__.items():
        if k == "timeline":
            detail_dict[k] = [
                ChangeEventResponse(**e.__dict__).model_dump(mode="json")
                for e in v
            ]
        elif k == "affected_assets":
            detail_dict[k] = [
                ChangeAssetResponse(**a.__dict__).model_dump(mode="json")
                for a in v
            ]
        elif k == "pir":
            detail_dict[k] = (
                PIRResponse(**v.__dict__).model_dump(mode="json")
                if v
                else None
            )
        else:
            detail_dict[k] = v
    return ChangeRequestDetailResponse(**detail_dict).model_dump(mode="json")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
def create_change_request(
    body: CreateChangeRequestSchema,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    change_id = str(ulid.new())
    handler = CreateChangeRequestCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            CreateChangeRequestCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                requested_by=current_user.id,
                title=body.title,
                change_type=body.change_type,
                planned_date=body.planned_date,
                rollback_plan=body.rollback_plan,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.get("")
def list_change_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    change_status: Optional[str] = Query(None, alias="status"),
    change_type: Optional[str] = Query(None, alias="type"),
    assigned_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = ListChangeRequestsQueryHandler(
        change_repo=change_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    items, total = handler.handle(
        ListChangeRequestsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=change_status,
            change_type=change_type,
            assigned_to=assigned_to,
            search=search,
        )
    )
    return {
        "data": [
            ChangeRequestListItemResponse(
                **i.__dict__
            ).model_dump(mode="json")
            for i in items
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/dashboard")
def get_change_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = ChangeDashboardQueryHandler(
        change_repo=change_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    dto = handler.handle(
        ChangeDashboardQuery(company_id=current_user.company_id)
    )
    return ChangeDashboardResponse(
        total_open=dto.total_open,
        pending_approval=dto.pending_approval,
        in_progress=dto.in_progress,
        implemented=dto.implemented,
        scheduled_this_week=dto.scheduled_this_week,
        status_counts=dto.status_counts,
        type_counts=dto.type_counts,
        upcoming_scheduled=[
            UpcomingChangeResponse(**u.__dict__)
            for u in dto.upcoming_scheduled
        ],
        recently_implemented=[
            RecentImplementedResponse(**r.__dict__)
            for r in dto.recently_implemented
        ],
        rolled_back_90_days=dto.rolled_back_90_days,
    ).model_dump(mode="json")


@router.get("/{change_id}")
def get_change_request(
    change_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo=Depends(get_asset_repo),
):
    return _get_detail(
        change_id,
        current_user.company_id,
        change_repo,
        user_repo,
        asset_repo,
    )


@router.patch("/{change_id}")
def update_change_request(
    change_id: str,
    body: UpdateChangeRequestSchema,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = UpdateChangeRequestCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            UpdateChangeRequestCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                title=body.title,
                description=body.description,
                change_type=body.change_type,
                business_justification=body.business_justification,
                risk_assessment=body.risk_assessment,
                rollback_plan=body.rollback_plan,
                planned_date=body.planned_date,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except ChangeNotEditableError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/submit")
def submit_change_request(
    change_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = SubmitChangeRequestCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            SubmitChangeRequestCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RollbackPlanRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/approve")
def approve_change_request(
    change_id: str,
    body: ApproveChangeRequestSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = ApproveChangeRequestCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            ApproveChangeRequestCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
                notes=body.notes,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()

    change = change_repo.find_by_id(change_id, current_user.company_id)
    if change:
        notification = ChangeEventFactory.change_approved(change, actor_id=current_user.id)
        event_bus.publish(notification, db)

    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/reject")
def reject_change_request(
    change_id: str,
    body: RejectChangeRequestSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = RejectChangeRequestCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            RejectChangeRequestCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
                reason=body.reason,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RejectionReasonRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()

    change = change_repo.find_by_id(change_id, current_user.company_id)
    if change:
        notification = ChangeEventFactory.change_rejected(
            change, actor_id=current_user.id, reason=body.reason
        )
        event_bus.publish(notification, db)

    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/start")
def start_change(
    change_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = StartChangeCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            StartChangeCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/implement")
def implement_change(
    change_id: str,
    body: ImplementChangeSchema,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = ImplementChangeCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            ImplementChangeCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                notes=body.notes,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/rollback")
def rollback_change(
    change_id: str,
    body: RollbackChangeSchema,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = RollbackChangeCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            RollbackChangeCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                reason=body.reason,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RollbackReasonRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/close")
def close_change(
    change_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = CloseChangeCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            CloseChangeCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PIRRequiredForEmergencyCloseError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


@router.post("/{change_id}/assign")
def assign_change(
    change_id: str,
    body: AssignChangeSchema,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
):
    handler = AssignChangeCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            AssignChangeCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                assigned_to=body.assigned_to,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(status_code=404, detail="Change request not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()
    return _get_detail(change_id, current_user.company_id, change_repo, user_repo)


# ---------------------------------------------------------------------------
# Asset linking endpoints (F1)
# ---------------------------------------------------------------------------


@router.post(
    "/{change_id}/assets", status_code=status.HTTP_204_NO_CONTENT
)
def link_assets(
    change_id: str,
    body: LinkAssetsRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    asset_repo=Depends(get_asset_repo),
    db: Session = Depends(get_db),
):
    handler = LinkAssetsCommandHandler(
        change_repo=change_repo, asset_repo=asset_repo
    )
    try:
        handler.handle(
            LinkAssetsCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                asset_ids=body.asset_ids,
                actor_id=current_user.id,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(
            status_code=404, detail="Change request not found"
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()


@router.delete(
    "/{change_id}/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_asset(
    change_id: str,
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    db: Session = Depends(get_db),
):
    handler = UnlinkAssetCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            UnlinkAssetCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                asset_id=asset_id,
                actor_id=current_user.id,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(
            status_code=404, detail="Change request not found"
        )
    except ChangeNotUnlinkableError as e:
        raise HTTPException(status_code=422, detail=str(e))
    db.commit()


# ---------------------------------------------------------------------------
# Post-Implementation Review endpoint (F2)
# ---------------------------------------------------------------------------


@router.post("/{change_id}/pir")
def create_pir(
    change_id: str,
    body: CreatePIRRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    change_repo: ChangeRequestRepository = Depends(get_change_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    asset_repo=Depends(get_asset_repo),
    db: Session = Depends(get_db),
):
    handler = CreatePIRCommandHandler(change_repo=change_repo)
    try:
        handler.handle(
            CreatePIRCommand(
                change_id=change_id,
                company_id=current_user.company_id,
                outcome=body.outcome,
                issues_found=body.issues_found,
                lessons_learned=body.lessons_learned,
                follow_up_actions=body.follow_up_actions,
                performed_by=current_user.id,
                performed_by_role=current_user.role.value,
            )
        )
    except ChangeNotFoundError:
        raise HTTPException(
            status_code=404, detail="Change request not found"
        )
    except UnauthorizedApprovalError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except PIRAlreadyExistsError:
        raise HTTPException(
            status_code=409,
            detail="A post-implementation review already exists for this change",
        )
    db.commit()
    return _get_detail(
        change_id, current_user.company_id, change_repo, user_repo, asset_repo
    )
