from unittest.mock import MagicMock

import pytest

from src.company_bc.employee_role.application.commands.update_employee_role import (  # noqa: E501
    EmployeeRoleNotFoundError,
    EmployeeRoleNameExistsError,
    UpdateEmployeeRoleCommand,
    UpdateEmployeeRoleCommandHandler,
)
from src.company_bc.employee_role.domain.entities import (
    EmployeeRole,
)


class TestUpdateEmployeeRole:
    def test_success(self):
        role = EmployeeRole.create(
            id="er1",
            company_id="comp1",
            name="Old Name",
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        repo.find_by_name.return_value = None

        handler = UpdateEmployeeRoleCommandHandler(
            role_repo=repo,
        )
        handler.handle(
            UpdateEmployeeRoleCommand(
                role_id="er1",
                company_id="comp1",
                name="New Name",
                description="Updated desc",
            )
        )

        repo.save.assert_called_once()
        saved = repo.save.call_args[0][0]
        assert saved.name == "New Name"
        assert saved.description == "Updated desc"

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = UpdateEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleNotFoundError):
            handler.handle(
                UpdateEmployeeRoleCommand(
                    role_id="bad",
                    company_id="comp1",
                    name="Name",
                )
            )

    def test_duplicate_name_raises(self):
        role = EmployeeRole.create(
            id="er1",
            company_id="comp1",
            name="Engineer",
        )
        conflicting = EmployeeRole.create(
            id="er2",
            company_id="comp1",
            name="Designer",
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        repo.find_by_name.return_value = conflicting

        handler = UpdateEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleNameExistsError):
            handler.handle(
                UpdateEmployeeRoleCommand(
                    role_id="er1",
                    company_id="comp1",
                    name="Designer",
                )
            )
