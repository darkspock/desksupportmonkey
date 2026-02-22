from unittest.mock import MagicMock, patch

import pytest

from src.auth_bc.user.application.commands.google_oauth_login import (
    GoogleEmailNotVerified,
    GoogleNotConfiguredError,
    GoogleOAuthLoginRequest,
    GoogleOAuthLoginService,
    GoogleTokenInvalidError,
)
from src.auth_bc.user.application.services.google_token_verifier import (
    GoogleEmailNotVerifiedError,
    GoogleTokenVerificationError,
    GoogleUserInfo,
)
from src.auth_bc.user.application.services.oauth_login_service import (
    CompanyRestrictedError,
    InvalidEmailDomainError,
    UserDeactivatedError,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_settings(google_client_id="google-client-id"):
    settings = MagicMock()
    settings.GOOGLE_CLIENT_ID = google_client_id
    return settings


def _make_service(user_repo=None, company_lookup=None, jwt_service=None, google_client_id="google-client-id"):
    if user_repo is None:
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = None
        user_repo.find_by_email.return_value = None
    if company_lookup is None:
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", True)
    if jwt_service is None:
        jwt_service = MagicMock()
        jwt_service.create_token.return_value = "jwt_token"
    return GoogleOAuthLoginService(
        user_repo=user_repo,
        company_lookup=company_lookup,
        jwt_service=jwt_service,
        oauth_settings=_make_settings(google_client_id),
    )


def _valid_google_user_info():
    return GoogleUserInfo(
        sub="google_sub_123",
        email="employee@company.com",
        name="Jane Doe",
        email_verified=True,
    )


class TestGoogleOAuthLoginServiceNotConfigured:
    def test_raises_when_google_client_id_empty(self):
        service = _make_service(google_client_id="")
        with pytest.raises(GoogleNotConfiguredError):
            service.handle(GoogleOAuthLoginRequest(id_token="any"))


class TestGoogleOAuthLoginServiceTokenVerification:
    def test_raises_google_token_invalid_on_verification_error(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            side_effect=GoogleTokenVerificationError("bad token"),
        ):
            with pytest.raises(GoogleTokenInvalidError):
                service.handle(GoogleOAuthLoginRequest(id_token="bad"))

    def test_raises_google_email_not_verified_on_unverified_email(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            side_effect=GoogleEmailNotVerifiedError("not verified"),
        ):
            with pytest.raises(GoogleEmailNotVerified):
                service.handle(GoogleOAuthLoginRequest(id_token="token"))


class TestGoogleOAuthLoginServiceSuccess:
    def test_returns_jwt_for_new_user(self):
        service = _make_service()
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            token = service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))
        assert token == "jwt_token"

    def test_returns_jwt_for_existing_user_by_google_id(self):
        existing_user = User.create(
            email="employee@company.com", role=UserRole.EMPLOYEE, company_id="comp1"
        )
        existing_user.link_google("google_sub_123")
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = existing_user
        service = _make_service(user_repo=user_repo)
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            token = service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))
        assert token == "jwt_token"

    def test_returns_jwt_for_existing_user_found_by_email(self):
        existing_user = User.create(
            email="employee@company.com", role=UserRole.EMPLOYEE, company_id="comp1"
        )
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = None
        user_repo.find_by_email.return_value = existing_user
        service = _make_service(user_repo=user_repo)
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            token = service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))
        assert token == "jwt_token"


class TestGoogleOAuthLoginServiceErrors:
    def test_deactivated_user_raises_forbidden(self):
        user = User.create(
            email="employee@company.com", role=UserRole.EMPLOYEE, company_id="comp1"
        )
        user.deactivate()
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = None
        user_repo.find_by_email.return_value = user
        service = _make_service(user_repo=user_repo)
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            with pytest.raises(UserDeactivatedError):
                service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))

    def test_invalid_domain_raises_error(self):
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = None
        user_repo.find_by_email.return_value = None
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = None
        service = _make_service(user_repo=user_repo, company_lookup=company_lookup)
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            with pytest.raises(InvalidEmailDomainError):
                service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))

    def test_restricted_company_raises_error(self):
        user_repo = MagicMock()
        user_repo.find_by_google_id.return_value = None
        user_repo.find_by_email.return_value = None
        company_lookup = MagicMock()
        company_lookup.find_company_by_email_domain.return_value = ("comp1", False)
        service = _make_service(user_repo=user_repo, company_lookup=company_lookup)
        with patch(
            "src.auth_bc.user.application.commands.google_oauth_login.GoogleTokenVerifier.verify",
            return_value=_valid_google_user_info(),
        ):
            with pytest.raises(CompanyRestrictedError):
                service.handle(GoogleOAuthLoginRequest(id_token="valid_token"))
