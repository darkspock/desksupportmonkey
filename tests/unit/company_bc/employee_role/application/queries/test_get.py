from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.company_bc.employee_role.application.queries.get_employee_role import (
    EmployeeRoleNotFoundError,
    EmployeeRoleReadModel,
    GetEmployeeRoleQuery,
    GetEmployeeRoleQueryHandler,
)
from src.company_bc.employee_role.domain.entities import EmployeeRole


class TestGetEmployeeRole:
    def test_success(self):
        now = datetime(2024, 1, 1, 12, 0, 0)
        role = EmployeeRole(
            id="er1",
            company_id="comp1",
            name="Software Engineer",
            description="Builds software",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        repo = MagicMock()
        repo.find_by_id.return_value = role
        handler = GetEmployeeRoleQueryHandler(role_repo=repo)

        result = handler.handle(
            GetEmployeeRoleQuery(role_id="er1", company_id="comp1")
        )

        assert isinstance(result, EmployeeRoleReadModel)
        assert result.id == "er1"
        assert result.name == "Software Engineer"
        assert result.description == "Builds software"
        assert result.is_active is True
        assert result.created_at == now
        repo.find_by_id.assert_called_once_with("er1", "comp1")

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetEmployeeRoleQueryHandler(role_repo=repo)

        with pytest.raises(EmployeeRoleNotFoundError):
            handler.handle(
                GetEmployeeRoleQuery(role_id="missing", company_id="comp1")
            )
