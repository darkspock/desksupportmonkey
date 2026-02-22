# Tasks: F3 - Company Admin Billing UI

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F2](../f2-webhook-listener/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Application Layer — Query

### T1.1: BillingOverviewDto
- [x] **File:** `src/company_bc/company/application/queries/billing/get_billing_overview.py` (NEW)
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
- [x] **File:** `src/company_bc/company/application/queries/billing/get_billing_overview.py` (same file as T1.1)
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
- [x] **File:** `src/company_bc/company/application/services/stripe_billing_service.py` (NEW)
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
- [x] **File:** `adapters/http/api/auth/dependencies.py` (MODIFY)
- After loading the user and their company, add grace period expiry check
- Only runs when `OPEN_SOURCE_MODE=False`

---

## Phase 4: HTTP Layer

### T4.1: Extend billing router with admin endpoints
- [x] **File:** `adapters/http/api/billing/routers.py` (MODIFY)
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
- [x] **File:** `adapters/http/api/billing/schemas.py` (NEW)
- `BillingOverviewResponse`: mirrors `BillingOverviewDto` fields, all JSON-serializable
- `CheckoutRequest`: `target_plan: str`
- `CheckoutResponse`: `checkout_url: str`
- `PortalResponse`: `portal_url: str`

---

## Phase 5: Frontend

### T5.1: Create BillingPage
- [x] **File:** `web/app/src/pages/admin/BillingPage.tsx` (NEW)
- Displays plan badge, billing status badge, complimentary badge, usage bars, grace/suspended warnings, upgrade/manage buttons
- Uses `GET /api/v1/billing/` via React Query

### T5.2: Create BillingProcessingPage
- [x] **File:** `web/app/src/pages/admin/BillingProcessingPage.tsx` (NEW)
- Route: `/billing/processing`
- Polls `GET /api/v1/billing/` every 2 seconds for up to 60 seconds
- Redirects to `/billing` when `billing_status = active`
- On timeout: shows error with link back to `/billing`

### T5.3: Add billing routes to router
- [x] **File:** `web/app/src/router.tsx` (MODIFY)
- Added `/billing` and `/billing/processing` routes for `admin` role

### T5.4: Add BillingBanner to AppLayout
- [x] **File:** `web/app/src/components/layout/AppLayout.tsx` (MODIFY)
- Yellow banner for grace_period, red banner for suspended
- Fetch via React Query (cached with billing-overview key)

### T5.5: Add billing to Sidebar navigation
- [x] **File:** `web/app/src/components/layout/Sidebar.tsx` (MODIFY)
- Added "Billing" nav item for `admin` role

### T5.6: Add i18n strings
- [x] **File:** `web/app/src/locales/en.ts` (MODIFY)
- [x] **File:** `web/app/src/locales/es.ts` (MODIFY)
- Added all billing keys

---

## Phase 6: Tests

### T6.1: Unit tests — GetBillingOverviewQueryHandler
- [x] **File:** `tests/unit/company_bc/company/application/queries/billing/test_get_billing_overview.py` (NEW)
- 7 tests: DTO with counts/limits, premium/enterprise limits, grace days, boundary conditions, company not found

### T6.2: Unit tests — grace period expiry boundary
- [x] Same file as T6.1

### T6.3: Integration tests — billing endpoints
- [x] **File:** `tests/integration/test_billing_endpoints.py` (MODIFY)
- Tests: GET overview (admin + non-admin), checkout URL, portal URL, lazy suspension

---

## Phase 7: Verification

### T7.1: Run linter
- [x] `make lint` — no new errors (4 pre-existing OAuth stub errors unchanged)

### T7.2: Run all tests
- [x] `make test` — 1184 unit tests pass
- Integration tests pass

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
