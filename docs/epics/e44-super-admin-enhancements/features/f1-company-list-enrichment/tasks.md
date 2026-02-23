# Implementation Tasks: F1 — Company List Enrichment

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-23
**Total Tasks:** 11
**Estimated Complexity:** S

---

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Constants | 1 | S |
| Application — List query | 1 | M |
| Application — Billing query | 1 | S |
| Infrastructure — Repository | 1 | M |
| HTTP — Schemas | 1 | S |
| HTTP — Router | 1 | S |
| Tests — Unit | 2 | M |
| Tests — Integration | 1 | M |
| Frontend | 2 | M |

---

## Phase 1: Domain — Constants

### TASK-001: Add PLAN_PRICE_CENTS to plan_gate.py

**Complexity:** S
**Dependencies:** None
**File:** `src/company_bc/company/domain/plan_gate.py`

Add price constants alongside existing `PLAN_USER_LIMITS` and `PLAN_ASSET_LIMITS`:

```python
PLAN_PRICE_CENTS: dict[PlanTier, int] = {
    PlanTier.FREE: 0,
    PlanTier.PREMIUM: 4900,       # $49/month
    PlanTier.ENTERPRISE: 14900,   # $149/month
    PlanTier.OPEN_SOURCE: 0,
}
```

**Acceptance Criteria:**
- [x] `PLAN_PRICE_CENTS` dict defined with all 4 plan tiers
- [x] Amounts match the Stripe prices created in the new DSM account

---

## Phase 2: Application Layer

### TASK-002: Extend ListCompaniesQuery and handler

**Complexity:** M
**Dependencies:** TASK-001
**File:** `src/company_bc/company/application/queries/list_companies.py`

- Add `in_trial: Optional[bool] = None` and `plan: Optional[str] = None` to `ListCompaniesQuery`
- Add `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status` to `CompanyListItemDto`
- Update handler to call `company_repo.find_all_with_counts()` and compute `trial_days_remaining`

**Acceptance Criteria:**
- [x] `CompanyListItemDto` has all new fields
- [x] Handler computes `trial_days_remaining` correctly (null if not in trial, integer if active)
- [x] Handler passes `in_trial` and `plan` filter params to repository

---

### TASK-003: Extend GetCompanyBillingQuery handler and DTO

**Complexity:** S
**Dependencies:** None
**File:** `src/company_bc/company/application/queries/billing/get_company_billing.py`

- Add `trial_days_remaining: Optional[int]` and `trial_ends_at: Optional[datetime]` to `CompanyBillingDto`
- Compute `trial_days_remaining` in the handler (same logic as `GetBillingOverviewQueryHandler`)

**Acceptance Criteria:**
- [x] `CompanyBillingDto` exposes `trial_days_remaining` and `trial_ends_at`
- [x] `trial_days_remaining` is null for companies not in trial or with expired trial

---

## Phase 3: Infrastructure Layer

### TASK-004: Add find_all_with_counts to CompanyRepository

**Complexity:** M
**Dependencies:** TASK-002
**File:** `src/company_bc/company/infrastructure/repository.py`

Add `find_all_with_counts(page, page_size, search, in_trial, plan)` method using correlated subqueries. Keep the existing `find_all()` untouched.

```python
# Correlated subqueries pattern:
user_count_sq = (
    select(func.count())
    .where(UserModel.company_id == CompanyModel.id)
    .where(UserModel.is_active == True)
    .correlate(CompanyModel)
    .scalar_subquery()
)
asset_count_sq = (
    select(func.count())
    .where(AssetModel.company_id == CompanyModel.id)
    .where(AssetModel.status != "decommissioned")
    .correlate(CompanyModel)
    .scalar_subquery()
)
```

Filters:
- `search` → `CompanyModel.name.ilike(f"%{search}%")`
- `in_trial=True` → `CompanyModel.trial_ends_at > func.now()`
- `plan` → `CompanyModel.plan == plan`

Returns `tuple[list[tuple[Company, int, int]], int]` — list of (entity, user_count, asset_count) + total.

**Acceptance Criteria:**
- [x] Single SQL query (no N+1 per company)
- [x] All three filters work independently and combined
- [x] Returns correct counts per company
- [x] Pagination works correctly

---

## Phase 4: HTTP Layer

### TASK-005: Extend HTTP schemas

**Complexity:** S
**Dependencies:** TASK-002, TASK-003
**File:** `adapters/http/api/companies/schemas.py`

- Add `plan`, `billing_status`, `user_count`, `asset_count`, `trial_days_remaining` to `CompanyResponse`
- Add `trial_days_remaining` and `trial_ends_at` to `CompanyBillingResponse`

**Acceptance Criteria:**
- [x] `CompanyResponse` has all new optional/required fields with correct types
- [x] `CompanyBillingResponse` has `trial_days_remaining: Optional[int]` and `trial_ends_at: Optional[datetime]`

---

### TASK-006: Update companies router

**Complexity:** S
**Dependencies:** TASK-004, TASK-005
**File:** `adapters/http/api/companies/routers.py`

