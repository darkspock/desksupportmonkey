from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_dependencies
from adapters.http.api.auth.dependencies import get_company_repo
from app import app
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _company_user() -> User:
    return User.create(
        email="employee@company.com",
        role=UserRole.EMPLOYEE,
        company_id="comp1",
    )


def _super_admin_user() -> User:
    return User.create(
        email="root@desksupportmonkey.com",
        role=UserRole.SUPER_ADMIN,
        company_id=None,
    )


def _mock_nav_config_repo():
    """Return a mock NavConfigRepository whose find_by_company returns None."""
    mock = MagicMock()
    mock.return_value.find_by_company.return_value = None
    return mock


@pytest.fixture
def mock_company_repo():
    return MagicMock()


@pytest.fixture
def company_client(mock_company_repo):
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: _company_user()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def super_admin_client(mock_company_repo):
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: _super_admin_user()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAuthMeEndpoint:
    @patch(
        "src.company_bc.nav_config.infrastructure.repository.NavConfigRepository",
        new_callable=_mock_nav_config_repo,
    )
    def test_includes_company_name_when_company_is_present(self, _nav_repo, company_client, mock_company_repo):
        mock_company_repo.find_by_id.return_value = SimpleNamespace(
            name="Acme Corp",
            plan=SimpleNamespace(value="open_source"),
            onboarding_completed_at=None,
        )

        response = company_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["company_id"] == "comp1"
        assert data["company_name"] == "Acme Corp"
        assert data["hidden_nav_items"] is None
        mock_company_repo.find_by_id.assert_called_once_with("comp1")

    def test_skips_company_lookup_for_super_admin(self, super_admin_client, mock_company_repo):
        response = super_admin_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["company_id"] is None
        assert data["company_name"] is None
        assert data["hidden_nav_items"] is None
        mock_company_repo.find_by_id.assert_not_called()
