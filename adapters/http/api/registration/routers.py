import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.registration.schemas import RegisterCompanyRequest
from core.database import get_db
from core.email import SMTPEmailService
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/register", tags=["registration"])


@router.post("", status_code=status.HTTP_201_CREATED)
def register_company(
    body: RegisterCompanyRequest,
    db: Session = Depends(get_db),
):
    """Public endpoint for self-service company registration."""
    handler = CreateCompanyCommandHandler(
        company_repo=CompanyRepository(db),
        user_repo=UserRepository(db),
        magic_link_repo=MagicLinkRepository(db),
        email_service=SMTPEmailService(),
    )
    try:
        handler.handle(
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
    return {"data": {"message": "Company registered. Check your email for the magic link."}}
