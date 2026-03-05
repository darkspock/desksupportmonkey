import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.company_bc.company.application.commands.billing.activate_subscription import (
    ActivateSubscriptionCommand,
    ActivateSubscriptionCommandHandler,
)
from src.company_bc.company.application.commands.billing.cancel_subscription import (
    CancelSubscriptionCommand,
    CancelSubscriptionCommandHandler,
)
from src.company_bc.company.application.commands.billing.restore_billing import (
    RestoreBillingCommand,
    RestoreBillingCommandHandler,
)
from src.company_bc.company.application.commands.billing.sync_plan_change import (
    SyncPlanChangeCommand,
    SyncPlanChangeCommandHandler,
)
from src.company_bc.company.domain.billing_enums import PlanTier
from src.company_bc.company.domain.repository import CompanyRepositoryInterface

logger = logging.getLogger(__name__)


def _parse_plan(metadata: dict) -> PlanTier:
    plan_str = metadata.get("plan", "")
    try:
        return PlanTier(plan_str)
    except ValueError:
        return PlanTier.PREMIUM


def _parse_optional_plan(metadata: dict, key: str) -> Optional[PlanTier]:
    plan_str = metadata.get(key)
    if not plan_str:
        return None
    try:
        return PlanTier(plan_str)
    except ValueError:
        return None


def _unix_to_datetime(ts: int) -> datetime:
    return datetime.fromtimestamp(ts, tz=timezone.utc)


class StripeWebhookDispatcher:
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
    ) -> None:
        self.company_repo = company_repo

    def dispatch(self, event: dict) -> None:
        event_id = event["id"]
        event_type = event["type"]

        # Idempotency check
        if self.company_repo.is_stripe_event_processed(event_id):
            logger.info("Stripe event already processed, skipping: %s", event_id)
            return

        try:
            self._route(event_type, event)
        except Exception as exc:
            logger.error("Error dispatching Stripe event %s (%s): %s", event_id, event_type, exc)
            raise

        self.company_repo.mark_stripe_event_processed(event_id)

    def _route(self, event_type: str, event: dict) -> None:
        obj = event["data"]["object"]

        if event_type == "checkout.session.completed":
            metadata = obj.get("metadata") or {}
            plan = _parse_plan(metadata)
            # current_period_end is not in checkout.session — use 30-day placeholder;
            # customer.subscription.updated fires right after and corrects it.
            period_end = datetime.now(timezone.utc) + timedelta(days=30)
            ActivateSubscriptionCommandHandler(self.company_repo).handle(
                ActivateSubscriptionCommand(
                    stripe_customer_id=obj["customer"],
                    stripe_subscription_id=obj["subscription"],
                    plan=plan,
                    current_period_end=period_end,
                )
            )

        elif event_type == "customer.subscription.updated":
            metadata = obj.get("metadata") or {}
            plan = _parse_plan(metadata)
            pending = _parse_optional_plan(metadata, "pending_downgrade_plan")
            period_end = _unix_to_datetime(obj["current_period_end"])
            SyncPlanChangeCommandHandler(self.company_repo).handle(
                SyncPlanChangeCommand(
                    stripe_customer_id=obj["customer"],
                    new_plan=plan,
                    subscription_status=obj["status"],
                    current_period_end=period_end,
                    pending_downgrade_plan=pending,
                )
            )

        elif event_type == "customer.subscription.deleted":
            CancelSubscriptionCommandHandler(self.company_repo).handle(
                CancelSubscriptionCommand(stripe_customer_id=obj["customer"])
            )

        elif event_type == "invoice.payment_succeeded":
            RestoreBillingCommandHandler(self.company_repo).handle(
                RestoreBillingCommand(stripe_customer_id=obj["customer"])
            )

        elif event_type == "invoice.payment_failed":
            logger.warning(
                "Invoice payment failed for customer=%s", obj.get("customer", "unknown")
            )

        else:
            logger.debug("Ignoring unhandled Stripe event type: %s", event_type)
