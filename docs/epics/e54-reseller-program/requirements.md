# Epic E54 — Reseller Program

**Date:** 2026-03-02
**Priority:** Medium
**Status:** Pending
**Bounded Context:** `reseller_bc` (new)
**Dependencies:** E43 (Billing) — Done, E24 (Google & Microsoft Login) — Done

---

## Business Alignment

### Objective

Enable third parties (IT consultants, MSPs, system integrators) to sell DeskSupportMonkey to their clients and earn commissions on recurring payments. The reseller program is a low-friction channel for customer acquisition: resellers get a simple portal to create client accounts, track commissions, and request payouts — we get organic distribution without a sales team.

### KPI Targets

| KPI | Target |
|-----|--------|
| Reseller sign-ups | 20 resellers in first 3 months |
| Accounts created via resellers | 30% of new paid accounts come through reseller channel within 6 months |
| Referral link conversion | 10%+ of referral link visits result in account creation |
| Payout requests | Average reseller earns enough for first payout within 90 days |

### Evidence

- Partner/reseller programs are standard in B2B SaaS (Freshworks, Zendesk, HubSpot all have them)
- IT consultants and MSPs are natural distribution channels — they already advise SMBs on tooling
- Commission-based model aligns incentives: resellers earn only when clients pay, zero upfront cost for us
- Referral links are the simplest acquisition channel with highest attribution accuracy

---

## Problem Statement

### Current Situation

Today, DeskSupportMonkey has no partner or reseller channel. All customer acquisition happens through direct sign-up. There is no way for a third party to:
- Create and manage client accounts on their behalf
- Earn commissions on client payments
- Track their earnings or request payouts
- Refer prospects via a tracked link

### Pain Points

| Problem | Impact |
|---------|--------|
| No reseller channel | Miss distribution through IT consultants and MSPs who advise SMBs |
| No commission tracking | No financial incentive for third parties to recommend the product |
| No referral attribution | Can't track which accounts came from which partner |
| No demo account creation | Resellers can't show the product to prospects with realistic data |

### Who Is Affected

- **Resellers (new audience):** IT consultants, MSPs, system integrators who want to earn commissions
- **Super Admin:** Needs to onboard resellers, configure commission rates, and approve payouts
- **Prospects:** Benefit from guided onboarding when a reseller creates their account

---

## Proposed Solution

### Overview

A standalone reseller portal with its own authentication (Google/Microsoft OAuth only — no passwords), separate user table, and a simple dashboard. Resellers can:

1. **Create demo accounts** — pre-filled with seed data so prospects can explore the product immediately
2. **Create normal client accounts** — standard empty account, linked to the reseller for commission tracking
3. **Share a referral link** — prospects who sign up through the link are automatically attributed to the reseller
4. **Track commissions** — see each client's payments and the commission earned (percentage configured per reseller)
5. **Request payouts** — once accumulated commissions reach a configurable minimum threshold

No white-label support in this epic. Reseller-created accounts use standard DSM branding.

---

## Domain Model

### New Bounded Context: `reseller_bc`

Completely separate from the main user system. Resellers do NOT exist in the `users` table.

#### Entity: `Reseller`

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `email` | String(255) | Email from OAuth provider, unique |
| `name` | String(150) | Display name from OAuth profile |
| `google_id` | String(255), nullable | Google OAuth subject ID |
| `microsoft_id` | String(255), nullable | Microsoft OAuth subject ID |
| `avatar_url` | String(500), nullable | Profile picture URL from OAuth |
| `company_name` | String(200), nullable | Reseller's own company name |
| `tax_id` | String(50), nullable | VAT/Tax ID for invoicing |
| `commission_pct` | Decimal(5,2) | Commission percentage (e.g. 15.00 = 15%) |
| `min_payout_cents` | Integer | Minimum balance to request payout (e.g. 5000 = €50) |
| `referral_code` | String(20), unique | Short code for referral URLs (auto-generated) |
| `status` | Enum | `active`, `suspended`, `deactivated` |
| `created_at` | DateTime | Registration timestamp |
| `updated_at` | DateTime | Last update |

