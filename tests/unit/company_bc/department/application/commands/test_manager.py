from unittest.mock import MagicMock

import pytest

from src.company_bc.department.application.commands.assign_manager import (
    AssignDepartmentManagerCommand,
    AssignDepartmentManagerCommandHandler,
    CrossCompanyError,
    DepartmentNotFoundError as AssignDeptNotFoundError,
    UserInactiveError,
    UserNotFoundError,
)
from src.company_bc.department.application.commands.remove_manager import (
    DepartmentNotFoundError as RemoveDeptNotFoundError,
    RemoveDepartmentManagerCommand,
    RemoveDepartmentManagerCommandHandler,
)
from src.company_bc.department.domain.entities import Department


class TestAssignDepartmentManager:
    def test_success(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_by_id.return_value = dept

        user = MagicMock()
        user.is_active = True
        user.company_id = "comp1"
        user_lookup = MagicMock()
        user_lookup.find_by_id.return_value = user

        handler = AssignDepartmentManagerCommandHandler(
            department_repo=repo, user_lookup=user_lookup,
        )
        handler.handle(
            AssignDepartmentManagerCommand(
                department_id=dept.id,
                company_id="comp1",
                manager_user_id="user1",
                performed_by="admin1",
            )
        )

        assert dept.manager_user_id == "user1"
        repo.save.assert_called_once_with(dept)

    def test_department_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        user_lookup = MagicMock()

        handler = AssignDepartmentManagerCommandHandler(
            department_repo=repo, user_lookup=user_lookup,
        )

        with pytest.raises(AssignDeptNotFoundError):
            handler.handle(
                AssignDepartmentManagerCommand(
                    department_id="bad",
                    company_id="comp1",
                    manager_user_id="user1",
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()

    def test_user_not_found(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        user_lookup = MagicMock()
        user_lookup.find_by_id.return_value = None

        handler = AssignDepartmentManagerCommandHandler(
            department_repo=repo, user_lookup=user_lookup,
        )

        with pytest.raises(UserNotFoundError):
            handler.handle(
                AssignDepartmentManagerCommand(
                    department_id=dept.id,
                    company_id="comp1",
                    manager_user_id="bad",
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()

    def test_cross_company_rejected(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_by_id.return_value = dept

        user = MagicMock()
        user.is_active = True
        user.company_id = "comp2"
        user_lookup = MagicMock()
        user_lookup.find_by_id.return_value = user

        handler = AssignDepartmentManagerCommandHandler(
            department_repo=repo, user_lookup=user_lookup,
        )

        with pytest.raises(CrossCompanyError):
            handler.handle(
                AssignDepartmentManagerCommand(
                    department_id=dept.id,
                    company_id="comp1",
                    manager_user_id="user1",
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()

    def test_user_inactive_rejected(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_by_id.return_value = dept

        user = MagicMock()
        user.is_active = False
        user.company_id = "comp1"
        user_lookup = MagicMock()
        user_lookup.find_by_id.return_value = user

        handler = AssignDepartmentManagerCommandHandler(
            department_repo=repo, user_lookup=user_lookup,
        )

        with pytest.raises(UserInactiveError):
            handler.handle(
                AssignDepartmentManagerCommand(
                    department_id=dept.id,
                    company_id="comp1",
                    manager_user_id="user1",
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()


class TestRemoveDepartmentManager:
    def test_success(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        dept.assign_manager("user1")
        repo = MagicMock()
        repo.find_by_id.return_value = dept

        handler = RemoveDepartmentManagerCommandHandler(
            department_repo=repo,
        )
        handler.handle(
            RemoveDepartmentManagerCommand(
                department_id=dept.id,
                company_id="comp1",
                performed_by="admin1",
            )
        )

        assert dept.manager_user_id is None
        repo.save.assert_called_once_with(dept)

    def test_no_current_manager_idempotent(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        assert dept.manager_user_id is None
        repo = MagicMock()
        repo.find_by_id.return_value = dept

        handler = RemoveDepartmentManagerCommandHandler(
            department_repo=repo,
        )
        handler.handle(
            RemoveDepartmentManagerCommand(
                department_id=dept.id,
                company_id="comp1",
                performed_by="admin1",
            )
        )

        assert dept.manager_user_id is None
        repo.save.assert_called_once_with(dept)

    def test_department_not_found(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = RemoveDepartmentManagerCommandHandler(
            department_repo=repo,
        )

        with pytest.raises(RemoveDeptNotFoundError):
            handler.handle(
                RemoveDepartmentManagerCommand(
                    department_id="bad",
                    company_id="comp1",
                    performed_by="admin1",
                )
            )

        repo.save.assert_not_called()
