# Feature F1: Company List Enrichment

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** E43 (Company entity has `trial_ends_at`, repository has `count_users`/`count_assets`)
**Complexity:** S

---

## Scope

### Included

- Add `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status` to the companies list response
- Add `in_trial` and `plan` query filters to `GET /api/v1/companies`
- Add `trial_days_remaining` and `trial_ends_at` to the super admin company billing endpoint
- Frontend: add Users and Assets columns, trial badge, plan/trial filters to CompaniesPage
- Frontend: show trial expiry info in CompanyBillingModal
- Add plan price amount constants (`PLAN_PRICE_PREMIUM_CENTS`, `PLAN_PRICE_ENTERPRISE_CENTS`) to `plan_gate.py` for use in F3

### Excluded

- Invoice history (F2)
- Revenue overview (F3)
- Notifications on trial expiry

---

## User Value

Super admin can see at a glance how much each company is using, which companies are in trial and for how many more days, and filter by plan or trial status — without clicking into each company individually.

---

## Acceptance Criteria

- [ ] `GET /api/v1/companies` response includes `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status` per company
- [ ] `trial_days_remaining` is `null` for companies not in trial; a positive integer for active trials
- [ ] `?in_trial=true` filter returns only companies currently in trial
- [ ] `?plan=premium` filter returns only companies on the specified plan
- [ ] Both filters can be combined with `search` and pagination
- [ ] `GET /api/v1/companies/{id}/billing` response includes `trial_days_remaining` and `trial_ends_at`
- [ ] All counts computed in a single batch query (no N+1 per company)
- [ ] Frontend company table shows Users, Assets columns
- [ ] Frontend shows trial badge with days remaining next to company name when in trial
- [ ] Frontend has filter dropdowns for Plan and Trial Status
- [ ] Frontend billing modal shows trial expiry section when company is in trial
- [ ] 403 for non-super-admin on all endpoints (unchanged)

---

## Technical Scope

### Entities (used from dependencies)

- `Company` (from E43) — `trial_ends_at`, `plan`, `billing_status`
- `CompanyRepository` — `count_users()`, `count_assets()` (existing, add batch variant)

### Key Components

**Backend:**
- `ListCompaniesQuery` — add `in_trial: Optional[bool]`, `plan: Optional[str]` params
- `ListCompaniesQueryHandler` — batch-fetch counts, compute `trial_days_remaining`
- `CompanyListItemDto` — add `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status`
- `CompanyRepository.find_all()` — add filter support + batch count subquery
- `CompanyResponse` schema (HTTP) — add new fields
- `GetCompanyBillingQueryHandler` — add `trial_days_remaining`, `trial_ends_at` to DTO
- `CompanyBillingResponse` schema — add new fields
- `plan_gate.py` — add `PLAN_PRICE_PREMIUM_CENTS = 4900` and `PLAN_PRICE_ENTERPRISE_CENTS = 14900` constants

**Frontend:**
- `CompaniesPage.tsx` — new columns, filters, trial badge
- `CompanyBillingModal.tsx` — trial expiry section
- `web/app/src/types/index.ts` — add `plan`, `billing_status`, `user_count`, `asset_count`, `trial_days_remaining` to Company type

---

## Notes

**Avoiding N+1:** The current `count_users()` and `count_assets()` methods make one query per company. For the list endpoint, use a single query with correlated subqueries or a GROUP BY join to fetch all counts in one round-trip.

**Plan price constants:** Adding `PLAN_PRICE_PREMIUM_CENTS` and `PLAN_PRICE_ENTERPRISE_CENTS` to `plan_gate.py` establishes the project as the source of truth for pricing — Stripe prices were created with these amounts and should always match.
