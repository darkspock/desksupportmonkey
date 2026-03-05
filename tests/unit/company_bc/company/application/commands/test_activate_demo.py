"""Unit tests for ActivateDemoCommand + Handler."""

from unittest.mock import MagicMock

import pytest

from src.company_bc.company.application.commands.activate_demo import (
    ActivateDemoCommand,
    ActivateDemoCommandHandler,
    CompanyNotFoundError,
    NotDemoAccountError,
)
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.entities import Company


@pytest.fixture
def stripe_client():
    mock = MagicMock()
    mock.create_customer.return_value = "cus_demo_activated"
    return mock


@pytest.fixture
def demo_company():
    return Company.create(
        name="Demo Co (Demo)", email_domains=["demo.local"], is_demo=True,
    )


@pytest.fixture
def handler(stripe_client, demo_company):
    company_repo = MagicMock()
    company_repo.find_by_id.return_value = demo_company
    return ActivateDemoCommandHandler(
        company_repo=company_repo,
        stripe_client=stripe_client,
    )


class TestActivateDemoCommand:
    def test_happy_path_activates_demo(self, handler, demo_company, stripe_client):
        handler.handle(
            ActivateDemoCommand(
                company_id=demo_company.id,
                company_name="Real Company",
                email_domains=["realco.com"],
            )
        )

        assert demo_company.plan == PlanTier.FREE
        assert demo_company.name == "Real Company"
        assert demo_company.email_domains == ["realco.com"]
        assert demo_company.stripe_customer_id == "cus_demo_activated"
        handler.company_repo.save.assert_called_once()
        handler.company_repo.save_domains.assert_called_once()
        stripe_client.create_customer.assert_called_once()

    def test_happy_path_without_name_change(self, handler, demo_company):
        original_name = demo_company.name
        handler.handle(
            ActivateDemoCommand(company_id=demo_company.id),
        )

        assert demo_company.plan == PlanTier.FREE
        assert demo_company.name == original_name
        handler.company_repo.save_domains.assert_not_called()

    def test_creates_stripe_customer(self, handler, demo_company, stripe_client):
        handler.handle(
            ActivateDemoCommand(company_id=demo_company.id),
        )

        stripe_client.create_customer.assert_called_once_with(
            name=demo_company.name,
            email="",
            metadata={"company_id": demo_company.id},
        )

    def test_company_not_found_raises(self, handler):
        handler.company_repo.find_by_id.return_value = None

        with pytest.raises(CompanyNotFoundError):
            handler.handle(
                ActivateDemoCommand(company_id="nonexistent"),
            )

    def test_non_demo_company_raises(self, handler):
        free_company = Company.create(
            name="Real Co", email_domains=["real.com"],
        )
        handler.company_repo.find_by_id.return_value = free_company

        with pytest.raises(NotDemoAccountError):
            handler.handle(
                ActivateDemoCommand(company_id=free_company.id),
            )

    def test_keep_demo_data_default_true(self, handler, demo_company):
        cmd = ActivateDemoCommand(company_id=demo_company.id)
        assert cmd.keep_demo_data is True

    def test_invalid_email_domains_raises(self, handler, demo_company):
        with pytest.raises(ValueError, match="At least one email domain"):
            handler.handle(
                ActivateDemoCommand(
                    company_id=demo_company.id,
                    email_domains=[],
                ),
            )

    def test_empty_name_raises(self, handler, demo_company):
        with pytest.raises(ValueError, match="Company name is required"):
            handler.handle(
                ActivateDemoCommand(
                    company_id=demo_company.id,
                    company_name="   ",
                ),
            )

    def test_does_not_save_domains_when_not_changed(self, handler, demo_company):
        handler.handle(
            ActivateDemoCommand(
                company_id=demo_company.id,
                company_name="New Name",
            ),
        )

        handler.company_repo.save_domains.assert_not_called()
