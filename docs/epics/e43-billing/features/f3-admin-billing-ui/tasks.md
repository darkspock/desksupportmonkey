# Tasks: F3 - Company Admin Billing UI

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F2](../f2-webhook-listener/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Application Layer — Query

### T1.1: BillingOverviewDto
- **File:** `src/company_bc/company/application/queries/billing/get_billing_overview.py` (NEW)
- Define `BillingOverviewDto`:
  - `plan: PlanTier`
  - `billing_status: BillingStatus`
  - `complimentary: bool`
  - `user_count: int`
  - `user_limit: Optional[int]`
  - `asset_count: int`
  - `asset_limit: Optional[int]`
  - `grace_days_remaining: Optional[int]`
  - `current_period_end: Optional[datetime]`
  - `pending_downgrade_plan: Optional[PlanTier]`

### T1.2: GetBillingOverviewQuery + Handler
- **File:** `src/company_bc/company/application/queries/billing/get_billing_overview.py` (same file as T1.1)
- `@dataclass class GetBillingOverviewQuery(Query):`
  - `company_id: str`
- Handler:
  1. Find company by `company_id` → raise `CompanyNotFoundError` if not found
  2. Count active users for company (via `company_repo.count_users()`)
  3. Count active assets for company (via `asset_repo.count_by_company()` — read-only call)
  4. Calculate `grace_days_remaining`: if `grace_period_started_at` is set, compute `15 - (now - grace_period_started_at).days`; clamp to 0
  5. Use `PlanGate.get_user_limit(plan)` and `PlanGate.get_asset_limit(plan)`
  6. Return `BillingOverviewDto`

---

## Phase 2: Application Layer — BillingService

### T2.1: StripeBillingService
- **File:** `src/company_bc/company/application/services/stripe_billing_service.py` (NEW)
- Class `StripeBillingService`:
  - Dependencies: `stripe_client: StripeClient`, `open_source_mode: bool`
  - `create_checkout_session(stripe_customer_id: str, target_plan: PlanTier, success_url: str, cancel_url: str) -> str`
    - If `open_source_mode`: return `""`
    - Calls `stripe.checkout.Session.create(...)` with:
      - `customer=stripe_customer_id`
      - `mode="subscription"`
      - `line_items=[{"price": price_id, "quantity": 1}]` where price_id = `STRIPE_PRICE_PREMIUM` or `STRIPE_PRICE_ENTERPRISE`
      - `success_url=success_url`, `cancel_url=cancel_url`
    - Returns `session.url`
    - On `stripe.error.StripeError`: raise `StripeUnavailableError`
  - `create_portal_session(stripe_customer_id: str, return_url: str) -> str`
    - If `open_source_mode`: return `""`
    - Calls `stripe.billing_portal.Session.create(customer=stripe_customer_id, return_url=return_url)`
    - Returns `session.url`
    - On `stripe.error.StripeError`: raise `StripeUnavailableError`

---

## Phase 3: Grace Period Middleware

### T3.1: Add lazy grace period enforcement in get_current_user
- **File:** `adapters/http/dependencies.py` (MODIFY — or wherever `get_current_user` lives)
- After loading the user and their company, add:
  ```python
  if company.billing_status == BillingStatus.GRACE_PERIOD and company.grace_period_started_at:
      if company.grace_period_started_at + timedelta(days=15) < datetime.utcnow():
          # Suspend with WHERE guard to avoid race conditions
          db.execute(
              update(CompanyModel)
              .where(CompanyModel.id == company.id)
              .where(CompanyModel.billing_status == "grace_period")
              .values(billing_status="suspended")
          )
          db.commit()
          company.billing_status = BillingStatus.SUSPENDED
  ```
- Only runs when `OPEN_SOURCE_MODE=False`

---

## Phase 4: HTTP Layer

### T4.1: Extend billing router with admin endpoints
- **File:** `adapters/http/api/billing/routers.py` (MODIFY)
- Add `GET /` (role: admin):
  - Returns `BillingOverviewDto` as JSON
  - Map `CompanyNotFoundError` → 404
- Add `POST /checkout` (role: admin):
  - Request body: `target_plan: str`
  - Calls `StripeBillingService.create_checkout_session()`
  - Returns `{"checkout_url": "..."}`
  - On `StripeUnavailableError`: 503
  - If `company.stripe_customer_id` is None (pre-F1 company): 422 with `detail="stripe_customer_not_provisioned"`
- Add `POST /portal` (role: admin):
  - Calls `StripeBillingService.create_portal_session()`
  - Returns `{"portal_url": "..."}`
  - On `StripeUnavailableError`: 503

### T4.2: Add billing schemas
- **File:** `adapters/http/api/billing/schemas.py` (NEW)
- `BillingOverviewResponse`: mirrors `BillingOverviewDto` fields, all JSON-serializable
- `CheckoutRequest`: `target_plan: str`
- `CheckoutResponse`: `checkout_url: str`
- `PortalResponse`: `portal_url: str`

---

## Phase 5: Frontend

### T5.1: Create BillingPage
- **File:** `web/app/src/pages/BillingPage.tsx` (NEW)
- Displays:
  - Plan badge (Free / Premium / Enterprise / Open Source)
  - Billing status badge (Active / Grace Period / Suspended / Over Limit)
  - Complimentary badge if `complimentary=true`
  - Usage bars: "X / Y users", "X / Y assets" (infinite symbol for unlimited)
  - Grace period warning box with days remaining (only when `billing_status = grace_period`)
  - Suspended warning box (only when `billing_status = suspended`)
  - "Upgrade Plan" button → calls `POST /billing/checkout`, redirects to returned URL
  - "Manage Billing" button → calls `POST /billing/portal`, redirects to returned URL
  - Both buttons hidden when `OPEN_SOURCE_MODE` or `complimentary=true`
- Uses `GET /api/v1/billing/` via React Query

### T5.2: Create BillingProcessingPage
- **File:** `web/app/src/pages/BillingProcessingPage.tsx` (NEW)
- Route: `/billing/processing`
- Polls `GET /api/v1/billing/` every 2 seconds for up to 60 seconds
- While polling: spinner + "Processing your payment..." message
- When `billing_status = active` and plan changed: redirect to `/billing`
- On timeout (60s): show error message with link back to `/billing`

### T5.3: Add billing routes to router
- **File:** `web/app/src/router.tsx` (or main routing file, MODIFY)
- Add routes under authenticated layout:
  - `/billing` → `BillingPage`
  - `/billing/processing` → `BillingProcessingPage`
- Both routes visible to `admin` role only

### T5.4: Add BillingBanner to AppLayout
- **File:** `web/app/src/components/layout/AppLayout.tsx` (MODIFY)
- After the Header, add persistent banner (admin role only, not super_admin):
  - Yellow banner: `billing_status = grace_period` — "Payment failed. X days remaining before read-only mode. [Manage Billing →]"
  - Red banner: `billing_status = suspended` — "Account suspended — read-only mode. [Manage Billing →]"
  - No banner: `billing_status = active`, `open_source_mode`, or non-admin role
- Fetch billing status via React Query `GET /api/v1/billing/` (same query as BillingPage — cached)
- Banner links to `/billing`

### T5.5: Add billing to Sidebar navigation
- **File:** `web/app/src/components/layout/Sidebar.tsx` (MODIFY)
- Add "Billing" nav item for `admin` role, linking to `/billing`
- Hide when `OPEN_SOURCE_MODE=true` (check via env var or feature flag from backend)

### T5.6: Add i18n strings
- **File:** `web/app/src/lib/i18n/en.ts` (MODIFY)
- **File:** `web/app/src/lib/i18n/es.ts` (MODIFY)
- Add keys for:
  - `billing.title`, `billing.plan`, `billing.status`, `billing.users`, `billing.assets`
  - `billing.upgrade`, `billing.manage`, `billing.processing`, `billing.grace_warning`
  - `billing.suspended_warning`, `billing.complimentary`, `billing.unlimited`
  - `billing.status.active`, `billing.status.grace_period`, `billing.status.suspended`, `billing.status.over_limit`
  - `billing.plan.free`, `billing.plan.premium`, `billing.plan.enterprise`, `billing.plan.open_source`

---

## Phase 6: Tests

### T6.1: Unit tests — GetBillingOverviewQueryHandler
- **File:** `tests/unit/company_bc/company/application/queries/billing/test_get_billing_overview.py` (NEW)
- Test: returns correct DTO with counts and limits
- Test: grace_days_remaining calculated correctly (boundary: 14 days = 1 day remaining)
- Test: grace_days_remaining = 0 when expired
- Test: company not found → CompanyNotFoundError

### T6.2: Unit tests — grace period expiry boundary
- **File:** `tests/unit/company_bc/company/application/queries/billing/test_get_billing_overview.py` (same file)
- Test: company with `grace_period_started_at = now - 14 days` → 1 day remaining
- Test: company with `grace_period_started_at = now - 15 days` → 0 days remaining (suspended)

### T6.3: Integration tests — billing endpoints
- **File:** `tests/integration/test_billing_endpoints.py` (MODIFY — F2 already created this file)
- Test: `GET /api/v1/billing/` returns 200 with billing overview for admin
- Test: `GET /api/v1/billing/` returns 403 for non-admin user
- Test: `POST /api/v1/billing/checkout` returns checkout_url (mock Stripe)
- Test: `POST /api/v1/billing/portal` returns portal_url (mock Stripe)
- Test: lazy suspension — company with expired grace period is suspended on request

---

## Phase 7: Verification

### T7.1: Run linter
- `make lint` — no mypy or flake8 errors

### T7.2: Run all tests
- `make test` — all unit tests pass
- `make test-integration` — integration tests pass

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Query | T1.1-T1.2 | 1 new | — |
| 2. BillingService | T2.1 | 1 new | — |
| 3. Middleware | T3.1 | — | 1 modified (get_current_user) |
| 4. HTTP | T4.1-T4.2 | 1 new | 1 modified (billing router) |
| 5. Frontend | T5.1-T5.6 | 2 new pages | 3 modified (router, AppLayout, Sidebar) + 2 i18n |
| 6. Tests | T6.1-T6.3 | 1 new | 1 modified |
| 7. Verification | T7.1-T7.2 | — | — |
