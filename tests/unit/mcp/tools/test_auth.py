"""Unit tests for MCP auth & API key tools."""
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip(
    "mcp", reason="mcp package required for MCP tool tests"
)

from adapters.mcp.tools.auth import (  # noqa: E402
    handle_create_api_key,
    handle_get_current_user,
    handle_list_api_keys,
    handle_revoke_api_key,
    handle_set_password,
)
from core.tenant import TenantContext  # noqa: E402
from src.auth_bc.user.application.commands.set_password import (  # noqa: E402,E501
    NotAdminError,
    WeakPasswordError,
)
from src.auth_bc.user.domain.entities import (  # noqa: E402
    User,
)
from src.auth_bc.user.domain.enums import (  # noqa: E402
    UserRole,
)
from src.mcp_bc.server.application.commands.create_api_key import (  # noqa: E402,E501
    MaxApiKeysReachedError,
)
from src.mcp_bc.server.application.commands.revoke_api_key import (  # noqa: E402,E501
    ApiKeyNotFoundError,
)
from src.mcp_bc.server.domain.entities import (  # noqa: E402
    ApiKey,
    ApiKeyAlreadyRevokedError,
)


def _make_tenant(**overrides) -> TenantContext:
    defaults = {
        "company_id": "company-1",
        "user_id": "user-1",
        "role": "employee",
    }
    defaults.update(overrides)
    return TenantContext(**defaults)


def _make_user(**overrides) -> User:
    defaults = {
        "id": "user-1",
        "email": "user@acme.com",
        "role": UserRole.ADMIN,
        "company_id": "company-1",
        "name": "Test User",
        "department_id": "dept-1",
        "is_active": True,
        "password_hash": None,
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "updated_at": datetime(2024, 1, 15, 10, 0, 0),
    }
    defaults.update(overrides)
    return User(**defaults)


def _make_api_key(**overrides) -> ApiKey:
    defaults = {
        "id": "key-1",
        "user_id": "user-1",
        "key_hash": "hashed",
        "name": "Claude Desktop",
        "created_at": datetime(2024, 1, 15, 10, 0, 0),
        "last_used_at": None,
        "is_active": True,
    }
    defaults.update(overrides)
    return ApiKey(**defaults)


def _parse_result(result):
    assert len(result) == 1
    return json.loads(result[0].text)


_P = "adapters.mcp.tools.auth"


@pytest.fixture
def mock_db():
    with patch(f"{_P}.SessionLocal") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def mock_tenant():
    tenant = _make_tenant()
    with patch(
        f"{_P}.get_tenant", return_value=tenant,
    ):
        yield tenant


class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_tenant,
    ):
        user = _make_user()

        with patch(
            f"{_P}.UserRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_by_id.return_value = user

            result = await handle_get_current_user({})

        data = _parse_result(result)
        assert data["id"] == "user-1"
        assert data["email"] == "user@acme.com"
        assert data["role"] == "admin"
        assert data["company_id"] == "company-1"
        assert data["department_id"] == "dept-1"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.UserRepository"
        ) as MockRepo:
            repo = MockRepo.return_value
            repo.find_by_id.return_value = None

            result = await handle_get_current_user({})

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"].lower()


class TestSetPassword:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.SetPasswordCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.PasswordService"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_set_password({
                "password": "secure_pass_123",
            })

        data = _parse_result(result)
        assert "message" in data
        assert "success" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_not_admin(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.SetPasswordCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.PasswordService"
        ):
            MockHandler.return_value.handle.side_effect = (
                NotAdminError(
                    "Only admins can set a password"
                )
            )

            result = await handle_set_password({
                "password": "secure_pass_123",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "admin" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_weak_password(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.SetPasswordCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.UserRepository"
        ), patch(
            f"{_P}.PasswordService"
        ):
            MockHandler.return_value.handle.side_effect = (
                WeakPasswordError(
                    "Password must be at least "
                    "8 characters"
                )
            )

            result = await handle_set_password({
                "password": "short",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "8 characters" in data["error"]


class TestCreateApiKey:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_tenant,
    ):
        api_key = _make_api_key()

        with patch(
            f"{_P}.CreateApiKeyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ) as MockRepo, patch(
            f"{_P}.generate_api_key"
        ) as mock_gen, patch(
            f"{_P}.ulid"
        ) as mock_ulid:
            mock_gen.return_value = (
                "dsm_abc123", "hashed",
            )
            mock_ulid.new.return_value = "key-1"
            MockHandler.return_value.handle.return_value = (
                None
            )
            MockRepo.return_value.find_by_id.return_value = (
                api_key
            )

            result = await handle_create_api_key({
                "name": "Claude Desktop",
            })

        data = _parse_result(result)
        assert data["id"] == "key-1"
        assert data["name"] == "Claude Desktop"
        assert data["raw_key"] == "dsm_abc123"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_max_keys_reached(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.CreateApiKeyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ), patch(
            f"{_P}.generate_api_key"
        ) as mock_gen, patch(
            f"{_P}.ulid"
        ) as mock_ulid:
            mock_gen.return_value = (
                "dsm_abc123", "hashed",
            )
            mock_ulid.new.return_value = "key-1"
            MockHandler.return_value.handle.side_effect = (
                MaxApiKeysReachedError(
                    "Maximum 10 active API keys"
                )
            )

            result = await handle_create_api_key({
                "name": "Claude Desktop",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "10" in data["error"]


class TestListApiKeys:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_tenant,
    ):
        keys = [
            _make_api_key(),
            _make_api_key(
                id="key-2",
                name="Cursor",
                is_active=False,
            ),
        ]

        with patch(
            f"{_P}.ListApiKeysQueryHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                keys
            )

            result = await handle_list_api_keys({})

        data = _parse_result(result)
        assert len(data) == 2
        assert data[0]["id"] == "key-1"
        assert data[0]["name"] == "Claude Desktop"
        assert data[0]["is_active"] is True
        assert data[1]["name"] == "Cursor"
        assert data[1]["is_active"] is False
        # No raw_key exposed
        assert "raw_key" not in data[0]
        assert "key_hash" not in data[0]


class TestRevokeApiKey:
    @pytest.mark.asyncio
    async def test_success(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.RevokeApiKeyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ):
            MockHandler.return_value.handle.return_value = (
                None
            )

            result = await handle_revoke_api_key({
                "key_id": "key-1",
            })

        data = _parse_result(result)
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_not_found(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.RevokeApiKeyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                ApiKeyNotFoundError(
                    "API key 'xyz' not found"
                )
            )

            result = await handle_revoke_api_key({
                "key_id": "xyz",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "not found" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_already_revoked(
        self, mock_db, mock_tenant,
    ):
        with patch(
            f"{_P}.RevokeApiKeyCommandHandler"
        ) as MockHandler, patch(
            f"{_P}.ApiKeyRepository"
        ):
            MockHandler.return_value.handle.side_effect = (
                ApiKeyAlreadyRevokedError(
                    "API key 'key-1' is already "
                    "revoked"
                )
            )

            result = await handle_revoke_api_key({
                "key_id": "key-1",
            })

        data = _parse_result(result)
        assert "error" in data
        assert "revoked" in data["error"].lower()