#### Entity: `ResellerClient`

Links a reseller to the companies they brought in.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `reseller_id` | UUID FK | The reseller who created/referred this client |
| `company_id` | UUID FK | The client company in the main system |
| `source` | Enum | `manual` (reseller created), `referral` (signed up via link) |
| `created_at` | DateTime | When the relationship was established |

#### Entity: `ResellerCommission`

One record per client payment that generates a commission.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `reseller_id` | UUID FK | The reseller |
| `reseller_client_id` | UUID FK | The client relationship |
| `company_id` | UUID FK | The paying company |
| `payment_amount_cents` | Integer | Original payment amount |
| `commission_pct` | Decimal(5,2) | Rate applied (snapshot at time of payment) |
| `commission_amount_cents` | Integer | Calculated commission |
| `stripe_invoice_id` | String(255), nullable | Stripe invoice reference |
| `period_start` | Date | Billing period start |
| `period_end` | Date | Billing period end |
| `status` | Enum | `pending`, `confirmed`, `paid`, `clawed_back` |
| `created_at` | DateTime | When the commission was recorded |

#### Entity: `ResellerPayout`

Payout requests from resellers.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `reseller_id` | UUID FK | The reseller |
| `amount_cents` | Integer | Payout amount requested |
| `status` | Enum | `requested`, `approved`, `paid`, `rejected` |
| `requested_at` | DateTime | When the reseller requested |
| `processed_at` | DateTime, nullable | When super_admin processed it |
| `processed_by` | UUID FK, nullable | Super admin who processed |
| `payment_reference` | String(255), nullable | Bank transfer / PayPal reference |
| `notes` | Text, nullable | Admin notes |

---

## Authentication

Resellers authenticate **exclusively via Google or Microsoft OAuth**. No password, no magic link.

### Flow

1. Reseller visits `/reseller/login`
2. Clicks "Sign in with Google" or "Sign in with Microsoft"
3. OAuth callback verifies the token
4. If the email matches an existing `Reseller` record → issue session/JWT
5. If the email does NOT match → show "Not registered as a reseller. Contact us to apply."
6. Reseller onboarding is manual: super_admin creates the reseller record first, then the reseller can log in

### Why Separate Auth

- Resellers are NOT users of the platform — they don't access any company's data
- Separate `resellers` table avoids any risk of role confusion or accidental data access
- Simplifies the auth flow: no password management, no magic links, no role checks against company users
- OAuth-only eliminates password support burden for this audience

### Session Management

- JWT token with `type: reseller` claim to distinguish from regular user JWTs
- Separate middleware that validates reseller tokens and injects reseller context
- No overlap with the main `useAuth` / user session system

---

## Features

### F1 — Reseller Portal & Authentication

**Overview:** A standalone mini-app at `/reseller/*` with Google/Microsoft OAuth login, a dashboard, and navigation.

**User Stories:**

1. As a reseller, I can log in with my Google or Microsoft account so that I don't need to manage a separate password.
2. As a reseller, I can see my dashboard with total clients, total commissions earned, available balance, and pending payout status.
3. As a reseller, I can edit my own profile (company name, tax ID) from the portal.
4. As a super_admin, I can create a new reseller record (email, name, commission %, payout threshold) so that the person can then log in.
5. As a super_admin, I can edit reseller settings (commission %, payout threshold, status) at any time.
6. As a super_admin, I can see a list of all resellers with their client count and earnings.

### F2 — Account Creation

**Overview:** Resellers can create two types of accounts for their clients.

**Demo Account:**
- Pre-filled with seed data (same as `make seed` — sample assets, requests, users, departments)
- Clearly marked as demo in the reseller's client list
- The demo company gets the Free plan by default
- Admin credentials are shown to the reseller once at creation time
- **Auto-expires after 14 days** — company is suspended, data retained for 30 more days, then purged. A Celery beat task handles expiry checks daily.

