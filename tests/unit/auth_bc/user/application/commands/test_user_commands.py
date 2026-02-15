from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.change_user_role import (
    CannotAssignSuperAdminError,
    CannotChangeSelfError,
    ChangeUserRoleCommand,
    ChangeUserRoleCommandHandler,
    UserNotFoundError as RoleNotFoundError,
)
from src.auth_bc.user.application.commands.deactivate_user import (
    CannotDeactivateSelfError,
    DeactivateUserCommand,
    DeactivateUserCommandHandler,
    UserNotFoundError as DeactivateNotFoundError,
)
from src.auth_bc.user.application.commands.activate_user import (
    ActivateUserCommand,
    ActivateUserCommandHandler,
    UserNotFoundError as ActivateNotFoundError,
)
from src.auth_bc.user.application.commands.assign_department import (
    AssignDepartmentCommand,
    AssignDepartmentCommandHandler,
    DepartmentInactiveError,
    DepartmentNotFoundError,
    UserNotFoundError as AssignNotFoundError,
)
from src.company_bc.department.domain.entities import Department


def _make_user(user_id="user1", company_id="comp1"):
    user = User.create(email="test@example.com", role=UserRole.EMPLOYEE, company_id=company_id)
    user.id = user_id
    return user


class TestChangeUserRoleCommand:
    def test_success(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        result = handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="technician",
            )
        )

        assert result.role == UserRole.TECHNICIAN
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = None
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        with pytest.raises(RoleNotFoundError):
            handler.handle(
                ChangeUserRoleCommand(
                    user_id="bad", company_id="comp1",
                    current_user_id="admin1", new_role="admin",
                )
            )

    def test_cannot_change_self(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        with pytest.raises(CannotChangeSelfError):
            handler.handle(
                ChangeUserRoleCommand(
                    user_id="user1", company_id="comp1",
                    current_user_id="user1", new_role="admin",
                )
            )

    def test_cannot_assign_super_admin(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        with pytest.raises(CannotAssignSuperAdminError):
            handler.handle(
                ChangeUserRoleCommand(
                    user_id="user1", company_id="comp1",
                    current_user_id="admin1", new_role="super_admin",
                )
            )


class TestDeactivateUserCommand:
    def test_success(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = DeactivateUserCommandHandler(user_repo=repo)

        result = handler.handle(
            DeactivateUserCommand(user_id="user1", company_id="comp1", current_user_id="admin1")
        )

        assert result.is_active is False
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = None
        handler = DeactivateUserCommandHandler(user_repo=repo)

        with pytest.raises(DeactivateNotFoundError):
            handler.handle(
                DeactivateUserCommand(user_id="bad", company_id="comp1", current_user_id="admin1")
            )

    def test_cannot_deactivate_self(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = DeactivateUserCommandHandler(user_repo=repo)

        with pytest.raises(CannotDeactivateSelfError):
            handler.handle(
                DeactivateUserCommand(
                    user_id="user1", company_id="comp1", current_user_id="user1"
                )
            )


class TestActivateUserCommand:
    def test_success(self):
        user = _make_user()
        user.deactivate()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ActivateUserCommandHandler(user_repo=repo)

        result = handler.handle(ActivateUserCommand(user_id="user1", company_id="comp1"))

        assert result.is_active is True
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = None
        handler = ActivateUserCommandHandler(user_repo=repo)

        with pytest.raises(ActivateNotFoundError):
            handler.handle(ActivateUserCommand(user_id="bad", company_id="comp1"))


class TestAssignDepartmentCommand:
    def test_success(self):
        user = _make_user()
        dept = Department.create(company_id="comp1", name="Engineering")
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        dept_repo.find_by_id.return_value = dept
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        result = handler.handle(
            AssignDepartmentCommand(
                user_id="user1", company_id="comp1", department_id=dept.id
            )
        )

        assert result.department_id == dept.id
        user_repo.save.assert_called_once()

    def test_unassign(self):
        user = _make_user()
        user.department_id = "some-dept"
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        result = handler.handle(
            AssignDepartmentCommand(user_id="user1", company_id="comp1", department_id=None)
        )

        assert result.department_id is None
        user_repo.save.assert_called_once()

    def test_user_not_found_raises(self):
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = None
        dept_repo = MagicMock()
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        with pytest.raises(AssignNotFoundError):
            handler.handle(
                AssignDepartmentCommand(user_id="bad", company_id="comp1", department_id="d1")
            )

    def test_department_not_found_raises(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        dept_repo.find_by_id.return_value = None
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        with pytest.raises(DepartmentNotFoundError):
            handler.handle(
                AssignDepartmentCommand(user_id="user1", company_id="comp1", department_id="bad")
            )

    def test_department_inactive_raises(self):
        user = _make_user()
        dept = Department.create(company_id="comp1", name="Old")
        dept.deactivate()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        dept_repo.find_by_id.return_value = dept
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        with pytest.raises(DepartmentInactiveError):
            handler.handle(
                AssignDepartmentCommand(
                    user_id="user1", company_id="comp1", department_id=dept.id
                )
            )
