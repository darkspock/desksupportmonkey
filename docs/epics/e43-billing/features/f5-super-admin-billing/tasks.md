# Tasks: F5 - Super Admin Billing Management

**Epic:** [slicing.md](../../slicing.md)
**Depends on:** [F4](../f4-plan-enforcement/tasks.md)
**Date:** 2026-02-22

---

## Phase 1: Application Layer — Queries & Commands

### T1.1: CompanyBillingDto + GetCompanyBillingQuery + Handler
- [ ] **File:** `src/company_bc/company/application/queries/billing/get_company_billing.py` (NEW)
- `CompanyBillingDto`:
  - `company_id: str`, `company_name: str`, `plan: PlanTier`, `billing_status: BillingStatus`
  - `complimentary: bool`, `stripe_customer_id: Optional[str]`, `stripe_subscription_id: Optional[str]`
  - `current_period_end: Optional[datetime]`, `pending_downgrade_plan: Optional[PlanTier]`, `grace_period_started_at: Optional[datetime]`
- Handler: find company by id → raise `CompanyNotFoundError` if not found → return `CompanyBillingDto`

### T1.2: OverrideCompanyPlanCommand + Handler
- [ ] **File:** `src/company_bc/company/application/commands/billing/override_company_plan.py` (NEW)
- `@dataclass class OverrideCompanyPlanCommand(Command):`
  - `company_id: str`, `new_plan: PlanTier`
- Handler:
  1. Find company → raise `CompanyNotFoundError` if not found
  2. Set `company.plan = new_plan`, `company.billing_status = BillingStatus.ACTIVE` directly (no Stripe)
  3. Save company

### T1.3: GrantComplimentaryPlanCommand + Handler
- [ ] **File:** `src/company_bc/company/application/commands/billing/grant_complimentary_plan.py` (NEW)
- `@dataclass class GrantComplimentaryPlanCommand(Command):`
  - `company_id: str`, `plan: PlanTier`
- Handler:
  1. Find company → raise `CompanyNotFoundError` if not found
  2. If `company.stripe_subscription_id` is not None: call `stripe_client.cancel_subscription(...)`, set `company.stripe_subscription_id = None`
  3. Call `company.grant_complimentary(plan)`
  4. Save company

### T1.4: RevokeComplimentaryPlanCommand + Handler
- [ ] **File:** `src/company_bc/company/application/commands/billing/revoke_complimentary_plan.py` (NEW)
- `@dataclass class RevokeComplimentaryPlanCommand(Command):`
  - `company_id: str`
- Handler:
  1. Find company → raise `CompanyNotFoundError` if not found
  2. If `company.complimentary == False`: raise `ValueError("Company is not on complimentary plan")`
  3. Call `company.revoke_complimentary()` → sets `complimentary=False`, `plan=FREE`, `billing_status=OVER_LIMIT`
  4. Save company

---

## Phase 2: HTTP Layer

### T2.1: Add billing schemas to companies schemas
- [ ] **File:** `adapters/http/api/companies/schemas.py` (MODIFY)
- `CompanyBillingResponse`: mirrors `CompanyBillingDto`
- `OverridePlanRequest`: `new_plan: str` (validated against PlanTier values)
- `GrantComplimentaryRequest`: `plan: str` (validated against PlanTier values)

### T2.2: Add billing endpoints to companies router
- [ ] **File:** `adapters/http/api/companies/routers.py` (MODIFY)
- `GET /api/v1/companies/{id}/billing` (super_admin): returns `CompanyBillingResponse`
  - Map `CompanyNotFoundError` → 404
- `PATCH /api/v1/companies/{id}/billing/plan` (super_admin): overrides plan
  - Body: `OverridePlanRequest`
  - Returns updated `CompanyBillingResponse`
- `POST /api/v1/companies/{id}/billing/complimentary` (super_admin): grants complimentary
  - Body: `GrantComplimentaryRequest`
  - Returns updated `CompanyBillingResponse`
  - Map `StripeUnavailableError` → 503
- `DELETE /api/v1/companies/{id}/billing/complimentary` (super_admin): revokes complimentary
  - Returns updated `CompanyBillingResponse`
  - Map `ValueError` (not complimentary) → 422

