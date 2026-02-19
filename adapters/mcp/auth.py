"""API key and JWT authentication for MCP server."""
import logging

from sqlalchemy.orm import Session

from core.jwt import JWTService, ExpiredTokenError, InvalidTokenError
from core.password import PasswordService
from core.tenant import set_tenant
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.domain.enums import CompanyStatus
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.mcp_bc.server.infrastructure.repository import ApiKeyRepository

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when API key authentication fails."""
    pass


def authenticate_api_key(raw_key: str, db: Session) -> User:
    """Authenticate an API key and return the associated user.

    Steps:
    1. Validate key format (dsm_<40 hex chars>)
    2. Iterate through active API keys and verify with bcrypt
    3. Resolve user from api_key.user_id
    4. Check user is active
    5. Check company is active (if applicable)
    6. Set tenant context (set_tenant)
    7. Update last_used_at
    8. Return user

    Raises:
        AuthenticationError: If key is invalid, user inactive,
            or company restricted
    """
    if not raw_key.startswith("dsm_") or len(raw_key) != 44:
        raise AuthenticationError("Invalid API key format")

    api_key_repo = ApiKeyRepository(db)
    active_keys = api_key_repo.find_all_active()

    for api_key in active_keys:
        if PasswordService.verify_password(raw_key, api_key.key_hash):
            logger.info("API key authenticated: key_id=%s", api_key.id)

            user_repo = UserRepository(db)
            user = user_repo.find_by_id(api_key.user_id)

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            if user.company_id:
                company_repo = CompanyRepository(db)
                company = company_repo.find_by_id(user.company_id)
                if company and company.status != CompanyStatus.ACTIVE:
                    raise AuthenticationError(
                        "Company access is currently restricted"
                    )

            set_tenant(
                company_id=user.company_id,
                user_id=user.id,
                role=user.role.value,
            )

            api_key_repo.update_last_used(api_key.id)

            logger.info(
                "User authenticated: user_id=%s, role=%s, company_id=%s",
                user.id,
                user.role.value,
                user.company_id,
            )

            return user

    raise AuthenticationError("Invalid API key")


def authenticate_bearer_token(
    token: str, db: Session,
) -> User:
    """Authenticate a Bearer token (API key or JWT).

    API keys start with 'dsm_' and are verified via bcrypt.
    Everything else is treated as a JWT.

    Raises:
        AuthenticationError: If token is invalid.
    """
    if token.startswith("dsm_"):
        return authenticate_api_key(token, db)

    # JWT path
    try:
        payload = JWTService().decode_token(token)
    except (ExpiredTokenError, InvalidTokenError) as e:
        raise AuthenticationError(str(e))

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token")

    user_repo = UserRepository(db)
    user = user_repo.find_by_id(user_id)

    if not user or not user.is_active:
        raise AuthenticationError(
            "User not found or inactive"
        )

    if user.company_id:
        company_repo = CompanyRepository(db)
        company = company_repo.find_by_id(
            user.company_id,
        )
        if company and company.status != CompanyStatus.ACTIVE:
            raise AuthenticationError(
                "Company access is currently restricted"
            )

    set_tenant(
        company_id=user.company_id,
        user_id=user.id,
        role=user.role.value,
    )

    logger.info(
        "JWT authenticated: user_id=%s, role=%s",
        user.id,
        user.role.value,
    )

    return user
