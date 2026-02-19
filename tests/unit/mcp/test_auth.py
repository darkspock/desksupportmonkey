from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from adapters.mcp.auth import AuthenticationError, authenticate_api_key
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus
from src.mcp_bc.server.domain.entities import ApiKey


def _make_user(
    user_id: str = "user123",
    role: UserRole = UserRole.ADMIN,
    company_id: str = "company123",
    is_active: bool = True,
) -> User:
    return User(
        id=user_id,
        email="admin@test.com",
        role=role,
        company_id=company_id,
        name="Test User",
        is_active=is_active,
    )


def _make_api_key(
    key_id: str = "key123",
    user_id: str = "user123",
    key_hash: str = "hashed_key",
    is_active: bool = True,
) -> ApiKey:
    return ApiKey(
        id=key_id,
        user_id=user_id,
        key_hash=key_hash,
        name="Test Key",
        created_at=datetime(2025, 1, 1),
        is_active=is_active,
    )


def _make_company(
    company_id: str = "company123",
    status: CompanyStatus = CompanyStatus.ACTIVE,
) -> Company:
    return Company(
        id=company_id,
        name="Test Company",
        status=status,
        email_domains=["test.com"],
    )


# Valid raw key format: dsm_ + 40 hex chars = 44 total
VALID_RAW_KEY = "dsm_" + "a" * 40


class TestAuthenticateApiKey:
    @patch("adapters.mcp.auth.CompanyRepository")
    @patch("adapters.mcp.auth.UserRepository")
    @patch("adapters.mcp.auth.ApiKeyRepository")
    @patch("adapters.mcp.auth.PasswordService")
    def test_authenticate_valid_key(
        self, mock_pw, mock_api_repo_cls,
        mock_user_repo_cls, mock_company_repo_cls,
    ):
        api_key = _make_api_key()
        user = _make_user()
        company = _make_company()

        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = [api_key]
        mock_api_repo_cls.return_value = mock_api_repo

        mock_pw.verify_password.return_value = True

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo_cls.return_value = mock_user_repo

        mock_company_repo = MagicMock()
        mock_company_repo.find_by_id.return_value = company
        mock_company_repo_cls.return_value = mock_company_repo

        db = MagicMock()
        result = authenticate_api_key(VALID_RAW_KEY, db)

        assert result.id == "user123"
        assert result.role == UserRole.ADMIN
        mock_api_repo.update_last_used.assert_called_once_with("key123")

    def test_authenticate_invalid_format_no_prefix(self):
        db = MagicMock()
        with pytest.raises(
            AuthenticationError, match="Invalid API key format"
        ):
            authenticate_api_key("invalid_key_no_prefix", db)

    def test_authenticate_invalid_format_wrong_length(self):
        db = MagicMock()
        with pytest.raises(
            AuthenticationError, match="Invalid API key format"
        ):
            authenticate_api_key("dsm_tooshort", db)

    @patch("adapters.mcp.auth.ApiKeyRepository")
    @patch("adapters.mcp.auth.PasswordService")
    def test_authenticate_wrong_key(self, mock_pw, mock_api_repo_cls):
        api_key = _make_api_key()

        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = [api_key]
        mock_api_repo_cls.return_value = mock_api_repo

        mock_pw.verify_password.return_value = False

        db = MagicMock()
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            authenticate_api_key(VALID_RAW_KEY, db)

    @patch("adapters.mcp.auth.ApiKeyRepository")
    def test_authenticate_no_active_keys(self, mock_api_repo_cls):
        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = []
        mock_api_repo_cls.return_value = mock_api_repo

        db = MagicMock()
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            authenticate_api_key(VALID_RAW_KEY, db)

    @patch("adapters.mcp.auth.UserRepository")
    @patch("adapters.mcp.auth.ApiKeyRepository")
    @patch("adapters.mcp.auth.PasswordService")
    def test_authenticate_inactive_user(
        self, mock_pw, mock_api_repo_cls, mock_user_repo_cls
    ):
        api_key = _make_api_key()
        user = _make_user(is_active=False)

        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = [api_key]
        mock_api_repo_cls.return_value = mock_api_repo

        mock_pw.verify_password.return_value = True

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo_cls.return_value = mock_user_repo

        db = MagicMock()
        with pytest.raises(
            AuthenticationError,
            match="User not found or inactive",
        ):
            authenticate_api_key(VALID_RAW_KEY, db)

    @patch("adapters.mcp.auth.CompanyRepository")
    @patch("adapters.mcp.auth.UserRepository")
    @patch("adapters.mcp.auth.ApiKeyRepository")
    @patch("adapters.mcp.auth.PasswordService")
    def test_authenticate_restricted_company(
        self, mock_pw, mock_api_repo_cls,
        mock_user_repo_cls, mock_company_repo_cls,
    ):
        api_key = _make_api_key()
        user = _make_user()
        company = _make_company(status=CompanyStatus.SUSPENDED)

        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = [api_key]
        mock_api_repo_cls.return_value = mock_api_repo

        mock_pw.verify_password.return_value = True

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo_cls.return_value = mock_user_repo

        mock_company_repo = MagicMock()
        mock_company_repo.find_by_id.return_value = company
        mock_company_repo_cls.return_value = mock_company_repo

        db = MagicMock()
        with pytest.raises(
            AuthenticationError, match="Company access is currently restricted"
        ):
            authenticate_api_key(VALID_RAW_KEY, db)

    @patch("adapters.mcp.auth.set_tenant")
    @patch("adapters.mcp.auth.CompanyRepository")
    @patch("adapters.mcp.auth.UserRepository")
    @patch("adapters.mcp.auth.ApiKeyRepository")
    @patch("adapters.mcp.auth.PasswordService")
    def test_tenant_context_set(
        self,
        mock_pw,
        mock_api_repo_cls,
        mock_user_repo_cls,
        mock_company_repo_cls,
        mock_set_tenant,
    ):
        api_key = _make_api_key()
        user = _make_user()
        company = _make_company()

        mock_api_repo = MagicMock()
        mock_api_repo.find_all_active.return_value = [api_key]
        mock_api_repo_cls.return_value = mock_api_repo

        mock_pw.verify_password.return_value = True

        mock_user_repo = MagicMock()
        mock_user_repo.find_by_id.return_value = user
        mock_user_repo_cls.return_value = mock_user_repo

        mock_company_repo = MagicMock()
        mock_company_repo.find_by_id.return_value = company
        mock_company_repo_cls.return_value = mock_company_repo

        db = MagicMock()
        authenticate_api_key(VALID_RAW_KEY, db)

        mock_set_tenant.assert_called_once_with(
            company_id="company123",
            user_id="user123",
            role="admin",
        )
