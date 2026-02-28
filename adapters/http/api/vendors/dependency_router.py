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
from adapters.http.api.vendors.dependency_dependencies import (
    get_dependency_repo,
)
from adapters.http.api.vendors.dependency_schemas import (
    ConcentrationRiskItemResponse,
    CreateDependencyRequest,
    DependencyResponse,
    UpdateDependencyRequest,
)
from adapters.http.api.vendors.dependencies import get_vendor_repo
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.commands.create_dependency import (
    CreateDependencyCommand,
    CreateDependencyCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_dependency import (  # noqa: E501
    SoftDeleteDependencyCommand,
    SoftDeleteDependencyCommandHandler,
)
from src.procurement_bc.vendor.application.commands.update_dependency import (
    UpdateDependencyCommand,
    UpdateDependencyCommandHandler,
)
from src.procurement_bc.vendor.application.queries.concentration_risk import (
    ConcentrationRiskQuery,
    ConcentrationRiskQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_dependencies import (
    DependencyDto,
    ListDependenciesQuery,
    ListDependenciesQueryHandler,
)
from src.procurement_bc.vendor.domain.exceptions import (
    DependencyNotFoundError,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorDependencyRepository,
    VendorRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vendor-dependencies"])


def _to_response(dto: DependencyDto) -> DependencyResponse:
    return DependencyResponse(
        id=dto.id,
        vendor_id=dto.vendor_id,
        company_id=dto.company_id,
        service_description=dto.service_description,
        business_function=dto.business_function,
        is_critical=dto.is_critical,
        notes=dto.notes,
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


@router.post(
    "/api/v1/vendors/{vendor_id}/dependencies",
    status_code=status.HTTP_201_CREATED,
)
def create_dependency(
    vendor_id: str,
    body: CreateDependencyRequest,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    dependency_repo: VendorDependencyRepository = Depends(
        get_dependency_repo,
    ),
):
    _require_admin(current_user)

    dep_id = str(ulid.new())
    handler = CreateDependencyCommandHandler(
        vendor_repo=vendor_repo,
        dependency_repo=dependency_repo,
    )
    try:
        handler.handle(
            CreateDependencyCommand(
                id=dep_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                service_description=body.service_description,
                business_function=body.business_function,
                is_critical=body.is_critical,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except VendorNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    dep = dependency_repo.find_by_id(
        dep_id, vendor_id, current_user.company_id,
    )
    from src.procurement_bc.vendor.application.queries.list_dependencies import DependencyDto as DD
    dto = DD(
        id=dep.id,
        vendor_id=dep.vendor_id,
        company_id=dep.company_id,
        service_description=dep.service_description,
        business_function=dep.business_function.value,
        is_critical=dep.is_critical,
        notes=dep.notes,
        created_at=dep.created_at.isoformat() if dep.created_at else None,
    )
    return {
        "data": _to_response(dto).model_dump(mode="json"),
    }


@router.get("/api/v1/vendors/{vendor_id}/dependencies")
def list_dependencies(
    vendor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    dependency_repo: VendorDependencyRepository = Depends(
        get_dependency_repo,
    ),
):
    _require_technician(current_user)

    handler = ListDependenciesQueryHandler(
        dependency_repo=dependency_repo,
    )
    dtos, total = handler.handle(
        ListDependenciesQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
        )
    )
    return {
        "data": [_to_response(d).model_dump(mode="json") for d in dtos],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.put("/api/v1/vendors/{vendor_id}/dependencies/{dependency_id}")
def update_dependency(
    vendor_id: str,
    dependency_id: str,
    body: UpdateDependencyRequest,
    current_user: User = Depends(get_current_user),
    dependency_repo: VendorDependencyRepository = Depends(
        get_dependency_repo,
    ),
):
    _require_admin(current_user)

    handler = UpdateDependencyCommandHandler(
        dependency_repo=dependency_repo,
    )
    try:
        handler.handle(
            UpdateDependencyCommand(
                dependency_id=dependency_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                service_description=body.service_description,
                business_function=body.business_function,
                is_critical=body.is_critical,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except DependencyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    dep = dependency_repo.find_by_id(
        dependency_id, vendor_id, current_user.company_id,
    )
    from src.procurement_bc.vendor.application.queries.list_dependencies import DependencyDto as DD
    dto = DD(
        id=dep.id,
        vendor_id=dep.vendor_id,
        company_id=dep.company_id,
        service_description=dep.service_description,
        business_function=dep.business_function.value,
        is_critical=dep.is_critical,
        notes=dep.notes,
        created_at=dep.created_at.isoformat() if dep.created_at else None,
    )
    return {
        "data": _to_response(dto).model_dump(mode="json"),
    }


@router.delete(
    "/api/v1/vendors/{vendor_id}/dependencies/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_dependency(
    vendor_id: str,
    dependency_id: str,
    current_user: User = Depends(get_current_user),
    dependency_repo: VendorDependencyRepository = Depends(
        get_dependency_repo,
    ),
):
    _require_admin(current_user)

    handler = SoftDeleteDependencyCommandHandler(
        dependency_repo=dependency_repo,
    )
    try:
        handler.handle(
            SoftDeleteDependencyCommand(
                dependency_id=dependency_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except DependencyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dependency not found",
        )


@router.get("/api/v1/vendors/concentration-risk")
def get_concentration_risk(
    current_user: User = Depends(get_current_user),
    dependency_repo: VendorDependencyRepository = Depends(
        get_dependency_repo,
    ),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
):
    _require_admin(current_user)

    handler = ConcentrationRiskQueryHandler(
        dependency_repo=dependency_repo,
        vendor_repo=vendor_repo,
    )
    items = handler.handle(
        ConcentrationRiskQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": [
            ConcentrationRiskItemResponse(
                vendor_id=item.vendor_id,
                vendor_name=item.vendor_name,
                critical_count=item.critical_count,
                total_critical=item.total_critical,
                percentage=item.percentage,
                is_above_threshold=item.is_above_threshold,
            ).model_dump(mode="json")
            for item in items
        ],
    }
