from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_dependencies
from app import app
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.commands.update_company import DomainAlreadyTakenError


def _admin_user() -> User:
    return User.create(
        email="admin@company.com",
        role=UserRole.ADMIN,
        company_id="comp1",
    )


def _super_admin_user() -> User:
    return User.create(
        email="root@desksupportmonkey.com",
        role=UserRole.SUPER_ADMIN,
        company_id=None,
    )


@pytest.fixture
def admin_client():
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: _admin_user()
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


class TestMyCompanySettingsEndpoint:
    @patch("adapters.http.api.my.routers.GetCompanyQueryHandler")
    def test_get_company_settings(self, MockGetCompanyQueryHandler, admin_client):
        MockGetCompanyQueryHandler.return_value.handle.return_value = SimpleNamespace(
            company=SimpleNamespace(
                id="comp1",
                name="Acme Corp",
                email_domains=["company.com", "company.org"],
                sector=None,
            )
        )

        response = admin_client.get("/api/v1/my/company-settings")

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["id"] == "comp1"
        assert payload["name"] == "Acme Corp"
        assert payload["email_domains"] == ["company.com", "company.org"]

    @patch("adapters.http.api.my.routers.GetCompanyQueryHandler")
    @patch("adapters.http.api.my.routers.UpdateCompanyCommandHandler")
    def test_update_company_settings_domains(self, MockUpdateCompanyCommandHandler, MockGetCompanyQueryHandler, admin_client):
        MockGetCompanyQueryHandler.return_value.handle.return_value = SimpleNamespace(
            company=SimpleNamespace(
                id="comp1",
                name="Acme Corp",
                email_domains=["company.com", "new.company.com"],
                sector=None,
            )
        )

        response = admin_client.put(
            "/api/v1/my/company-settings",
            json={"email_domains": ["company.com", "new.company.com"]},
        )

        assert response.status_code == 200
        payload = response.json()["data"]
        assert payload["email_domains"] == ["company.com", "new.company.com"]

        command = MockUpdateCompanyCommandHandler.return_value.handle.call_args[0][0]
        assert command.company_id == "comp1"
        assert command.email_domains == ["company.com", "new.company.com"]

    @patch("adapters.http.api.my.routers.UpdateCompanyCommandHandler")
    def test_update_company_settings_conflict(self, MockUpdateCompanyCommandHandler, admin_client):
        MockUpdateCompanyCommandHandler.return_value.handle.side_effect = DomainAlreadyTakenError("taken.com")

        response = admin_client.put(
            "/api/v1/my/company-settings",
            json={"email_domains": ["taken.com"]},
        )

        assert response.status_code == 409
        payload = response.json()
        message = payload.get("detail") or payload.get("error", {}).get("message", "")
        assert "taken.com" in message

    def test_super_admin_forbidden(self, super_admin_client):
        response = super_admin_client.get("/api/v1/my/company-settings")

        assert response.status_code == 403
        payload = response.json()
        message = payload.get("detail") or payload.get("error", {}).get("message")
        assert message == "Only company admins can access company settings"
