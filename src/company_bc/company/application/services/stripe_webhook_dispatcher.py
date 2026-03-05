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
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.commission.application.commands.clawback_commission import (
    ClawbackCommissionCommand,
    ClawbackCommissionCommandHandler,
)
from src.reseller_bc.commission.application.commands.create_commission import (
    CreateCommissionCommand,
    CreateCommissionCommandHandler,
)
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface

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
        client_repo: Optional[ResellerClientRepositoryInterface] = None,
        commission_repo: Optional[ResellerCommissionRepositoryInterface] = None,
        reseller_repo: Optional[ResellerRepositoryInterface] = None,
    ) -> None:
        self.company_repo = company_repo
        self.client_repo = client_repo
        self.commission_repo = commission_repo
        self.reseller_repo = reseller_repo

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
            # Create commission if applicable
            if self.client_repo and self.commission_repo and self.reseller_repo:
                company = self.company_repo.find_by_stripe_customer_id(obj["customer"])
                if company:
                    try:
                        CreateCommissionCommandHandler(
                            commission_repo=self.commission_repo,
                            client_repo=self.client_repo,
                            reseller_repo=self.reseller_repo,
                        ).handle(CreateCommissionCommand(
                            stripe_invoice_id=obj["id"],
                            company_id=company.id,
                            payment_amount_cents=obj["amount_paid"],
                            period_start=_unix_to_datetime(obj["period_start"]) if obj.get("period_start") else None,
                            period_end=_unix_to_datetime(obj["period_end"]) if obj.get("period_end") else None,
                        ))
                    except Exception:
                        logger.warning("Commission creation failed for invoice=%s", obj["id"], exc_info=True)

        elif event_type == "charge.refunded":
            if self.commission_repo:
                invoice_id = obj.get("invoice")
                if invoice_id:
                    try:
                        ClawbackCommissionCommandHandler(
                            commission_repo=self.commission_repo,
                        ).handle(ClawbackCommissionCommand(
                            stripe_invoice_id=invoice_id,
                        ))
                    except Exception:
                        logger.warning("Commission clawback failed for charge=%s", obj.get("id"), exc_info=True)

        elif event_type == "invoice.payment_failed":
            logger.warning(
                "Invoice payment failed for customer=%s", obj.get("customer", "unknown")
            )

        else:
            logger.debug("Ignoring unhandled Stripe event type: %s", event_type)
