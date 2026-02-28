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
from adapters.http.api.vendors.contract_dependencies import (
    get_contract_repo,
    get_contract_document_repo,
)
from adapters.http.api.vendors.contract_schemas import (
    ChangeContractStatusRequest,
    ContractResponse,
    CreateContractRequest,
    UpdateContractRequest,
)
from adapters.http.api.vendors.dependencies import get_vendor_repo
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.procurement_bc.vendor.application.commands.change_contract_status import (  # noqa: E501
    ChangeContractStatusCommand,
    ChangeContractStatusCommandHandler,
)
from src.procurement_bc.vendor.application.commands.create_contract import (
    CreateContractCommand,
    CreateContractCommandHandler,
)
from src.procurement_bc.vendor.application.commands.soft_delete_contract import (  # noqa: E501
    SoftDeleteContractCommand,
    SoftDeleteContractCommandHandler,
)
from src.procurement_bc.vendor.application.commands.update_contract import (
    UpdateContractCommand,
    UpdateContractCommandHandler,
)
from src.procurement_bc.vendor.application.queries.get_contract import (
    GetContractQuery,
    GetContractQueryHandler,
)
from src.procurement_bc.vendor.application.queries.list_contracts import (
    ListContractsQuery,
    ListContractsQueryHandler,
)
from src.procurement_bc.vendor.domain.entities import VendorContract
from src.procurement_bc.vendor.domain.exceptions import (
    ContractNotFoundError,
    InvalidContractTransitionError,
    VendorNotFoundError,
)
from src.procurement_bc.vendor.infrastructure.repository import (
    VendorContractDocumentRepository,
    VendorContractRepository,
    VendorRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/vendors/{vendor_id}/contracts",
    tags=["vendor-contracts"],
)


def _to_response(
    contract: VendorContract,
    document_count: int | None = None,
) -> ContractResponse:
    return ContractResponse(
        id=contract.id,
        vendor_id=contract.vendor_id,
        company_id=contract.company_id,
        contract_type=contract.contract_type.value,
        title=contract.title,
        start_date=contract.start_date,
        end_date=contract.end_date,
        renewal_date=contract.renewal_date,
        auto_renewal=contract.auto_renewal,
        annual_value=contract.annual_value,
        currency=contract.currency,
        security_clauses=contract.security_clauses,
        notes=contract.notes,
        status=contract.status.value,
        document_count=document_count,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_contract(
    vendor_id: str,
    body: CreateContractRequest,
    current_user: User = Depends(get_current_user),
    vendor_repo: VendorRepository = Depends(get_vendor_repo),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    contract_id = str(ulid.new())
    handler = CreateContractCommandHandler(
        vendor_repo=vendor_repo,
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            CreateContractCommand(
                id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                contract_type=body.contract_type,
                title=body.title,
                start_date=body.start_date,
                end_date=body.end_date,
                renewal_date=body.renewal_date,
                auto_renewal=body.auto_renewal,
                annual_value=body.annual_value,
                currency=body.currency,
                security_clauses=body.security_clauses,
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

    contract = contract_repo.find_by_id(
        contract_id, vendor_id, current_user.company_id,
    )
    return {
        "data": _to_response(contract).model_dump(mode="json"),
    }


@router.get("")
def list_contracts(
    vendor_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    contract_status: str = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_technician(current_user)

    handler = ListContractsQueryHandler(
        contract_repo=contract_repo,
    )
    contracts, total = handler.handle(
        ListContractsQuery(
            vendor_id=vendor_id,
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            status=contract_status,
        )
    )
    return {
        "data": [
            _to_response(c).model_dump(mode="json")
            for c in contracts
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/{contract_id}")
def get_contract(
    vendor_id: str,
    contract_id: str,
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
    document_repo: VendorContractDocumentRepository = Depends(
        get_contract_document_repo,
    ),
):
    _require_technician(current_user)

    handler = GetContractQueryHandler(
        contract_repo=contract_repo,
        document_repo=document_repo,
    )
    try:
        result = handler.handle(
            GetContractQuery(
                contract_id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
            )
        )
    except ContractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    return {
        "data": _to_response(
            result.contract, result.document_count,
        ).model_dump(mode="json"),
    }


@router.put("/{contract_id}")
def update_contract(
    vendor_id: str,
    contract_id: str,
    body: UpdateContractRequest,
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    handler = UpdateContractCommandHandler(
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            UpdateContractCommand(
                contract_id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                title=body.title,
                contract_type=body.contract_type,
                start_date=body.start_date,
                end_date=body.end_date,
                renewal_date=body.renewal_date,
                auto_renewal=body.auto_renewal,
                annual_value=body.annual_value,
                currency=body.currency,
                security_clauses=body.security_clauses,
                notes=body.notes,
                performed_by=current_user.id,
            )
        )
    except ContractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    contract = contract_repo.find_by_id(
        contract_id, vendor_id, current_user.company_id,
    )
    return {
        "data": _to_response(contract).model_dump(mode="json"),
    }


@router.post("/{contract_id}/change-status")
def change_contract_status(
    vendor_id: str,
    contract_id: str,
    body: ChangeContractStatusRequest,
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    handler = ChangeContractStatusCommandHandler(
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            ChangeContractStatusCommand(
                contract_id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                new_status=body.status,
                performed_by=current_user.id,
            )
        )
    except ContractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    except InvalidContractTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    contract = contract_repo.find_by_id(
        contract_id, vendor_id, current_user.company_id,
    )
    return {
        "data": _to_response(contract).model_dump(mode="json"),
    }


@router.delete(
    "/{contract_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_contract(
    vendor_id: str,
    contract_id: str,
    current_user: User = Depends(get_current_user),
    contract_repo: VendorContractRepository = Depends(
        get_contract_repo,
    ),
):
    _require_admin(current_user)

    handler = SoftDeleteContractCommandHandler(
        contract_repo=contract_repo,
    )
    try:
        handler.handle(
            SoftDeleteContractCommand(
                contract_id=contract_id,
                vendor_id=vendor_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ContractNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
