from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.queries.get_company import (
    CompanyNotFoundError,
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.application.queries.list_companies import (
    ListCompaniesQuery,
    ListCompaniesQueryHandler,
)
from src.company_bc.company.domain.entities import Company


class TestListCompaniesQuery:
    def test_returns_paginated_results(self):
        companies = [
            Company.create(name="A", email_domains=["a.com"]),
            Company.create(name="B", email_domains=["b.com"]),
        ]
        handler = ListCompaniesQueryHandler(company_repo=MagicMock())
        handler.company_repo.find_all_with_counts.return_value = (
            [(c, 0, 0) for c in companies],
            2,
        )

        result, total = handler.handle(ListCompaniesQuery(page=1, page_size=20))

        assert len(result) == 2
        assert total == 2
        handler.company_repo.find_all_with_counts.assert_called_once_with(
            page=1, page_size=20, search=None, in_trial=None, plan=None
        )


class TestGetCompanyQuery:
    def test_returns_detail_with_counts(self):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler = GetCompanyQueryHandler(company_repo=MagicMock())
        handler.company_repo.find_by_id.return_value = company
        handler.company_repo.count_users.return_value = 5
        handler.company_repo.count_departments.return_value = 3

        detail = handler.handle(GetCompanyQuery(company_id=company.id))

        assert detail.company.name == "Acme"
        assert detail.user_count == 5
        assert detail.department_count == 3

    def test_not_found_raises(self):
        handler = GetCompanyQueryHandler(company_repo=MagicMock())
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(GetCompanyQuery(company_id="nonexistent"))
