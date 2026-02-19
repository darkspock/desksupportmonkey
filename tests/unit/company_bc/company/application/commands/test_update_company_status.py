from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.update_company_status import (
    CompanyNotFoundError,
    UpdateCompanyStatusCommand,
    UpdateCompanyStatusCommandHandler,
)
from src.company_bc.company.domain.entities import Company, InvalidStatusTransitionError
from src.company_bc.company.domain.enums import CompanyStatus


@pytest.fixture
def handler():
    return UpdateCompanyStatusCommandHandler(company_repo=MagicMock())


class TestUpdateCompanyStatusCommand:
    def test_successful_status_change(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler.company_repo.find_by_id.return_value = company

        handler.handle(
            UpdateCompanyStatusCommand(company_id=company.id, new_status="suspended")
        )

        handler.company_repo.save.assert_called_once()

    def test_company_not_found(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                UpdateCompanyStatusCommand(company_id="nonexistent", new_status="suspended")
            )

    def test_invalid_transition(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        company.change_status(CompanyStatus.DEACTIVATED)
        handler.company_repo.find_by_id.return_value = company

        with pytest.raises(InvalidStatusTransitionError):
            handler.handle(
                UpdateCompanyStatusCommand(company_id=company.id, new_status="active")
            )

    def test_invalid_status_string(self, handler):
        company = Company.create(name="Acme", email_domains=["acme.com"])
        handler.company_repo.find_by_id.return_value = company

        with pytest.raises(ValueError):
            handler.handle(
                UpdateCompanyStatusCommand(company_id=company.id, new_status="invalid")
            )
