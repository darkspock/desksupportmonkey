import logging
from dataclasses import dataclass

from core.jwt import JWTService
from src.auth_bc.magic_link.domain.repository import MagicLinkRepositoryInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface

logger = logging.getLogger(__name__)


class InvalidTokenError(Exception):
    pass


class ExpiredTokenError(Exception):
    pass


class UsedTokenError(Exception):
    pass


class CompanyRestrictedError(Exception):
    pass


@dataclass
class VerifyMagicLinkRequest:
    token: str


# Application service: returns str (JWT), not a CQRS command handler
class VerifyMagicLinkService:
    def __init__(
        self,
        magic_link_repo: MagicLinkRepositoryInterface,
        user_repo: UserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        jwt_service: JWTService,
    ):
        self.magic_link_repo = magic_link_repo
        self.user_repo = user_repo
        self.company_lookup = company_lookup
        self.jwt_service = jwt_service

    def handle(self, command: VerifyMagicLinkRequest) -> str:
        """Verify magic link and return JWT token."""
        magic_link = self.magic_link_repo.find_by_token(command.token)
        if magic_link is None:
            raise InvalidTokenError("Invalid link")

        if magic_link.is_used():
            raise UsedTokenError("Link already used")

        if magic_link.is_expired():
            raise ExpiredTokenError("Link expired")

        # Mark as used
        magic_link.mark_used()
        self.magic_link_repo.update_used_at(magic_link.id, magic_link.used_at)  # type: ignore[arg-type]

        # Find existing user or create via company lookup
        user = self.user_repo.find_by_email(magic_link.email)
        if user is None:
            # New user: must match a company domain
            result = self.company_lookup.find_company_by_email_domain(magic_link.email)
            if result is None:
                raise InvalidTokenError("Company not found for this email domain")
            company_id, is_active = result
            if not is_active:
                raise CompanyRestrictedError("Company access is currently restricted")
            user = User.create(
                email=magic_link.email,
                role=UserRole.EMPLOYEE,
                company_id=company_id,
            )
            self.user_repo.save(user)
            logger.info("Created new user %s with employee role", user.email)
        else:
            # Existing user: check their company is active via domain lookup
            result = self.company_lookup.find_company_by_email_domain(magic_link.email)
            if result is not None and not result[1]:
                raise CompanyRestrictedError("Company access is currently restricted")

        if not user.is_active:
            raise InvalidTokenError("User account is deactivated")

        # Generate JWT
        token = self.jwt_service.create_token(
            user_id=user.id,
            company_id=user.company_id,
            role=user.role.value,
        )
        logger.info("Magic link verified for %s", user.email)
        return token
