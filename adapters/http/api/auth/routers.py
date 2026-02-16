import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import get_current_user
from adapters.http.api.auth.schemas import (
    MagicLinkRequest,
    PasswordLoginRequest,
    SetPasswordRequest,
    TokenResponse,
    UserResponse,
    VerifyRequest,
)
from core.database import get_db
from core.email import SMTPEmailService
from core.jwt import JWTService
from core.password import PasswordService
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
from src.auth_bc.user.application.commands.password_login import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordLoginCommand,
    PasswordLoginCommandHandler,
)
from src.auth_bc.user.application.commands.set_password import (
    NotAdminError,
    SetPasswordCommand,
    SetPasswordCommandHandler,
    UserNotFoundError as SetPasswordUserNotFoundError,
    WeakPasswordError,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _user_response(user: User) -> dict:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        company_id=user.company_id,
        is_active=user.is_active,
        password_set=user.has_password,
    ).model_dump()


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
        user_repo=UserRepository(db),
    )
    try:
        handler.handle(CreateMagicLinkCommand(email=body.email))
    except InvalidEmailDomainError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your company is not registered yet",
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
    user_repo = UserRepository(db)
    handler = VerifyMagicLinkCommandHandler(
        magic_link_repo=MagicLinkRepository(db),
        user_repo=user_repo,
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

    # Decode token to get user_id, then fetch user for password_set flag
    jwt_service = JWTService()
    payload = jwt_service.decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    password_set = user.has_password if user else False

    return {
        "data": {
            **TokenResponse(access_token=access_token).model_dump(),
            "password_set": password_set,
        }
    }


@router.post("/login", response_model=None)
def password_login(
    body: PasswordLoginRequest,
    db: Session = Depends(get_db),
):
    """Login with email and password (admin accounts only)."""
    handler = PasswordLoginCommandHandler(
        user_repo=UserRepository(db),
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        password_service=PasswordService(),
    )
    try:
        access_token = handler.handle(
            PasswordLoginCommand(email=body.email, password=body.password)
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except AccountInactiveError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.post("/set-password", status_code=status.HTTP_200_OK)
def set_password(
    body: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set password for the current admin user."""
    handler = SetPasswordCommandHandler(
        user_repo=UserRepository(db),
        password_service=PasswordService(),
    )
    try:
        handler.handle(SetPasswordCommand(user_id=current_user.id, password=body.password))
    except SetPasswordUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except NotAdminError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin accounts can set a password",
        )
    except WeakPasswordError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters",
        )
    return {"data": {"message": "Password set successfully"}}


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return {"data": _user_response(current_user)}