**Normal Account:**
- Creates an empty company with a single admin user
- The reseller specifies: company name, admin email, plan (defaults to Free)
- The admin receives the standard onboarding flow (magic link or the reseller tells them to sign in with Google/Microsoft)
- The company is automatically linked to the reseller via `ResellerClient`

**User Stories:**

1. As a reseller, I can create a demo account with pre-filled data so that I can show the product to a prospect immediately.
2. As a reseller, I can create a normal client account with a company name and admin email so that the client can start using the platform.
3. As a reseller, I can see the list of all accounts I've created with their current plan and billing status.

### F3 — Referral Link

**Overview:** Each reseller gets a unique referral link. Prospects who register through it are automatically attributed.

**Mechanics:**
- URL format: `https://app.desksupportmonkey.com/auth/register?ref={referral_code}`
- When a company registers via a referral link, a `ResellerClient` record is created with `source = referral`
- The referral code is stored in a cookie (30-day expiry) so that if the prospect doesn't register immediately, attribution is preserved
- The reseller sees referral-originated clients in their dashboard alongside manually created ones

**User Stories:**

1. As a reseller, I can copy my unique referral link from the dashboard.
2. As a prospect, when I register through a referral link, the process is identical to normal registration — I don't notice anything different.
3. As a reseller, I can see which of my clients came from the referral link vs. which I created manually.

### F4 — Commission Tracking

**Overview:** When a reseller's client makes a payment, the system calculates the commission automatically.

