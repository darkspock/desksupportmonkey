from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from adapters.http.api.auth import dependencies as auth_dependencies
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
def admin_client():
    admin = _admin_user()
    app.dependency_overrides[auth_dependencies.get_current_user] = lambda: admin
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestInviteUserEndpoint:
    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    @patch("adapters.http.api.users.routers.UserRepository")
    @patch("adapters.http.api.users.routers.CompanyRepository")
    def test_creates_employee_immediately(self, MockCompanyRepo, MockUserRepo, MockHandler, admin_client):
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        user_repo = MockUserRepo.return_value
        user_repo.find_by_email.return_value = None

        response = admin_client.post("/api/v1/users/invite", json={"email": "new.employee@company.com"})

        assert response.status_code == 201
        assert response.json()["data"]["message"] == "Invitation sent"
        user_repo.save.assert_called_once()
        saved_user = user_repo.save.call_args[0][0]
        assert saved_user.email == "new.employee@company.com"
        assert saved_user.role == UserRole.EMPLOYEE
        assert saved_user.company_id == "comp1"
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    @patch("adapters.http.api.users.routers.UserRepository")
    @patch("adapters.http.api.users.routers.CompanyRepository")
    def test_reinvite_existing_employee_same_company(self, MockCompanyRepo, MockUserRepo, MockHandler, admin_client):
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_user = User.create(
            email="employee@company.com",
            role=UserRole.EMPLOYEE,
            company_id="comp1",
        )
        user_repo = MockUserRepo.return_value
        user_repo.find_by_email.return_value = existing_user

        response = admin_client.post("/api/v1/users/invite", json={"email": "employee@company.com"})

        assert response.status_code == 201
        user_repo.save.assert_not_called()
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    @patch("adapters.http.api.users.routers.UserRepository")
    @patch("adapters.http.api.users.routers.CompanyRepository")
    def test_reactivates_inactive_employee(self, MockCompanyRepo, MockUserRepo, MockHandler, admin_client):
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_user = User.create(
            email="inactive@company.com",
            role=UserRole.EMPLOYEE,
            company_id="comp1",
        )
        existing_user.deactivate()
        user_repo = MockUserRepo.return_value
        user_repo.find_by_email.return_value = existing_user

        response = admin_client.post("/api/v1/users/invite", json={"email": "inactive@company.com"})

        assert response.status_code == 201
        user_repo.save.assert_called_once()
        reactivated_user = user_repo.save.call_args[0][0]
        assert reactivated_user.is_active is True
        MockHandler.return_value.handle.assert_called_once()

    @patch("adapters.http.api.users.routers.CreateMagicLinkCommandHandler")
    @patch("adapters.http.api.users.routers.UserRepository")
    @patch("adapters.http.api.users.routers.CompanyRepository")
    def test_rejects_existing_non_employee(self, MockCompanyRepo, MockUserRepo, MockHandler, admin_client):
        MockCompanyRepo.return_value.find_by_id.return_value = MagicMock(email_domains=["company.com"])
        existing_admin = User.create(
            email="existing.admin@company.com",
            role=UserRole.ADMIN,
            company_id="comp1",
        )
        user_repo = MockUserRepo.return_value
        user_repo.find_by_email.return_value = existing_admin

        response = admin_client.post("/api/v1/users/invite", json={"email": "existing.admin@company.com"})

        assert response.status_code == 409
        payload = response.json()
        message = payload.get("detail") or payload.get("error", {}).get("message")
        assert message == "User with this email already exists"
        user_repo.save.assert_not_called()
        MockHandler.return_value.handle.assert_not_called()
