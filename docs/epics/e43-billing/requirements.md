# Epic E43: Billing & Subscriptions

**Date:** 2026-02-22
**Priority:** Critical
**Status:** Pending

---

## Overview

DeskSupportMonkey charges companies a monthly subscription based on a tiered plan. Each company admin manages their own subscription from within the app using Stripe Billing. Invoicing, payment method management, and billing history are handled via the Stripe Customer Portal — no custom billing UI needed. A webhook listener keeps the platform in sync with Stripe events in real time.

---

## Plans

Pricing is based on **number of employees** in the client company, not on user seats or asset counts.

| Plan | Price | Company Size | Features |
|---|---|---|---|
| **Free** | €0/month | Up to 10 employees | Core features: assets, tickets, dashboard, magic link auth, password login |
| **Starter** | €49/month | Up to 25 employees | All Free features + reports, OAuth login, API keys, AI classification, appointments, shipments, maintenance, procurement |
| **Growth** | €99/month | Up to 100 employees | All Starter features + MCP server, Audit Trail, Custom Fields, SLA Management, Knowledge Base |
| **Scale** | €199/month | 100+ employees | All Growth features + SSO/Directory Sync, Workflow Automations, Onboarding/Offboarding, advanced compliance reports |
| **Open Source** | Free (self-hosted) | Unlimited | All features unlocked — no Stripe integration, no limits |

> Open Source plan: users self-host on their own server. The platform detects `OPEN_SOURCE_MODE=true` in the environment and defaults to Open Source mode with all features enabled and no billing UI shown.

---

## Billing Status

Billing status is stored in a **separate field** `billing_status` on the Company entity, independent of the existing `CompanyStatus` (`active / suspended / deactivated`). Both fields coexist — `CompanyStatus` handles operational lifecycle, `billing_status` handles payment state.

| `billing_status` | Meaning |
|---|---|
| `active` | Subscription in good standing |
| `grace_period` | Payment failed; 15-day window to pay before suspension |
| `suspended` | 15-day grace period expired unpaid; read-only access |

### Read-only Mode (suspended or downgrade over-limit)

When a company is in `suspended` billing status, or when downgrading leaves them over the new plan's limits:
- Users can log in and **read** all existing data
- All write operations are blocked (create, update, delete)
- A banner is shown explaining why and what action to take

---

## Billing Rules

### Plan Changes
- **Upgrade**: takes effect immediately. Stripe prorates the charge for the remainder of the current billing period.
- **Downgrade**: scheduled at end of current billing period. Company keeps current plan access until then. When the downgrade applies, if the company exceeds the new plan limits (e.g. 30 users → Free limit 5), they enter **read-only mode** until they delete resources to fall within the new limits.

### Payment Failure & Grace Period
- On failed payment, Stripe retries automatically (built-in dunning).
- When a payment fails, the platform sets `billing_status = grace_period` and records `grace_period_started_at`.
- **Grace period enforcement**: checked lazily on every authenticated request. If `grace_period_started_at + 15 days < now`, the company is automatically moved to `billing_status = suspended`.
- During grace period: full access, persistent warning banner showing days remaining.
- When suspended: read-only access, banner explaining payment is required.
- On successful payment: `billing_status` reset to `active`, full write access restored immediately.

### Resource Limit Enforcement
- Active user count and active asset count are checked on every relevant write action (invite user, create asset).
- If the limit is reached, the action is blocked with a clear error message and an upgrade prompt.
- Limit checks are performed at the API layer (not just frontend).

---

## Complimentary Plans (Super Admin)

The super admin can grant any company a complimentary plan at any tier (e.g. Enterprise for free). This sets `complimentary = true` on the Company and bypasses Stripe entirely — no subscription is created or required.

- If the company had an active Stripe subscription before, it is cancelled when `complimentary` is granted.
- If `complimentary` is revoked, the company falls to **Free plan** (`plan = free`, `complimentary = false`) in **read-only mode** until they subscribe to a paid plan.

---

## User Stories

