import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.companies.schemas import (
    CompanyDetailResponse,
    CompanyResponse,
    CreateCompanyRequest,
    UpdateCompanyRequest,
    UpdateCompanyStatusRequest,
)
from adapters.http.schemas.responses import ListResponse, PaginationMeta
from core.database import get_db
from core.email import SMTPEmailService
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


@router.post("", status_code=status.HTTP_201_CREATED)
def create_company(
    body: CreateCompanyRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    handler = CreateCompanyCommandHandler(
        company_repo=CompanyRepository(db),
        user_repo=UserRepository(db),
        magic_link_repo=MagicLinkRepository(db),
        email_service=SMTPEmailService(),
    )
    try:
        company = handler.handle(
            CreateCompanyCommand(
                name=body.name,
                email_domains=body.email_domains,
                admin_email=body.admin_email,
            )
        )
    except CompanyNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Company with this name already exists",
        )
    except DomainAlreadyTakenError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )
    return {"data": _to_response(company).model_dump(mode="json")}


@router.get("")
def list_companies(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    handler = ListCompaniesQueryHandler(company_repo=CompanyRepository(db))
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
    db: Session = Depends(get_db),
):
    handler = GetCompanyQueryHandler(company_repo=CompanyRepository(db))
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
    db: Session = Depends(get_db),
):
    handler = UpdateCompanyCommandHandler(company_repo=CompanyRepository(db))
    try:
        company = handler.handle(
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
    return {"data": _to_response(company).model_dump(mode="json")}


@router.patch("/{company_id}/status")
def update_company_status(
    company_id: str,
    body: UpdateCompanyStatusRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    handler = UpdateCompanyStatusCommandHandler(company_repo=CompanyRepository(db))
    try:
        company = handler.handle(
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
    return {"data": _to_response(company).model_dump(mode="json")}
