import logging

import ulid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from adapters.http.api.auth.dependencies import (
    get_current_user,
)
from adapters.http.api.vendors.dependencies import (
    get_vendor_repo,
)
from adapters.http.api.vendors.schemas import (
    VendorCreateRequest,
    VendorResponse,
    VendorUpdateRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.commands.activate_vendor import (  # noqa: E501
    ActivateVendorCommand,
    ActivateVendorCommandHandler,
    VendorNotFoundError as ActivateNotFoundError,
)
from src.procurement_bc.vendor.application.commands.create_vendor import (  # noqa: E501
    CreateVendorCommand,
    CreateVendorCommandHandler,
    DuplicateVendorNameError,
)
from src.procurement_bc.vendor.application.commands.deactivate_vendor import (  # noqa: E501
    DeactivateVendorCommand,
    DeactivateVendorCommandHandler,
    VendorNotFoundError as DeactivateNotFoundError,
)
from src.procurement_bc.vendor.application.commands.update_vendor import (  # noqa: E501
    UpdateVendorCommand,
    UpdateVendorCommandHandler,
)
from src.procurement_bc.vendor.domain.exceptions import (
    VendorNotFoundError as UpdateNotFoundError,
)
from src.procurement_bc.vendor.application.queries.get_vendor import (  # noqa: E501
    GetVendorQuery,
    GetVendorQueryHandler,
    VendorNotFoundError as GetNotFoundError,
)
from src.procurement_bc.vendor.application.queries.list_vendors import (  # noqa: E501
    ListVendorsQuery,
    ListVendorsQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import (
    Vendor,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors",
    tags=["vendors"],
)


def _to_response(vendor: Vendor) -> VendorResponse:
    return VendorResponse(
        id=vendor.id,
        company_id=vendor.company_id,
        name=vendor.name,
        contact_email=vendor.contact_email,
        phone=vendor.phone,
        address=vendor.address,
        notes=vendor.notes,
        is_active=vendor.is_active,
        is_critical_ict=vendor.is_critical_ict,
        risk_level=vendor.risk_level.value if vendor.risk_level else None,
        website=vendor.website,
        category=vendor.category.value if vendor.category else None,
        created_at=vendor.created_at,
        updated_at=vendor.updated_at,
    )


def _require_technician(user: User) -> None:
    if not user.role.has_access(UserRole.TECHNICIAN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Technician access required",
        )


def _require_procurement_access(user: User) -> None:
    if not user.role.has_access(UserRole.PROCUREMENT_MANAGER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Procurement manager access required",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vendor(
    body: VendorCreateRequest,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_technician(current_user)

    vendor_id = str(ulid.new())
    handler = CreateVendorCommandHandler(
        vendor_repo=vendor_repo,
    )
    try:
        handler.handle(
            CreateVendorCommand(
                id=vendor_id,
                company_id=current_user.company_id,
                name=body.name,
                contact_email=body.contact_email,
                phone=body.phone,
                address=body.address,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except DuplicateVendorNameError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A vendor with this name already exists",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    vendor = GetVendorQueryHandler(
        vendor_repo=vendor_repo,
    ).handle(
        GetVendorQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(vendor).model_dump(
            mode="json",
        ),
    }


@router.get("")
def list_vendors(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    is_active: bool = Query(None),
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_technician(current_user)

    handler = ListVendorsQueryHandler(
        vendor_repo=vendor_repo,
    )
    vendors, total = handler.handle(
        ListVendorsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            search=search,
            is_active=is_active,
        )
    )
    return {
        "data": [
            _to_response(v).model_dump(mode="json")
            for v in vendors
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_technician(current_user)

    handler = GetVendorQueryHandler(
        vendor_repo=vendor_repo,
    )
    try:
        vendor = handler.handle(
            GetVendorQuery(
                vendor_id=vendor_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    return {
        "data": _to_response(vendor).model_dump(
            mode="json",
        ),
    }


@router.put("/{vendor_id}")
def update_vendor(
    vendor_id: str,
    body: VendorUpdateRequest,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_technician(current_user)

    handler = UpdateVendorCommandHandler(
        vendor_repo=vendor_repo,
    )
    try:
        handler.handle(
            UpdateVendorCommand(
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                name=body.name,
                contact_email=body.contact_email,
                phone=body.phone,
                address=body.address,
                notes=body.notes,
                category=body.category,
                website=body.website,
                is_critical_ict=body.is_critical_ict,
                performed_by=current_user.id,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    vendor = GetVendorQueryHandler(
        vendor_repo=vendor_repo,
    ).handle(
        GetVendorQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(vendor).model_dump(
            mode="json",
        ),
    }


@router.post("/{vendor_id}/activate")
def activate_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_procurement_access(current_user)

    handler = ActivateVendorCommandHandler(
        vendor_repo=vendor_repo,
    )
    try:
        handler.handle(
            ActivateVendorCommand(
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ActivateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    vendor = GetVendorQueryHandler(
        vendor_repo=vendor_repo,
    ).handle(
        GetVendorQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(vendor).model_dump(
            mode="json",
        ),
    }


@router.post("/{vendor_id}/deactivate")
def deactivate_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(
        get_vendor_repo,
    ),
):
    _require_procurement_access(current_user)

    handler = DeactivateVendorCommandHandler(
        vendor_repo=vendor_repo,
    )
    try:
        handler.handle(
            DeactivateVendorCommand(
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except DeactivateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found",
        )

    vendor = GetVendorQueryHandler(
        vendor_repo=vendor_repo,
    ).handle(
        GetVendorQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(vendor).model_dump(
            mode="json",
        ),
    }