### Company Admin

- As a company admin, I can see the current plan, usage (users used / limit, assets used / limit), and billing status on a Billing page.
- As a company admin, I can upgrade my plan immediately via Stripe Checkout.
- As a company admin, I can downgrade my plan, effective at end of current billing period.
- As a company admin, I can open the Stripe Customer Portal to manage payment method, download invoices, and cancel subscription.
- As a company admin, I see a warning banner during the grace period with days remaining.
- As a company admin in read-only mode after downgrade, I see which resources I need to delete to regain write access.

### Platform (Automatic)

- The platform enforces plan limits on user invites and asset creation.
- The platform enforces read-only access for suspended companies and over-limit downgraded companies on every write request.
- The platform checks grace period expiry lazily on each authenticated request and suspends the company if 15 days have passed.
- The platform restores write access immediately on successful payment.
- The platform upgrades/downgrades the company plan when Stripe sends the relevant webhook events.

### Super Admin

- As a super admin, I can see the billing plan and billing status of each company.
- As a super admin, I can manually override a company's plan (for trials or exceptions).
- As a super admin, I can grant a complimentary plan at any tier to any company, bypassing Stripe entirely.
- As a super admin, I can revoke a complimentary plan, which drops the company to Free in read-only mode.

---

## Stripe Integration

### Stripe Customer
- On company creation (registration), a Stripe Customer is created **synchronously**. If Stripe is unavailable, registration fails — this is intentional since payment capability is required.
- `stripe_customer_id` is stored on the Company entity.
- Free plan companies have a Stripe Customer but **no Stripe Subscription** (no €0 subscription).

### Stripe Subscription
- `stripe_subscription_id` is stored on the Company entity (nullable; null = Free plan).
- Created when the company upgrades for the first time via Stripe Checkout.

### Stripe Checkout (Upgrade Flow)
- Backend creates a Stripe Checkout Session in subscription mode.
- `success_url`: `/billing/processing?session_id={CHECKOUT_SESSION_ID}` — a "processing payment" page that waits for the webhook to confirm activation.
- `cancel_url`: `/billing` — returns to the billing page.
- Plan is activated via `checkout.session.completed` webhook, not on redirect.

### Stripe Customer Portal
- Backend creates a Stripe Billing Portal Session and redirects admin to the Stripe-hosted portal.
- Portal handles: invoice history, PDF download, payment method update, subscription cancellation, downgrade.

### Webhooks

Webhook endpoint: `POST /api/v1/billing/webhook` — validated with Stripe signature (`STRIPE_WEBHOOK_SECRET`). Returns `400` on signature failure.

**Idempotency**: all webhook handlers check the Stripe event ID against a `processed_stripe_events` table before applying any state change. Duplicate events are silently acknowledged with `200`.

| Event | Action |
|---|---|
| `checkout.session.completed` | Activate new subscription, update `plan`, `stripe_subscription_id`, `billing_status = active` |
| `customer.subscription.updated` | Sync plan change (upgrade/downgrade); on `status=past_due` → `billing_status = grace_period`, record `grace_period_started_at` |
| `customer.subscription.deleted` | Downgrade to Free plan, `stripe_subscription_id = null` |
| `invoice.payment_succeeded` | Set `billing_status = active`, clear `grace_period_started_at` |
| `invoice.payment_failed` | Log only (grace period is triggered by `subscription.updated` with `status=past_due`) |

---

## Data Model

### Company entity additions
- `stripe_customer_id: Optional[str]` — Stripe Customer ID (set on registration)
- `stripe_subscription_id: Optional[str]` — Stripe Subscription ID (null = Free plan)
- `plan: PlanTier` — enum: `free | premium | enterprise | open_source`
- `billing_status: BillingStatus` — enum: `active | grace_period | suspended` (default: `active`)
- `grace_period_started_at: Optional[datetime]`
- `current_period_end: Optional[datetime]` — end of current Stripe billing period
- `pending_downgrade_plan: Optional[PlanTier]` — plan scheduled at period end
- `complimentary: bool` — when True, plan granted for free by super admin; Stripe billing does not apply

