# Epic Slicing: E43 - Billing & Subscriptions

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-22
**Total Features:** 6

---

## Slicing Rationale

E43 is sliced into 6 features following a strict dependency chain. The foundation (F0) extends the Company entity and database schema with all billing fields, and introduces the `PlanGate` service and `OPEN_SOURCE_MODE` bypass — everything that later features rely on. F1 integrates Stripe Customer creation into company registration, completing the data plumbing. F2 builds the webhook listener that keeps the platform in sync with Stripe events. F3 provides the self-service billing UI for company admins (Checkout + Customer Portal) and the lazy grace-period enforcement middleware. F4 enforces plan limits and feature gating on existing write endpoints across the platform. F5 delivers the super-admin billing management capabilities.

---

## Dependency Graph

```
F0: Billing Domain Foundation (Company entity, PlanGate, enums, migration, Open Source mode)
 │
 └── F1: Stripe Customer Bootstrap (create Stripe Customer on registration)
      │
      └── F2: Webhook Listener (Stripe event handling, idempotency, plan sync)
           │
           └── F3: Company Admin Billing UI (Checkout, Portal, billing page, grace period middleware)
                │
                └── F4: Plan Enforcement (resource limits + feature gating on write endpoints)
                     │
                     └── F5: Super Admin Billing Management (plan override, complimentary grants)
```

F0 and F1 may be implemented in parallel since F1 only needs F0's Company entity fields and migration, but F1 should be merged before F2.

---

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---|---|---|---|---|
| F0 | Billing Domain Foundation | — | Company entity billing fields, PlanGate service, enums, migration, Open Source mode bypass | M | Done |
| F1 | Stripe Customer Bootstrap | F0 | Stripe Customer created synchronously on registration; `stripe_customer_id` persisted | S | Done |
| F2 | Webhook Listener | F1 | Platform stays in sync with Stripe — plan changes, payment failures, grace period, restoration | L | Done |
| F3 | Company Admin Billing UI | F2 | Admin can view plan/usage, upgrade via Checkout, manage via Portal; grace period banner; processing page | L | Done |
| F4 | Plan Enforcement | F3 | Login blocked for suspended companies; user limit checked on employee add | L | Done |
| F5 | Super Admin Billing Management | F4 | Super admin can view, override, grant complimentary and revoke plans per company | M | Pending |

---

## F0: Billing Domain Foundation

**Scope:** Extend the Company domain entity and database model with all billing-related fields. Define the `PlanTier` and `BillingStatus` enums. Create the `processed_stripe_events` table. Introduce the `PlanGate` domain service. Add Stripe and Open Source mode configuration. No Stripe API calls yet.

**Depends on:** Existing Company BC.

**Includes:**

### Enums
- New file `src/company_bc/company/domain/billing_enums.py`:
  - `PlanTier(str, Enum)`: `free | premium | enterprise | open_source`
  - `BillingStatus(str, Enum)`: `active | grace_period | suspended | over_limit`

### Company Entity Extension
- New fields on `Company`:
  - `plan: PlanTier` (default: `PlanTier.FREE`)
  - `billing_status: BillingStatus` (default: `BillingStatus.ACTIVE`)
  - `stripe_customer_id: Optional[str]`
  - `stripe_subscription_id: Optional[str]`
  - `grace_period_started_at: Optional[datetime]`
  - `current_period_end: Optional[datetime]`
  - `pending_downgrade_plan: Optional[PlanTier]`
  - `complimentary: bool` (default: `False`)
- New domain methods: `set_billing_status`, `apply_plan_change`, `enter_grace_period`, `restore_billing`, `grant_complimentary`, `revoke_complimentary`

### PlanGate Service
- New file `src/company_bc/company/domain/plan_gate.py`:
  - `is_feature_available(plan, billing_status, complimentary, open_source_mode, feature) -> bool`
  - `is_write_allowed(billing_status, open_source_mode) -> bool`
  - `get_user_limit(plan) -> Optional[int]` — `None` = unlimited
  - `get_asset_limit(plan) -> Optional[int]`
  - Feature-to-plan mapping constants

### Infrastructure — Model Extension
- New columns on `CompanyModel`: `plan`, `billing_status`, `stripe_customer_id`, `stripe_subscription_id`, `grace_period_started_at`, `current_period_end`, `pending_downgrade_plan`, `complimentary`
- New model `ProcessedStripeEventModel` (`processed_stripe_events` table):
  - `id: Mapped[str]` (Stripe event ID, primary key)
  - `processed_at: Mapped[datetime]`

### Repository Extension
- `find_by_stripe_customer_id(customer_id: str) -> Optional[Company]`
- `mark_stripe_event_processed(event_id: str) -> None`
- `is_stripe_event_processed(event_id: str) -> bool`

### Alembic Migration
- Single migration adding all new columns to `companies` (all nullable or server-defaulted) and creating `processed_stripe_events` table. Fully backward compatible.

