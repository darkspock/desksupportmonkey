import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.auth.schemas import (
    MagicLinkRequest,
    TokenResponse,
    UserResponse,
    VerifyRequest,
)
from core.database import get_db
from core.email import SMTPEmailService
from core.jwt import JWTService
from src.auth_bc.company_lookup.infrastructure.service import CompanyLookupService
from src.auth_bc.magic_link.application.commands.create_magic_link import (
    CompanyRestrictedError,
    CreateMagicLinkCommand,
    CreateMagicLinkCommandHandler,
    InvalidEmailDomainError,
    RateLimitExceededError,
)
from src.auth_bc.magic_link.application.commands.verify_magic_link import (
    CompanyRestrictedError as VerifyCompanyRestrictedError,
    ExpiredTokenError,
    InvalidTokenError,
    UsedTokenError,
    VerifyMagicLinkCommand,
    VerifyMagicLinkCommandHandler,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/magic-link", status_code=status.HTTP_200_OK)
def request_magic_link(
    body: MagicLinkRequest,
    db: Session = Depends(get_db),
):
    """Request a magic link for passwordless authentication."""
    handler = CreateMagicLinkCommandHandler(
        magic_link_repo=MagicLinkRepository(db),
        company_lookup=CompanyLookupService(db),
        email_service=SMTPEmailService(),
    )
    try:
        handler.handle(CreateMagicLinkCommand(email=body.email))
    except InvalidEmailDomainError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only corporate email addresses are allowed",
        )
    except CompanyRestrictedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access is currently restricted",
        )
    except RateLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait before requesting another link.",
        )
    return {"data": {"message": "Magic link sent. Check your email."}}


@router.post("/verify", response_model=None)
def verify_magic_link(
    body: VerifyRequest,
    db: Session = Depends(get_db),
):
    """Verify magic link token and return JWT."""
    handler = VerifyMagicLinkCommandHandler(
        magic_link_repo=MagicLinkRepository(db),
        user_repo=UserRepository(db),
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
    )
    try:
        access_token = handler.handle(VerifyMagicLinkCommand(token=body.token))
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid link",
        )
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Link expired",
        )
    except UsedTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Link already used",
        )
    except VerifyCompanyRestrictedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Company access is currently restricted",
        )
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {
        "data": UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            role=current_user.role.value,
            company_id=current_user.company_id,
            is_active=current_user.is_active,
        ).model_dump()
    }
