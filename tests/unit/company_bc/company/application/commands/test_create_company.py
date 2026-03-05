from unittest.mock import MagicMock, patch

import pytest

from core.stripe_client import StripeUnavailableError
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def stripe_client():
    mock = MagicMock()
    mock.create_customer.return_value = "cus_test123"
    return mock


@pytest.fixture
def handler(stripe_client):
    company_repo = MagicMock()
    company_repo.slug_exists.return_value = False
    return CreateCompanyCommandHandler(
        company_repo=company_repo,
        user_repo=MagicMock(),
        magic_link_repo=MagicMock(),
        email_service=MagicMock(),
        stripe_client=stripe_client,
    )


class TestCreateCompanyCommand:
    def test_successful_creation_no_admin(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None

        handler.handle(
            CreateCompanyCommand(name="Acme Corp", email_domains=["acme.com"])
        )

        # save() called twice: initial save + after setting stripe_customer_id
        assert handler.company_repo.save.call_count == 2
        handler.company_repo.save_domains.assert_called_once()
        handler.user_repo.save.assert_not_called()

    def test_successful_creation_with_admin(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None
        handler.user_repo.find_by_email.return_value = None

        handler.handle(
            CreateCompanyCommand(
                name="Acme Corp",
                email_domains=["acme.com"],
                admin_email="admin@acme.com",
            )
        )

        # save() called twice: initial save + after setting stripe_customer_id
        assert handler.company_repo.save.call_count == 2
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

        handler.handle(
            CreateCompanyCommand(
                name="New Corp",
                email_domains=["foo.bar"],
                admin_email="admin@gmail.com",
            )
        )

        assert handler.company_repo.save.call_count == 2

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

    def test_domains_with_leading_at_are_normalized(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None

        handler.handle(
            CreateCompanyCommand(name="Acme Corp", email_domains=["@acme.tech"])
        )

        saved_company = handler.company_repo.save.call_args[0][0]
        assert saved_company.email_domains == ["acme.tech"]
        handler.company_repo.find_domain.assert_called_once_with("acme.tech")
        handler.company_repo.save_domains.assert_called_once_with(saved_company.id, ["acme.tech"])


class TestCreateCompanyBillingExtension:
    def test_stripe_customer_id_persisted(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None

        handler.handle(
            CreateCompanyCommand(name="Acme Corp", email_domains=["acme.com"])
        )

        # save() called twice: first save, then with stripe_customer_id
        assert handler.company_repo.save.call_count == 2
        second_save_company = handler.company_repo.save.call_args_list[1][0][0]
        assert second_save_company.stripe_customer_id == "cus_test123"

    def test_stripe_unavailable_propagates(self, handler):
        handler.company_repo.find_by_name.return_value = None
        handler.company_repo.find_domain.return_value = None
        handler.stripe_client.create_customer.side_effect = StripeUnavailableError("Stripe down")

        with pytest.raises(StripeUnavailableError):
            handler.handle(
                CreateCompanyCommand(name="Acme Corp", email_domains=["acme.com"])
            )
