from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.change_user_role import (
    CannotAssignSuperAdminError,
    CannotChangeSelfError,
    ChangeUserRoleCommand,
    ChangeUserRoleCommandHandler,
    LastAdminError,
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


def _make_user(user_id="user1", company_id="comp1", role=UserRole.EMPLOYEE):
    user = User.create(email="test@example.com", role=role, company_id=company_id)
    user.id = user_id
    return user


class TestChangeUserRoleCommand:
    def test_success(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="technician",
            )
        )

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

    def test_same_role_for_self_is_noop(self):
        user = _make_user(role=UserRole.ADMIN)
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="user1", new_role="admin",
            )
        )

        repo.save.assert_not_called()

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

    def test_last_admin_cannot_be_demoted(self):
        user = _make_user(role=UserRole.ADMIN)
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        repo.count_admins_by_company.return_value = 1
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        with pytest.raises(LastAdminError):
            handler.handle(
                ChangeUserRoleCommand(
                    user_id="user1", company_id="comp1",
                    current_user_id="admin2", new_role="employee",
                )
            )

    def test_admin_can_be_demoted_when_multiple_admins(self):
        user = _make_user(role=UserRole.ADMIN)
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        repo.count_admins_by_company.return_value = 2
        handler = ChangeUserRoleCommandHandler(user_repo=repo)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin2", new_role="employee",
            )
        )

        repo.save.assert_called_once()

    def test_promote_to_admin_sends_notification(self):
        user = _make_user()
        existing_admin = _make_user(user_id="admin1", role=UserRole.ADMIN)
        existing_admin.email = "admin1@example.com"
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        repo.find_admins_by_company.return_value = [existing_admin, user]
        email_service = MagicMock()
        handler = ChangeUserRoleCommandHandler(user_repo=repo, email_service=email_service)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="admin",
            )
        )

        email_service.send.assert_called_once()

    def test_promote_notification_failure_does_not_block(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        repo.find_admins_by_company.side_effect = Exception("SMTP error")
        email_service = MagicMock()
        handler = ChangeUserRoleCommandHandler(user_repo=repo, email_service=email_service)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="admin",
            )
        )

        # Role change should still succeed despite email failure
        repo.save.assert_called_once()


class TestDeactivateUserCommand:
    def test_success(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = DeactivateUserCommandHandler(user_repo=repo)

        handler.handle(
            DeactivateUserCommand(user_id="user1", company_id="comp1", current_user_id="admin1")
        )

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

        handler.handle(ActivateUserCommand(user_id="user1", company_id="comp1"))

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

        handler.handle(
            AssignDepartmentCommand(
                user_id="user1", company_id="comp1", department_id=dept.id
            )
        )

        user_repo.save.assert_called_once()

    def test_unassign(self):
        user = _make_user()
        user.department_id = "some-dept"
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=dept_repo)

        handler.handle(
            AssignDepartmentCommand(user_id="user1", company_id="comp1", department_id=None)
        )

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


# --- Dual-write tests (CompanyUser membership) ---

from src.auth_bc.company_user.domain.entities import CompanyUser


def _make_membership(user_id="user1", company_id="comp1", role=UserRole.EMPLOYEE):
    return CompanyUser.create(user_id=user_id, company_id=company_id, role=role)


