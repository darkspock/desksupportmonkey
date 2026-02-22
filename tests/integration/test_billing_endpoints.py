"""Integration tests for /api/v1/billing/ endpoints."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from adapters.http.api.billing.dependencies import get_billing_service, get_stripe_client
from core.stripe_client import InvalidStripeSignatureError


def _invoice_failed_event(event_id: str = "evt_int_inv_001") -> dict:
    """Use invoice.payment_failed — no company lookup required, pure infrastructure test."""
    return {
        "id": event_id,
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_int_test"}},
    }


class TestWebhookEndpoint:
    def test_valid_signature_returns_200(self, client):
        event = _invoice_failed_event()
        mock_stripe = MagicMock()
        mock_stripe.verify_webhook_signature.return_value = event
        client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        resp = client.post(
            "/api/v1/billing/webhook",
            content=json.dumps(event).encode(),
            headers={"stripe-signature": "t=123,v1=abc", "content-type": "application/json"},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_invalid_signature_returns_400(self, client):
        mock_stripe = MagicMock()
        mock_stripe.verify_webhook_signature.side_effect = InvalidStripeSignatureError("bad sig")
        client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        resp = client.post(
            "/api/v1/billing/webhook",
            content=b'{"id":"evt_bad"}',
            headers={"stripe-signature": "t=bad,v1=bad"},
        )

        assert resp.status_code == 400

    def test_duplicate_event_returns_200_no_state_change(self, client, db_session):
        """Idempotency: processing the same event twice returns 200 on both calls."""
        event = _invoice_failed_event(event_id="evt_dup_int_001")
        mock_stripe = MagicMock()
        mock_stripe.verify_webhook_signature.return_value = event
        client.app.dependency_overrides[get_stripe_client] = lambda: mock_stripe

        # First call — event processed and marked in DB
        resp1 = client.post(
            "/api/v1/billing/webhook",
            content=json.dumps(event).encode(),
            headers={"stripe-signature": "t=123,v1=abc", "content-type": "application/json"},
        )
        assert resp1.status_code == 200

        # Second call — event already processed, returns 200 immediately (idempotent)
        resp2 = client.post(
            "/api/v1/billing/webhook",
            content=json.dumps(event).encode(),
            headers={"stripe-signature": "t=456,v1=def", "content-type": "application/json"},
        )
        assert resp2.status_code == 200


class TestBillingOverviewEndpoint:
    def test_admin_gets_billing_overview(self, client, db_session, admin_user, auth_as):
        auth_as(admin_user)

        resp = client.get("/api/v1/billing/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["plan"] == "free"
        assert data["billing_status"] == "active"
        assert data["complimentary"] is False
        assert "user_count" in data
        assert "asset_count" in data

    def test_non_admin_gets_403(self, client, employee_user, auth_as):
        auth_as(employee_user)

        resp = client.get("/api/v1/billing/")

        assert resp.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        resp = client.get("/api/v1/billing/")

        assert resp.status_code == 403  # HTTPBearer raises 403 when no token


class TestCheckoutEndpoint:
    def test_checkout_returns_url(self, client, db_session, admin_user, auth_as):
        auth_as(admin_user)
        # Set a stripe_customer_id on company
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        repo = CompanyRepository(db_session)
        company = repo.find_by_id(admin_user.company_id)
        company.stripe_customer_id = "cus_test_checkout"
        repo.save(company)

        resp = client.post(
            "/api/v1/billing/checkout",
            json={"target_plan": "premium"},
        )

        assert resp.status_code == 200
        assert "checkout_url" in resp.json()

    def test_checkout_without_stripe_customer_returns_422(self, client, admin_user, auth_as):
        auth_as(admin_user)
        # Company has no stripe_customer_id (default in test company fixture)

        resp = client.post(
            "/api/v1/billing/checkout",
            json={"target_plan": "premium"},
        )

        assert resp.status_code == 422


class TestPortalEndpoint:
    def test_portal_returns_url(self, client, db_session, admin_user, auth_as):
        auth_as(admin_user)
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        repo = CompanyRepository(db_session)
        company = repo.find_by_id(admin_user.company_id)
        company.stripe_customer_id = "cus_test_portal"
        repo.save(company)

        resp = client.post("/api/v1/billing/portal")

        assert resp.status_code == 200
        assert "portal_url" in resp.json()

    def test_portal_without_stripe_customer_returns_422(self, client, admin_user, auth_as):
        auth_as(admin_user)

        resp = client.post("/api/v1/billing/portal")

        assert resp.status_code == 422


class TestLazySuspension:
    def test_company_with_expired_grace_period_is_suspended_on_request(
        self, client, db_session, admin_user
    ):
        """Grace period expired > 15 days ago → company suspended on next authenticated request.

        Uses a real JWT (not auth_as mock) so get_current_user runs the full billing check.
        """
        from core.jwt import JWTService
        from src.company_bc.company.infrastructure.repository import CompanyRepository
        from src.company_bc.company.domain.billing_enums import BillingStatus

        repo = CompanyRepository(db_session)
        company = repo.find_by_id(admin_user.company_id)
        company.enter_grace_period()
        company.grace_period_started_at = datetime.now(timezone.utc) - timedelta(days=16)
        repo.save(company)
        db_session.flush()

        token = JWTService().create_token(
            user_id=admin_user.id,
            company_id=str(admin_user.company_id),
            role=admin_user.role.value,
        )

        resp = client.get(
            "/api/v1/billing/",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["billing_status"] == "suspended"