### Configuration
- New `StripeSettings` in `core/config.py`: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PREMIUM`, `STRIPE_PRICE_ENTERPRISE`, `OPEN_SOURCE_MODE: bool = False`
- Add all new vars to `.env.example`

### Tests
- Unit tests: `PlanGate` — feature availability, write-allow logic, limits per plan, Open Source bypass
- Unit tests: Company entity billing domain methods

---

## F1: Stripe Customer Bootstrap

**Scope:** Create a Stripe Customer synchronously during company registration and persist `stripe_customer_id`. If Stripe is unavailable, registration fails. Free plan companies have a Stripe Customer but no Stripe Subscription.

**Depends on:** F0.

**Includes:**

### Stripe Client
- New `core/stripe_client.py`:
  - `create_customer(name, email, metadata) -> str` — returns Stripe `customer.id`
  - `StripeUnavailableError` raised on API failure
  - When `OPEN_SOURCE_MODE=True`, returns `""` (no-op)

### Command Extension
- Extend `CreateCompanyCommandHandler`: after saving company, call `stripe_client.create_customer()` and persist the ID
- On failure: raise `StripeUnavailableError` → router maps to `HTTP 503`

### Tests
- Unit test: customer ID persisted; Stripe error propagates
- Integration test: registration endpoint with mocked Stripe — `stripe_customer_id` saved on company

---

## F2: Webhook Listener

**Scope:** `POST /api/v1/billing/webhook` — validates Stripe signature, routes events, applies state changes with idempotency. Handles all 5 required Stripe event types.

**Depends on:** F1.

**Includes:**

### Commands (one per event)
- `ActivateSubscriptionCommand` → triggered by `checkout.session.completed`
- `SyncPlanChangeCommand` → triggered by `customer.subscription.updated`
- `CancelSubscriptionCommand` → triggered by `customer.subscription.deleted`
- `RestoreBillingCommand` → triggered by `invoice.payment_succeeded`
- `invoice.payment_failed` → log only, no state change

### Webhook Dispatcher
- `src/company_bc/company/application/services/stripe_webhook_dispatcher.py`
- Checks idempotency via `is_stripe_event_processed(event["id"])` before dispatching
- Marks event as processed after handling
- Routes by `event["type"]`, resolves `company_id` from `stripe_customer_id`

### HTTP Layer
- New router `adapters/http/api/billing/routers.py`:
  - `POST /webhook` (public, no auth): verify signature → dispatch → `200`
  - Returns `400` on invalid signature, `200` on duplicate (idempotent)

### Tests
- Unit tests: each command handler; dispatcher routing; idempotency path
- Integration test: valid/invalid signature; duplicate event_id returns 200 without re-applying

---

## F3: Company Admin Billing UI

**Scope:** Billing overview endpoint, Checkout session creation, Customer Portal session creation. Frontend billing page, processing page, grace period banner. Lazy grace period expiry enforcement in `get_current_user`.

**Depends on:** F2.

**Includes:**

### Query
- `GetBillingOverviewQuery(company_id)` → `BillingOverviewDto` (plan, billing_status, complimentary, user_count/limit, asset_count/limit, grace_days_remaining, current_period_end, pending_downgrade_plan)

### BillingService (Application Service)
- `StripeBillingService` wrapping Stripe SDK:
  - `create_checkout_session(stripe_customer_id, target_plan, success_url, cancel_url) -> str`
  - `create_portal_session(stripe_customer_id, return_url) -> str`
  - No-ops returning dummy URLs when `OPEN_SOURCE_MODE=True`

### HTTP Layer
- `GET /api/v1/billing/` (role: admin)
- `POST /api/v1/billing/checkout` (role: admin) → `{"checkout_url": "..."}`
- `POST /api/v1/billing/portal` (role: admin) → `{"portal_url": "..."}`

### Grace Period Middleware
- In `get_current_user`: if `billing_status == grace_period` and `grace_period_started_at + 15 days < now`, set `billing_status = suspended` (single UPDATE with WHERE guard to avoid race conditions)

### Frontend
- `BillingPage.tsx`: plan badge, billing status badge, usage bars, grace period warning, upgrade/downgrade buttons, "Manage Billing" → Portal
- `BillingProcessingPage.tsx` (`/billing/processing?session_id=...`): polls `GET /billing/` every 2s up to 60s until plan activates, then redirects
- Persistent billing banner in `AppLayout.tsx`: yellow (grace period + days remaining) or red (suspended) — admin role only
- i18n strings EN + ES

### Tests
- Unit tests: `GetBillingOverviewQueryHandler`, grace period expiry boundary conditions
- Integration tests: all 3 billing endpoints; lazy suspension on request

---

## F4: Plan Enforcement

**Scope:** Enforce resource limits and feature gating across all existing write endpoints. Block writes for suspended/over-limit companies with `402` responses.

**Depends on:** F3.

**Includes:**

### Enforcement Dependencies
- `require_write_access(company, plan_gate)` → `HTTP 402 {"detail": "account_suspended" | "account_read_only"}`
- `require_feature(feature)` factory → `HTTP 402 {"detail": "feature_not_available_on_plan"}`
- `require_user_limit_not_reached(company, user_repo)` → `HTTP 402 {"detail": "plan_limit_reached"}`
- `require_asset_limit_not_reached(company, asset_repo)` → same

### Endpoint Updates (additive only)
- **Users router**: add `require_user_limit_not_reached` + `require_write_access` to invite/create
- **Assets router**: add `require_asset_limit_not_reached` + `require_write_access` to create
- **All write endpoints**: add `require_write_access`
- **Feature-gated endpoints** (reports, API keys, AI classification, appointments, shipments, maintenance, procurement, MCP, SSO, audit trail, custom fields, automations, SLA, knowledge base, onboarding): add `require_feature("feature_key")`

### Tests
- Unit tests: all enforcement dependencies
- Integration tests: `402` on user limit reached, asset limit reached, suspended company, wrong plan for feature

---

## F5: Super Admin Billing Management

**Scope:** Super-admin-only endpoints to view, override, grant and revoke company billing plans. Frontend in Companies page.

**Depends on:** F4.

**Includes:**

### Queries & Commands
- `GetCompanyBillingQuery(company_id)` → `CompanyBillingDto`
- `OverrideCompanyPlanCommand(company_id, new_plan)`: manually sets `plan` without Stripe
- `GrantComplimentaryPlanCommand(company_id, plan)`: sets `complimentary = True`, cancels active Stripe subscription if any
- `RevokeComplimentaryPlanCommand(company_id)`: sets `complimentary = False`, `plan = free`, `billing_status = over_limit`

### HTTP Layer
- `GET /api/v1/companies/{id}/billing` (super_admin)
- `PATCH /api/v1/companies/{id}/billing/plan` (super_admin)
- `POST /api/v1/companies/{id}/billing/complimentary` (super_admin)
- `DELETE /api/v1/companies/{id}/billing/complimentary` (super_admin)

### Frontend
- Extend `CompaniesPage.tsx`: add plan + billing status columns, "Billing" action button per row
- Billing modal: current plan/status, override plan, grant/revoke complimentary
- i18n strings EN + ES

### Tests
- Unit tests: all 3 commands (especially `GrantComplimentary` verifies Stripe cancel called)
- Integration tests: all 4 endpoints — happy path + error cases

---

## Recommended Order

1. **F0** — Must be first. Foundation for everything.
2. **F1** — Immediately after. Ensures new companies have Stripe Customer from day one.
3. **F2** — Must precede F3. Webhook confirms Checkout activation.
4. **F3** — First user-visible feature. Activates grace period enforcement.
5. **F4** — Activates limits and gating. Only after billing lifecycle is confirmed working.
6. **F5** — Operational tooling. Delivered after core billing loop is live.

---

## Migration Strategy

**F0** delivers a single Alembic migration:
- Adds 8 columns to `companies` (all nullable or server-defaulted — non-breaking)
- Creates `processed_stripe_events` table

Existing companies get `plan = free`, `billing_status = active`, `stripe_customer_id = null` automatically. No data migration required. Existing companies without `stripe_customer_id` return an appropriate error on Checkout/Portal until provisioned.

---

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1 → F2 → F3 → F4 → F5)
- [x] Each feature independently deployable
- [x] Vertical slices — each feature spans domain, infrastructure, HTTP, and frontend
- [x] Shared foundation identified (F0)
- [x] No overlapping scope between features
- [x] Each feature delivers minimum viable, testable value
- [x] All acceptance criteria from requirements.md covered
- [x] Open Source mode handled in F0 via PlanGate
- [x] Idempotency addressed in F0 (schema) and F2 (usage)

---

## Risk Notes

- **F0 modifies the Company entity** — central to the platform. Run full regression suite before merging.
- **F1 makes Stripe a hard dependency on registration** — ensure `StripeUnavailableError` surfaces as `503` and integration tests mock the Stripe client.
- **F2 webhook endpoint is public** — Stripe signature verification is the sole security layer. Add monitoring on webhook 400 error rate.
- **F3 lazy grace period enforcement** runs on every authenticated request — the suspension UPDATE must use a WHERE guard to avoid race conditions under concurrent requests.
- **F4 is cross-cutting** — touching every write endpoint carries regression risk. Each change must be accompanied by a targeted integration test.
- **F5 `GrantComplimentaryPlanCommand`** cancels an active Stripe subscription — must be tested with a mocked Stripe client.
- **`over_limit` billing status** (downgrade with excess resources) — added as a fourth `BillingStatus` value in F0 to support this state cleanly.
