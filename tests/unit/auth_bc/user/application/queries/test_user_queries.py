from unittest.mock import MagicMock

import pytest

from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.queries.list_users import (
    ListUsersQuery,
    ListUsersQueryHandler,
)
from src.auth_bc.user.application.queries.get_user_detail import (
    GetUserDetailQuery,
    GetUserDetailQueryHandler,
    UserNotFoundError,
)


def _make_user():
    return User.create(email="test@example.com", role=UserRole.EMPLOYEE, company_id="comp1")


class TestListUsersQuery:
    def test_returns_paginated(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_all_by_company.return_value = ([user], 1)
        handler = ListUsersQueryHandler(user_repo=repo)

        users, total = handler.handle(
            ListUsersQuery(company_id="comp1", page=1, page_size=20)
        )

        assert len(users) == 1
        assert total == 1

    def test_with_filters(self):
        repo = MagicMock()
        repo.find_all_by_company.return_value = ([], 0)
        handler = ListUsersQueryHandler(user_repo=repo)

        handler.handle(
            ListUsersQuery(
                company_id="comp1", role="admin", is_active=True,
                department_id="dept1", search="john",
            )
        )

        repo.find_all_by_company.assert_called_once_with(
            company_id="comp1", page=1, page_size=20,
            role="admin", is_active=True,
            department_id="dept1", search="john",
        )


class TestGetUserDetailQuery:
    def test_success(self):
        user = _make_user()
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = user
        handler = GetUserDetailQueryHandler(user_repo=repo)

        result = handler.handle(
            GetUserDetailQuery(user_id=user.id, company_id="comp1")
        )

        assert result.email == "test@example.com"

    def test_not_found_raises(self):
        repo = MagicMock()
        repo.find_by_id_and_company.return_value = None
        handler = GetUserDetailQueryHandler(user_repo=repo)

        with pytest.raises(UserNotFoundError):
            handler.handle(GetUserDetailQuery(user_id="bad", company_id="comp1"))
