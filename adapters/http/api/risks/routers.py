import csv
import io
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.risks.dependencies import get_risk_repo, get_user_repo
from adapters.http.api.risks.schemas import (
    AddLinkRequest,
    AddMitigationRequest,
    AssessRiskRequest,
    ChangeStatusRequest,
    CreateRiskRequest,
    MitigationResponse,
    RiskDashboardResponse,
    RiskDetailResponse,
    RiskHistoryResponse,
    RiskLinkResponse,
    RiskListItemResponse,
    SetTreatmentRequest,
    UpdateMitigationRequest,
    UpdateRiskRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.risk_bc.risk.application.commands.add_link import (
    AddLinkCommand,
    AddLinkCommandHandler,
)
from src.risk_bc.risk.application.commands.add_mitigation import (
    AddMitigationCommand,
    AddMitigationCommandHandler,
)
from src.risk_bc.risk.application.commands.assess_risk import (
    AssessRiskCommand,
    AssessRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.change_risk_status import (
    ChangeRiskStatusCommand,
    ChangeRiskStatusCommandHandler,
)
from src.risk_bc.risk.application.commands.create_risk import (
    CreateRiskCommand,
    CreateRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.delete_mitigation import (
    DeleteMitigationCommand,
    DeleteMitigationCommandHandler,
)
from src.risk_bc.risk.application.commands.delete_risk import (
    DeleteRiskCommand,
    DeleteRiskCommandHandler,
)
from src.risk_bc.risk.application.commands.remove_link import (
    RemoveLinkCommand,
    RemoveLinkCommandHandler,
)
from src.risk_bc.risk.application.commands.set_treatment import (
    SetTreatmentCommand,
    SetTreatmentCommandHandler,
)
from src.risk_bc.risk.application.commands.update_mitigation import (
    UpdateMitigationCommand,
    UpdateMitigationCommandHandler,
)
from src.risk_bc.risk.application.commands.update_risk import (
    UpdateRiskCommand,
    UpdateRiskCommandHandler,
)
from src.risk_bc.risk.application.queries.get_risk_detail import (
    GetRiskDetailQuery,
    GetRiskDetailQueryHandler,
)
from src.risk_bc.risk.application.queries.list_risks import (
    ListRisksQuery,
    ListRisksQueryHandler,
)
from src.risk_bc.risk.domain.exceptions import (
    DuplicateLinkError,
    InvalidStatusTransitionError,
    LinkNotFoundError,
    MitigationNotFoundError,
    RiskClosedError,
    RiskNotFoundError,
)
from src.risk_bc.risk.infrastructure.repository import RiskRepository

router = APIRouter(prefix="/api/v1/risks", tags=["risks"])


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


# --- Risk CRUD ---


@router.post("", status_code=status.HTTP_201_CREATED)
def create_risk(
    body: CreateRiskRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    risk_id = str(ulid.new())
    handler = CreateRiskCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            CreateRiskCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                title=body.title,
                description=body.description,
                category=body.category,
                created_by=current_user.id,
                owner_id=body.owner_id,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetRiskDetailQuery(risk_id=risk_id, company_id=current_user.company_id)
    )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


@router.get("")
def list_risks(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_level: Optional[str] = None,
    treatment: Optional[str] = None,
    search: Optional[str] = None,
):
    handler = ListRisksQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    risks, total = handler.handle(
        ListRisksQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            category=category,
            status=status_filter,
            risk_level=risk_level,
            treatment=treatment,
            search=search,
        )
    )
    return {
        "data": [
            RiskListItemResponse.model_validate(r.__dict__).model_dump(mode="json")
            for r in risks
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/dashboard")
def get_risk_dashboard(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    from src.risk_bc.risk.application.queries.get_dashboard import (
        GetRiskDashboardQuery,
        GetRiskDashboardQueryHandler,
    )

    handler = GetRiskDashboardQueryHandler(risk_repo=risk_repo)
    dashboard = handler.handle(
        GetRiskDashboardQuery(company_id=current_user.company_id)
    )
    return {
        "data": RiskDashboardResponse.model_validate(dashboard.__dict__).model_dump(mode="json")
    }


@router.get("/export")
def export_risks_csv(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    """Export all risks as CSV."""
    handler = ListRisksQueryHandler(risk_repo=risk_repo)
    risks, _ = handler.handle(
        ListRisksQuery(
            company_id=current_user.company_id,
            page=1,
            page_size=10000,
        )
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Title", "Category", "Status", "Risk Level",
        "Likelihood", "Impact", "Treatment", "Owner", "Created",
    ])
    for r in risks:
        writer.writerow([
            r.id,
            r.title,
            r.category,
            r.status,
            r.risk_level or "",
            r.likelihood or "",
            r.impact or "",
            r.treatment or "",
            r.owner_name or "",
            r.created_at.isoformat() if r.created_at else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=risks.csv"},
    )


@router.get("/{risk_id}")
def get_risk_detail(
    risk_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    try:
        detail = handler.handle(
            GetRiskDetailQuery(
                risk_id=risk_id, company_id=current_user.company_id
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


@router.put("/{risk_id}")
def update_risk(
    risk_id: str,
    body: UpdateRiskRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = UpdateRiskCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            UpdateRiskCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                title=body.title,
                description=body.description,
                category=body.category,
                owner_id=body.owner_id,
                review_cadence=body.review_cadence,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetRiskDetailQuery(risk_id=risk_id, company_id=current_user.company_id)
    )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


@router.delete("/{risk_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_risk(
    risk_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    handler = DeleteRiskCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            DeleteRiskCommand(
                risk_id=risk_id, company_id=current_user.company_id
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )


# --- Assess, Treatment, Status ---


@router.post("/{risk_id}/assess")
def assess_risk(
    risk_id: str,
    body: AssessRiskRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = AssessRiskCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            AssessRiskCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                likelihood=body.likelihood,
                impact=body.impact,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetRiskDetailQuery(risk_id=risk_id, company_id=current_user.company_id)
    )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


@router.post("/{risk_id}/treatment")
def set_treatment(
    risk_id: str,
    body: SetTreatmentRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = SetTreatmentCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            SetTreatmentCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                treatment=body.treatment,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetRiskDetailQuery(risk_id=risk_id, company_id=current_user.company_id)
    )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


@router.post("/{risk_id}/status")
def change_risk_status(
    risk_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = ChangeRiskStatusCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            ChangeRiskStatusCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                new_status=body.status,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetRiskDetailQueryHandler(
        risk_repo=risk_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetRiskDetailQuery(risk_id=risk_id, company_id=current_user.company_id)
    )
    return {"data": RiskDetailResponse.model_validate(detail.__dict__).model_dump(mode="json")}


# --- History ---


@router.get("/{risk_id}/history")
def get_risk_history(
    risk_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    risk = risk_repo.find_by_id(risk_id, current_user.company_id)
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    history = risk_repo.get_history(risk_id)
    resolver = _user_name_resolver_factory(user_repo)
    actor_ids = list({h.actor_id for h in history if h.actor_id})
    name_map = resolver(actor_ids) if actor_ids else {}

    return {
        "data": [
            RiskHistoryResponse(
                id=h.id,
                event_type=h.event_type.value,
                description=h.description,
                actor_id=h.actor_id,
                actor_name=name_map.get(h.actor_id),
                metadata=h.metadata,
                created_at=h.created_at,
            ).model_dump(mode="json")
            for h in history
        ]
    }


# --- Mitigations (F1 endpoints, included here for router completeness) ---


@router.post("/{risk_id}/mitigations", status_code=status.HTTP_201_CREATED)
def add_mitigation(
    risk_id: str,
    body: AddMitigationRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    mitigation_id = str(ulid.new())
    handler = AddMitigationCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            AddMitigationCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                mitigation_id=mitigation_id,
                description=body.description,
                owner_id=body.owner_id,
                target_date=body.target_date,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    mit = risk_repo.find_mitigation_by_id(mitigation_id, risk_id)
    resolver = _user_name_resolver_factory(user_repo)
    owner_name = None
    if mit and mit.owner_id:
        nm = resolver([mit.owner_id])
        owner_name = nm.get(mit.owner_id)

    return {
        "data": MitigationResponse(
            id=mit.id,
            description=mit.description,
            status=mit.status.value,
            owner_id=mit.owner_id,
            owner_name=owner_name,
            target_date=mit.target_date,
            created_at=mit.created_at,
        ).model_dump(mode="json")
    }


@router.put("/{risk_id}/mitigations/{mitigation_id}")
def update_mitigation(
    risk_id: str,
    mitigation_id: str,
    body: UpdateMitigationRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = UpdateMitigationCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            UpdateMitigationCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                mitigation_id=mitigation_id,
                description=body.description,
                status=body.status,
                owner_id=body.owner_id,
                target_date=body.target_date,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except MitigationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mitigation plan not found",
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    mit = risk_repo.find_mitigation_by_id(mitigation_id, risk_id)
    resolver = _user_name_resolver_factory(user_repo)
    owner_name = None
    if mit and mit.owner_id:
        nm = resolver([mit.owner_id])
        owner_name = nm.get(mit.owner_id)

    return {
        "data": MitigationResponse(
            id=mit.id,
            description=mit.description,
            status=mit.status.value,
            owner_id=mit.owner_id,
            owner_name=owner_name,
            target_date=mit.target_date,
            created_at=mit.created_at,
        ).model_dump(mode="json")
    }


@router.delete(
    "/{risk_id}/mitigations/{mitigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mitigation(
    risk_id: str,
    mitigation_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    handler = DeleteMitigationCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            DeleteMitigationCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                mitigation_id=mitigation_id,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except MitigationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mitigation plan not found",
        )


# --- Links (F1 endpoints) ---


@router.post("/{risk_id}/links", status_code=status.HTTP_201_CREATED)
def add_link(
    risk_id: str,
    body: AddLinkRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    link_id = str(ulid.new())
    handler = AddLinkCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            AddLinkCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                link_id=link_id,
                link_type=body.link_type,
                entity_id=body.link_id,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except DuplicateLinkError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except (RiskClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    return {
        "data": RiskLinkResponse(
            id=link_id,
            link_type=body.link_type,
            link_id=body.link_id,
        ).model_dump(mode="json")
    }


@router.delete(
    "/{risk_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_link(
    risk_id: str,
    link_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    risk_repo: RiskRepository = Depends(get_risk_repo),
):
    handler = RemoveLinkCommandHandler(risk_repo=risk_repo)
    try:
        handler.handle(
            RemoveLinkCommand(
                risk_id=risk_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                link_id=link_id,
            )
        )
    except RiskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Risk not found"
        )
    except LinkNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Risk link not found",
        )
