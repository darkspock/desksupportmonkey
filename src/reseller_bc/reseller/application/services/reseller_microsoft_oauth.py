import logging
from dataclasses import dataclass

from core.config import OAuthSettings
from core.jwt import JWTService
from src.auth_bc.user.application.services.microsoft_token_verifier import (
    MicrosoftMissingEmailError,
    MicrosoftTokenVerificationError,
    MicrosoftTokenVerifier,
)
from src.reseller_bc.reseller.application.services.reseller_oauth_login import (
    OAuthUserInfo,
    ResellerOAuthLoginService,
)
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface

logger = logging.getLogger(__name__)


class ResellerMicrosoftNotConfiguredError(Exception):
    pass


class ResellerMicrosoftTokenInvalidError(Exception):
    pass


class ResellerMicrosoftMissingEmail(Exception):
    pass


@dataclass
class MicrosoftOAuthLoginRequest:
    id_token: str


class ResellerMicrosoftOAuthService:
    def __init__(
        self,
        repo: ResellerRepositoryInterface,
        jwt_service: JWTService,
        oauth_settings: OAuthSettings,
    ):
        self._repo = repo
        self._jwt_service = jwt_service
        self._oauth_settings = oauth_settings

    def handle(self, request: MicrosoftOAuthLoginRequest) -> str:
        if not self._oauth_settings.MICROSOFT_CLIENT_ID:
            raise ResellerMicrosoftNotConfiguredError("Microsoft OAuth is not configured")

        verifier = MicrosoftTokenVerifier(
            client_id=self._oauth_settings.MICROSOFT_CLIENT_ID,
            tenant_id=self._oauth_settings.MICROSOFT_TENANT_ID or "common",
        )
        try:
            user_info = verifier.verify(request.id_token)
        except MicrosoftMissingEmailError as exc:
            raise ResellerMicrosoftMissingEmail(str(exc)) from exc
        except MicrosoftTokenVerificationError as exc:
            raise ResellerMicrosoftTokenInvalidError(str(exc)) from exc

        service = ResellerOAuthLoginService(
            repo=self._repo,
            jwt_service=self._jwt_service,
        )
        info = OAuthUserInfo(
            email=user_info.email,
            name=user_info.name,
            provider_id=user_info.oid,
            provider_field="microsoft_id",
        )
        return service.login(info)
