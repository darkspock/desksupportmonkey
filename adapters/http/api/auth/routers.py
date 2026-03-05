import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import (
    get_company_repo,
    get_company_user_repo,
    get_current_user,
    get_google_oauth_login_service,
    get_magic_link_repo,
    get_membership_auth_service,
    get_microsoft_oauth_login_service,
    get_oauth_settings,
    get_user_repo,
)
from adapters.http.api.auth.schemas import (
    MagicLinkRequest,
    OAuthLoginRequest,
    OAuthProvidersResponse,
    PasswordLoginRequest,
    SetPasswordRequest,
    SwitchCompanyRequest as SwitchCompanyBody,
    TokenResponse,
    UserCompanyResponse,
    UserResponse,
    VerifyRequest,
)
from core.config import OAuthSettings
from core.database import get_db
from core.email import get_email_service
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
    VerifyMagicLinkRequest,
    VerifyMagicLinkService,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.application.commands.password_login import (
    AccountInactiveError,
    InvalidCredentialsError,
    PasswordLoginRequest as PasswordLoginInput,
    PasswordLoginService,
)
from src.auth_bc.user.application.commands.google_oauth_login import (
    GoogleEmailNotVerified,
    GoogleNotConfiguredError,
    GoogleOAuthLoginRequest,
    GoogleOAuthLoginService,
    GoogleTokenInvalidError,
)
from src.auth_bc.user.application.commands.microsoft_oauth_login import (
    MicrosoftMissingEmail,
    MicrosoftNotConfiguredError,
    MicrosoftOAuthLoginRequest,
    MicrosoftOAuthLoginService,
    MicrosoftTokenInvalidError,
)
from src.auth_bc.user.application.commands.set_password import (
    NotAdminError,
    SetPasswordCommand,
    SetPasswordCommandHandler,
    UserNotFoundError as SetPasswordUserNotFoundError,
    WeakPasswordError,
)
from src.auth_bc.user.application.services.oauth_login_service import (
    CompanyRestrictedError as OAuthCompanyRestrictedError,
    InvalidEmailDomainError as OAuthInvalidEmailDomainError,
    UserDeactivatedError,
)
from src.auth_bc.company_user.domain.entities import (
    MembershipDeactivatedError,
    MembershipNotAllowedError,
    MembershipNotFoundError,
)
from src.auth_bc.user.application.commands.switch_company import (
    SwitchCompanyRequest as SwitchCompanyInput,
    SwitchCompanyService,
)
from src.auth_bc.user.application.queries.list_user_companies import (
    ListUserCompaniesQuery,
    ListUserCompaniesQueryHandler,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.exceptions import OAuthProviderAlreadyLinkedError
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def _resolve_slug(slug: str, db: Session):
    """Resolve slug to active company, or raise HTTPException."""
    company_repo = CompanyRepository(db)
    company = company_repo.find_by_slug(slug)
    if not company or not company.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


def _check_slug_billing(company, db: Session) -> None:
    """Check billing status for slug-scoped endpoints."""
    from core.config import settings as _settings
    if _settings.stripe.OPEN_SOURCE_MODE or company.complimentary:
        return
    from src.company_bc.company.domain.billing_enums import BillingStatus
    if not company.is_in_trial() and company.billing_status == BillingStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="account_suspended",
        )


def _check_multi_company(email: str, db: Session) -> None:
    """Check if email matches multiple companies; raise 409 if so."""
    company_lookup = CompanyLookupService(db)
    companies = company_lookup.find_companies_by_email_domain(email)
    active_companies = [
        (cid, slug, active) for cid, slug, active in companies if active
    ]
    if len(active_companies) > 1:
        slugs = [slug for _, slug, _ in active_companies]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=json.dumps({"error": "multiple_companies", "slugs": slugs}),
        )


def _check_billing_not_suspended(user: Optional[User], db: Session) -> None:
    """Block new login sessions for billing-suspended companies (skip for open source / complimentary)."""
    if not user or not user.company_id:
        return
    from core.config import settings as _settings
    if _settings.stripe.OPEN_SOURCE_MODE:
        return
    from src.company_bc.company.infrastructure.repository import CompanyRepository as _CompanyRepository
    from src.company_bc.company.domain.billing_enums import BillingStatus
    company = _CompanyRepository(db).find_by_id(user.company_id)
    if company and not company.complimentary and not company.is_in_trial() and company.billing_status == BillingStatus.SUSPENDED:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="account_suspended")


