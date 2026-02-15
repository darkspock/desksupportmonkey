from unittest.mock import MagicMock

import pytest

from src.company_bc.department.application.commands.create_department import (
    CreateDepartmentCommand,
    CreateDepartmentCommandHandler,
    DepartmentNameExistsError,
)
from src.company_bc.department.application.commands.update_department import (
    DepartmentNotFoundError as UpdateNotFoundError,
    DepartmentNameExistsError as UpdateNameExistsError,
    UpdateDepartmentCommand,
    UpdateDepartmentCommandHandler,
)
from src.company_bc.department.application.commands.delete_department import (
    DeleteDepartmentCommand,
    DeleteDepartmentCommandHandler,
    DepartmentHasUsersError,
    DepartmentNotFoundError as DeleteNotFoundError,
)
from src.company_bc.department.domain.entities import Department


class TestCreateDepartmentCommand:
    def test_success(self):
        repo = MagicMock()
        repo.find_by_name.return_value = None
        handler = CreateDepartmentCommandHandler(department_repo=repo)

        dept = handler.handle(CreateDepartmentCommand(company_id="comp1", name="Engineering"))

        assert dept.name == "Engineering"
        assert dept.company_id == "comp1"
        repo.save.assert_called_once()

    def test_duplicate_name_raises(self):
        repo = MagicMock()
        repo.find_by_name.return_value = Department.create(company_id="comp1", name="Engineering")
        handler = CreateDepartmentCommandHandler(department_repo=repo)

        with pytest.raises(DepartmentNameExistsError):
            handler.handle(CreateDepartmentCommand(company_id="comp1", name="Engineering"))

        repo.save.assert_not_called()


class TestUpdateDepartmentCommand:
    def test_success(self):
        dept = Department.create(company_id="comp1", name="Old Name")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        repo.find_by_name.return_value = None
        handler = UpdateDepartmentCommandHandler(department_repo=repo)

        result = handler.handle(
            UpdateDepartmentCommand(department_id=dept.id, company_id="comp1", name="New Name")
        )

        assert result.name == "New Name"
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = UpdateDepartmentCommandHandler(department_repo=repo)

        with pytest.raises(UpdateNotFoundError):
            handler.handle(
                UpdateDepartmentCommand(department_id="bad", company_id="comp1", name="X")
            )

    def test_duplicate_name_raises(self):
        dept = Department.create(company_id="comp1", name="Old")
        other = Department.create(company_id="comp1", name="Taken")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        repo.find_by_name.return_value = other
        handler = UpdateDepartmentCommandHandler(department_repo=repo)

        with pytest.raises(UpdateNameExistsError):
            handler.handle(
                UpdateDepartmentCommand(department_id=dept.id, company_id="comp1", name="Taken")
            )


class TestDeleteDepartmentCommand:
    def test_success(self):
        dept = Department.create(company_id="comp1", name="To Delete")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        repo.count_users.return_value = 0
        handler = DeleteDepartmentCommandHandler(department_repo=repo)

        result = handler.handle(
            DeleteDepartmentCommand(department_id=dept.id, company_id="comp1")
        )

        assert result.is_active is False
        repo.save.assert_called_once()

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = DeleteDepartmentCommandHandler(department_repo=repo)

        with pytest.raises(DeleteNotFoundError):
            handler.handle(DeleteDepartmentCommand(department_id="bad", company_id="comp1"))

    def test_has_users_raises(self):
        dept = Department.create(company_id="comp1", name="Busy")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        repo.count_users.return_value = 3
        handler = DeleteDepartmentCommandHandler(department_repo=repo)

        with pytest.raises(DepartmentHasUsersError):
            handler.handle(
                DeleteDepartmentCommand(department_id=dept.id, company_id="comp1")
            )

        repo.save.assert_not_called()
