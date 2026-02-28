from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from core.database import get_db

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.dependencies import get_event_bus
from adapters.http.api.vulnerabilities.dependencies import (
    get_asset_repo,
    get_request_repo,
    get_user_repo,
    get_vuln_asset_repo,
    get_vulnerability_repo,
)
from adapters.http.api.vulnerabilities.schemas import (
    ChangeVulnerabilityStatusRequest,
    CreateTicketsResponse,
    CreateVulnerabilityRequest,
    ImportResponse,
    ImportRowErrorResponse,
    LinkAssetsRequest,
    LinkAssetsResponse,
    TicketCreatedResponse,
    UpdateRemediationStatusRequest,
    UpdateVulnerabilityRequest,
    VulnerabilityDetailResponse,
    VulnerabilityListItemResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.vulnerability_bc.vulnerability.application.commands.change_vulnerability_status import (
    ChangeVulnerabilityStatusCommand,
    ChangeVulnerabilityStatusCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.commands.import_csv import (
    ImportVulnerabilitiesCsvRequest,
    ImportVulnerabilitiesCsvService,
    InvalidCSVError,
)
from src.vulnerability_bc.vulnerability.application.commands.create_remediation_tickets import (
    CreateRemediationTicketsCommand,
    CreateRemediationTicketsCommandHandler,
    InvalidVulnerabilityStatusForTicketsError,
    NoExposedAssetsError,
)
from src.vulnerability_bc.vulnerability.application.commands.create_vulnerability import (
    CreateVulnerabilityCommand,
    CreateVulnerabilityCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.commands.link_assets import (
    LinkAssetsToVulnerabilityCommand,
    LinkAssetsToVulnerabilityCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.commands.unlink_asset import (
    UnlinkAssetFromVulnerabilityCommand,
    UnlinkAssetFromVulnerabilityCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.commands.update_remediation_status import (
    UpdateRemediationStatusCommand,
    UpdateRemediationStatusCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.commands.update_vulnerability import (
    UpdateVulnerabilityCommand,
    UpdateVulnerabilityCommandHandler,
)
from src.vulnerability_bc.vulnerability.application.queries.get_vulnerability_detail import (
    GetVulnerabilityDetailQuery,
    GetVulnerabilityDetailQueryHandler,
)
from src.vulnerability_bc.vulnerability.application.queries.list_vulnerabilities import (
    ListVulnerabilitiesQuery,
    ListVulnerabilitiesQueryHandler,
)
from src.vulnerability_bc.vulnerability.application.queries.vulnerability_dashboard import (
    GetVulnerabilityDashboardQuery,
    GetVulnerabilityDashboardQueryHandler,
)
from src.notification_bc.notification.application.services.event_bus import EventBus
from src.vulnerability_bc.vulnerability.application.services.event_factory import (
    VulnerabilityEventFactory,
)
from src.vulnerability_bc.vulnerability.domain.enums import VulnerabilitySeverity
from src.vulnerability_bc.vulnerability.domain.exceptions import (
    DuplicateCveError,
    InvalidRemediationTransitionError,
    InvalidVulnerabilityTransitionError,
    JustificationRequiredError,
    VulnerabilityAssetNotFoundError,
    VulnerabilityClosedError,
    VulnerabilityNotFoundError,
)
from src.vulnerability_bc.vulnerability.infrastructure.repository import (
    VulnerabilityRepository,
)
from src.vulnerability_bc.vulnerability.infrastructure.vuln_asset_repository import (
    VulnerabilityAssetRepository,
)
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.request_bc.request.infrastructure.repository import RequestRepository

router = APIRouter(prefix="/api/v1/vulnerabilities", tags=["vulnerabilities"])


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


def _detail_to_response(detail) -> dict:  # type: ignore[no-untyped-def]
    from dataclasses import asdict

    d = asdict(detail)
    return VulnerabilityDetailResponse.model_validate(d).model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vulnerability(
    body: CreateVulnerabilityRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    vuln_id = str(ulid.new())
    handler = CreateVulnerabilityCommandHandler(vuln_repo=vuln_repo)
    try:
        handler.handle(
            CreateVulnerabilityCommand(
                vulnerability_id=vuln_id,
                company_id=current_user.company_id,
                title=body.title,
                created_by=current_user.id,
                source="manual",
                cve_id=body.cve_id,
                description=body.description,
                cvss_score=body.cvss_score,
                severity=body.severity,
                affected_software=body.affected_software,
                affected_versions=body.affected_versions,
                published_at=body.published_at,
                discovered_at=body.discovered_at,
                remediation_notes=body.remediation_notes,
                vendor_id=body.vendor_id,
            )
        )
    except DuplicateCveError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetVulnerabilityDetailQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetVulnerabilityDetailQuery(
            vulnerability_id=vuln_id, company_id=current_user.company_id
        )
    )

    # Notify admins when a critical vulnerability is registered
    vuln = vuln_repo.find_by_id(vuln_id, current_user.company_id)
    if vuln and vuln.severity == VulnerabilitySeverity.CRITICAL:
        event = VulnerabilityEventFactory.critical_registered(vuln, actor_id=current_user.id)
        event_bus.publish(event, db)

    return {"data": _detail_to_response(detail)}


@router.get("")
def list_vulnerabilities(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    affected_software: Optional[str] = None,
    search: Optional[str] = None,
):
    handler = ListVulnerabilitiesQueryHandler(vuln_repo=vuln_repo)
    vulns, total = handler.handle(
        ListVulnerabilitiesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            severity=severity,
            status=status_filter,
            affected_software=affected_software,
            search=search,
        )
    )
    return {
        "data": [
            VulnerabilityListItemResponse.model_validate(
                v.__dict__
            ).model_dump(mode="json")
            for v in vulns
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total
        ).model_dump(),
    }


@router.get("/dashboard")
def get_vulnerability_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
):
    handler = GetVulnerabilityDashboardQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
    )
    dto = handler.handle(
        GetVulnerabilityDashboardQuery(company_id=current_user.company_id)
    )
    from dataclasses import asdict

    return {"data": asdict(dto)}


def _parse_csv_upload(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be UTF-8 encoded",
        )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_vulnerabilities(
    file: UploadFile,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
):
    if file.size and file.size > 1_048_576:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 1MB limit",
        )
    csv_content = _parse_csv_upload(await file.read())
    try:
        result = ImportVulnerabilitiesCsvService(vuln_repo=vuln_repo).handle(
            ImportVulnerabilitiesCsvRequest(
                company_id=current_user.company_id,
                performed_by=current_user.id,
                csv_content=csv_content,
            )
        )
    except InvalidCSVError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    return {
        "data": ImportResponse(
            total=result.total,
            successful=result.successful,
            skipped=result.skipped,
            failed=[
                ImportRowErrorResponse(row=e.row, error=e.error)
                for e in result.failed
            ],
        ).model_dump()
    }


@router.get("/{vuln_id}")
def get_vulnerability_detail(
    vuln_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = GetVulnerabilityDetailQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    try:
        detail = handler.handle(
            GetVulnerabilityDetailQuery(
                vulnerability_id=vuln_id, company_id=current_user.company_id
            )
        )
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    return {"data": _detail_to_response(detail)}


@router.put("/{vuln_id}")
def update_vulnerability(
    vuln_id: str,
    body: UpdateVulnerabilityRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = UpdateVulnerabilityCommandHandler(vuln_repo=vuln_repo)
    try:
        handler.handle(
            UpdateVulnerabilityCommand(
                vulnerability_id=vuln_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                title=body.title,
                description=body.description,
                cvss_score=body.cvss_score,
                affected_software=body.affected_software,
                affected_versions=body.affected_versions,
                remediation_notes=body.remediation_notes,
            )
        )
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except (VulnerabilityClosedError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetVulnerabilityDetailQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetVulnerabilityDetailQuery(
            vulnerability_id=vuln_id, company_id=current_user.company_id
        )
    )
    return {"data": _detail_to_response(detail)}


@router.patch("/{vuln_id}/status")
def change_vulnerability_status(
    vuln_id: str,
    body: ChangeVulnerabilityStatusRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    db: Session = Depends(get_db),
    event_bus: EventBus = Depends(get_event_bus),
):
    handler = ChangeVulnerabilityStatusCommandHandler(vuln_repo=vuln_repo)
    try:
        handler.handle(
            ChangeVulnerabilityStatusCommand(
                vulnerability_id=vuln_id,
                company_id=current_user.company_id,
                actor_id=current_user.id,
                new_status=body.status,
                justification=body.justification,
            )
        )
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except InvalidVulnerabilityTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except JustificationRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetVulnerabilityDetailQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetVulnerabilityDetailQuery(
            vulnerability_id=vuln_id, company_id=current_user.company_id
        )
    )

    # Notify admins when a critical vulnerability is confirmed
    if body.status == "confirmed":
        vuln = vuln_repo.find_by_id(vuln_id, current_user.company_id)
        if vuln and vuln.severity == VulnerabilitySeverity.CRITICAL:
            event = VulnerabilityEventFactory.critical_registered(vuln, actor_id=current_user.id)
            event_bus.publish(event, db)

    return {"data": _detail_to_response(detail)}


@router.post("/{vuln_id}/assets", status_code=status.HTTP_200_OK)
def link_assets(
    vuln_id: str,
    body: LinkAssetsRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    command = LinkAssetsToVulnerabilityCommand(
        vulnerability_id=vuln_id,
        company_id=current_user.company_id,
        asset_ids=body.asset_ids,
        actor_id=current_user.id,
        notes=body.notes,
    )
    handler = LinkAssetsToVulnerabilityCommandHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
    )
    try:
        handler.handle(command)
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )

    return {
        "data": LinkAssetsResponse(
            linked=command.result["linked"],
            skipped=command.result["skipped"],
            errors=command.result["errors"],
        ).model_dump()
    }


@router.post("/{vuln_id}/create-tickets", status_code=status.HTTP_200_OK)
def create_remediation_tickets(
    vuln_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    request_repo: RequestRepository = Depends(get_request_repo),
):
    handler = CreateRemediationTicketsCommandHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        request_repo=request_repo,
        asset_repo=asset_repo,
    )
    try:
        command = CreateRemediationTicketsCommand(
            vulnerability_id=vuln_id,
            company_id=current_user.company_id,
            performed_by=current_user.id,
        )
        handler.handle(command)
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except InvalidVulnerabilityStatusForTicketsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except NoExposedAssetsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    result = command.result  # type: ignore[attr-defined]
    return {
        "data": CreateTicketsResponse(
            created=[
                TicketCreatedResponse(**t) for t in result["created"]
            ],
            skipped=result["skipped"],
            errors=result["errors"],
        ).model_dump()
    }


@router.post(
    "/{vuln_id}/assets/{asset_id}/create-ticket",
    status_code=status.HTTP_200_OK,
)
def create_single_remediation_ticket(
    vuln_id: str,
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    request_repo: RequestRepository = Depends(get_request_repo),
):
    handler = CreateRemediationTicketsCommandHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        request_repo=request_repo,
        asset_repo=asset_repo,
    )
    try:
        command = CreateRemediationTicketsCommand(
            vulnerability_id=vuln_id,
            company_id=current_user.company_id,
            performed_by=current_user.id,
            asset_id=asset_id,
        )
        handler.handle(command)
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except VulnerabilityAssetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not linked to this vulnerability",
        )
    except InvalidVulnerabilityStatusForTicketsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except NoExposedAssetsError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    result = command.result  # type: ignore[attr-defined]
    return {
        "data": CreateTicketsResponse(
            created=[
                TicketCreatedResponse(**t) for t in result["created"]
            ],
            skipped=result["skipped"],
            errors=result["errors"],
        ).model_dump()
    }


