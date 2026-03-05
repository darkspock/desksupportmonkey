from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.update_company_slug import (
    CompanyNotFoundError,
    UpdateCompanySlugCommand,
    UpdateCompanySlugCommandHandler,
)
from src.company_bc.company.domain.entities import Company, SlugAlreadyTakenError


@pytest.fixture
def handler():
    return UpdateCompanySlugCommandHandler(company_repo=MagicMock())


@pytest.fixture
def existing_company():
    company = Company.create(name="Acme Corp", email_domains=["acme.com"])
    company.slug = "acme-corp"
    return company


class TestUpdateCompanySlugCommand:
    def test_update_slug_success(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.slug_exists.return_value = False

        handler.handle(
            UpdateCompanySlugCommand(
                company_id=existing_company.id, slug="new-acme"
            )
        )

        handler.company_repo.save.assert_called_once()
        assert existing_company.slug == "new-acme"

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                UpdateCompanySlugCommand(company_id="nonexistent", slug="test")
            )

    def test_invalid_slug_format_raises(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        with pytest.raises(ValueError, match="lowercase alphanumeric"):
            handler.handle(
                UpdateCompanySlugCommand(
                    company_id=existing_company.id, slug="INVALID"
                )
            )

    def test_reserved_slug_raises(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company

        with pytest.raises(ValueError, match="reserved"):
            handler.handle(
                UpdateCompanySlugCommand(
                    company_id=existing_company.id, slug="admin"
                )
            )

    def test_slug_already_taken_raises(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.slug_exists.return_value = True

        with pytest.raises(SlugAlreadyTakenError):
            handler.handle(
                UpdateCompanySlugCommand(
                    company_id=existing_company.id, slug="taken-slug"
                )
            )

    def test_slug_exists_called_with_exclude(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.slug_exists.return_value = False

        handler.handle(
            UpdateCompanySlugCommand(
                company_id=existing_company.id, slug="new-slug"
            )
        )

        handler.company_repo.slug_exists.assert_called_once_with(
            "new-slug", exclude_company_id=existing_company.id
        )
