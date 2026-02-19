from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.update_company import (
    CompanyNameExistsError,
    CompanyNotFoundError,
    DomainAlreadyTakenError,
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def handler():
    return UpdateCompanyCommandHandler(company_repo=MagicMock())


@pytest.fixture
def existing_company():
    return Company.create(name="Acme Corp", email_domains=["acme.com"])


class TestUpdateCompanyCommand:
    def test_update_name_only(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.find_by_name.return_value = None

        handler.handle(
            UpdateCompanyCommand(company_id=existing_company.id, name="New Acme")
        )

        handler.company_repo.save.assert_called_once()

    def test_update_domains_only(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.find_domain.return_value = None

        handler.handle(
            UpdateCompanyCommand(
                company_id=existing_company.id,
                email_domains=["new.com", "new.co.uk"],
            )
        )

        handler.company_repo.save.assert_called_once()
        handler.company_repo.save_domains.assert_called_once()

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(UpdateCompanyCommand(company_id="nonexistent", name="X"))

    def test_duplicate_name_raises(self, handler, existing_company):
        other = Company.create(name="Other Corp", email_domains=["other.com"])
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.find_by_name.return_value = other

        with pytest.raises(CompanyNameExistsError):
            handler.handle(
                UpdateCompanyCommand(company_id=existing_company.id, name="Other Corp")
            )

    def test_duplicate_domain_raises(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.find_domain.return_value = "other-company-id"

        with pytest.raises(DomainAlreadyTakenError):
            handler.handle(
                UpdateCompanyCommand(
                    company_id=existing_company.id, email_domains=["taken.com"]
                )
            )

    def test_same_name_no_conflict(self, handler, existing_company):
        handler.company_repo.find_by_id.return_value = existing_company
        handler.company_repo.find_by_name.return_value = existing_company

        handler.handle(
            UpdateCompanyCommand(company_id=existing_company.id, name="Acme Corp")
        )
        handler.company_repo.save.assert_called_once()