@router.delete(
    "/{vuln_id}/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlink_asset(
    vuln_id: str,
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
):
    handler = UnlinkAssetFromVulnerabilityCommandHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
    )
    try:
        handler.handle(
            UnlinkAssetFromVulnerabilityCommand(
                vulnerability_id=vuln_id,
                company_id=current_user.company_id,
                asset_id=asset_id,
                actor_id=current_user.id,
            )
        )
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except VulnerabilityAssetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not linked to this vulnerability",
        )


@router.patch("/{vuln_id}/assets/{asset_id}/status")
def update_remediation_status(
    vuln_id: str,
    asset_id: str,
    body: UpdateRemediationStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    vuln_repo: VulnerabilityRepository = Depends(get_vulnerability_repo),
    vuln_asset_repo: VulnerabilityAssetRepository = Depends(get_vuln_asset_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    cmd_handler = UpdateRemediationStatusCommandHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
    )
    try:
        cmd_handler.handle(
            UpdateRemediationStatusCommand(
                vulnerability_id=vuln_id,
                company_id=current_user.company_id,
                asset_id=asset_id,
                actor_id=current_user.id,
                new_status=body.status,
                notes=body.notes,
            )
        )
    except VulnerabilityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vulnerability not found",
        )
    except VulnerabilityAssetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not linked to this vulnerability",
        )
    except InvalidRemediationTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    detail_handler = GetVulnerabilityDetailQueryHandler(
        vuln_repo=vuln_repo,
        vuln_asset_repo=vuln_asset_repo,
        asset_repo=asset_repo,
        user_name_resolver=_user_name_resolver_factory(user_repo),
    )
    detail = detail_handler.handle(
        GetVulnerabilityDetailQuery(
            vulnerability_id=vuln_id, company_id=current_user.company_id
        )
    )
    return {"data": _detail_to_response(detail)}
