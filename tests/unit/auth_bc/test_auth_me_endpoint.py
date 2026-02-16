from unittest.mock import MagicMock, patch
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_dependencies
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


@pytest.fixture
def company_client():
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: _company_user()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def super_admin_client():
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: _super_admin_user()
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestAuthMeEndpoint:
    @patch("adapters.http.api.auth.routers.CompanyRepository")
    def test_includes_company_name_when_company_is_present(self, MockCompanyRepository, company_client):
        MockCompanyRepository.return_value.find_by_id.return_value = SimpleNamespace(name="Acme Corp")

        response = company_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["company_id"] == "comp1"
        assert data["company_name"] == "Acme Corp"
        MockCompanyRepository.return_value.find_by_id.assert_called_once_with("comp1")

    @patch("adapters.http.api.auth.routers.CompanyRepository")
    def test_skips_company_lookup_for_super_admin(self, MockCompanyRepository, super_admin_client):
        response = super_admin_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["company_id"] is None
        assert data["company_name"] is None
        MockCompanyRepository.return_value.find_by_id.assert_not_called()
