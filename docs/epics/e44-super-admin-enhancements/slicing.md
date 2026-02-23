# Epic Slicing: E44 - Super Admin Enhancements

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-23
**Total Features:** 3

---

## Slicing Rationale

E44 is sliced into 3 independent features. F1 is foundational — it enriches existing data surfaces with information already computed or stored in the database, requiring no new external dependencies. F2 adds Stripe invoice fetching, which needs an existing `stripe_customer_id` (available after E43) but is otherwise isolated. F3 builds an aggregated overview query on top of the enriched data from F1.

---

## Dependency Graph

```
F1: Company List Enrichment (usage counts + trial info in list and billing detail)
 │
 ├── F2: Stripe Invoice History (view invoices per company via Stripe API)
 │
 └── F3: Founder Dashboard (MRR dashboard, plan distribution, trial stats)
```

F2 and F3 can be implemented in parallel after F1 is merged.

---

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---|---|---|---|---|
| F1 | Company List Enrichment | E43 | User/asset counts and trial days in company list and billing detail | S | Done |
| F2 | Stripe Invoice History | F1 | Super admin can see payment history per company | M | Done |
| F3 | Founder Dashboard | F1 | MRR, trial pipeline, churn risk, growth, milestone tracker | M | Done |

---

## F1: Company List Enrichment

**Scope:** Extend the companies list and billing detail endpoints to expose usage counts and trial information. All data already exists in the database — this is purely additive.

**Depends on:** E43 (Company entity has `trial_ends_at`, user/asset counts already computed in detail endpoint).

**Includes:**

### Backend

#### Query Extension — GetCompaniesQuery
- Add `user_count: int`, `asset_count: int`, `trial_days_remaining: Optional[int]` to `CompanyListItemDto`
- `trial_days_remaining` computed from `trial_ends_at`: `max(0, (trial_ends_at - now).days)` if in trial, else `None`
- Both counts already retrieved in `GetCompanyDetailQueryHandler` — replicate the joins in the list query

#### Query Extension — GetCompanyBillingQuery (super admin)
- Add `trial_days_remaining: Optional[int]` and `trial_ends_at: Optional[datetime]` to `CompanyBillingDto`
- Mirror the same computation already used in the company-admin `GetBillingOverviewQuery`

#### HTTP Layer
- `GET /api/v1/companies` response: add `user_count`, `asset_count`, `trial_days_remaining`
- `GET /api/v1/companies/{id}/billing` response: add `trial_days_remaining`, `trial_ends_at`

### Frontend

#### CompaniesPage.tsx
- Add **Users** and **Assets** columns to the company table (numeric, compact)
- Add trial badge (`N days left`) next to company name when `trial_days_remaining !== null`

#### CompanyBillingModal.tsx
- Show trial section when `trial_days_remaining !== null`:
  - Days remaining pill
  - Trial end date formatted as `MMM DD, YYYY`

### Tests
- Unit tests: `CompanyListItemDto` includes trial/usage fields; null when not in trial
- Integration tests: list endpoint returns counts; billing detail includes trial fields

---

## F2: Stripe Invoice History

**Scope:** New endpoint `GET /api/v1/companies/{id}/invoices` that fetches the Stripe invoice list for a company. Results are fetched live from Stripe — no caching or local storage. Frontend shows invoices in the company billing modal.

**Depends on:** F1, E43 (Stripe client exists).

**Includes:**

### Backend

#### Query
- `GetCompanyInvoicesQuery(company_id: str, limit: int = 20)` → `list[InvoiceDto]`
- `InvoiceDto`: `invoice_id`, `date`, `period_start`, `period_end`, `amount_cents`, `currency`, `status`, `invoice_url`, `pdf_url`
- Returns `[]` if company has no `stripe_customer_id`
- Raises `StripeUnavailableError` on Stripe API failure → maps to `503`

