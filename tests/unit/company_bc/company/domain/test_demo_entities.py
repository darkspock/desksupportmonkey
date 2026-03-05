"""Unit tests for Company DEMO plan domain logic."""

from datetime import datetime, timedelta, timezone

import pytest

from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.entities import Company
from src.company_bc.company.domain.enums import CompanyStatus


class TestCompanyCreateDemo:
    def test_create_demo_sets_demo_plan(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        assert company.plan == PlanTier.DEMO

    def test_create_demo_sets_trial_ends_at_14_days(self):
        before = datetime.now(timezone.utc)
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        after = datetime.now(timezone.utc)
        assert company.trial_ends_at is not None
        assert before + timedelta(days=14) <= company.trial_ends_at <= after + timedelta(days=14)

    def test_create_non_demo_does_not_set_demo_plan(self):
        company = Company.create(name="Real Co", email_domains=["real.com"])
        assert company.plan == PlanTier.FREE


class TestIsDemoAccount:
    def test_is_demo_account_true_for_demo_plan(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        assert company.is_demo_account is True

    def test_is_demo_account_false_for_free_plan(self):
        company = Company.create(name="Real Co", email_domains=["real.com"])
        assert company.is_demo_account is False


class TestDemoDaysRemaining:
    def test_returns_none_for_non_demo(self):
        company = Company.create(name="Real Co", email_domains=["real.com"])
        assert company.demo_days_remaining is None

    def test_returns_none_for_demo_without_trial_ends_at(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        company.trial_ends_at = None
        assert company.demo_days_remaining is None

    def test_returns_days_for_active_demo(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        # trial_ends_at is 14 days from now
        remaining = company.demo_days_remaining
        assert remaining is not None
        assert 13 <= remaining <= 14

    def test_returns_zero_for_expired_demo(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        company.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
        assert company.demo_days_remaining == 0

    def test_handles_naive_trial_ends_at(self):
        company = Company.create(
            name="Demo Co", email_domains=["demo.local"], is_demo=True,
        )
        # Simulate a naive datetime from the database
        company.trial_ends_at = datetime.utcnow() + timedelta(days=7)
        remaining = company.demo_days_remaining
        assert remaining is not None
        assert 6 <= remaining <= 7


class TestActivateFromDemo:
    def _make_demo(self) -> Company:
        return Company.create(
            name="Demo Co (Demo)", email_domains=["demo.local"], is_demo=True,
        )

    def test_changes_plan_to_free(self):
        company = self._make_demo()
        company.activate_from_demo()
        assert company.plan == PlanTier.FREE

    def test_sets_trial_ends_at_15_days(self):
        company = self._make_demo()
        before = datetime.now(timezone.utc)
        company.activate_from_demo()
        after = datetime.now(timezone.utc)
        assert company.trial_ends_at is not None
        assert before + timedelta(days=15) <= company.trial_ends_at <= after + timedelta(days=15)

    def test_updates_name(self):
        company = self._make_demo()
        company.activate_from_demo(name="Real Company")
        assert company.name == "Real Company"

    def test_strips_name(self):
        company = self._make_demo()
        company.activate_from_demo(name="  Real Company  ")
        assert company.name == "Real Company"

    def test_updates_email_domains(self):
        company = self._make_demo()
        company.activate_from_demo(email_domains=["realco.com"])
        assert company.email_domains == ["realco.com"]

    def test_raises_for_non_demo(self):
        company = Company.create(name="Real Co", email_domains=["real.com"])
        with pytest.raises(ValueError, match="not a demo account"):
            company.activate_from_demo()

    def test_raises_for_empty_name(self):
        company = self._make_demo()
        with pytest.raises(ValueError, match="Company name is required"):
            company.activate_from_demo(name="   ")

    def test_raises_for_empty_domains(self):
        company = self._make_demo()
        with pytest.raises(ValueError, match="At least one email domain"):
            company.activate_from_demo(email_domains=[])

    def test_keeps_name_when_not_provided(self):
        company = self._make_demo()
        original_name = company.name
        company.activate_from_demo()
        assert company.name == original_name

    def test_keeps_domains_when_not_provided(self):
        company = self._make_demo()
        original_domains = company.email_domains[:]
        company.activate_from_demo()
        assert company.email_domains == original_domains
