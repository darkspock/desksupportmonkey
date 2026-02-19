from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_dependencies
from adapters.http.api.users.dependencies import (
    get_company_repo,
    get_magic_link_repo,
    get_user_repo,
)
from app import app
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _admin_user() -> User:
    return User.create(
        email="admin@company.com",
        role=UserRole.ADMIN,
        company_id="comp1",
    )


@pytest.fixture
def mock_user_repo():
    return MagicMock()


@pytest.fixture
def mock_company_repo():
    return MagicMock()


@pytest.fixture
def mock_magic_link_repo():
    return MagicMock()


@pytest.fixture
def admin_client(mock_user_repo, mock_company_repo, mock_magic_link_repo):
    admin = _admin_user()
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_user_repo] = lambda: mock_user_repo
    app.dependency_overrides[get_company_repo] = lambda: mock_company_repo
    app.dependency_overrides[get_magic_link_repo] = lambda: mock_magic_link_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestInviteUserEndpoint:
    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    def test_creates_employee_immediately(self, MockHandler, admin_client, mock_company_repo, mock_user_repo):
        mock_company_repo.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        mock_user_repo.find_by_email.return_value = None

        response = admin_client.post("/api/v1/users/invite", json={"email": "new.employee@company.com"})

        assert response.status_code == 201
        assert response.json()["data"]["message"] == "Invitation sent"
        mock_user_repo.save.assert_called_once()
        saved_user = mock_user_repo.save.call_args[0][0]
        assert saved_user.email == "new.employee@company.com"
        assert saved_user.role == UserRole.EMPLOYEE
        assert saved_user.company_id == "comp1"
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    def test_reinvite_existing_employee_same_company(self, MockHandler, admin_client, mock_company_repo, mock_user_repo):
        mock_company_repo.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_user = User.create(
            email="employee@company.com",
            role=UserRole.EMPLOYEE,
            company_id="comp1",
        )
        mock_user_repo.find_by_email.return_value = existing_user

        response = admin_client.post("/api/v1/users/invite", json={"email": "employee@company.com"})

        assert response.status_code == 201
        mock_user_repo.save.assert_not_called()
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    def test_reactivates_inactive_employee(self, MockHandler, admin_client, mock_company_repo, mock_user_repo):
        mock_company_repo.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_user = User.create(
            email="inactive@company.com",
            role=UserRole.EMPLOYEE,
            company_id="comp1",
        )
        existing_user.deactivate()
        mock_user_repo.find_by_email.return_value = existing_user

        response = admin_client.post("/api/v1/users/invite", json={"email": "inactive@company.com"})

        assert response.status_code == 201
        mock_user_repo.save.assert_called_once()
        reactivated_user = mock_user_repo.save.call_args[0][0]
        assert reactivated_user.is_active is True
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    def test_rejects_existing_non_employee(self, MockHandler, admin_client, mock_company_repo, mock_user_repo):
        mock_company_repo.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_admin = User.create(
            email="existing.admin@company.com",
            role=UserRole.ADMIN,
            company_id="comp1",
        )
        mock_user_repo.find_by_email.return_value = existing_admin

        response = admin_client.post("/api/v1/users/invite", json={"email": "existing.admin@company.com"})

        assert response.status_code == 409
        payload = response.json()
        message = payload.get("detail") or payload.get("error", {}).get("message")
        assert message == "User with this email already exists"
        mock_user_repo.save.assert_not_called()
        MockHandler.return_value.handle.assert_not_called()
