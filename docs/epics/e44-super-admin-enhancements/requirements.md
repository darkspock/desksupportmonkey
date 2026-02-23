# Epic E44: Super Admin Enhancements

**Date:** 2026-02-23
**Priority:** High
**Status:** Pending

---

## Overview

The current super admin panel provides basic company lifecycle management and billing overrides, but lacks the operational visibility needed to run a SaaS business effectively. Specifically: trial status is invisible, the company list shows no usage data, and there is no way to see payment history or revenue without leaving the platform. This epic closes those gaps.

---

## Problems to Solve

| Problem | Impact |
|---|---|
| `trial_ends_at` is stored on Company but never exposed to super admin | Cannot tell which companies are in trial or when they expire |
| Company list shows only name and status — no usage data | Must click into every company to see user/asset counts |
| No invoice or payment history | Cannot confirm if a company paid without opening Stripe dashboard |
| No revenue overview | No way to know MRR, plan distribution, or revenue trend from within the app |

---

## User Stories

### Super Admin

- As a super admin, I can see trial status and days remaining for each company, so I know which companies are about to convert or churn.
- As a super admin, I can see user and asset counts directly in the company list, without opening each company.
- As a super admin, I can view the invoice history for any company — invoice date, amount, status (paid / failed), and a link to the PDF.
- As a super admin, I can see a revenue overview: total MRR, number of companies per plan, and count of active trials.

---

## Scope

### F1: Company List Enrichment

Extend the companies list endpoint and UI to include:
- `user_count` and `asset_count` per company (already computed in detail endpoint — add to list)
- `trial_days_remaining` (if in trial) — derived from `trial_ends_at`
- `trial_ends_at` exposed in the company billing endpoint
- Filter by `in_trial=true` (only companies currently in trial)
- Filter by `plan` (free | premium | enterprise | open_source)

### F2: Stripe Invoice History

Super admin can view the Stripe invoice history for any company:
- List invoices: date, amount, currency, status (paid / open / uncollectible / void), period covered
- Link to hosted invoice URL or PDF download
- Fetched live from Stripe API (not cached — always fresh)
- Returns empty list if company has no `stripe_customer_id` or no invoices

### F3: Revenue Overview

New super admin dashboard page with:
- **MRR** — sum of active monthly subscriptions, calculated using plan price constants defined in the project config (same amounts used when creating Stripe prices). Stripe is the reflection of these constants, not the source of truth for amounts.
- **Company distribution** — count of companies per plan (free, premium, enterprise, open_source, complimentary)
- **Active trials** — count of companies currently in trial with their trial end dates
- **Recent signups** — last 10 companies created (name, plan, trial status, created_at)
- Data computed server-side from the `companies` table — no Stripe API calls needed

---

## API Endpoints

| Method | Path | Description | Role |
|---|---|---|---|
| `GET` | `/api/v1/companies` | **Modified** — add `user_count`, `asset_count`, `trial_days_remaining`; filters: `in_trial`, `plan` | super_admin |
| `GET` | `/api/v1/companies/{id}/billing` | **Modified** — add `trial_days_remaining`, `trial_ends_at` | super_admin |
| `GET` | `/api/v1/companies/{id}/invoices` | List Stripe invoices for a company | super_admin |
| `GET` | `/api/v1/super-admin/overview` | Revenue overview: MRR, plan distribution, trials, recent signups | super_admin |

---

## Data Contracts

### Modified: CompanyListItemResponse (F1)
```
user_count: int
asset_count: int
trial_days_remaining: int | null   # null = not in trial
```

### Modified: CompanyBillingResponse (F1)
```
trial_days_remaining: int | null
trial_ends_at: datetime | null
```

### New: InvoiceResponse (F2)
```
invoice_id: str           # Stripe invoice ID
date: datetime            # invoice creation date
period_start: datetime
period_end: datetime
amount: int               # in cents
currency: str
status: str               # paid | open | uncollectible | void
invoice_url: str | null   # hosted Stripe invoice page
pdf_url: str | null       # PDF download URL
```

### New: SuperAdminOverviewResponse (F3)
```
mrr_cents: int                          # sum of active subscriptions
companies_by_plan: dict[str, int]       # {"free": 10, "premium": 3, ...}
active_trials: int                      # companies with trial_ends_at in the future
expiring_trials_7d: int                 # trials expiring within 7 days
recent_signups: list[RecentSignupDto]   # last 10 companies
```

---

## Out of Scope

- Annual billing / ARR tracking
- Churn rate calculation
- Per-company revenue history charts
- Trial expiry alerts/notifications (email or in-app) — deferred to a notifications epic
- Automated trial-to-paid conversion flows

---

## Acceptance Criteria

- [ ] Company list includes `user_count`, `asset_count`, `trial_days_remaining` for each company
- [ ] Company billing detail includes `trial_days_remaining` and `trial_ends_at`
- [ ] Super admin can list invoices for any company; empty list returned if no Stripe customer or no invoices
- [ ] Invoice list shows date, amount, status, and link to PDF/hosted page
- [ ] Revenue overview returns MRR, plan distribution, active trial count, expiring trials count, recent signups
- [ ] MRR calculation is correct for current plan configuration ($49 Premium, $149 Enterprise)
- [ ] All new endpoints return 403 for non-super-admin roles
- [ ] Frontend company list shows usage columns and trial badge
- [ ] Frontend billing modal shows trial expiry date for companies in trial
- [ ] Frontend invoices tab visible in company billing modal
- [ ] Frontend revenue overview page accessible from super admin navigation
