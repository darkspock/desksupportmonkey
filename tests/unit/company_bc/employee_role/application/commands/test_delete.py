from unittest.mock import MagicMock

import pytest

from src.company_bc.employee_role.application.commands.delete_employee_role import (  # noqa: E501
    DeleteEmployeeRoleCommand,
    DeleteEmployeeRoleCommandHandler,
    EmployeeRoleInUseError,
    EmployeeRoleNotFoundError,
)
from src.company_bc.employee_role.domain.entities import (
    EmployeeRole,
)


class TestDeleteEmployeeRole:
    def test_success(self):
        role = EmployeeRole.create(
            id="er1",
            company_id="comp1",
            name="Old Role",
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        repo.count_users.return_value = 0
        repo.count_equipment_profiles.return_value = 0

        handler = DeleteEmployeeRoleCommandHandler(
            role_repo=repo,
        )
        handler.handle(
            DeleteEmployeeRoleCommand(
                role_id="er1",
                company_id="comp1",
            )
        )

        repo.delete.assert_called_once_with("er1")

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None

        handler = DeleteEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleNotFoundError):
            handler.handle(
                DeleteEmployeeRoleCommand(
                    role_id="bad",
                    company_id="comp1",
                )
            )

    def test_in_use_by_users_raises(self):
        role = EmployeeRole.create(
            id="er1",
            company_id="comp1",
            name="In Use",
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        repo.count_users.return_value = 3
        repo.count_equipment_profiles.return_value = 0

        handler = DeleteEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleInUseError):
            handler.handle(
                DeleteEmployeeRoleCommand(
                    role_id="er1",
                    company_id="comp1",
                )
            )

        repo.delete.assert_not_called()

    def test_in_use_by_profiles_raises(self):
        role = EmployeeRole.create(
            id="er1",
            company_id="comp1",
            name="In Use",
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        repo.count_users.return_value = 0
        repo.count_equipment_profiles.return_value = 2

        handler = DeleteEmployeeRoleCommandHandler(
            role_repo=repo,
        )

        with pytest.raises(EmployeeRoleInUseError):
            handler.handle(
                DeleteEmployeeRoleCommand(
                    role_id="er1",
                    company_id="comp1",
                )
            )

        repo.delete.assert_not_called()
