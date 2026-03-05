import logging
from dataclasses import dataclass
from typing import Optional

from core.config import OAuthSettings
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.user.application.services.google_token_verifier import (
    GoogleEmailNotVerifiedError,
    GoogleTokenVerificationError,
    GoogleTokenVerifier,
)
from src.auth_bc.user.application.services.oauth_login_service import (
    CompanyRestrictedError,
    InvalidEmailDomainError,
    OAuthLoginService,
    OAuthUserInfo,
    UserDeactivatedError,
)
from src.auth_bc.user.domain.exceptions import OAuthProviderAlreadyLinkedError
from src.auth_bc.user.domain.repository import UserRepositoryInterface
from core.jwt import JWTService

logger = logging.getLogger(__name__)


class GoogleNotConfiguredError(Exception):
    pass


class GoogleTokenInvalidError(Exception):
    pass


class GoogleEmailNotVerified(Exception):
    pass


@dataclass
class GoogleOAuthLoginRequest:
    id_token: str
    company_id: Optional[str] = None


class GoogleOAuthLoginService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        jwt_service: JWTService,
        oauth_settings: OAuthSettings,
    ):
        self._user_repo = user_repo
        self._company_lookup = company_lookup
        self._jwt_service = jwt_service
        self._oauth_settings = oauth_settings

    def handle(self, request: GoogleOAuthLoginRequest) -> str:
        if not self._oauth_settings.GOOGLE_CLIENT_ID:
            raise GoogleNotConfiguredError("Google OAuth is not configured")

        verifier = GoogleTokenVerifier(self._oauth_settings.GOOGLE_CLIENT_ID)
        try:
            user_info = verifier.verify(request.id_token)
        except GoogleEmailNotVerifiedError as exc:
            raise GoogleEmailNotVerified(str(exc)) from exc
        except GoogleTokenVerificationError as exc:
            raise GoogleTokenInvalidError(str(exc)) from exc

        service = OAuthLoginService(
            user_repo=self._user_repo,
            company_lookup=self._company_lookup,
            jwt_service=self._jwt_service,
        )
        info = OAuthUserInfo(
            email=user_info.email,
            name=user_info.name,
            provider_id=user_info.sub,
            provider_field="google_id",
        )
        return service.login_or_create(info, company_id=request.company_id)
