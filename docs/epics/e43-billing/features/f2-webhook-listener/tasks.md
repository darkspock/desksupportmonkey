# Tasks: F2 - Webhook Listener

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F1](../f1-stripe-bootstrap/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Application Layer — Commands

### T1.1: ActivateSubscriptionCommand + Handler
- [x] **File:** `src/company_bc/company/application/commands/billing/activate_subscription.py` (NEW)
- Triggered by Stripe event `checkout.session.completed`
- `@dataclass class ActivateSubscriptionCommand(Command):`
  - `stripe_customer_id: str`
  - `stripe_subscription_id: str`
  - `plan: PlanTier`
  - `current_period_end: datetime`
- Handler:
  1. Find company by `stripe_customer_id` → raise `CompanyNotFoundError` if not found
  2. Call `company.apply_plan_change(plan, subscription_id, period_end)`
  3. Call `company.set_billing_status(BillingStatus.ACTIVE)`
  4. Save company

### T1.2: SyncPlanChangeCommand + Handler
- [x] **File:** `src/company_bc/company/application/commands/billing/sync_plan_change.py` (NEW)
- Triggered by Stripe event `customer.subscription.updated`
- `@dataclass class SyncPlanChangeCommand(Command):`
  - `stripe_customer_id: str`
  - `new_plan: PlanTier`
  - `subscription_status: str` (e.g., "active", "past_due")
  - `current_period_end: datetime`
  - `pending_downgrade_plan: Optional[PlanTier]`
- Handler:
  1. Find company by `stripe_customer_id` → raise `CompanyNotFoundError` if not found
  2. If `subscription_status == "past_due"`: call `company.enter_grace_period()`
  3. Else: update plan and period_end; set or clear `pending_downgrade_plan`
  4. Save company

### T1.3: CancelSubscriptionCommand + Handler
- [x] **File:** `src/company_bc/company/application/commands/billing/cancel_subscription.py` (NEW)
- Triggered by Stripe event `customer.subscription.deleted`
- `@dataclass class CancelSubscriptionCommand(Command):`
  - `stripe_customer_id: str`
- Handler:
  1. Find company by `stripe_customer_id` → raise `CompanyNotFoundError` if not found
  2. Set `company.plan = PlanTier.FREE`, `company.stripe_subscription_id = None`, `company.billing_status = BillingStatus.ACTIVE`
  3. Save company

### T1.4: RestoreBillingCommand + Handler
- [x] **File:** `src/company_bc/company/application/commands/billing/restore_billing.py` (NEW)
- Triggered by Stripe event `invoice.payment_succeeded`
- `@dataclass class RestoreBillingCommand(Command):`
  - `stripe_customer_id: str`
- Handler:
  1. Find company by `stripe_customer_id` → raise `CompanyNotFoundError` if not found
  2. If `billing_status` is `GRACE_PERIOD` or `SUSPENDED`: call `company.restore_billing()`
  3. Save company

---

## Phase 2: Webhook Dispatcher

### T2.1: Create StripeWebhookDispatcher
- [x] **File:** `src/company_bc/company/application/services/stripe_webhook_dispatcher.py` (NEW)
- Class `StripeWebhookDispatcher`:
  - Dependencies: `company_repo: CompanyRepositoryInterface`
  - Method `dispatch(event: dict) -> None`:
    1. Extract `event_id = event["id"]`
    2. Check `company_repo.is_stripe_event_processed(event_id)` → if True, return immediately (idempotency)
    3. Route by `event["type"]`:
       - `"checkout.session.completed"` → build + handle `ActivateSubscriptionCommand`
       - `"customer.subscription.updated"` → build + handle `SyncPlanChangeCommand`
       - `"customer.subscription.deleted"` → build + handle `CancelSubscriptionCommand`
       - `"invoice.payment_succeeded"` → build + handle `RestoreBillingCommand`
       - `"invoice.payment_failed"` → log only, no state change
       - Unknown events → ignore silently
    4. Mark event processed: `company_repo.mark_stripe_event_processed(event_id)`

### T2.2: Add signature verification to StripeClient
- [x] **File:** `core/stripe_client.py` (MODIFY)
- Add `verify_webhook_signature(payload: bytes, sig_header: str, webhook_secret: str) -> dict`
  - Calls `stripe.Webhook.construct_event(payload, sig_header, webhook_secret)`
  - On `stripe.error.SignatureVerificationError`: raise `InvalidStripeSignatureError`
  - Returns the parsed event dict

---

## Phase 3: HTTP Layer

### T3.1: Create billing router with webhook endpoint
- [x] **File:** `adapters/http/api/billing/__init__.py` (NEW — empty)
- [x] **File:** `adapters/http/api/billing/routers.py` (NEW)
- `POST /webhook` (public, no auth):
  - Reads raw request body as `bytes` (do NOT use Pydantic — Stripe sends raw JSON)
  - Reads `Stripe-Signature` header
  - Calls `stripe_client.verify_webhook_signature(body, sig_header, settings.STRIPE_WEBHOOK_SECRET)`
  - On `InvalidStripeSignatureError`: return `400`
  - Calls `dispatcher.dispatch(event)`
  - Returns `200 {"status": "ok"}`

### T3.2: Register billing router in app.py
- [x] **File:** `app.py` (MODIFY)
- `app.include_router(billing_router, prefix="/api/v1/billing")`

---

## Phase 4: Tests

### T4.1: Unit tests — ActivateSubscriptionCommand
- [x] **File:** `tests/unit/company_bc/company/application/commands/billing/test_activate_subscription.py` (NEW)
- Test: plan activated, subscription_id saved, billing_status = ACTIVE
- Test: company not found → CompanyNotFoundError

### T4.2: Unit tests — SyncPlanChangeCommand
- [x] **File:** `tests/unit/company_bc/company/application/commands/billing/test_sync_plan_change.py` (NEW)
- Test: plan change applied, period_end updated
- Test: `status=past_due` → grace period entered

### T4.3: Unit tests — CancelSubscriptionCommand
- [x] **File:** `tests/unit/company_bc/company/application/commands/billing/test_cancel_subscription.py` (NEW)
- Test: plan reset to FREE, subscription_id cleared

### T4.4: Unit tests — RestoreBillingCommand
- [x] **File:** `tests/unit/company_bc/company/application/commands/billing/test_restore_billing.py` (NEW)
- Test: billing restored from grace_period → active
- Test: billing restored from suspended → active

### T4.5: Unit tests — StripeWebhookDispatcher
- [x] **File:** `tests/unit/company_bc/company/application/services/test_stripe_webhook_dispatcher.py` (NEW)
- Test: each event type routes to correct command
- Test: duplicate event_id → returns immediately without dispatching (idempotency)
- Test: unknown event type → ignored silently
- Test: `invoice.payment_failed` → no command, no error

### T4.6: Integration tests — webhook endpoint
- [x] **File:** `tests/integration/test_billing_endpoints.py` (NEW)
- Test: valid Stripe signature + known event → 200
- Test: invalid Stripe signature → 400
- Test: duplicate event_id → 200 without re-applying state change
- Mock `stripe.Webhook.construct_event` in all tests

---

## Phase 5: Verification

### T5.1: Run linter
- [x] `make lint` — no new errors (pre-existing E24 issues in google/microsoft token verifiers only)

### T5.2: Run all tests
- [x] `make test` — 1177 passed
- [x] `make test-integration` — 322 passed (7 pre-existing failures unchanged)

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Commands | T1.1-T1.4 | 4 new | — |
| 2. Dispatcher | T2.1-T2.2 | 1 new | 1 modified (stripe_client) |
| 3. HTTP | T3.1-T3.2 | 2 new | 1 modified (app.py) |
| 4. Tests | T4.1-T4.6 | 6 new | — |
| 5. Verification | T5.1-T5.2 | — | — |