#### Stripe Client Extension
- Add `list_invoices(stripe_customer_id: str, limit: int) -> list[dict]` to `core/stripe_client.py`
- When `OPEN_SOURCE_MODE=True`: returns `[]`

#### HTTP Layer
- `GET /api/v1/companies/{id}/invoices` (role: super_admin)
- Query param: `limit` (default 20, max 100)
- Response: `{"data": [InvoiceResponse, ...]}`
- Returns `404` if company not found
- Returns `503` if Stripe unavailable

### Frontend

#### CompanyBillingModal.tsx
- Add **Invoices** tab (alongside existing billing info)
- Invoice table: Date | Period | Amount | Status | Actions
- Status badge: green (paid), yellow (open), red (uncollectible/void)
- "Download PDF" and "View" links per invoice
- Loading and empty states
- Error state for Stripe unavailability

### Tests
- Unit tests: `GetCompanyInvoicesQueryHandler` — returns empty for missing Stripe ID; maps Stripe response correctly; propagates `StripeUnavailableError`
- Integration tests: `GET /companies/{id}/invoices` — mocked Stripe client returns invoice list; 404 for unknown company; 503 on Stripe error

---

## F3: Founder Dashboard

**Scope:** New super admin dashboard page with MRR, plan distribution, active trial stats, and recent signups. All data aggregated from the `companies` table — no Stripe API calls. Single new endpoint. New frontend page.

**Depends on:** F1.

**Includes:**

### Backend

#### Query
- `GetSuperAdminOverviewQuery()` → `SuperAdminOverviewDto`
- Fields:
  - `mrr_cents: int` — computed as `(premium_count × 4900) + (enterprise_count × 14900)` for `billing_status = active` and `complimentary = false`
  - `companies_by_plan: dict[str, int]` — count per plan tier
  - `active_trials: int` — companies with `trial_ends_at > now`
  - `expiring_trials_7d: int` — active trials ending within 7 days
  - `recent_signups: list[RecentSignupDto]` — last 10 companies by `created_at`, with `name`, `plan`, `trial_days_remaining`, `created_at`
- Single DB query using aggregate functions and subqueries (no N+1)

#### HTTP Layer
- `GET /api/v1/super-admin/overview` (role: super_admin)
- New router file: `adapters/http/api/super_admin/routers.py`

### Frontend

#### New Page: SuperAdminOverviewPage (`/overview`)
- Available only to `super_admin` role
- Add to sidebar navigation

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  MRR           Companies   Active Trials  Expiring
│  $X,XXX/mo     XX total    XX             XX (7d)
├─────────────────────────────────────────────────┤
│  Plan Distribution          Recent Signups
│  Free: XX  Premium: XX      [company list]
│  Enterprise: XX             [with plan + trial]
└─────────────────────────────────────────────────┘
```

- Stat cards row (MRR, total companies, active trials, expiring soon)
- Plan distribution: horizontal bar or count list
- Recent signups: compact table (name, plan badge, trial badge, date)
- Refresh button (re-fetch on demand)

### Tests
- Unit tests: `GetSuperAdminOverviewQueryHandler` — MRR calculation, trial counts, plan distribution
- Integration tests: endpoint returns correct aggregates; 403 for non-super-admin

---

## Recommended Order

1. **F1** — Pure data enrichment; no new external dependencies; highest immediate value.
2. **F2** — Adds invoice visibility; only needs existing Stripe client.
3. **F3** — Founder Dashboard; builds on enriched data from F1.

---

## Slicing Validation

- [x] No circular dependencies
- [x] Each feature independently deployable
- [x] Vertical slices (domain → infra → HTTP → frontend)
- [x] F2 and F3 can be developed in parallel after F1
- [x] No Stripe API calls in F1 or F3 — safe if Stripe is down
- [x] All acceptance criteria from requirements.md covered
- [x] Open Source mode handled: F2 returns `[]` invoices; F3 MRR = 0
