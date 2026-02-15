from unittest.mock import MagicMock

import pytest

from src.company_bc.department.application.queries.list_departments import (
    ListDepartmentsQuery,
    ListDepartmentsQueryHandler,
)
from src.company_bc.department.application.queries.get_department import (
    DepartmentNotFoundError,
    GetDepartmentQuery,
    GetDepartmentQueryHandler,
)
from src.company_bc.department.domain.entities import Department


class TestListDepartmentsQuery:
    def test_returns_paginated(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_all.return_value = ([dept], 1)
        handler = ListDepartmentsQueryHandler(department_repo=repo)

        departments, total = handler.handle(
            ListDepartmentsQuery(company_id="comp1", page=1, page_size=20)
        )

        assert len(departments) == 1
        assert total == 1
        repo.find_all.assert_called_once_with(
            company_id="comp1", page=1, page_size=20, include_inactive=False
        )


class TestGetDepartmentQuery:
    def test_success(self):
        dept = Department.create(company_id="comp1", name="Engineering")
        repo = MagicMock()
        repo.find_by_id.return_value = dept
        repo.count_users.return_value = 5
        handler = GetDepartmentQueryHandler(department_repo=repo)

        detail = handler.handle(
            GetDepartmentQuery(department_id=dept.id, company_id="comp1")
        )

        assert detail.department.name == "Engineering"
        assert detail.user_count == 5

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id.return_value = None
        handler = GetDepartmentQueryHandler(department_repo=repo)

        with pytest.raises(DepartmentNotFoundError):
            handler.handle(GetDepartmentQuery(department_id="bad", company_id="comp1"))
