from unittest.mock import MagicMock, patch

import pytest

from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus


@pytest.fixture
def handler():
    return CreateCompanyCommandHandler(
        company_repo=MagicMock(),
        user_repo=MagicMock(),
        magic_link_repo=MagicMock(),
        email_service=MagicMock(),
    )


class TestCreateCompanyCommand:
    def test_successful_creation_no_admin(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None

        result = handler.handle(
            CreateCompanyCommand(name="Acme Corp", email_domains=["acme.com"])
        )

        assert result.name == "Acme Corp"
        assert result.status == CompanyStatus.ACTIVE
        assert result.email_domains == ["acme.com"]
        handler.company_repo.save.assert_called_once()
        handler.company_repo.save_domains.assert_called_once()
        handler.user_repo.save.assert_not_called()

    def test_successful_creation_with_admin(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None
        handler.user_repo.find_by_email.return_value = None

        result = handler.handle(
            CreateCompanyCommand(
                name="Acme Corp",
                email_domains=["acme.com"],
                admin_email="admin@acme.com",
            )
        )

        assert result.name == "Acme Corp"
        handler.user_repo.save.assert_called_once()
        handler.magic_link_repo.save.assert_called_once()
        handler.email_service.send.assert_called_once()

    def test_duplicate_name_raises(self, handler):
        handler.company_repo.find_by_name.return_value = Company.create(
            name="Acme Corp", email_domains=["old.com"]
        )

        with pytest.raises(CompanyNameExistsError):
            handler.handle(
                CreateCompanyCommand(name="Acme Corp", email_domains=["acme.com"])
            )

    def test_duplicate_domain_raises(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = "other-company-id"

        with pytest.raises(DomainAlreadyTakenError) as exc_info:
            handler.handle(
                CreateCompanyCommand(name="New Corp", email_domains=["taken.com"])
            )
        assert "taken.com" in str(exc_info.value)

    def test_admin_domain_not_auto_added_to_company(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None
        handler.user_repo.find_by_email.return_value = None

        result = handler.handle(
            CreateCompanyCommand(
                name="New Corp",
                email_domains=["foo.bar"],
                admin_email="admin@gmail.com",
            )
        )

        assert "gmail.com" not in result.email_domains
        assert result.email_domains == ["foo.bar"]

    def test_admin_email_user_exists_raises(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None
        handler.user_repo.find_by_email.return_value = MagicMock()

        with pytest.raises(UserAlreadyExistsError):
            handler.handle(
                CreateCompanyCommand(
                    name="Acme",
                    email_domains=["acme.com"],
                    admin_email="existing@acme.com",
                )
            )
