import logging
from dataclasses import dataclass
from typing import Optional

from core.jwt import JWTService
from core.password import PasswordService
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.repository import UserRepositoryInterface

logger = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    pass


class AccountInactiveError(Exception):
    pass


@dataclass
class PasswordLoginRequest:
    email: str
    password: str
    company_id: Optional[str] = None


# Application service: returns str (JWT), not a CQRS command handler
class PasswordLoginService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        jwt_service: JWTService,
        password_service: PasswordService,
    ):
        self.user_repo = user_repo
        self.company_lookup = company_lookup
        self.jwt_service = jwt_service
        self.password_service = password_service

    def handle(self, command: PasswordLoginRequest) -> str:
        user = self.user_repo.find_by_email(command.email)
        if user is None:
            raise InvalidCredentialsError("Invalid credentials")

        if user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
            raise InvalidCredentialsError("Invalid credentials")

        if user.password_hash is None:
            raise InvalidCredentialsError("Invalid credentials")

        if not self.password_service.verify_password(command.password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")

        if not user.is_active:
            raise AccountInactiveError("Account is inactive")

        # Super admins have no company — skip company check
        if user.role != UserRole.SUPER_ADMIN:
            result = self.company_lookup.find_company_by_email_domain(user.email)
            if result is None:
                raise InvalidCredentialsError("Invalid credentials")
            company_id, is_active = result
            if not is_active:
                raise AccountInactiveError("Account is inactive")

        token = self.jwt_service.create_token(
            user_id=user.id,
            company_id=user.company_id,
            role=user.role.value,
        )
        logger.info("Password login for %s", user.email)
        return token