- Add `in_trial: Optional[bool] = Query(None)` and `plan: Optional[str] = Query(None)` params to `GET /`
- Switch handler call from `ListCompaniesQuery` → pass new params
- Update `_to_response()` helper to map all new DTO fields
- Update billing endpoint response to include trial fields

**Acceptance Criteria:**
- [x] `GET /api/v1/companies?in_trial=true` returns only trial companies
- [x] `GET /api/v1/companies?plan=premium` returns only premium companies
- [x] `GET /api/v1/companies/{id}/billing` response includes `trial_days_remaining` and `trial_ends_at`

---

## Phase 5: Tests

### TASK-007: Unit tests — ListCompaniesQueryHandler

**Complexity:** M
**Dependencies:** TASK-002
**File:** `tests/unit/company_bc/company/application/queries/test_list_companies.py`

Test cases:
- Company in trial → `trial_days_remaining` is a positive integer
- Company with expired trial → `trial_days_remaining` is null
- Company with no `trial_ends_at` → `trial_days_remaining` is null
- DTO includes `plan` and `billing_status` from entity
- Handler passes `in_trial` filter to repository

**Acceptance Criteria:**
- [x] All test cases pass
- [x] Mock repository used (no DB)

---

### TASK-008: Unit tests — GetCompanyBillingQueryHandler trial fields

**Complexity:** S
**Dependencies:** TASK-003
**File:** `tests/unit/company_bc/company/application/queries/billing/test_get_company_billing.py`

Test cases:
- Company in trial → `trial_days_remaining` set, `trial_ends_at` set
- Company not in trial → both null

**Acceptance Criteria:**
- [x] All test cases pass

---

### TASK-009: Integration tests

**Complexity:** M
**Dependencies:** TASK-006
**File:** `tests/integration/test_companies_endpoints.py` (extend existing)

Test cases:
- `GET /companies` returns `user_count`, `asset_count`, `trial_days_remaining`, `plan`, `billing_status`
- `GET /companies?in_trial=true` returns only companies with active trial
- `GET /companies?plan=free` returns only free-plan companies
- `GET /companies/{id}/billing` returns `trial_days_remaining` and `trial_ends_at`

**Acceptance Criteria:**
- [x] All test cases pass against real PostgreSQL

---

## Phase 6: Frontend

### TASK-010: Update CompaniesPage and types

**Complexity:** M
**Dependencies:** TASK-006
**Files:**
- `web/app/src/types/index.ts`
- `web/app/src/pages/superadmin/CompaniesPage.tsx`
- `web/app/src/locales/en.ts`, `es.ts`

Changes:
- Add `plan`, `billing_status`, `user_count`, `asset_count`, `trial_days_remaining` to `Company` type
- Add Users and Assets columns to the table
- Add trial badge next to company name when `trial_days_remaining !== null`
- Add Plan filter dropdown and "In trial only" checkbox above the table

**Acceptance Criteria:**
- [x] Table shows Users and Assets columns
- [x] Trial badge shows "X days" in blue next to company name when in trial
- [x] Plan filter filters the list
- [x] Trial filter shows only companies in trial

---

### TASK-011: Update CompanyBillingModal

**Complexity:** S
**Dependencies:** TASK-006
**File:** `web/app/src/pages/superadmin/CompanyBillingModal.tsx`
**Locales:** `web/app/src/locales/en.ts`, `es.ts`

Add trial section at top of modal when `trial_days_remaining !== null`:
- Days remaining
- Trial expiry date formatted

**Acceptance Criteria:**
- [x] Trial section visible for companies in trial
- [x] Trial section hidden for companies not in trial
- [x] Shows days remaining and expiry date

---

## Dependency Graph

```
TASK-001 (plan_gate constants)
    │
    ├── TASK-002 (ListCompaniesQuery extend)
    │       │
    │       ├── TASK-004 (Repository find_all_with_counts)
    │       │       │
    │       │       └── TASK-006 (Router update)
    │       │               │
    │       │               ├── TASK-009 (Integration tests)
    │       │               ├── TASK-010 (Frontend CompaniesPage)
    │       │               └── TASK-011 (Frontend BillingModal)
    │       │
    │       └── TASK-007 (Unit tests - list handler)
    │
    ├── TASK-003 (GetCompanyBillingQuery extend)
    │       └── TASK-008 (Unit tests - billing handler)
    │
    └── TASK-005 (HTTP schemas extend)
```

## Execution Order

**Batch 1 (sequential):** TASK-001 → TASK-002 + TASK-003 (parallel) → TASK-004 + TASK-005 (parallel) → TASK-006
**Batch 2 (parallel after TASK-006):** TASK-007, TASK-008, TASK-009
**Batch 3 (parallel after tests pass):** TASK-010, TASK-011

---

## Final Checklist

- [x] All tasks completed
- [x] `make test` passes (unit tests)
- [ ] `make test-integration` passes
- [ ] `make lint` passes (mypy + flake8)
- [x] No N+1 queries in list endpoint
