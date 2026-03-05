"""Unit tests for SwitchCompanyService."""

import pytest
from unittest.mock import MagicMock

from core.jwt import JWTService
from src.auth_bc.company_user.domain.entities import (
    CompanyUser,
    MembershipDeactivatedError,
    MembershipNotFoundError,
)
from src.auth_bc.user.application.commands.switch_company import (
    SwitchCompanyRequest,
    SwitchCompanyService,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_user(company_id="comp-a", role=UserRole.ADMIN):
    return User(
        id="user-1",
        email="alice@example.com",
        role=role,
        company_id=company_id,
    )


def _make_membership(company_id, role=UserRole.EMPLOYEE, department_id="dept-1", employee_role_id="er-1", is_active=True):
    cu = CompanyUser.create(user_id="user-1", company_id=company_id, role=role)
    cu.assign_department(department_id)
    cu.assign_employee_role(employee_role_id)
    if not is_active:
        cu.deactivate()
    return cu


class TestSwitchCompanyService:
    def test_success_copies_membership_and_returns_jwt(self):
        user = _make_user(company_id="comp-a", role=UserRole.ADMIN)
        membership = _make_membership("comp-b", role=UserRole.EMPLOYEE, department_id="dept-b", employee_role_id="er-b")

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        jwt_service = JWTService()

        service = SwitchCompanyService(
            user_repo=user_repo,
            company_user_repo=company_user_repo,
            jwt_service=jwt_service,
        )
        token = service.handle(SwitchCompanyRequest(
            user_id="user-1",
            target_company_id="comp-b",
        ))

        # Verify user row was updated
        assert user.company_id == "comp-b"
        assert user.role == UserRole.EMPLOYEE
        assert user.department_id == "dept-b"
        assert user.employee_role_id == "er-b"
        user_repo.save.assert_called_once_with(user)

        # Verify JWT was returned
        assert isinstance(token, str)
        decoded = jwt_service.decode_token(token)
        assert decoded["sub"] == "user-1"
        assert decoded["company_id"] == "comp-b"
        assert decoded["role"] == "employee"

    def test_no_membership_raises_not_found(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = None

        service = SwitchCompanyService(
            user_repo=user_repo,
            company_user_repo=company_user_repo,
            jwt_service=JWTService(),
        )
        with pytest.raises(MembershipNotFoundError):
            service.handle(SwitchCompanyRequest(
                user_id="user-1",
                target_company_id="comp-nonexistent",
            ))

    def test_inactive_membership_raises_deactivated(self):
        user = _make_user()
        membership = _make_membership("comp-b", is_active=False)

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership

        service = SwitchCompanyService(
            user_repo=user_repo,
            company_user_repo=company_user_repo,
            jwt_service=JWTService(),
        )
        with pytest.raises(MembershipDeactivatedError):
            service.handle(SwitchCompanyRequest(
                user_id="user-1",
                target_company_id="comp-b",
            ))

    def test_user_not_found_raises_not_found(self):
        user_repo = MagicMock()
        user_repo.find_by_id.return_value = None
        company_user_repo = MagicMock()

        service = SwitchCompanyService(
            user_repo=user_repo,
            company_user_repo=company_user_repo,
            jwt_service=JWTService(),
        )
        with pytest.raises(MembershipNotFoundError):
            service.handle(SwitchCompanyRequest(
                user_id="nonexistent",
                target_company_id="comp-b",
            ))

    def test_copies_all_four_fields(self):
        user = _make_user(company_id="comp-a", role=UserRole.ADMIN)
        user.department_id = "old-dept"
        user.employee_role_id = "old-er"

        membership = _make_membership(
            "comp-b", role=UserRole.EMPLOYEE,
            department_id="new-dept", employee_role_id="new-er",
        )

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership

        service = SwitchCompanyService(
            user_repo=user_repo,
            company_user_repo=company_user_repo,
            jwt_service=JWTService(),
        )
        service.handle(SwitchCompanyRequest(
            user_id="user-1",
            target_company_id="comp-b",
        ))

        assert user.company_id == "comp-b"
        assert user.role == UserRole.EMPLOYEE
        assert user.department_id == "new-dept"
        assert user.employee_role_id == "new-er"
