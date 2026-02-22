from unittest.mock import MagicMock, patch

import pytest

from src.auth_bc.user.application.commands.microsoft_oauth_login import (
    MicrosoftMissingEmail,
    MicrosoftNotConfiguredError,
    MicrosoftOAuthLoginRequest,
    MicrosoftOAuthLoginService,
    MicrosoftTokenInvalidError,
)
from src.auth_bc.user.application.services.microsoft_token_verifier import (
    MicrosoftMissingEmailError,
    MicrosoftTokenVerificationError,
    MicrosoftUserInfo,
)
from src.auth_bc.user.application.services.oauth_login_service import (
    CompanyRestrictedError,
    InvalidEmailDomainError,
    UserDeactivatedError,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_settings(microsoft_client_id="ms-client-id", tenant_id="common"):
    settings = MagicMock()
    settings.MICROSOFT_CLIENT_ID = microsoft_client_id
    settings.MICROSOFT_TENANT_ID = tenant_id
    return settings


def _make_service(user_repo=None, company_lookup=None, jwt_service=None, microsoft_client_id="ms-client-id"):
    if user_repo is None:
        user_repo = MagicMock()
        user_repo.find_by_microsoft_id.return_value = None
        user_repo.find_by_email.return_value = None
    if company_lookup is None:
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", True)
    if jwt_service is None:
        jwt_service = MagicMock()
        jwt_service.create_token.return_value = "jwt_token"
    return MicrosoftOAuthLoginService(
        user_repo=user_repo,
        company_lookup=company_lookup,
        jwt_service=jwt_service,
        oauth_settings=_make_settings(microsoft_client_id),
    )


def _valid_ms_user_info():
    return MicrosoftUserInfo(
        oid="ms_oid_123",
        email="employee@company.com",
        name="Jane Doe",
    )


class TestMicrosoftOAuthLoginServiceNotConfigured:
    def test_raises_when_microsoft_client_id_empty(self):
        service = _make_service(microsoft_client_id="")
        with pytest.raises(MicrosoftNotConfiguredError):
            service.handle(MicrosoftOAuthLoginRequest(id_token="any"))


class TestMicrosoftOAuthLoginServiceTokenVerification:
    def test_raises_token_invalid_on_verification_error(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            side_effect=MicrosoftTokenVerificationError("bad token"),
        ):
            with pytest.raises(MicrosoftTokenInvalidError):
                service.handle(MicrosoftOAuthLoginRequest(id_token="bad"))

    def test_raises_missing_email_on_missing_email_error(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            side_effect=MicrosoftMissingEmailError("no email"),
        ):
            with pytest.raises(MicrosoftMissingEmail):
                service.handle(MicrosoftOAuthLoginRequest(id_token="token"))


class TestMicrosoftOAuthLoginServiceSuccess:
    def test_returns_jwt_for_new_user(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            return_value=_valid_ms_user_info(),
        ):
            token = service.handle(MicrosoftOAuthLoginRequest(id_token="valid_token"))
        assert token == "jwt_token"

    def test_returns_jwt_for_existing_user_by_microsoft_id(self):
        existing_user = User.create(
            email="employee@company.com", role=UserRole.EMPLOYEE, company_id="comp1"
        )
        existing_user.link_microsoft("ms_oid_123")
        user_repo = MagicMock()
        user_repo.find_by_microsoft_id.return_value = existing_user
        service = _make_service(user_repo=user_repo)
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            return_value=_valid_ms_user_info(),
        ):
            token = service.handle(MicrosoftOAuthLoginRequest(id_token="valid_token"))
        assert token == "jwt_token"


class TestMicrosoftOAuthLoginServiceErrors:
    def test_deactivated_user_raises_error(self):
        user = User.create(
            email="employee@company.com", role=UserRole.EMPLOYEE, company_id="comp1"
        )
        user.deactivate()
        user_repo = MagicMock()
        user_repo.find_by_microsoft_id.return_value = None
        user_repo.find_by_email.return_value = user
        service = _make_service(user_repo=user_repo)
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            return_value=_valid_ms_user_info(),
        ):
            with pytest.raises(UserDeactivatedError):
                service.handle(MicrosoftOAuthLoginRequest(id_token="valid_token"))

    def test_invalid_domain_raises_error(self):
        user_repo = MagicMock()
        user_repo.find_by_microsoft_id.return_value = None
        user_repo.find_by_email.return_value = None
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = None
        service = _make_service(user_repo=user_repo, company_lookup=company_lookup)
        with patch(
            "src.auth_bc.user.application.commands.microsoft_oauth_login.MicrosoftTokenVerifier.verify",
            return_value=_valid_ms_user_info(),
        ):
            with pytest.raises(InvalidEmailDomainError):
                service.handle(MicrosoftOAuthLoginRequest(id_token="valid_token"))