**Mechanics:**
- Triggered by the Stripe webhook `invoice.payment_succeeded` event (already handled in E43's `StripeWebhookDispatcher`)
- When a payment comes in, check if the paying company has a `ResellerClient` record
- If yes → create a `ResellerCommission` record with the reseller's current `commission_pct`
- Commission = `payment_amount_cents * commission_pct / 100`, rounded down to the nearest cent
- Commission status starts as `pending`, moves to `confirmed` after 30 days (chargeback protection window)
- **Confirmation mechanism:** A Celery beat task runs daily, queries commissions where `status = pending AND created_at < now - 30 days`, and transitions them to `confirmed`
- **Refund clawback:** On `charge.refunded` Stripe webhook, find the matching commission by `stripe_invoice_id`. If found, set status to `clawed_back` regardless of current status (pending, confirmed, or paid). If already paid out, create a negative-amount commission record to deduct from the reseller's available balance

**User Stories:**

1. As a reseller, I can see a list of all commissions with client name, payment amount, commission %, commission earned, and status.
2. As a reseller, I can see my total available balance (sum of `confirmed` commissions minus already-paid payouts minus clawbacks).
3. As a super_admin, I can see all commissions across all resellers.
4. As a reseller, I can see clawed-back commissions clearly marked when a client received a refund.

### F5 — Payout Requests

**Overview:** Resellers can request a payout when their available balance reaches the minimum threshold.

**Mechanics:**
- Reseller clicks "Request Payout" → creates a `ResellerPayout` with `status = requested`
- Payout amount = current available balance (all `confirmed` commissions minus previous payouts)
- Button is disabled if balance < `min_payout_cents`
- Super_admin reviews the request and either approves or rejects
- When approved, super_admin processes the actual payment externally (bank transfer, PayPal, etc.) and marks it as `paid` with a payment reference
- The paid commissions are marked as `paid` to prevent double-counting

**User Stories:**

1. As a reseller, I can request a payout when my available balance meets the minimum threshold.
2. As a reseller, I can see my payout history with status, amount, and payment reference.
3. As a super_admin, I can see all pending payout requests and approve/reject them.
4. As a super_admin, I can mark a payout as paid and add a payment reference.

---

## API Endpoints

### Reseller Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/reseller/auth/google` | Exchange Google OAuth token for reseller JWT |
| POST | `/reseller/auth/microsoft` | Exchange Microsoft OAuth token for reseller JWT |
| GET | `/reseller/auth/me` | Get current reseller profile |

### Reseller Portal

| Method | Path | Description |
|--------|------|-------------|
| GET | `/reseller/dashboard` | Dashboard summary (clients, earnings, balance) |
| GET | `/reseller/clients` | List reseller's clients with plan/billing info |
| POST | `/reseller/clients/demo` | Create a demo account |
| POST | `/reseller/clients/account` | Create a normal client account |
| GET | `/reseller/commissions` | List commissions (paginated) |
| PATCH | `/reseller/profile` | Update reseller's own company_name and tax_id |
| GET | `/reseller/payouts` | List payout requests |
| POST | `/reseller/payouts` | Request a payout |

### Super Admin Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/resellers` | List all resellers |
| POST | `/admin/resellers` | Create a reseller |
| PATCH | `/admin/resellers/:id` | Update reseller settings |
| GET | `/admin/resellers/:id/clients` | List reseller's clients |
| GET | `/admin/resellers/:id/commissions` | List reseller's commissions |
| GET | `/admin/payouts` | List all payout requests |
| PATCH | `/admin/payouts/:id` | Approve/reject/mark-paid a payout |

---

## Referral Attribution on Registration

When processing a new company registration (`POST /auth/register`):

1. Check for `ref` query parameter or `dsm_ref` cookie
2. If present, look up the `referral_code` in the `resellers` table
3. If found and reseller is `active`, create a `ResellerClient` record with `source = referral`
4. Set `dsm_ref` cookie with 30-day expiry on the register page load (frontend)

This is the only touch point between the reseller system and the main registration flow.

---

## Scope

### In Scope

- Separate reseller user table with Google/Microsoft OAuth only
- Reseller portal: dashboard, client list, commissions, payouts
- Demo account creation with seed data
- Normal account creation linked to reseller
- Referral link with cookie-based attribution
- Commission calculation from Stripe webhooks
- Payout request/approval workflow
- Super admin management UI for resellers

### Out of Scope (future)

- White-label / custom branding for reseller clients
- Reseller self-registration (manual onboarding by super_admin for now)
- Tiered commission rates (same % for all clients of a reseller)
- Automatic payouts via Stripe Connect or PayPal API
- Reseller API keys / programmatic access
- Multi-level resellers (reseller of resellers)

---

## Business Rules

1. Resellers authenticate **only** via Google or Microsoft OAuth. No password, no magic link.
2. Reseller accounts are created **only** by super_admin. No self-registration.
3. Each reseller has a **single commission percentage** applied to all their clients equally.
4. Commission is calculated on the **full payment amount** (not on profit margin).
5. Commissions start as `pending` and become `confirmed` after **30 days** (chargeback window).
6. Payout can only be requested when available balance >= reseller's `min_payout_cents`.
7. A payout request locks the current available balance — new commissions go toward the next payout.
8. Actual money transfer is **manual** (super_admin does the bank transfer and records the reference).
9. If a reseller is `suspended`, they can still view their data but cannot create accounts or request payouts.
10. If a reseller is `deactivated`, they cannot log in. Their clients remain linked for historical tracking.
11. Referral cookie expires after **30 days**. If the prospect registers after that, no attribution.
12. A company can only be linked to **one reseller**. First attribution wins (manual creation or referral, whichever happens first).
13. Demo accounts count toward the reseller's client list but do **not** generate commissions (they're on the Free plan and don't pay).
14. Demo accounts **auto-expire after 14 days**: the company is suspended, data retained for 30 more days, then purged. A Celery beat task checks daily.
15. On Stripe `charge.refunded`, the matching commission is set to `clawed_back` regardless of current status. If already paid out, a **negative commission record** is created to deduct from the reseller's available balance.
16. Commission confirmation is handled by a **Celery beat task** that runs daily, querying commissions where `status = pending AND created_at < now - 30 days`, and transitions them to `confirmed`.
17. Resellers can **edit their own profile** (`company_name`, `tax_id`) from the portal. All other reseller settings (commission %, payout threshold, status) are super_admin-only.
18. After a payout is **rejected**, the reseller can **immediately request a new payout** with the same balance — no cooldown period.
19. OAuth credentials are **shared** between regular users and resellers (same Google/Microsoft OAuth app). Callback URLs handle both flows.
20. The reseller portal is part of the **same React app** with a separate route tree under `/reseller/*` and a dedicated `ResellerAuthProvider` context that checks for `type: reseller` JWT.

---

## Collateral Impact

| Component | Impact | Action |
|-----------|--------|--------|
| Registration flow (`POST /auth/register`) | Check for referral code | Add referral attribution hook |
| Stripe webhook handler (E43) | Check for reseller client on `invoice.payment_succeeded` | Add commission creation hook |
| Stripe webhook handler (E43) | Handle refund events | Add `charge.refunded` webhook handler for commission clawback |
| Super admin UI | New "Resellers" section | Add pages for reseller management and payout approval |
| Frontend router | New `/reseller/*` routes | Same React app, separate route tree under `/reseller/*` with `ResellerAuthProvider` context |
| OAuth config | Reseller OAuth uses same client IDs | Same Google/Microsoft OAuth app credentials; callback URLs handle both user and reseller flows |
| Database | 4 new tables | New migration |
| Seed data command | Needs to be callable for demo accounts | Refactor `make seed` to accept a target company_id parameter |
| Celery beat | Two new periodic tasks | 1) Daily commission confirmation (pending → confirmed after 30 days). 2) Daily demo account expiry check (suspend after 14 days, purge after 44 days) |

