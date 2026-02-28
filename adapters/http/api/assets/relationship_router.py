from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.assets.dependencies import get_asset_repo, get_ci_relationship_repo
from adapters.http.api.assets.schemas import (
    CIRelationshipResponse,
    CreateCIRelationshipRequest,
    UpdateCIRelationshipRequest,
)
from src.asset_bc.asset.application.commands.create_ci_relationship import (
    AssetNotFoundError,
    CreateCIRelationshipCommand,
    CreateCIRelationshipCommandHandler,
    DecommissionedTargetError,
    DuplicateRelationshipError,
    SelfReferenceError,
)
from src.asset_bc.asset.application.commands.update_ci_relationship import (
    CIRelationshipNotFoundError as UpdateNotFoundError,
    UpdateCIRelationshipCommand,
    UpdateCIRelationshipCommandHandler,
)
from src.asset_bc.asset.application.commands.delete_ci_relationship import (
    CIRelationshipNotFoundError as DeleteNotFoundError,
    DeleteCIRelationshipCommand,
    DeleteCIRelationshipCommandHandler,
)
from src.asset_bc.asset.application.queries.list_ci_relationships import (
    ListCIRelationshipsQuery,
    ListCIRelationshipsQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset, CIRelationship
from src.asset_bc.asset.infrastructure.ci_relationship_repository import CIRelationshipRepository
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole

relationship_router = APIRouter()


def _enrich_response(
    rel: CIRelationship,
    asset_map: dict[str, Asset],
) -> CIRelationshipResponse:
    source = asset_map.get(rel.source_asset_id)
    target = asset_map.get(rel.target_asset_id)
    return CIRelationshipResponse(
        id=rel.id,
        source_asset_id=rel.source_asset_id,
        target_asset_id=rel.target_asset_id,
        relationship_type=rel.relationship_type.value,
        description=rel.description,
        created_at=rel.created_at,
        created_by=rel.created_by,
        target_asset_name=f"{target.brand} {target.model}" if target else None,
        target_asset_serial=target.serial_number if target else None,
        target_asset_type=target.type if target else None,
        target_asset_criticality=target.criticality.value if target and target.criticality else None,
        target_asset_status=target.status.value if target else None,
        source_asset_name=f"{source.brand} {source.model}" if source else None,
        source_asset_serial=source.serial_number if source else None,
        source_asset_type=source.type if source else None,
        source_asset_criticality=source.criticality.value if source and source.criticality else None,
        source_asset_status=source.status.value if source else None,
    )


def _build_asset_map(
    relationships: list[CIRelationship],
    asset_repo: AssetRepository,
    company_id: str,
) -> dict[str, Asset]:
    asset_ids = set()
    for rel in relationships:
        asset_ids.add(rel.source_asset_id)
        asset_ids.add(rel.target_asset_id)
    if not asset_ids:
        return {}
    all_assets = asset_repo.find_all_by_company(company_id)
    return {a.id: a for a in all_assets if a.id in asset_ids}


@relationship_router.post(
    "",
    response_model=CIRelationshipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_relationship(
    asset_id: str,
    request: CreateCIRelationshipRequest,
    user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    ci_repo: CIRelationshipRepository = Depends(get_ci_relationship_repo),
):
    handler = CreateCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    try:
        handler.handle(CreateCIRelationshipCommand(
            company_id=user.company_id,
            source_asset_id=asset_id,
            target_asset_id=request.target_asset_id,
            relationship_type=request.relationship_type,
            performed_by=user.id,
            description=request.description,
        ))
    except SelfReferenceError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except AssetNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DecommissionedTargetError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except DuplicateRelationshipError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    relationships = ListCIRelationshipsQueryHandler(ci_repo=ci_repo).handle(
        ListCIRelationshipsQuery(asset_id=asset_id, company_id=user.company_id)
    )
    asset_map = _build_asset_map(relationships, asset_repo, user.company_id)
    created = [r for r in relationships if r.source_asset_id == asset_id and r.target_asset_id == request.target_asset_id and r.relationship_type.value == request.relationship_type]
    if created:
        return _enrich_response(created[0], asset_map)
    return _enrich_response(relationships[-1], asset_map)


@relationship_router.get(
    "",
    response_model=list[CIRelationshipResponse],
)
def list_relationships(
    asset_id: str,
    user: User = Depends(require_role(UserRole.TECHNICIAN)),
    ci_repo: CIRelationshipRepository = Depends(get_ci_relationship_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    handler = ListCIRelationshipsQueryHandler(ci_repo=ci_repo)
    relationships = handler.handle(
        ListCIRelationshipsQuery(asset_id=asset_id, company_id=user.company_id)
    )
    asset_map = _build_asset_map(relationships, asset_repo, user.company_id)
    return [_enrich_response(r, asset_map) for r in relationships]


@relationship_router.patch(
    "/{relationship_id}",
    response_model=CIRelationshipResponse,
)
def update_relationship(
    asset_id: str,
    relationship_id: str,
    request: UpdateCIRelationshipRequest,
    user: User = Depends(require_role(UserRole.TECHNICIAN)),
    ci_repo: CIRelationshipRepository = Depends(get_ci_relationship_repo),
    asset_repo: AssetRepository = Depends(get_asset_repo),
):
    handler = UpdateCIRelationshipCommandHandler(ci_repo=ci_repo)
    try:
        handler.handle(UpdateCIRelationshipCommand(
            relationship_id=relationship_id,
            company_id=user.company_id,
            description=request.description,
            performed_by=user.id,
        ))
    except UpdateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    updated = ci_repo.find_by_id(relationship_id, user.company_id)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relationship not found")
    asset_map = _build_asset_map([updated], asset_repo, user.company_id)
    return _enrich_response(updated, asset_map)


@relationship_router.delete(
    "/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_relationship(
    asset_id: str,
    relationship_id: str,
    user: User = Depends(require_role(UserRole.TECHNICIAN)),
    asset_repo: AssetRepository = Depends(get_asset_repo),
    ci_repo: CIRelationshipRepository = Depends(get_ci_relationship_repo),
):
    handler = DeleteCIRelationshipCommandHandler(asset_repo=asset_repo, ci_repo=ci_repo)
    try:
        handler.handle(DeleteCIRelationshipCommand(
            relationship_id=relationship_id,
            company_id=user.company_id,
            source_asset_id=asset_id,
            performed_by=user.id,
        ))
    except DeleteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
