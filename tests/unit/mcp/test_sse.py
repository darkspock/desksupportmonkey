"""Unit tests for MCP SSE transport and bearer auth."""
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tests"
)

from adapters.mcp.auth import (  # noqa: E402
    AuthenticationError,
    authenticate_bearer_token,
)
from src.auth_bc.user.domain.entities import (  # noqa: E402
    User,
)
from src.auth_bc.user.domain.enums import (  # noqa: E402
    UserRole,
)


def _make_user(**overrides) -> User:
    defaults = {
        "id": "user-1",
        "email": "user@acme.com",
        "role": UserRole.ADMIN,
        "company_id": "company-1",
        "name": "Test User",
        "department_id": None,
        "is_active": True,
        "password_hash": None,
        "created_at": None,
        "updated_at": None,
    }
    defaults.update(overrides)
    return User(**defaults)


_AUTH = "adapters.mcp.auth"


class TestAuthenticateBearerTokenApiKey:
    def test_api_key_delegates(self):
        """API key tokens (dsm_ prefix) delegate to
        authenticate_api_key."""
        user = _make_user()
        db = MagicMock()

        with patch(
            f"{_AUTH}.authenticate_api_key",
            return_value=user,
        ) as mock_auth:
            result = authenticate_bearer_token(
                "dsm_" + "a" * 40, db,
            )

        assert result.id == "user-1"
        mock_auth.assert_called_once_with(
            "dsm_" + "a" * 40, db,
        )


class TestAuthenticateBearerTokenJWT:
    def test_jwt_success(self):
        """JWT tokens resolve user and set tenant."""
        user = _make_user()
        db = MagicMock()

        with patch(
            f"{_AUTH}.JWTService"
        ) as MockJWT, patch(
            f"{_AUTH}.UserRepository"
        ) as MockUserRepo, patch(
            f"{_AUTH}.CompanyRepository"
        ) as MockCompanyRepo, patch(
            f"{_AUTH}.set_tenant"
        ):
            MockJWT.return_value.decode_token.return_value = {
                "sub": "user-1",
            }
            MockUserRepo.return_value.find_by_id.return_value = (
                user
            )
            MockCompanyRepo.return_value.find_by_id.return_value = (
                None
            )

            result = authenticate_bearer_token(
                "eyJhbGciOi.jwt.token", db,
            )

        assert result.id == "user-1"
        assert result.role == UserRole.ADMIN

    def test_jwt_invalid_token(self):
        """Invalid JWT raises AuthenticationError."""
        db = MagicMock()

        from core.jwt import InvalidTokenError

        with patch(
            f"{_AUTH}.JWTService"
        ) as MockJWT:
            MockJWT.return_value.decode_token.side_effect = (
                InvalidTokenError("Invalid token")
            )

            with pytest.raises(AuthenticationError):
                authenticate_bearer_token(
                    "bad.jwt.token", db,
                )

    def test_jwt_user_not_found(self):
        """JWT with unknown user raises error."""
        db = MagicMock()

        with patch(
            f"{_AUTH}.JWTService"
        ) as MockJWT, patch(
            f"{_AUTH}.UserRepository"
        ) as MockUserRepo:
            MockJWT.return_value.decode_token.return_value = {
                "sub": "nonexistent",
            }
            MockUserRepo.return_value.find_by_id.return_value = (
                None
            )

            with pytest.raises(AuthenticationError):
                authenticate_bearer_token(
                    "eyJhbGciOi.jwt.token", db,
                )


class TestCreateSseApp:
    def test_returns_starlette_app(self):
        """create_sse_app returns a Starlette app."""
        from adapters.mcp.sse import create_sse_app
        from starlette.applications import Starlette

        app = create_sse_app()
        assert isinstance(app, Starlette)

    def test_has_sse_and_messages_routes(self):
        """SSE app has /sse and /messages routes."""
        from adapters.mcp.sse import create_sse_app

        app = create_sse_app()
        paths = [r.path for r in app.routes]
        assert "/sse" in paths
        assert "/messages" in paths


class TestMcpMounting:
    def test_not_mounted_when_disabled(self):
        """MCP routes are not present when disabled."""
        with patch(
            "app.settings"
        ) as mock_settings:
            mock_settings.mcp.MCP_ENABLED = False
            mock_settings.SENTRY_DSN = ""
            mock_settings.cors_origins_list = [
                "http://localhost:5173",
            ]

            from app import create_app
            application = create_app()

        route_paths = [
            r.path for r in application.routes
            if hasattr(r, "path")
        ]
        assert "/mcp" not in route_paths

    def test_mounted_when_enabled(self):
        """MCP routes are present when enabled."""
        with patch(
            "app.settings"
        ) as mock_settings:
            mock_settings.mcp.MCP_ENABLED = True
            mock_settings.mcp.MCP_SSE_PATH = "/mcp"
            mock_settings.SENTRY_DSN = ""
            mock_settings.cors_origins_list = [
                "http://localhost:5173",
            ]

            from app import create_app
            application = create_app()

        route_paths = [
            r.path for r in application.routes
            if hasattr(r, "path")
        ]
        assert "/mcp" in route_paths
