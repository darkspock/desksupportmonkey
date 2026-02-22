from unittest.mock import MagicMock

import pytest

from src.company_bc.employee_role.application.commands.create_employee_role import (  # noqa: E501
    CreateEmployeeRoleCommand,
    CreateEmployeeRoleCommandHandler,
    EmployeeRoleNameExistsError,
)


class TestCreateEmployeeRole:
    def test_success(self):
        repo = MagicMock()
        repo.find_by_name.return_value = None
        handler = CreateEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        handler.handle(
            CreateEmployeeRoleCommand(
                id="er1",
                company_id="comp1",
                name="Software Engineer",
                description="Builds software",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.id == "er1"
        assert saved.name == "Software Engineer"
        assert saved.description == "Builds software"
        assert saved.is_active is True

    def test_duplicate_name_raises(self):
        existing = MagicMock()
        repo = MagicMock()
        repo.find_by_name.return_value = existing
        handler = CreateEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleNameExistsError):
            handler.handle(
                CreateEmployeeRoleCommand(
                    company_id="comp1",
                    name="Software Engineer",
                )
            )

        repo.save.assert_not_called()

    def test_create_without_description(self):
        repo = MagicMock()
        repo.find_by_name.return_value = None
        handler = CreateEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        handler.handle(
            CreateEmployeeRoleCommand(
                id="er2",
                company_id="comp1",
                name="Designer",
            )
        )

        saved = repo.save.call_args[0][0]
        assert saved.name == "Designer"
        assert saved.description is None