---

## Testing Requirements

### Unit Tests
- Commission calculation (rounding, edge cases with 0% or 100%)
- Payout available balance calculation (including negative commissions from clawbacks)
- Referral code generation uniqueness
- Reseller status transitions
- JWT token generation with `type: reseller` claim
- Demo account expiry logic (14-day suspension, 44-day purge)
- Clawback logic: pending → clawed_back, confirmed → clawed_back, paid → negative record created

### Integration Tests
- Reseller OAuth login (mock Google/Microsoft tokens)
- Create demo account → verify seed data is populated
- Create normal account → verify `ResellerClient` record
- Stripe webhook `invoice.payment_succeeded` → verify commission created for reseller client
- Stripe webhook `charge.refunded` → verify commission clawed back
- Stripe webhook `charge.refunded` on already-paid commission → verify negative commission record
- Payout request → approve → mark paid flow
- Payout request → reject → immediate re-request flow
- Referral registration → verify attribution
- Demo account expiry → verify company suspended after 14 days
- Reseller profile self-edit → verify only company_name and tax_id updatable

---

## Definition of Done

- [ ] Resellers table with separate OAuth-only authentication
- [ ] Reseller login page with Google and Microsoft buttons
- [ ] Reseller dashboard showing clients, commissions, and available balance
- [ ] Demo account creation with pre-filled seed data
- [ ] Normal account creation linked to reseller
- [ ] Referral link with 30-day cookie attribution
- [ ] Commission auto-calculation on Stripe `invoice.payment_succeeded`
- [ ] 30-day pending → confirmed commission lifecycle via Celery beat
- [ ] Refund clawback: `charge.refunded` → commission set to `clawed_back` (negative record if already paid)
- [ ] Demo account auto-expiry after 14 days via Celery beat
- [ ] Payout request with minimum threshold enforcement
- [ ] Rejected payout allows immediate re-request
- [ ] Reseller profile self-edit (company_name, tax_id)
- [ ] Super admin: create/edit resellers, approve/reject payouts
- [ ] All unit and integration tests pass
- [ ] No access from reseller portal to any company data
- [ ] Reseller JWT is distinct from user JWT — cannot be used interchangeably
- [ ] Same React app with separate `/reseller/*` route tree and `ResellerAuthProvider`