---

## Phase 3: Frontend

### T3.1: Extend CompaniesPage with billing columns
- [ ] **File:** `web/app/src/pages/CompaniesPage.tsx` (MODIFY)
- Add "Plan" column: plan badge per row
- Add "Billing Status" column: status badge per row
- Add "Billing" action button per row → opens `CompanyBillingModal`
- Fetch billing data via `GET /api/v1/companies/{id}/billing` (per row, on demand or batch)

### T3.2: Create CompanyBillingModal
- [ ] **File:** `web/app/src/pages/companies/CompanyBillingModal.tsx` (NEW)
- Displays: current plan, billing status, complimentary badge, Stripe IDs, period end, pending downgrade
- "Override Plan" section: plan dropdown + "Apply" → `PATCH /companies/{id}/billing/plan`
- "Grant Complimentary" section: plan dropdown + "Grant" → `POST /companies/{id}/billing/complimentary`
- "Revoke Complimentary" button (shown only when `complimentary=true`) → `DELETE /companies/{id}/billing/complimentary`
- All mutations invalidate company list + billing queries on success

### T3.3: Add i18n strings
- [ ] **Files:** `web/app/src/lib/i18n/en.ts`, `es.ts` (MODIFY)
- Keys: `companies.billing_modal_title`, `companies.plan_column`, `companies.billing_status_column`
- Keys: `companies.override_plan`, `companies.grant_complimentary`, `companies.revoke_complimentary`, `companies.billing_action`

---

## Phase 4: Tests

### T4.1: Unit tests — OverrideCompanyPlanCommand
- [ ] **File:** `tests/unit/company_bc/company/application/commands/billing/test_override_company_plan.py` (NEW)
- Test: plan overridden, billing_status = ACTIVE
- Test: company not found → CompanyNotFoundError

### T4.2: Unit tests — GrantComplimentaryPlanCommand
- [ ] **File:** `tests/unit/company_bc/company/application/commands/billing/test_grant_complimentary_plan.py` (NEW)
- Test: complimentary granted, plan set, billing_status = ACTIVE
- Test: active Stripe subscription → `cancel_subscription` called
- Test: no Stripe subscription → no cancel call
- Test: company not found → CompanyNotFoundError

### T4.3: Unit tests — RevokeComplimentaryPlanCommand
- [ ] **File:** `tests/unit/company_bc/company/application/commands/billing/test_revoke_complimentary_plan.py` (NEW)
- Test: complimentary revoked → plan = FREE, billing_status = OVER_LIMIT
- Test: company not on complimentary → ValueError
- Test: company not found → CompanyNotFoundError

### T4.4: Integration tests — super admin billing endpoints
- [ ] **File:** `tests/integration/test_companies_billing_endpoints.py` (NEW)
- Test: `GET /companies/{id}/billing` → 200 for super_admin, 403 for non-super_admin
- Test: `PATCH .../billing/plan` → plan overridden
- Test: `POST .../billing/complimentary` → complimentary granted, Stripe sub cancelled (mocked)
- Test: `POST .../billing/complimentary` when Stripe fails → 503
- Test: `DELETE .../billing/complimentary` → revoked, billing_status = OVER_LIMIT
- Test: `DELETE` on non-complimentary company → 422

---

## Phase 5: Verification & Progress Tracking

### T5.1: Run linter
- [ ] `make lint`

### T5.2: Run all tests
- [ ] `make test` + `make test-integration`

### T5.3: Update slicing.md — mark all features Done
- [ ] Update `docs/epics/e43-billing/slicing.md` — set Status = "Done" for all F0-F5 rows (only when all tasks complete)

### T5.4: Update roadmap
- [ ] Update `docs/product/roadmap.md` — set E43 Status = "Done" (only when all features complete)

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Commands/Queries | T1.1-T1.4 | 4 new | — |
| 2. HTTP | T2.1-T2.2 | — | 1 modified (companies router + schemas) |
| 3. Frontend | T3.1-T3.3 | 1 new modal | 1 modified (CompaniesPage) + 2 i18n |
| 4. Tests | T4.1-T4.4 | 4 new | — |
| 5. Verification | T5.1-T5.4 | — | — |
