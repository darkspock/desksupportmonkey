import logging
from typing import Optional

import ulid

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from starlette.requests import Request

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.assets.dependencies import get_asset_repo, get_checkout_repo, get_user_repo
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
from adapters.http.api.assets.schemas import (
    AssignableUserResponse,
    AssetEventResponse,
    AssetLocationResponse,
    AssetResponse,
    AssignAssetRequest,
    ChangeStatusRequest,
    CreateAssetRequest,
    CreateLocationRequest,
    ImportResponse,
    ImportRowErrorResponse,
    MoveAssetRequest,
    UpdateAssetRequest,
    UpdateLocationRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.asset_bc.asset.application.commands.create_asset import (
    CreateAssetCommand,
    CreateAssetCommandHandler,
    SerialNumberExistsError,
)
from src.asset_bc.asset.application.commands.update_asset import (
    AssetNotFoundError as UpdateAssetNotFoundError,
    UpdateAssetCommand,
    UpdateAssetCommandHandler,
)
from src.asset_bc.asset.application.commands.change_asset_status import (
    AssetNotFoundError as StatusAssetNotFoundError,
    ChangeAssetStatusCommand,
    ChangeAssetStatusCommandHandler,
)
from src.asset_bc.asset.application.queries.list_assets import (
    ListAssetsQuery,
    ListAssetsQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset import (
    AssetNotFoundError as GetAssetNotFoundError,
    GetAssetQuery,
    GetAssetQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset_history import (
    AssetNotFoundError as HistoryAssetNotFoundError,
    GetAssetHistoryQuery,
    GetAssetHistoryQueryHandler,
)
from src.asset_bc.asset.application.commands.assign_asset import (
    AssetNotFoundError as AssignAssetNotFoundError,
    AssignAssetCommand,
    AssignAssetCommandHandler,
    UserNotFoundError,
    UserInactiveError,
)
from src.asset_bc.asset.application.commands.unassign_asset import (
    AssetNotFoundError as UnassignAssetNotFoundError,
    UnassignAssetCommand,
    UnassignAssetCommandHandler,
)
from src.asset_bc.checkout.domain.exceptions import CannotUnassignWithOpenCheckoutError
from src.asset_bc.checkout.infrastructure.repository import CheckoutRepository
from src.asset_bc.asset.application.commands.import_assets import (
    ImportAssetsRequest,
    ImportAssetsService,
    InvalidCSVError,
)
from src.asset_bc.asset.application.commands.create_location import (
    CreateLocationCommand,
    CreateLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.update_location import (
    UpdateLocationCommand,
    UpdateLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.delete_location import (
    DeleteLocationCommand,
    DeleteLocationCommandHandler,
)
from src.asset_bc.asset.application.commands.move_asset import (
    MoveAssetCommand,
    MoveAssetCommandHandler,
)
from src.asset_bc.asset.application.queries.list_locations import (
    ListLocationsQuery,
    ListLocationsQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset, AssetEvent, AssetLocation, InvalidAssignmentError
from src.asset_bc.asset.domain.enums import AssetStatus as AssetStatusEnum, InvalidStatusTransitionError
from src.asset_bc.asset.domain.exceptions import (
    LocationHasAssetsError,
    LocationNameExistsError,
    LocationNotFoundError,
    SystemLocationError,
)
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


def _to_response(
    asset: Asset,
    assigned_to_email: str | None = None,
    location_name: str | None = None,
    custom_fields: list | None = None,
) -> AssetResponse:
    return AssetResponse(
        id=asset.id,
        company_id=asset.company_id,
        type=asset.type,
        brand=asset.brand,
        model=asset.model,
        serial_number=asset.serial_number,
        status=asset.status.value,
        assigned_to=asset.assigned_to,
        assigned_to_email=assigned_to_email,
        department_id=asset.department_id,
        location_id=asset.location_id,
        location_name=location_name,
        purchase_date=asset.purchase_date,
        warranty_expiration=asset.warranty_expiration,
        notes=asset.notes,
        custom_fields=custom_fields,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _event_to_response(event: AssetEvent, performed_by_email: str | None = None) -> AssetEventResponse:
    return AssetEventResponse(
        id=event.id,
        asset_id=event.asset_id,
        event_type=event.event_type,
        data=event.data,
        performed_by=event.performed_by,
        performed_by_email=performed_by_email,
        created_at=event.created_at,
    )


def _resolve_location_names(
    asset_repo: AssetRepository,
    company_id: str,
    assets: list[Asset],
) -> dict[str, str]:
    """Build a map of location_id -> name for all locations referenced by assets."""
    location_ids = {a.location_id for a in assets if a.location_id}
    if not location_ids:
        return {}
    locations = asset_repo.find_locations_by_company(company_id)
    return {loc.id: loc.name for loc in locations if loc.id in location_ids}


def _fetch_asset_response(
    asset_repo: AssetRepository,
    user_repo: UserRepository,
    asset_id: str,
    company_id: str,
    cf_enricher: CustomFieldEnrichmentService | None = None,
) -> dict:
    """Fetch an asset by ID and resolve assigned_to_email + location_name, returning a JSON-ready dict."""
    query_handler = GetAssetQueryHandler(asset_repo=asset_repo)
    asset = query_handler.handle(GetAssetQuery(asset_id=asset_id, company_id=company_id))
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = user_repo.find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    location_name = None
    if asset.location_id:
        loc = asset_repo.find_location_by_id(asset.location_id, company_id)
        location_name = loc.name if loc else None
    custom_fields = None
    if cf_enricher:
        custom_fields = cf_enricher.enrich(company_id, "asset", asset.custom_fields_data or {})
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email, location_name=location_name, custom_fields=custom_fields).model_dump(mode="json")}


def _resolve_assigned_emails(
    user_repo: UserRepository,
    assets: list[Asset],
) -> dict[str, str | None]:
    """Build a map of user_id -> email for all assigned users in a list of assets."""
    assigned_ids = [a.assigned_to for a in assets if a.assigned_to]
    user_map = user_repo.find_by_ids(assigned_ids)
    return {
        uid: user_map[uid].email if uid in user_map else None
        for uid in assigned_ids
    }


def _location_to_response(loc: AssetLocation, asset_count: int = 0) -> AssetLocationResponse:
    return AssetLocationResponse(
        id=loc.id,
        name=loc.name,
        is_system=loc.is_system,
        system_key=loc.system_key,
        in_use=loc.in_use,
        street_line_1=loc.street_line_1,
        street_line_2=loc.street_line_2,
        city=loc.city,
        state=loc.state,
        postal_code=loc.postal_code,
        country=loc.country,
        phone=loc.phone,
        is_personal=loc.is_personal,
        user_id=loc.user_id,
        asset_count=asset_count,
        created_at=loc.created_at,
    )


def _parse_csv_upload(content: bytes) -> str:
    """Decode uploaded file bytes to UTF-8 CSV string, raising HTTP errors on failure."""
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be UTF-8 encoded",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_asset(
    body: CreateAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    cf_data: dict = {}
    if body.custom_fields_data:
        try:
            cf_data = cf_validator.validate_for_save(
                current_user.company_id, "asset", body.custom_fields_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    asset_id = str(ulid.new())
    handler = CreateAssetCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            CreateAssetCommand(
                company_id=current_user.company_id,
                type=body.type,
                brand=body.brand,
                model=body.model,
                serial_number=body.serial_number,
                purchase_date=body.purchase_date,
                warranty_expiration=body.warranty_expiration,
                notes=body.notes,
                performed_by=current_user.id,
                id=asset_id,
                custom_fields_data=cf_data,
            )
        )
    except SerialNumberExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset with this serial number already exists")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    asset = GetAssetQueryHandler(asset_repo=asset_repo).handle(
        GetAssetQuery(asset_id=asset_id, company_id=current_user.company_id)
    )
    custom_fields = cf_enricher.enrich(current_user.company_id, "asset", asset.custom_fields_data or {})
    return {"data": _to_response(asset, custom_fields=custom_fields).model_dump(mode="json")}


@router.get("")
def list_assets(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
    cf_def_repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    cf_filters = {
        k[3:]: v for k, v in request.query_params.items() if k.startswith("cf_")
    }
    cf_search_keys: list[str] | None = None
    if search:
        defs = cf_def_repo.find_active_by_entity_type(current_user.company_id, "asset")
        cf_search_keys = [d.field_key for d in defs if d.field_type in ("text", "number")]
    handler = ListAssetsQueryHandler(asset_repo=asset_repo)
    assets, total = handler.handle(
        ListAssetsQuery(
            company_id=current_user.company_id,
            page=page, page_size=page_size, search=search,
            type=type, status=status, department_id=department_id,
            assigned_to=assigned_to, location_id=location_id,
            sort_by=sort_by, sort_order=sort_order,
            custom_field_filters=cf_filters or None,
            custom_field_search_keys=cf_search_keys,
        )
    )
    email_map = _resolve_assigned_emails(user_repo, assets)
    location_map = _resolve_location_names(asset_repo, current_user.company_id, assets)
    cf_batch = cf_enricher.enrich_batch(
        current_user.company_id, "asset", [a.custom_fields_data or {} for a in assets]
    )
    return {
        "data": [
            _to_response(
                a,
                assigned_to_email=email_map.get(a.assigned_to),
                location_name=location_map.get(a.location_id),
                custom_fields=cf_batch[i],
            ).model_dump(mode="json")
            for i, a in enumerate(assets)
        ],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_assets(
    file: UploadFile,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
):
    if file.size and file.size > 1_048_576:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds 1MB limit")
    csv_content = _parse_csv_upload(await file.read())
    try:
        result = ImportAssetsService(asset_repo=asset_repo, cf_validation_service=cf_validator).handle(
            ImportAssetsRequest(
                company_id=current_user.company_id,
                performed_by=current_user.id,
                csv_content=csv_content,
            )
        )
    except InvalidCSVError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {
        "data": ImportResponse(
            total=result.total, successful=result.successful,
            failed=[ImportRowErrorResponse(row=e.row, error=e.error) for e in result.failed],
        ).model_dump()
    }


@router.get("/assignable-users")
def list_assignable_users(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    users, _ = user_repo.find_all_by_company(
        company_id=current_user.company_id,
        page=1,
        page_size=500,
        is_active=True,
    )
    return {
        "data": [
            AssignableUserResponse(id=u.id, email=u.email, name=u.name).model_dump(mode="json")
            for u in users
        ]
    }


@router.get("/locations")
def list_locations(
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    handler = ListLocationsQueryHandler(asset_repo=asset_repo)
    locations = handler.handle(
        ListLocationsQuery(company_id=current_user.company_id)
    )
    return {
        "data": [
            _location_to_response(loc, asset_repo.count_assets_at_location(loc.id)).model_dump(mode="json")
            for loc in locations
        ]
    }


@router.post("/locations", status_code=status.HTTP_201_CREATED)
def create_location(
    body: CreateLocationRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    loc_id = str(ulid.new())
    handler = CreateLocationCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            CreateLocationCommand(
                company_id=current_user.company_id,
                name=body.name,
                in_use=body.in_use,
                id=loc_id,
                street_line_1=body.street_line_1,
                street_line_2=body.street_line_2,
                city=body.city,
                state=body.state,
                postal_code=body.postal_code,
                country=body.country,
                phone=body.phone,
            )
        )
    except LocationNameExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location with this name already exists")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    loc = asset_repo.find_location_by_id(loc_id, current_user.company_id)
    return {"data": _location_to_response(loc, 0).model_dump(mode="json")}


@router.put("/locations/{location_id}")
def update_location(
    location_id: str,
    body: UpdateLocationRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    from src.asset_bc.asset.application.commands.update_location import _UNSET
    cmd_kwargs: dict = {
        "location_id": location_id,
        "company_id": current_user.company_id,
        "name": body.name,
        "in_use": body.in_use,
    }
    for field_name in ("street_line_1", "street_line_2", "city", "state", "postal_code", "country", "phone"):
        val = getattr(body, field_name, None)
        if val is not None:
            cmd_kwargs[field_name] = val
    handler = UpdateLocationCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(UpdateLocationCommand(**cmd_kwargs))
    except LocationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    except SystemLocationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except LocationNameExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Location with this name already exists")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    loc = asset_repo.find_location_by_id(location_id, current_user.company_id)
    return {"data": _location_to_response(loc, asset_repo.count_assets_at_location(loc.id)).model_dump(mode="json")}


@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    handler = DeleteLocationCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            DeleteLocationCommand(
                location_id=location_id,
                company_id=current_user.company_id,
            )
        )
    except LocationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    except SystemLocationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except LocationHasAssetsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{asset_id}")
def get_asset(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    handler = GetAssetQueryHandler(asset_repo=asset_repo)
    try:
        asset = handler.handle(
            GetAssetQuery(asset_id=asset_id, company_id=current_user.company_id)
        )
    except GetAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    assigned_to_email = None
    if asset.assigned_to:
        assigned_user = user_repo.find_by_id(asset.assigned_to)
        assigned_to_email = assigned_user.email if assigned_user else None
    location_name = None
    if asset.location_id:
        loc = asset_repo.find_location_by_id(asset.location_id, current_user.company_id)
        location_name = loc.name if loc else None
    custom_fields = cf_enricher.enrich(current_user.company_id, "asset", asset.custom_fields_data or {})
    return {"data": _to_response(asset, assigned_to_email=assigned_to_email, location_name=location_name, custom_fields=custom_fields).model_dump(mode="json")}


@router.put("/{asset_id}")
def update_asset(
    asset_id: str,
    body: UpdateAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_validator: CustomFieldValidationService = Depends(get_cf_validation_service),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    cf_data = None
    if body.custom_fields_data is not None:
        try:
            cf_data = cf_validator.validate_for_save(
                current_user.company_id, "asset", body.custom_fields_data
            )
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    handler = UpdateAssetCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            UpdateAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
                brand=body.brand,
                model=body.model,
                notes=body.notes,
                purchase_date=body.purchase_date,
                warranty_expiration=body.warranty_expiration,
                custom_fields_data=cf_data,
                type=body.type,
            )
        )
    except UpdateAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _fetch_asset_response(asset_repo, user_repo, asset_id, current_user.company_id, cf_enricher=cf_enricher)


@router.patch("/{asset_id}/status")
def change_asset_status(
    asset_id: str,
    body: ChangeStatusRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    handler = ChangeAssetStatusCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            ChangeAssetStatusCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                new_status=body.status,
                performed_by=current_user.id,
            )
        )
    except StatusAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return _fetch_asset_response(asset_repo, user_repo, asset_id, current_user.company_id, cf_enricher=cf_enricher)


@router.get("/{asset_id}/history")
def get_asset_history(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = GetAssetHistoryQueryHandler(asset_repo=asset_repo)
    try:
        events = handler.handle(
            GetAssetHistoryQuery(asset_id=asset_id, company_id=current_user.company_id)
        )
    except HistoryAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    user_map = user_repo.find_by_ids([e.performed_by for e in events])
    return {
        "data": [
            _event_to_response(
                e,
                performed_by_email=user_map[e.performed_by].email if e.performed_by in user_map else None,
            ).model_dump(mode="json")
            for e in events
        ]
    }


@router.patch("/{asset_id}/move")
def move_asset(
    asset_id: str,
    body: MoveAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    from src.asset_bc.asset.application.commands.move_asset import (
        AssetNotFoundError as MoveAssetNotFoundError,
        AssetDecommissionedError,
    )
    handler = MoveAssetCommandHandler(asset_repo=asset_repo)
    try:
        handler.handle(
            MoveAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                location_id=body.location_id,
                performed_by=current_user.id,
                notes=body.notes,
            )
        )
    except MoveAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except AssetDecommissionedError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except LocationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
    return _fetch_asset_response(asset_repo, user_repo, asset_id, current_user.company_id, cf_enricher=cf_enricher)


@router.patch("/{asset_id}/assign")
def assign_asset(
    asset_id: str,
    body: AssignAssetRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    cf_enricher: CustomFieldEnrichmentService = Depends(get_cf_enrichment_service),
):
    handler = AssignAssetCommandHandler(asset_repo=asset_repo, user_repo=user_repo)
    try:
        handler.handle(
            AssignAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                user_id=body.user_id,
                performed_by=current_user.id,
            )
        )
    except AssignAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except UserInactiveError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is inactive")
    except InvalidAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return _fetch_asset_response(asset_repo, user_repo, asset_id, current_user.company_id, cf_enricher=cf_enricher)


@router.patch("/{asset_id}/unassign")
def unassign_asset(
    asset_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    checkout_repo: CheckoutRepository = Depends(get_checkout_repo),
):
    handler = UnassignAssetCommandHandler(
        asset_repo=asset_repo, checkout_repo=checkout_repo,
    )
    try:
        handler.handle(
            UnassignAssetCommand(
                asset_id=asset_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except UnassignAssetNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    except CannotUnassignWithOpenCheckoutError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot unassign asset with an active checkout",
        )
    except InvalidAssignmentError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    query_handler = GetAssetQueryHandler(asset_repo=asset_repo)
    asset = query_handler.handle(GetAssetQuery(asset_id=asset_id, company_id=current_user.company_id))
    return {"data": _to_response(asset, assigned_to_email=None).model_dump(mode="json")}