### New table: `processed_stripe_events`
- `id: str` — Stripe event ID (primary key)
- `processed_at: datetime`

---

## Feature Gating

A `PlanGate` service checks whether a feature or action is available for the company's current plan and billing status.

```
Free:        core features only (assets, requests, dashboard, magic link, password login)
Premium:     Free + reports, OAuth, API keys, AI classification, appointments, shipments, maintenance, procurement
Enterprise:  Premium + MCP, SSO, audit trail, custom fields, automations, SLA, knowledge base, onboarding
Open Source: everything (no gating)
```

### Enforcement layers
1. **API layer**: endpoints return `402 Payment Required` with `{"detail": "feature_not_available_on_plan"}` or `{"detail": "plan_limit_reached"}` when the company's plan doesn't include the feature or limit is exceeded.
2. **API layer**: write endpoints return `402` with `{"detail": "account_suspended"}` or `{"detail": "account_read_only"}` when `billing_status = suspended` or company is in over-limit read-only mode.
3. **Frontend**: gated features show an upgrade prompt instead of the actual UI.

---

## API Endpoints

| Method | Path | Description | Role |
|---|---|---|---|
| `GET` | `/api/v1/billing/` | Current plan, usage, billing status | admin |
| `POST` | `/api/v1/billing/checkout` | Create Stripe Checkout Session (upgrade) | admin |
| `POST` | `/api/v1/billing/portal` | Create Stripe Customer Portal Session | admin |
| `POST` | `/api/v1/billing/webhook` | Stripe webhook listener | public (Stripe) |
| `GET` | `/api/v1/companies/{id}/billing` | Company billing overview | super_admin |
| `PATCH` | `/api/v1/companies/{id}/billing/plan` | Override plan (super admin) | super_admin |
| `POST` | `/api/v1/companies/{id}/billing/complimentary` | Grant complimentary plan | super_admin |
| `DELETE` | `/api/v1/companies/{id}/billing/complimentary` | Revoke complimentary plan | super_admin |

---

## Configuration

New environment variables:
```
OPEN_SOURCE_MODE=false
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PREMIUM=price_...
STRIPE_PRICE_ENTERPRISE=price_...
```

When `OPEN_SOURCE_MODE=true`: all features unlocked, no Stripe calls made, no billing UI shown, Stripe env vars ignored.

---

## Out of Scope

- Annual billing (monthly only for now)
- Per-seat pricing
- Custom enterprise contracts
- Stripe Tax / VAT calculation (can be enabled later in Stripe dashboard without code changes)
- Trial periods (Free plan serves as the trial)
- Metered/usage-based billing

---

## Acceptance Criteria

- [ ] Company admin can view current plan, usage, and billing status
- [ ] Upgrade flow via Stripe Checkout works end-to-end; plan activates on webhook, not on redirect
- [ ] Downgrade scheduled at period end via Stripe
- [ ] Stripe Customer Portal accessible from billing page
- [ ] Webhook listener processes all events correctly with idempotency
- [ ] Grace period triggered on `subscription.updated` with `status=past_due`
- [ ] Grace period expiry checked lazily on each authenticated request
- [ ] Company enters read-only mode after 15 days unpaid
- [ ] Access restored immediately on successful payment webhook
- [ ] Plan limits enforced on user invite and asset creation (API layer)
- [ ] Write operations blocked in read-only mode with `402` response
- [ ] Feature gating returns `402` for unavailable features
- [ ] Super admin can view and override company plan
- [ ] Super admin can grant and revoke complimentary plans
- [ ] Complimentary revocation drops company to Free in read-only mode
- [ ] Stripe Customer created synchronously on company registration
- [ ] `processed_stripe_events` table prevents duplicate webhook processing
- [ ] `OPEN_SOURCE_MODE=true` unlocks all features and disables billing UI
- [ ] Downgrade over-limit puts company in read-only mode until resources deleted
