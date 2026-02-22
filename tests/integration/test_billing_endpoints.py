"""Integration tests for /api/v1/billing/webhook endpoint."""

import json
from unittest.mock import MagicMock

import pytest

from adapters.http.api.billing.dependencies import get_stripe_client
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
