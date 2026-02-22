from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_deps
from app import app
from core.database import get_db
from core.jwt import JWTService
from src.auth_bc.user.application.commands.google_oauth_login import (
    CompanyRestrictedError,
    GoogleEmailNotVerified,
    GoogleNotConfiguredError,
    GoogleOAuthLoginService,
    GoogleTokenInvalidError,
    InvalidEmailDomainError,
    UserDeactivatedError,
)
from src.auth_bc.user.domain.exceptions import OAuthProviderAlreadyLinkedError


@pytest.fixture(autouse=True)
def clean_overrides():
    yield
    app.dependency_overrides.clear()


def _client_with_service(mock_service):
    mock_user = MagicMock()
    mock_user.company_id = None
    mock_user_repo = MagicMock()
    mock_user_repo.find_by_id.return_value = mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[auth_deps.get_user_repo] = lambda: mock_user_repo
    app.dependency_overrides[auth_deps.get_google_oauth_login_service] = lambda: mock_service
    return TestClient(app)


class TestGoogleOAuthEndpoint:
    def test_success_returns_token(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        real_token = JWTService().create_token("user-id", None, "admin")
        mock_service.handle.return_value = real_token
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "valid_google_token"})

        assert resp.status_code == 200
        assert resp.json()["data"]["access_token"] == real_token

    def test_not_configured_returns_501(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = GoogleNotConfiguredError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "any"})

        assert resp.status_code == 501

    def test_invalid_token_returns_401(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = GoogleTokenInvalidError("bad token")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "bad"})

        assert resp.status_code == 401

    def test_unverified_email_returns_401(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = GoogleEmailNotVerified("not verified")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "token"})

        assert resp.status_code == 401

    def test_deactivated_user_returns_403(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = UserDeactivatedError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "token"})

        assert resp.status_code == 403

    def test_restricted_company_returns_403(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = CompanyRestrictedError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "token"})

        assert resp.status_code == 403

    def test_invalid_domain_returns_403(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = InvalidEmailDomainError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "token"})

        assert resp.status_code == 403

    def test_provider_already_linked_returns_409(self):
        mock_service = MagicMock(spec=GoogleOAuthLoginService)
        mock_service.handle.side_effect = OAuthProviderAlreadyLinkedError("google_id")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/google", json={"id_token": "token"})

        assert resp.status_code == 409
