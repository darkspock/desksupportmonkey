import logging
from typing import Optional

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.addresses.dependencies import (
    get_address_repo,
)
from adapters.http.api.addresses.schemas import (
    AddressCreateRequest,
    AddressResponse,
    AddressUpdateRequest,
)
from adapters.http.api.auth.dependencies import (
    require_role,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.shipping_bc.address.application.commands.create_address import (
    CreateAddressCommand,
    CreateAddressCommandHandler,
)
from src.shipping_bc.address.application.commands.deactivate_address import (
    DeactivateAddressCommand,
    DeactivateAddressCommandHandler,
)
from src.shipping_bc.address.application.commands.deactivate_address import (
    AddressNotFoundError as DeactivateNotFoundError,
)
from src.shipping_bc.address.application.commands.update_address import (
    UpdateAddressCommand,
    UpdateAddressCommandHandler,
)
from src.shipping_bc.address.application.commands.update_address import (
    AddressNotFoundError as UpdateNotFoundError,
)
from src.shipping_bc.address.application.queries.addresses_by_user import (
    AddressesByUserQuery,
    AddressesByUserQueryHandler,
)
from src.shipping_bc.address.application.queries.get_address import (
    GetAddressQuery,
    GetAddressQueryHandler,
)
from src.shipping_bc.address.application.queries.get_address import (
    AddressNotFoundError as GetNotFoundError,
)
from src.shipping_bc.address.application.queries.list_addresses import (
    ListAddressesQuery,
    ListAddressesQueryHandler,
)
from src.shipping_bc.address.domain.entities import (
    ShippingAddress,
)
from src.shipping_bc.address.infrastructure.repository import (
    ShippingAddressRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/addresses", tags=["addresses"],
)

tech_dep = require_role(UserRole.TECHNICIAN)


def _to_response(address: ShippingAddress) -> dict:
    return AddressResponse(
        id=address.id,
        company_id=address.company_id,
        label=address.label,
        street_line_1=address.street_line_1,
        street_line_2=address.street_line_2,
        city=address.city,
        state=address.state,
        postal_code=address.postal_code,
        country=address.country,
        recipient_name=address.recipient_name,
        phone=address.phone,
        user_id=address.user_id,
        is_office=address.is_office,
        is_active=address.is_active,
        created_at=address.created_at,
        updated_at=address.updated_at,
    ).model_dump(mode="json")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_address(
    body: AddressCreateRequest,
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    address_id = ulid.new().str
    handler = CreateAddressCommandHandler(
        address_repo=address_repo,
    )
    handler.handle(
        CreateAddressCommand(
            address_id=address_id,
            company_id=current_user.company_id,
            label=body.label,
            street_line_1=body.street_line_1,
            city=body.city,
            state=body.state,
            postal_code=body.postal_code,
            country=body.country,
            street_line_2=body.street_line_2,
            recipient_name=body.recipient_name,
            phone=body.phone,
            user_id=body.user_id,
            is_office=body.is_office,
        )
    )

    address = address_repo.find_by_id(
        address_id, current_user.company_id,
    )
    return {"data": _to_response(address)}


@router.get("")
def list_addresses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    is_office: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(True),
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    handler = ListAddressesQueryHandler(
        address_repo=address_repo,
    )
    addresses, total = handler.handle(
        ListAddressesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            user_id=user_id,
            is_office=is_office,
            is_active=is_active,
        )
    )
    return {
        "data": [
            _to_response(a) for a in addresses
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/by-user/{user_id}")
def addresses_by_user(
    user_id: str,
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    handler = AddressesByUserQueryHandler(
        address_repo=address_repo,
    )
    addresses = handler.handle(
        AddressesByUserQuery(
            user_id=user_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": [
            _to_response(a) for a in addresses
        ],
    }


@router.get("/{address_id}")
def get_address(
    address_id: str,
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    handler = GetAddressQueryHandler(
        address_repo=address_repo,
    )
    try:
        address = handler.handle(
            GetAddressQuery(
                address_id=address_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    return {"data": _to_response(address)}


@router.put("/{address_id}")
def update_address(
    address_id: str,
    body: AddressUpdateRequest,
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    handler = UpdateAddressCommandHandler(
        address_repo=address_repo,
    )
    try:
        handler.handle(
            UpdateAddressCommand(
                address_id=address_id,
                company_id=current_user.company_id,
                label=body.label,
                street_line_1=body.street_line_1,
                street_line_2=body.street_line_2,
                city=body.city,
                state=body.state,
                postal_code=body.postal_code,
                country=body.country,
                recipient_name=body.recipient_name,
                phone=body.phone,
                user_id=body.user_id,
                is_office=body.is_office,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    address = address_repo.find_by_id(
        address_id, current_user.company_id,
    )
    return {"data": _to_response(address)}


@router.delete("/{address_id}")
def deactivate_address(
    address_id: str,
    current_user: User = Depends(tech_dep),
    address_repo: ShippingAddressRepository = Depends(
        get_address_repo,
    ),
):
    handler = DeactivateAddressCommandHandler(
        address_repo=address_repo,
    )
    try:
        handler.handle(
            DeactivateAddressCommand(
                address_id=address_id,
                company_id=current_user.company_id,
            )
        )
    except DeactivateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address not found",
        )

    address = address_repo.find_by_id(
        address_id, current_user.company_id,
    )
    return {"data": _to_response(address)}
