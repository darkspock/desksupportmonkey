from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_deps
from app import app
from core.database import get_db
from src.auth_bc.user.application.commands.microsoft_oauth_login import (
    CompanyRestrictedError,
    InvalidEmailDomainError,
    MicrosoftMissingEmail,
    MicrosoftNotConfiguredError,
    MicrosoftOAuthLoginService,
    MicrosoftTokenInvalidError,
    UserDeactivatedError,
)
from src.auth_bc.user.domain.exceptions import OAuthProviderAlreadyLinkedError


@pytest.fixture(autouse=True)
def clean_overrides():
    yield
    app.dependency_overrides.clear()


def _client_with_service(mock_service):
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[auth_deps.get_microsoft_oauth_login_service] = lambda: mock_service
    return TestClient(app)


class TestMicrosoftOAuthEndpoint:
    def test_success_returns_token(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.return_value = "jwt_token_here"
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "valid_ms_token"})

        assert resp.status_code == 200
        assert resp.json()["data"]["access_token"] == "jwt_token_here"

    def test_not_configured_returns_501(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.side_effect = MicrosoftNotConfiguredError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "any"})

        assert resp.status_code == 501

    def test_invalid_token_returns_401(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.side_effect = MicrosoftTokenInvalidError("bad token")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "bad"})

        assert resp.status_code == 401

    def test_missing_email_returns_401(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.side_effect = MicrosoftMissingEmail("no email")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "token"})

        assert resp.status_code == 401

    def test_deactivated_user_returns_403(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.side_effect = UserDeactivatedError()
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "token"})

        assert resp.status_code == 403

    def test_provider_already_linked_returns_409(self):
        mock_service = MagicMock(spec=MicrosoftOAuthLoginService)
        mock_service.handle.side_effect = OAuthProviderAlreadyLinkedError("microsoft_id")
        client = _client_with_service(mock_service)

        resp = client.post("/api/v1/auth/oauth/microsoft", json={"id_token": "token"})

        assert resp.status_code == 409
