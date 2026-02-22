import logging
from dataclasses import dataclass

from core.config import OAuthSettings
from src.auth_bc.company_lookup.domain.service import CompanyLookupInterface
from src.auth_bc.user.application.services.microsoft_token_verifier import (
    MicrosoftMissingEmailError,
    MicrosoftTokenVerificationError,
    MicrosoftTokenVerifier,
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


class MicrosoftNotConfiguredError(Exception):
    pass


class MicrosoftTokenInvalidError(Exception):
    pass


class MicrosoftMissingEmail(Exception):
    pass


@dataclass
class MicrosoftOAuthLoginRequest:
    id_token: str


class MicrosoftOAuthLoginService:
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

    def handle(self, request: MicrosoftOAuthLoginRequest) -> str:
        if not self._oauth_settings.MICROSOFT_CLIENT_ID:
            raise MicrosoftNotConfiguredError("Microsoft OAuth is not configured")

        verifier = MicrosoftTokenVerifier(
            client_id=self._oauth_settings.MICROSOFT_CLIENT_ID,
            tenant_id=self._oauth_settings.MICROSOFT_TENANT_ID or "common",
        )
        try:
            user_info = verifier.verify(request.id_token)
        except MicrosoftMissingEmailError as exc:
            raise MicrosoftMissingEmail(str(exc)) from exc
        except MicrosoftTokenVerificationError as exc:
            raise MicrosoftTokenInvalidError(str(exc)) from exc

        service = OAuthLoginService(
            user_repo=self._user_repo,
            company_lookup=self._company_lookup,
            jwt_service=self._jwt_service,
        )
        info = OAuthUserInfo(
            email=user_info.email,
            name=user_info.name,
            provider_id=user_info.oid,
            provider_field="microsoft_id",
        )
        return service.login_or_create(info)