class TestChangeUserRoleDualWrite:
    def test_dual_write_updates_membership_role(self):
        user = _make_user()
        membership = _make_membership()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        handler = ChangeUserRoleCommandHandler(
            user_repo=user_repo, company_user_repo=company_user_repo
        )

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="technician",
            )
        )

        user_repo.save.assert_called_once()
        company_user_repo.save.assert_called_once()
        saved_membership = company_user_repo.save.call_args[0][0]
        assert saved_membership.role == UserRole.TECHNICIAN

    def test_dual_write_no_membership_still_saves_user(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = None
        handler = ChangeUserRoleCommandHandler(
            user_repo=user_repo, company_user_repo=company_user_repo
        )

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="technician",
            )
        )

        user_repo.save.assert_called_once()
        company_user_repo.save.assert_not_called()

    def test_backward_compat_no_company_user_repo(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        handler = ChangeUserRoleCommandHandler(user_repo=user_repo)

        handler.handle(
            ChangeUserRoleCommand(
                user_id="user1", company_id="comp1",
                current_user_id="admin1", new_role="technician",
            )
        )

        user_repo.save.assert_called_once()


class TestDeactivateUserDualWrite:
    def test_dual_write_deactivates_membership(self):
        user = _make_user()
        membership = _make_membership()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        handler = DeactivateUserCommandHandler(
            user_repo=user_repo, company_user_repo=company_user_repo
        )

        handler.handle(
            DeactivateUserCommand(
                user_id="user1", company_id="comp1", current_user_id="admin1"
            )
        )

        user_repo.save.assert_called_once()
        company_user_repo.save.assert_called_once()
        saved_membership = company_user_repo.save.call_args[0][0]
        assert saved_membership.is_active is False

    def test_backward_compat_no_company_user_repo(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        handler = DeactivateUserCommandHandler(user_repo=user_repo)

        handler.handle(
            DeactivateUserCommand(
                user_id="user1", company_id="comp1", current_user_id="admin1"
            )
        )

        user_repo.save.assert_called_once()


class TestActivateUserDualWrite:
    def test_dual_write_activates_membership(self):
        user = _make_user()
        user.deactivate()
        membership = _make_membership()
        membership.deactivate()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        handler = ActivateUserCommandHandler(
            user_repo=user_repo, company_user_repo=company_user_repo
        )

        handler.handle(ActivateUserCommand(user_id="user1", company_id="comp1"))

        user_repo.save.assert_called_once()
        company_user_repo.save.assert_called_once()
        saved_membership = company_user_repo.save.call_args[0][0]
        assert saved_membership.is_active is True

    def test_backward_compat_no_company_user_repo(self):
        user = _make_user()
        user.deactivate()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        handler = ActivateUserCommandHandler(user_repo=user_repo)

        handler.handle(ActivateUserCommand(user_id="user1", company_id="comp1"))

        user_repo.save.assert_called_once()


class TestAssignDepartmentDualWrite:
    def test_dual_write_updates_membership_department(self):
        user = _make_user()
        dept = Department.create(company_id="comp1", name="Engineering")
        membership = _make_membership()
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        dept_repo.find_by_id.return_value = dept
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        handler = AssignDepartmentCommandHandler(
            user_repo=user_repo, department_repo=dept_repo,
            company_user_repo=company_user_repo,
        )

        handler.handle(
            AssignDepartmentCommand(
                user_id="user1", company_id="comp1", department_id=dept.id
            )
        )

        user_repo.save.assert_called_once()
        company_user_repo.save.assert_called_once()
        saved_membership = company_user_repo.save.call_args[0][0]
        assert saved_membership.department_id == dept.id

    def test_dual_write_unassign_department(self):
        user = _make_user()
        user.department_id = "old-dept"
        membership = _make_membership()
        membership.department_id = "old-dept"
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        company_user_repo = MagicMock()
        company_user_repo.find_by_user_and_company.return_value = membership
        handler = AssignDepartmentCommandHandler(
            user_repo=user_repo, department_repo=dept_repo,
            company_user_repo=company_user_repo,
        )

        handler.handle(
            AssignDepartmentCommand(
                user_id="user1", company_id="comp1", department_id=None
            )
        )

        saved_membership = company_user_repo.save.call_args[0][0]
        assert saved_membership.department_id is None

    def test_backward_compat_no_company_user_repo(self):
        user = _make_user()
        dept = Department.create(company_id="comp1", name="Engineering")
        user_repo = MagicMock()
        user_repo.find_by_id_and_company.return_value = user
        dept_repo = MagicMock()
        dept_repo.find_by_id.return_value = dept
        handler = AssignDepartmentCommandHandler(
            user_repo=user_repo, department_repo=dept_repo
        )

        handler.handle(
            AssignDepartmentCommand(
                user_id="user1", company_id="comp1", department_id=dept.id
            )
        )

        user_repo.save.assert_called_once()
