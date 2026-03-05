from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from core.jwt import JWTService
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.domain.exceptions import OAuthProviderAlreadyLinkedError
from src.auth_bc.user.domain.repository import UserRepositoryInterface

if TYPE_CHECKING:
    from src.auth_bc.company_user.domain.service import MembershipAuthService
    from src.company_bc.company.domain.repository import CompanyRepositoryInterface


class CompanyRestrictedError(Exception):
    pass


class InvalidEmailDomainError(Exception):
    pass


class UserDeactivatedError(Exception):
    pass


@dataclass
class OAuthUserInfo:
    email: str
    name: Optional[str]
    provider_id: str       # Google sub or Microsoft oid
    provider_field: str    # "google_id" or "microsoft_id"


class OAuthLoginService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        jwt_service: JWTService,
        membership_auth: Optional["MembershipAuthService"] = None,
        company_repo: Optional["CompanyRepositoryInterface"] = None,
    ):
        self.user_repo = user_repo
        self.company_lookup = company_lookup
        self.jwt_service = jwt_service
        self.membership_auth = membership_auth
        self.company_repo = company_repo

    def login_or_create(
        self, info: OAuthUserInfo, company_id: Optional[str] = None
    ) -> str:
        """Verify OAuth user info, find or create user, return JWT access_token."""
        # 1. Find by provider ID
        user = self._find_by_provider(info.provider_field, info.provider_id)

        # 2. Fallback: find by email
        if user is None:
            user = self.user_repo.find_by_email(info.email)

        # 3. Existing user checks + link provider
        if user is not None:
            if not user.is_active:
                raise UserDeactivatedError("User account is deactivated")

            if user.company_id:
                result = self.company_lookup.find_company_by_email_domain(info.email)
                if result is not None and not result[1]:
                    raise CompanyRestrictedError("Company access is currently restricted")

            self._link_provider(user, info)
            if info.name:
                user.name = info.name
            if user.email_verified_at is None:
                user.email_verified_at = datetime.now(timezone.utc)
            self.user_repo.save(user)

            # Scoped auth: resolve membership
            if (
                company_id is not None
                and self.membership_auth is not None
                and self.company_repo is not None
            ):
                company = self.company_repo.find_by_id(company_id)
                if company is not None:
                    auth_mode = company.auth_mode.value if hasattr(company.auth_mode, 'value') else str(company.auth_mode)
                    user = self.membership_auth.resolve_membership(
                        user, company_id, auth_mode
                    )

            return self.jwt_service.create_token(user.id, user.company_id, user.role.value)

        # 4. Auto-create new user
        result = self.company_lookup.find_company_by_email_domain(info.email)
        if result is None:
            raise InvalidEmailDomainError("Only corporate email addresses are allowed")
        resolved_company_id, is_active = result
        if not is_active:
            raise CompanyRestrictedError("Company access is currently restricted")

        new_user = User.create(
            email=info.email,
            role=UserRole.EMPLOYEE,
            company_id=resolved_company_id,
            name=info.name,
        )
        self._link_provider(new_user, info)
        new_user.email_verified_at = datetime.now(timezone.utc)
        self.user_repo.save(new_user)

        # Scoped auth: resolve membership for new user
        if (
            company_id is not None
            and self.membership_auth is not None
            and self.company_repo is not None
        ):
            company = self.company_repo.find_by_id(company_id)
            if company is not None:
                auth_mode = company.auth_mode.value if hasattr(company.auth_mode, 'value') else str(company.auth_mode)
                new_user = self.membership_auth.resolve_membership(
                    new_user, company_id, auth_mode
                )

        return self.jwt_service.create_token(new_user.id, new_user.company_id, new_user.role.value)

    def _find_by_provider(self, provider_field: str, provider_id: str) -> Optional[User]:
        if provider_field == "google_id":
            return self.user_repo.find_by_google_id(provider_id)
        if provider_field == "microsoft_id":
            return self.user_repo.find_by_microsoft_id(provider_id)
        return None

    def _link_provider(self, user: User, info: OAuthUserInfo) -> None:
        current = getattr(user, info.provider_field)
        if current is not None and current != info.provider_id:
            raise OAuthProviderAlreadyLinkedError(info.provider_field)
        if current is None:
            if info.provider_field == "google_id":
                user.link_google(info.provider_id)
            elif info.provider_field == "microsoft_id":
                user.link_microsoft(info.provider_id)
