import logging
from typing import Optional

import ulid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.companies.dependencies import (
    get_company_repo,
    get_magic_link_repo,
    get_user_repo,
)
from adapters.http.api.companies.schemas import (
    CompanyDetailResponse,
    CompanyResponse,
    CreateCompanyRequest,
    UpdateCompanyRequest,
    UpdateCompanyStatusRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.email import get_email_service
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.application.commands.update_company import (
    CompanyNotFoundError as UpdateCompanyNotFoundError,
)
from src.company_bc.company.application.commands.update_company import (
    CompanyNameExistsError as UpdateNameExistsError,
)
from src.company_bc.company.application.commands.update_company import (
    DomainAlreadyTakenError as UpdateDomainTakenError,
)
from src.company_bc.company.application.commands.update_company import (
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.application.queries.get_company import (
    CompanyNotFoundError,
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.application.queries.list_companies import (
    ListCompaniesQuery,
    ListCompaniesQueryHandler,
)
from src.company_bc.company.application.commands.update_company_status import (
    CompanyNotFoundError as StatusCompanyNotFoundError,
    UpdateCompanyStatusCommand,
    UpdateCompanyStatusCommandHandler,
)
from src.company_bc.company.domain.entities import Company, InvalidStatusTransitionError
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _to_response(company: Company) -> CompanyResponse:
    return CompanyResponse(
        id=company.id,
        name=company.name,
        status=company.status.value,
        email_domains=company.email_domains,
        is_active=company.is_active,
        created_at=company.created_at,
        updated_at=company.updated_at,
    )


def _get_company_response(company_repo: CompanyRepository, company_id: str) -> dict:
    query_handler = GetCompanyQueryHandler(company_repo=company_repo)
    detail = query_handler.handle(GetCompanyQuery(company_id=company_id))
    return {"data": _to_response(detail.company).model_dump(mode="json")}


def _handle_create_company_errors(handler: CreateCompanyCommandHandler, command: CreateCompanyCommand) -> None:
    try:
        handler.handle(command)
    except CompanyNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists",
        )
    except DomainAlreadyTakenError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(
    body: CreateCompanyRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
):
    company_id = str(ulid.new())
    handler = CreateCompanyCommandHandler(
        company_repo=company_repo,
        user_repo=user_repo,
        magic_link_repo=magic_link_repo,
        email_service=get_email_service(),
    )
    command = CreateCompanyCommand(
        name=body.name,
        email_domains=body.email_domains,
        admin_email=body.admin_email,
        id=company_id,
    )
    _handle_create_company_errors(handler, command)
    return _get_company_response(company_repo, company_id)


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = ListCompaniesQueryHandler(company_repo=company_repo)
    companies, total = handler.handle(
        ListCompaniesQuery(page=page, page_size=page_size, search=search)
    )
    return {
        "data": [_to_response(c).model_dump(mode="json") for c in companies],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{company_id}")
def get_company(
    company_id: str,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = GetCompanyQueryHandler(company_repo=company_repo)
    try:
        detail = handler.handle(GetCompanyQuery(company_id=company_id))
    except CompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return {
        "data": CompanyDetailResponse(
            id=detail.company.id,
            name=detail.company.name,
            status=detail.company.status.value,
            email_domains=detail.company.email_domains,
            is_active=detail.company.is_active,
            created_at=detail.company.created_at,
            updated_at=detail.company.updated_at,
            user_count=detail.user_count,
            department_count=detail.department_count,
        ).model_dump(mode="json")
    }


@router.put("/{company_id}")
def update_company(
    company_id: str,
    body: UpdateCompanyRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = UpdateCompanyCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanyCommand(
                company_id=company_id,
                name=body.name,
                email_domains=body.email_domains,
            )
        )
    except UpdateCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except UpdateNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists",
        )
    except UpdateDomainTakenError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return _get_company_response(company_repo, company_id)


@router.patch("/{company_id}/status")
def update_company_status(
    company_id: str,
    body: UpdateCompanyStatusRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    handler = UpdateCompanyStatusCommandHandler(company_repo=company_repo)
    try:
        handler.handle(
            UpdateCompanyStatusCommand(
                company_id=company_id,
                new_status=body.status,
            )
        )
    except StatusCompanyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid status value. Must be: active, suspended, or deactivated",
        )
    return _get_company_response(company_repo, company_id)
