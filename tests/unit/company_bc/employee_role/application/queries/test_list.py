from datetime import datetime
from unittest.mock import MagicMock

from src.company_bc.employee_role.application.queries.get_employee_role import (
    EmployeeRoleReadModel,
)
from src.company_bc.employee_role.application.queries.list_employee_roles import (
    ListEmployeeRolesQuery,
    ListEmployeeRolesQueryHandler,
)
from src.company_bc.employee_role.domain.entities import EmployeeRole


def _make_role(id: str, name: str) -> EmployeeRole:
    return EmployeeRole(
        id=id,
        company_id="comp1",
        name=name,
        description=None,
        is_active=True,
        created_at=datetime(2024, 1, 1),
        updated_at=datetime(2024, 1, 1),
    )


class TestListEmployeeRoles:
    def test_returns_read_models(self):
        roles = [_make_role("er1", "Engineer"), _make_role("er2", "Designer")]
        repo = MagicMock()
        repo.find_all.return_value = (roles, 2)
        handler = ListEmployeeRolesQueryHandler(role_repo=repo)

        result, total = handler.handle(
            ListEmployeeRolesQuery(company_id="comp1")
        )

        assert total == 2
        assert len(result) == 2
        assert all(isinstance(r, EmployeeRoleReadModel) for r in result)
        assert result[0].name == "Engineer"
        assert result[1].name == "Designer"
        repo.find_all.assert_called_once_with(
            company_id="comp1", page=1, page_size=20, include_inactive=False,
        )

    def test_empty_list(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListEmployeeRolesQueryHandler(role_repo=repo)

        result, total = handler.handle(
            ListEmployeeRolesQuery(company_id="comp1")
        )

        assert total == 0
        assert result == []

    def test_pagination_params_passed(self):
        repo = MagicMock()
        repo.find_all.return_value = ([], 0)
        handler = ListEmployeeRolesQueryHandler(role_repo=repo)

        handler.handle(
            ListEmployeeRolesQuery(
                company_id="comp1", page=3, page_size=10, include_inactive=True,
            )
        )

        repo.find_all.assert_called_once_with(
            company_id="comp1", page=3, page_size=10, include_inactive=True,
        )
