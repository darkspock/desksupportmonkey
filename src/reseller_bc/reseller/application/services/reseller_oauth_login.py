from dataclasses import dataclass
from typing import Optional

from core.jwt import JWTService
from src.reseller_bc.reseller.domain.enums import ResellerStatus
from src.reseller_bc.reseller.domain.exceptions import (
    ResellerDeactivatedException,
    ResellerNotRegisteredException,
    ResellerPendingApprovalException,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


@dataclass
class OAuthUserInfo:
    email: str
    name: Optional[str]
    provider_id: str
    provider_field: str  # "google_id" or "microsoft_id"
    avatar_url: Optional[str] = None


class ResellerOAuthLoginService:
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        jwt_service: JWTService,
    ):
        self.repo = repo
        self.jwt_service = jwt_service

    def login(self, info: OAuthUserInfo) -> str:
        """Find reseller by OAuth provider or email, link provider, return JWT."""
        # 1. Find by provider ID
        reseller = self._find_by_provider(info.provider_field, info.provider_id)

        # 2. Fallback: find by email
        if reseller is None:
            reseller = self.repo.find_by_email(info.email)

        # 3. Not found — resellers must be pre-created by super admin
        if reseller is None:
            raise ResellerNotRegisteredException(info.email)

        # 4. Check status
        if reseller.status == ResellerStatus.PENDING:
            raise ResellerPendingApprovalException()
        if reseller.status == ResellerStatus.DEACTIVATED:
            raise ResellerDeactivatedException(reseller.id)

        # 5. Link provider if not yet linked
        if info.provider_field == "google_id":
            reseller.link_google(info.provider_id)
        elif info.provider_field == "microsoft_id":
            reseller.link_microsoft(info.provider_id)

        # 6. Update avatar if provided
        if info.avatar_url:
            reseller.avatar_url = info.avatar_url

        # 7. Update name if provided and not set
        if info.name and not reseller.name:
            reseller.name = info.name

        self.repo.save(reseller)

        # 8. Issue JWT with type=reseller
        return self.jwt_service.create_token(
            user_id=reseller.id,
            company_id=None,
            role="reseller",
            type="reseller",
        )

    def _find_by_provider(self, provider_field: str, provider_id: str):
        if provider_field == "google_id":
            return self.repo.find_by_google_id(provider_id)
        if provider_field == "microsoft_id":
            return self.repo.find_by_microsoft_id(provider_id)
        return None
