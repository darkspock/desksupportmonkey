import ulid
from fastapi import APIRouter, Depends, HTTPException

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.asset_types.dependencies import (
    get_asset_type_repo,
)
from adapters.http.api.asset_types.schemas import (
    AssetTypeResponse,
    CreateAssetTypeRequest,
    ReorderAssetTypesRequest,
    UpdateAssetTypeRequest,
)
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.asset_type_bc.definition.application.commands.create_asset_type import (
    CreateAssetTypeCommand,
    CreateAssetTypeCommandHandler,
)
from src.asset_type_bc.definition.application.commands.delete_asset_type import (
    DeleteAssetTypeCommand,
    DeleteAssetTypeCommandHandler,
)
from src.asset_type_bc.definition.application.commands.reorder_asset_types import (
    ReorderAssetTypesCommand,
    ReorderAssetTypesCommandHandler,
)
from src.asset_type_bc.definition.application.commands.update_asset_type import (
    UpdateAssetTypeCommand,
    UpdateAssetTypeCommandHandler,
    _SENTINEL,
)
from src.asset_type_bc.definition.application.queries.get_asset_type import (
    GetAssetTypeQuery,
    GetAssetTypeQueryHandler,
)
from src.asset_type_bc.definition.application.queries.list_asset_types import (
    ListAssetTypesQuery,
    ListAssetTypesQueryHandler,
)
from src.asset_type_bc.definition.domain.exceptions import (
    AssetTypeDefinitionNotFoundError,
    AssetTypeInUseError,
    DuplicateAssetTypeCodeError,
)
from src.asset_type_bc.definition.infrastructure.repository import (
    AssetTypeDefinitionRepository,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/asset-types", tags=["asset-types"])

tech_dep = require_role(UserRole.TECHNICIAN)
admin_dep = require_role(UserRole.ADMIN)


def _to_response(dto) -> dict:
    return AssetTypeResponse(
        id=dto.id,
        code=dto.code,
        name=dto.name,
        icon=dto.icon,
        is_active=dto.is_active,
        sort_order=dto.sort_order,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    ).model_dump(mode="json")


@router.get("")
def list_asset_types(
    current_user: User = Depends(tech_dep),
    repo: AssetTypeDefinitionRepository = Depends(
        get_asset_type_repo
    ),
):
    handler = ListAssetTypesQueryHandler(repo=repo)
    types = handler.handle(
        ListAssetTypesQuery(
            company_id=current_user.company_id,
        )
    )
    return {"data": [_to_response(t) for t in types]}


@router.post("", status_code=201)
def create_asset_type(
    body: CreateAssetTypeRequest,
    current_user: User = Depends(admin_dep),
    repo: AssetTypeDefinitionRepository = Depends(
        get_asset_type_repo
    ),
):
    definition_id = str(ulid.new())
    handler = CreateAssetTypeCommandHandler(repo=repo)
    try:
        handler.handle(
            CreateAssetTypeCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
                name=body.name,
                icon=body.icon,
            )
        )
    except DuplicateAssetTypeCodeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    query_handler = GetAssetTypeQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetAssetTypeQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.put("/{definition_id}")
def update_asset_type(
    definition_id: str,
    body: UpdateAssetTypeRequest,
    current_user: User = Depends(admin_dep),
    repo: AssetTypeDefinitionRepository = Depends(
        get_asset_type_repo
    ),
):
    handler = UpdateAssetTypeCommandHandler(repo=repo)

    # Use sentinel for icon if not provided in request body
    raw = body.model_dump(exclude_unset=True)
    icon_value = raw.get("icon", _SENTINEL)

    try:
        handler.handle(
            UpdateAssetTypeCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
                name=body.name if "name" in raw else None,
                icon=icon_value,
                is_active=body.is_active if "is_active" in raw else None,
            )
        )
    except AssetTypeDefinitionNotFoundError:
        raise HTTPException(
            status_code=404, detail="Asset type not found"
        )
    except DuplicateAssetTypeCodeError as e:
        raise HTTPException(status_code=409, detail=str(e))

    query_handler = GetAssetTypeQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetAssetTypeQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.delete("/{definition_id}", status_code=204)
def delete_asset_type(
    definition_id: str,
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
    repo: AssetTypeDefinitionRepository = Depends(
        get_asset_type_repo
    ),
):
    asset_repo = AssetRepository(db)
    handler = DeleteAssetTypeCommandHandler(
        repo=repo, asset_repo=asset_repo
    )
    try:
        handler.handle(
            DeleteAssetTypeCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
            )
        )
    except AssetTypeDefinitionNotFoundError:
        raise HTTPException(
            status_code=404, detail="Asset type not found"
        )
    except AssetTypeInUseError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put("/reorder")
def reorder_asset_types(
    body: ReorderAssetTypesRequest,
    current_user: User = Depends(admin_dep),
    repo: AssetTypeDefinitionRepository = Depends(
        get_asset_type_repo
    ),
):
    handler = ReorderAssetTypesCommandHandler(repo=repo)
    handler.handle(
        ReorderAssetTypesCommand(
            company_id=current_user.company_id,
            type_ids=body.type_ids,
        )
    )
    list_handler = ListAssetTypesQueryHandler(repo=repo)
    types = list_handler.handle(
        ListAssetTypesQuery(
            company_id=current_user.company_id,
        )
    )
    return {"data": [_to_response(t) for t in types]}
