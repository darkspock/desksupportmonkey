import logging

import stripe

from core.stripe_client import StripeUnavailableError
from src.company_bc.company.domain.billing_enums import PlanTier

logger = logging.getLogger(__name__)


class StripeBillingService:
    def __init__(self, secret_key: str, open_source_mode: bool = False) -> None:
        self._open_source_mode = open_source_mode
        if not open_source_mode:
            stripe.api_key = secret_key

    def create_checkout_session(
        self,
        stripe_customer_id: str,
        target_plan: PlanTier,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        if self._open_source_mode:
            return ""
        try:
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={"plan": target_plan.value},
            )
            return session.url or ""
        except stripe.StripeError as exc:
            logger.error("Stripe checkout session error: %s", exc)
            raise StripeUnavailableError(str(exc)) from exc

    def create_portal_session(self, stripe_customer_id: str, return_url: str) -> str:
        if self._open_source_mode:
            return ""
        try:
            session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=return_url,
            )
            return session.url
        except stripe.StripeError as exc:
            logger.error("Stripe portal session error: %s", exc)
            raise StripeUnavailableError(str(exc)) from exc