def _user_response(
    user: User,
    company_name: Optional[str] = None,
    hidden_nav_items: Optional[dict] = None,
    needs_onboarding: bool = False,
    company_plan: Optional[str] = None,
    demo_days_remaining: Optional[int] = None,
) -> dict:
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        company_id=user.company_id,
        company_name=company_name,
        employee_role_id=user.employee_role_id,
        is_active=user.is_active,
        password_set=user.has_password,
        has_oauth=bool(user.google_id or user.microsoft_id),
        hidden_nav_items=hidden_nav_items,
        needs_onboarding=needs_onboarding,
        company_plan=company_plan,
        demo_days_remaining=demo_days_remaining,
    ).model_dump()


@router.get("/oauth/providers", response_model=None)
def get_oauth_providers(oauth: OAuthSettings = Depends(get_oauth_settings)):
    """Return which OAuth providers are enabled on this deployment."""
    return {"data": OAuthProvidersResponse(
        google=bool(oauth.GOOGLE_CLIENT_ID),
        microsoft=bool(oauth.MICROSOFT_CLIENT_ID),
    ).model_dump()}


@router.post("/magic-link", status_code=status.HTTP_200_OK)
def request_magic_link(
    body: MagicLinkRequest,
    db: Session = Depends(get_db),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Request a magic link for passwordless authentication."""
    _check_multi_company(body.email, db)
    handler = CreateMagicLinkCommandHandler(
        magic_link_repo=magic_link_repo,
        company_lookup=CompanyLookupService(db),
        email_service=get_email_service(),
        user_repo=user_repo,
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
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    membership_auth=Depends(get_membership_auth_service),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    """Verify magic link token and return JWT."""
    handler = VerifyMagicLinkService(
        magic_link_repo=magic_link_repo,
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        membership_auth=membership_auth,
        company_repo=company_repo,
    )
    try:
        access_token = handler.handle(VerifyMagicLinkRequest(token=body.token))
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid link")
    except ExpiredTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Link expired")
    except UsedTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Link already used")
    except VerifyCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except MembershipDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
    except MembershipNotAllowedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")

    payload = JWTService().decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    _check_billing_not_suspended(user, db)
    password_set = user.has_password if user else False
    return {"data": {**TokenResponse(access_token=access_token).model_dump(), "password_set": password_set}}


@router.post("/login", response_model=None)
def password_login(
    body: PasswordLoginRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Login with email and password (admin accounts only)."""
    _check_multi_company(body.email, db)
    handler = PasswordLoginService(
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        password_service=PasswordService(),
    )
    try:
        access_token = handler.handle(
            PasswordLoginInput(email=body.email, password=body.password)
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
    payload = JWTService().decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    _check_billing_not_suspended(user, db)
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.post("/set-password", status_code=status.HTTP_200_OK)
def set_password(
    body: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Set password for the current admin user."""
    handler = SetPasswordCommandHandler(
        user_repo=user_repo,
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


@router.post("/oauth/google", response_model=None)
def google_oauth_login(
    body: OAuthLoginRequest,
    db: Session = Depends(get_db),
    service: GoogleOAuthLoginService = Depends(get_google_oauth_login_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Exchange a Google ID token for a DeskSupportMonkey JWT."""
    try:
        access_token = service.handle(GoogleOAuthLoginRequest(id_token=body.id_token))
    except GoogleNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google login is not enabled on this server",
        )
    except (GoogleTokenInvalidError, GoogleEmailNotVerified) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UserDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    except OAuthCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except OAuthInvalidEmailDomainError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your company is not registered yet")
    except OAuthProviderAlreadyLinkedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Google account is already linked to another user")
    payload = JWTService().decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    _check_billing_not_suspended(user, db)
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.post("/oauth/microsoft", response_model=None)
def microsoft_oauth_login(
    body: OAuthLoginRequest,
    db: Session = Depends(get_db),
    service: MicrosoftOAuthLoginService = Depends(get_microsoft_oauth_login_service),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Exchange a Microsoft ID token for a DeskSupportMonkey JWT."""
    try:
        access_token = service.handle(MicrosoftOAuthLoginRequest(id_token=body.id_token))
    except MicrosoftNotConfiguredError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Microsoft login is not enabled on this server",
        )
    except (MicrosoftTokenInvalidError, MicrosoftMissingEmail) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UserDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    except OAuthCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except OAuthInvalidEmailDomainError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your company is not registered yet")
    except OAuthProviderAlreadyLinkedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Microsoft account is already linked to another user")
    payload = JWTService().decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    _check_billing_not_suspended(user, db)
    return {"data": TokenResponse(access_token=access_token).model_dump()}


# --- Slug-Scoped Endpoints ---


@router.post("/{slug}/magic-link", status_code=status.HTTP_200_OK)
def slug_request_magic_link(
    slug: str,
    body: MagicLinkRequest,
    db: Session = Depends(get_db),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Request a magic link scoped to a specific company."""
    company = _resolve_slug(slug, db)
    _check_slug_billing(company, db)
    handler = CreateMagicLinkCommandHandler(
        magic_link_repo=magic_link_repo,
        company_lookup=CompanyLookupService(db),
        email_service=get_email_service(),
        user_repo=user_repo,
    )
    try:
        handler.handle(CreateMagicLinkCommand(email=body.email, company_id=company.id))
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


@router.post("/{slug}/verify", response_model=None)
def slug_verify_magic_link(
    slug: str,
    body: VerifyRequest,
    db: Session = Depends(get_db),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Verify magic link token scoped to a specific company."""
    company = _resolve_slug(slug, db)
    _check_slug_billing(company, db)

    from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
    from src.auth_bc.company_user.domain.membership_auth_service import MembershipAuthService

    membership_auth = MembershipAuthService(
        company_user_repo=CompanyUserRepository(db),
        company_lookup=CompanyLookupService(db),
        user_repo=user_repo,
    )
    handler = VerifyMagicLinkService(
        magic_link_repo=magic_link_repo,
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        membership_auth=membership_auth,
        company_repo=CompanyRepository(db),
    )
    try:
        access_token = handler.handle(VerifyMagicLinkRequest(token=body.token))
    except InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid link")
    except ExpiredTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Link expired")
    except UsedTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Link already used")
    except VerifyCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except MembershipDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
    except MembershipNotAllowedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")

    payload = JWTService().decode_token(access_token)
    user = user_repo.find_by_id(payload["sub"])
    password_set = user.has_password if user else False
    return {"data": {**TokenResponse(access_token=access_token).model_dump(), "password_set": password_set}}


@router.post("/{slug}/login", response_model=None)
def slug_password_login(
    slug: str,
    body: PasswordLoginRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Password login scoped to a specific company."""
    company = _resolve_slug(slug, db)
    _check_slug_billing(company, db)

    from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
    from src.auth_bc.company_user.domain.membership_auth_service import MembershipAuthService

    membership_auth = MembershipAuthService(
        company_user_repo=CompanyUserRepository(db),
        company_lookup=CompanyLookupService(db),
        user_repo=user_repo,
    )
    handler = PasswordLoginService(
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        password_service=PasswordService(),
        membership_auth=membership_auth,
        company_repo=CompanyRepository(db),
    )
    try:
        access_token = handler.handle(
            PasswordLoginInput(email=body.email, password=body.password, company_id=company.id)
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    except AccountInactiveError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    except MembershipDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
    except MembershipNotAllowedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.post("/{slug}/oauth/google", response_model=None)
def slug_google_oauth_login(
    slug: str,
    body: OAuthLoginRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
    oauth_settings: OAuthSettings = Depends(get_oauth_settings),
):
    """Google OAuth login scoped to a specific company."""
    company = _resolve_slug(slug, db)
    _check_slug_billing(company, db)

    from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
    from src.auth_bc.company_user.domain.membership_auth_service import MembershipAuthService

    membership_auth = MembershipAuthService(
        company_user_repo=CompanyUserRepository(db),
        company_lookup=CompanyLookupService(db),
        user_repo=user_repo,
    )
    from src.auth_bc.user.application.services.oauth_login_service import OAuthLoginService
    oauth_service = OAuthLoginService(
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        membership_auth=membership_auth,
        company_repo=CompanyRepository(db),
    )
    service = GoogleOAuthLoginService(
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        oauth_settings=oauth_settings,
    )
    try:
        access_token = service.handle(GoogleOAuthLoginRequest(id_token=body.id_token, company_id=company.id))
    except GoogleNotConfiguredError:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Google login is not enabled on this server")
    except (GoogleTokenInvalidError, GoogleEmailNotVerified) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UserDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    except OAuthCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except OAuthInvalidEmailDomainError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your company is not registered yet")
    except OAuthProviderAlreadyLinkedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Google account is already linked to another user")
    except MembershipDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
    except MembershipNotAllowedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.post("/{slug}/oauth/microsoft", response_model=None)
def slug_microsoft_oauth_login(
    slug: str,
    body: OAuthLoginRequest,
    db: Session = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
    oauth_settings: OAuthSettings = Depends(get_oauth_settings),
):
    """Microsoft OAuth login scoped to a specific company."""
    company = _resolve_slug(slug, db)
    _check_slug_billing(company, db)

    service = MicrosoftOAuthLoginService(
        user_repo=user_repo,
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
        oauth_settings=oauth_settings,
    )
    try:
        access_token = service.handle(MicrosoftOAuthLoginRequest(id_token=body.id_token, company_id=company.id))
    except MicrosoftNotConfiguredError:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Microsoft login is not enabled on this server")
    except (MicrosoftTokenInvalidError, MicrosoftMissingEmail) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UserDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    except OAuthCompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except OAuthInvalidEmailDomainError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your company is not registered yet")
    except OAuthProviderAlreadyLinkedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Microsoft account is already linked to another user")
    except MembershipDeactivatedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
    except MembershipNotAllowedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")
    return {"data": TokenResponse(access_token=access_token).model_dump()}


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    """Get current authenticated user profile."""
    company_name: Optional[str] = None
    hidden_nav_items = None
    needs_onboarding = False
    company_plan: Optional[str] = None
    demo_days_remaining: Optional[int] = None
    if current_user.company_id:
        company = company_repo.find_by_id(current_user.company_id)
        company_name = company.name if company else None

        if company:
            company_plan = company.plan.value
            demo_days_remaining = company.demo_days_remaining

        from src.auth_bc.user.domain.enums import UserRole
        if current_user.role == UserRole.ADMIN and company:
            needs_onboarding = company.onboarding_completed_at is None

        # Load nav visibility config
        from src.company_bc.nav_config.infrastructure.repository import NavConfigRepository
        nav_config = NavConfigRepository(db).find_by_company(current_user.company_id)
        if nav_config:
            hidden_nav_items = nav_config.hidden_nav_items

    return {"data": _user_response(
        current_user,
        company_name=company_name,
        hidden_nav_items=hidden_nav_items,
        needs_onboarding=needs_onboarding,
        company_plan=company_plan,
        demo_days_remaining=demo_days_remaining,
    )}


@router.get("/my-companies")
def list_my_companies(
    current_user: User = Depends(get_current_user),
    company_user_repo=Depends(get_company_user_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """List all active company memberships for the current user."""
    if current_user.role == UserRole.SUPER_ADMIN:
        return {"data": []}

    handler = ListUserCompaniesQueryHandler(
        company_user_repo=company_user_repo,
        company_repo=company_repo,
        user_repo=user_repo,
    )
    dtos = handler.handle(ListUserCompaniesQuery(user_id=current_user.id))
    return {"data": [
        UserCompanyResponse(
            company_id=d.company_id,
            company_name=d.company_name,
            slug=d.slug,
            role=d.role,
            is_current=d.is_current,
        ).model_dump()
        for d in dtos
    ]}


@router.post("/switch-company")
def switch_company(
    body: SwitchCompanyBody,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    company_user_repo=Depends(get_company_user_repo),
):
    """Switch the current user's active company."""
    handler = SwitchCompanyService(
        user_repo=user_repo,
        company_user_repo=company_user_repo,
        jwt_service=JWTService(),
    )
    try:
        access_token = handler.handle(SwitchCompanyInput(
            user_id=current_user.id,
            target_company_id=body.company_id,
        ))
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active membership found in target company",
        )
    except MembershipDeactivatedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your membership in this company is deactivated",
        )
    return {"data": {"access_token": access_token}}
