from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.company_bc.company.application.services.stripe_webhook_dispatcher import (
    StripeWebhookDispatcher,
)
from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier
from src.company_bc.company.domain.entities import Company


def _make_company(stripe_customer_id: str = "cus_abc") -> Company:
    c = Company.create(name="Acme", email_domains=["acme.com"])
    c.stripe_customer_id = stripe_customer_id
    return c


def _checkout_event(customer: str = "cus_abc", subscription: str = "sub_123", plan: str = "premium") -> dict:
    return {
        "id": "evt_checkout_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": customer,
                "subscription": subscription,
                "metadata": {"plan": plan},
            }
        },
    }


def _subscription_updated_event(customer: str = "cus_abc", status: str = "active", plan: str = "premium") -> dict:
    import time
    return {
        "id": "evt_sub_updated_001",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "customer": customer,
                "id": "sub_123",
                "status": status,
                "current_period_end": int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp()),
                "metadata": {"plan": plan},
            }
        },
    }


def _subscription_deleted_event(customer: str = "cus_abc") -> dict:
    return {
        "id": "evt_sub_deleted_001",
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": customer}},
    }


def _invoice_paid_event(customer: str = "cus_abc") -> dict:
    return {
        "id": "evt_invoice_paid_001",
        "type": "invoice.payment_succeeded",
        "data": {"object": {"customer": customer}},
    }


def _invoice_failed_event(customer: str = "cus_abc") -> dict:
    return {
        "id": "evt_invoice_failed_001",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": customer}},
    }


@pytest.fixture
def dispatcher():
    repo = MagicMock()
    repo.is_stripe_event_processed.return_value = False
    return StripeWebhookDispatcher(company_repo=repo)


class TestStripeWebhookDispatcherRouting:
    def test_checkout_completed_activates_subscription(self, dispatcher):
        company = _make_company()
        dispatcher.company_repo.find_by_stripe_customer_id.return_value = company

        dispatcher.dispatch(_checkout_event(plan="premium"))

        assert company.plan == PlanTier.PREMIUM
        assert company.billing_status == BillingStatus.ACTIVE
        dispatcher.company_repo.mark_stripe_event_processed.assert_called_once_with("evt_checkout_001")

    def test_subscription_updated_syncs_plan(self, dispatcher):
        company = _make_company()
        dispatcher.company_repo.find_by_stripe_customer_id.return_value = company

        dispatcher.dispatch(_subscription_updated_event(plan="enterprise"))

        assert company.plan == PlanTier.ENTERPRISE
        dispatcher.company_repo.mark_stripe_event_processed.assert_called_once()

    def test_subscription_updated_past_due_enters_grace_period(self, dispatcher):
        company = _make_company()
        dispatcher.company_repo.find_by_stripe_customer_id.return_value = company

        dispatcher.dispatch(_subscription_updated_event(status="past_due"))

        assert company.billing_status == BillingStatus.GRACE_PERIOD

    def test_subscription_deleted_cancels_plan(self, dispatcher):
        company = _make_company()
        company.plan = PlanTier.PREMIUM
        dispatcher.company_repo.find_by_stripe_customer_id.return_value = company

        dispatcher.dispatch(_subscription_deleted_event())

        assert company.plan == PlanTier.FREE
        assert company.stripe_subscription_id is None

    def test_invoice_payment_succeeded_restores_billing(self, dispatcher):
        company = _make_company()
        company.enter_grace_period()
        dispatcher.company_repo.find_by_stripe_customer_id.return_value = company

        dispatcher.dispatch(_invoice_paid_event())

        assert company.billing_status == BillingStatus.ACTIVE

    def test_invoice_payment_failed_logs_no_state_change(self, dispatcher):
        dispatcher.dispatch(_invoice_failed_event())
        # No company lookup
        dispatcher.company_repo.find_by_stripe_customer_id.assert_not_called()
        dispatcher.company_repo.mark_stripe_event_processed.assert_called_once()

    def test_unknown_event_type_ignored_silently(self, dispatcher):
        event = {"id": "evt_unknown", "type": "unknown.event.type", "data": {"object": {}}}
        dispatcher.dispatch(event)
        dispatcher.company_repo.find_by_stripe_customer_id.assert_not_called()
        dispatcher.company_repo.mark_stripe_event_processed.assert_called_once_with("evt_unknown")


class TestStripeWebhookDispatcherIdempotency:
    def test_duplicate_event_returns_immediately_without_dispatch(self, dispatcher):
        dispatcher.company_repo.is_stripe_event_processed.return_value = True

        dispatcher.dispatch(_checkout_event())

        dispatcher.company_repo.find_by_stripe_customer_id.assert_not_called()
        dispatcher.company_repo.mark_stripe_event_processed.assert_not_called()
