import logging
from dataclasses import dataclass

from core.config import OAuthSettings
from core.jwt import JWTService
from src.auth_bc.user.application.services.google_token_verifier import (
    GoogleEmailNotVerifiedError,
    GoogleTokenVerificationError,
    GoogleTokenVerifier,
)
from src.reseller_bc.reseller.application.services.reseller_oauth_login import (
    OAuthUserInfo,
    ResellerOAuthLoginService,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface

logger = logging.getLogger(__name__)


class ResellerGoogleNotConfiguredError(Exception):
    pass


class ResellerGoogleTokenInvalidError(Exception):
    pass


class ResellerGoogleEmailNotVerified(Exception):
    pass


@dataclass
class GoogleOAuthLoginRequest:
    id_token: str


class ResellerGoogleOAuthService:
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        jwt_service: JWTService,
        oauth_settings: OAuthSettings,
    ):
        self._repo = repo
        self._jwt_service = jwt_service
        self._oauth_settings = oauth_settings

    def handle(self, request: GoogleOAuthLoginRequest) -> str:
        if not self._oauth_settings.GOOGLE_CLIENT_ID:
            raise ResellerGoogleNotConfiguredError("Google OAuth is not configured")

        verifier = GoogleTokenVerifier(self._oauth_settings.GOOGLE_CLIENT_ID)
        try:
            user_info = verifier.verify(request.id_token)
        except GoogleEmailNotVerifiedError as exc:
            raise ResellerGoogleEmailNotVerified(str(exc)) from exc
        except GoogleTokenVerificationError as exc:
            raise ResellerGoogleTokenInvalidError(str(exc)) from exc

        service = ResellerOAuthLoginService(
            repo=self._repo,
            jwt_service=self._jwt_service,
        )
        info = OAuthUserInfo(
            email=user_info.email,
            name=user_info.name,
            provider_id=user_info.sub,
            provider_field="google_id",
        )
        return service.login(info)
