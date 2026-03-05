"""Unit tests for ListUserCompaniesQueryHandler."""

from unittest.mock import MagicMock

from src.auth_bc.company_user.domain.entities import CompanyUser
from src.auth_bc.user.application.queries.list_user_companies import (
    ListUserCompaniesQuery,
    ListUserCompaniesQueryHandler,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole


def _make_user(company_id="comp-a"):
    return User(
        id="user-1",
        email="alice@example.com",
        role=UserRole.ADMIN,
        company_id=company_id,
    )


def _make_membership(company_id, role=UserRole.EMPLOYEE, is_active=True):
    cu = CompanyUser.create(user_id="user-1", company_id=company_id, role=role)
    if not is_active:
        cu.deactivate()
    return cu


def _make_company(company_id, name, slug, is_active=True):
    mock = MagicMock()
    mock.id = company_id
    mock.name = name
    mock.slug = slug
    mock.is_active = is_active
    return mock


class TestListUserCompaniesQueryHandler:
    def test_returns_active_memberships_with_company_data(self):
        user = _make_user(company_id="comp-a")
        memberships = [
            _make_membership("comp-a", role=UserRole.ADMIN),
            _make_membership("comp-b", role=UserRole.EMPLOYEE),
        ]
        companies = [
            _make_company("comp-a", "Company A", "company-a"),
            _make_company("comp-b", "Company B", "company-b"),
        ]

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_active_by_user_id.return_value = memberships
        company_repo = MagicMock()
        company_repo.find_by_ids.return_value = companies

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        result = handler.handle(ListUserCompaniesQuery(user_id="user-1"))

        assert len(result) == 2
        assert result[0].company_id == "comp-a"
        assert result[0].company_name == "Company A"
        assert result[0].slug == "company-a"
        assert result[0].role == "admin"
        assert result[1].company_id == "comp-b"
        assert result[1].role == "employee"

    def test_is_current_flag_matches_user_company_id(self):
        user = _make_user(company_id="comp-a")
        memberships = [
            _make_membership("comp-a"),
            _make_membership("comp-b"),
        ]
        companies = [
            _make_company("comp-a", "A", "a"),
            _make_company("comp-b", "B", "b"),
        ]

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_active_by_user_id.return_value = memberships
        company_repo = MagicMock()
        company_repo.find_by_ids.return_value = companies

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        result = handler.handle(ListUserCompaniesQuery(user_id="user-1"))

        current = [d for d in result if d.is_current]
        not_current = [d for d in result if not d.is_current]
        assert len(current) == 1
        assert current[0].company_id == "comp-a"
        assert len(not_current) == 1
        assert not_current[0].company_id == "comp-b"

    def test_filters_out_inactive_companies(self):
        user = _make_user(company_id="comp-a")
        memberships = [
            _make_membership("comp-a"),
            _make_membership("comp-inactive"),
        ]
        companies = [
            _make_company("comp-a", "A", "a", is_active=True),
            _make_company("comp-inactive", "Inactive", "inactive", is_active=False),
        ]

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_active_by_user_id.return_value = memberships
        company_repo = MagicMock()
        company_repo.find_by_ids.return_value = companies

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        result = handler.handle(ListUserCompaniesQuery(user_id="user-1"))

        assert len(result) == 1
        assert result[0].company_id == "comp-a"

    def test_returns_empty_for_user_not_found(self):
        user_repo = MagicMock()
        user_repo.find_by_id.return_value = None
        company_user_repo = MagicMock()
        company_repo = MagicMock()

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        result = handler.handle(ListUserCompaniesQuery(user_id="nonexistent"))

        assert result == []
        company_user_repo.find_active_by_user_id.assert_not_called()

    def test_returns_empty_for_no_memberships(self):
        user = _make_user()
        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_active_by_user_id.return_value = []
        company_repo = MagicMock()

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        result = handler.handle(ListUserCompaniesQuery(user_id="user-1"))

        assert result == []
        company_repo.find_by_ids.assert_not_called()

    def test_batch_fetches_companies(self):
        user = _make_user()
        memberships = [
            _make_membership("comp-a"),
            _make_membership("comp-b"),
            _make_membership("comp-c"),
        ]
        companies = [
            _make_company("comp-a", "A", "a"),
            _make_company("comp-b", "B", "b"),
            _make_company("comp-c", "C", "c"),
        ]

        user_repo = MagicMock()
        user_repo.find_by_id.return_value = user
        company_user_repo = MagicMock()
        company_user_repo.find_active_by_user_id.return_value = memberships
        company_repo = MagicMock()
        company_repo.find_by_ids.return_value = companies

        handler = ListUserCompaniesQueryHandler(
            company_user_repo=company_user_repo,
            company_repo=company_repo,
            user_repo=user_repo,
        )
        handler.handle(ListUserCompaniesQuery(user_id="user-1"))

        # Verify batch fetch called once with all IDs
        company_repo.find_by_ids.assert_called_once_with(
            ["comp-a", "comp-b", "comp-c"]
        )
