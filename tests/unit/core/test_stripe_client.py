from unittest.mock import MagicMock, patch

import pytest
import stripe

from core.stripe_client import StripeClient, StripeUnavailableError


class TestStripeClientCreateCustomer:
    @patch("stripe.Customer.create")
    def test_create_customer_returns_id(self, mock_create):
        mock_create.return_value = MagicMock(id="cus_abc123")
        client = StripeClient(secret_key="sk_test_xxx")

        result = client.create_customer(name="Acme", email="admin@acme.com", metadata={"company_id": "c1"})

        assert result == "cus_abc123"
        mock_create.assert_called_once_with(name="Acme", email="admin@acme.com", metadata={"company_id": "c1"})

    @patch("stripe.Customer.create")
    def test_open_source_mode_returns_empty_string_no_api_call(self, mock_create):
        client = StripeClient(secret_key="sk_test_xxx", open_source_mode=True)

        result = client.create_customer(name="Acme", email="admin@acme.com", metadata={})

        assert result == ""
        mock_create.assert_not_called()

    @patch("stripe.Customer.create", side_effect=stripe.error.StripeError("network error"))
    def test_stripe_error_raises_unavailable(self, mock_create):
        client = StripeClient(secret_key="sk_test_xxx")

        with pytest.raises(StripeUnavailableError):
            client.create_customer(name="Acme", email="admin@acme.com", metadata={})


class TestStripeClientCancelSubscription:
    @patch("stripe.Subscription.cancel")
    def test_open_source_mode_no_op(self, mock_cancel):
        client = StripeClient(secret_key="sk_test_xxx", open_source_mode=True)

        client.cancel_subscription("sub_abc123")

        mock_cancel.assert_not_called()

    @patch("stripe.Subscription.cancel")
    def test_cancel_subscription_calls_stripe(self, mock_cancel):
        client = StripeClient(secret_key="sk_test_xxx")

        client.cancel_subscription("sub_abc123")

        mock_cancel.assert_called_once_with("sub_abc123")

    @patch("stripe.Subscription.cancel", side_effect=stripe.error.StripeError("error"))
    def test_stripe_error_raises_unavailable(self, mock_cancel):
        client = StripeClient(secret_key="sk_test_xxx")

        with pytest.raises(StripeUnavailableError):
            client.cancel_subscription("sub_abc123")
