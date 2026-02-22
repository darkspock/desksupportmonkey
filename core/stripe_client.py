import logging

import stripe

logger = logging.getLogger(__name__)


class StripeUnavailableError(Exception):
    pass


class InvalidStripeSignatureError(Exception):
    pass


class StripeClient:
    def __init__(self, secret_key: str, open_source_mode: bool = False) -> None:
        self._open_source_mode = open_source_mode
        if not open_source_mode and secret_key:
            stripe.api_key = secret_key

    def create_customer(self, name: str, email: str, metadata: dict) -> str:
        if self._open_source_mode:
            return ""
        try:
            customer = stripe.Customer.create(name=name, email=email, metadata=metadata)
            return customer.id
        except stripe.error.StripeError as exc:
            logger.error("Stripe error creating customer: %s", exc)
            raise StripeUnavailableError("Stripe is unavailable") from exc

    def cancel_subscription(self, subscription_id: str) -> None:
        if self._open_source_mode:
            return
        try:
            stripe.Subscription.cancel(subscription_id)
        except stripe.error.StripeError as exc:
            logger.error("Stripe error cancelling subscription %s: %s", subscription_id, exc)
            raise StripeUnavailableError("Stripe is unavailable") from exc
