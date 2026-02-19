# Tasks: F4 — Budget Allocation & Enforcement

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 15
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Application - Services | 1 | L |
| Application - Commands | 1 | S |
| Application - Queries | 2 | S-M |
| Integration - Approve handler | 1 | M |
| Integration - Delete dept | 1 | S |
| Notifications | 1 | S |
| HTTP - Schemas + Deps | 2 | S |
| HTTP - Endpoints | 1 | M |
| Frontend | 1 | M |
| Tests - Unit | 1 | L |
| Tests - Integration | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Application Layer — Services

### 1. BudgetChecker service
- [x] Create `src/procurement_bc/budget/application/services/budget_checker.py`
  - `BudgetCheckResult` dataclass: allowed (bool), warning (Optional[str]), remaining_cents, spent_cents, allocated_cents
  - `BudgetChecker(budget_repo, po_repo, config_repo)` constructor
  - `check_approval(company_id, department_id, po_total_cents) -> BudgetCheckResult`:
    1. Get config → enforcement mode
    2. Get budget for dept + current fiscal year
    3. If no budget → return allowed=True (no enforcement)
    4. Compute spending from POs in countable statuses
    5. Check if po_total + spent > allocated
    6. If strict and over → allowed=False, warning=shortfall message
    7. If warn and over → allowed=True, warning=over-budget message
    8. Return result
  - `compute_spending(company_id, department_id, fiscal_year) -> int`:
    - Query PO repo for sum of totals in countable statuses for dept + fiscal year range
  - `get_fiscal_year(start_month: int) -> int`:
    - Given current date and start_month, return fiscal year integer
    - Example: start_month=4, current=March 2027 → FY 2026; April 2027 → FY 2027
  - `check_threshold(spent_before, spent_after, allocated) -> bool`:
    - Return True if 80% threshold was crossed (before < 80% AND after >= 80%)

---

## Phase 1: Application Layer — Commands

### 2. SetDepartmentBudgetCommand + handler
- [x] Create `src/procurement_bc/budget/application/commands/set_budget.py`
  - `SetDepartmentBudgetCommand(Command)`: company_id, department_id, fiscal_year, allocated_amount_cents, currency, performed_by
  - Handler: validate amount >= 0, upsert via repo (find_by_department_year → update or create)

---

## Phase 1: Application Layer — Queries

### 3. GetDepartmentBudgetQuery + handler
- [x] Create `src/procurement_bc/budget/application/queries/get_budget.py`
  - `GetDepartmentBudgetQuery(Query)`: company_id, department_id, fiscal_year?
  - Handler:
    1. Default fiscal_year to current (via BudgetChecker.get_fiscal_year)
    2. Find budget by dept + year
    3. Compute spending via BudgetChecker
    4. Return: budget entity + spent_cents + remaining_cents + utilization_pct

### 4. GetBudgetSummaryQuery + handler
- [x] Create `src/procurement_bc/budget/application/queries/get_summary.py`
  - `GetBudgetSummaryQuery(Query)`: company_id, fiscal_year?
  - Handler:
    1. Get all departments for company
    2. Get all budgets for fiscal year
    3. Compute spending per department
    4. Return: fiscal_year, total_allocated, total_spent, list of department budgets with spending

---

## Phase 2: Integration — Existing Handler Modifications

### 5. Add budget enforcement to ApprovePO handler
- [x] Edit `src/procurement_bc/purchase_order/application/commands/approve_po.py`
  - Add optional `budget_checker: Optional[BudgetChecker] = None` constructor param
  - Before `po.approve()`:
    1. If budget_checker provided → call `check_approval()`
    2. If strict mode and not allowed → raise `BudgetExceededException(shortfall_cents)`
    3. If warn mode and over → log warning, set response flag
  - After approval:
    1. Compute spending before and after
    2. If threshold crossed → emit `budget.threshold_reached` event

### 6. Add PO check to DeleteDepartment handler
- [x] Edit `src/company_bc/department/application/commands/delete_department.py`
  - Add PO repository dependency
  - Before deactivation: check if department has POs in non-terminal statuses
  - If open POs exist → raise `DepartmentHasOpenPOsError`
  - Follows existing pattern: department already blocks when users are assigned

---

## Phase 3: Notifications

### 7. Budget threshold notification
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add `budget.threshold_reached` event type
- [x] Edit `src/notification_bc/notification/application/services/notification_subscriber.py`
  - Handle budget.threshold_reached: "Department {name} has reached {pct}% of its budget ({spent}/{allocated})"
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - budget.threshold_reached → department manager + all admins in company

---

## Phase 4: HTTP Layer

### 8. Budget schemas
- [x] Create `adapters/http/api/budgets/schemas.py`
  - `BudgetSetRequest`: fiscal_year? (int), allocated_amount_cents (ge=0)
  - `BudgetResponse`: id?, department_id, department_name, fiscal_year, allocated_amount_cents, spent_cents, remaining_cents, utilization_pct, currency
  - `BudgetSummaryResponse`: fiscal_year, total_allocated_cents, total_spent_cents, departments[]

### 9. Budget dependencies
- [x] Create `adapters/http/api/budgets/dependencies.py`
  - `get_budget_repo(db) -> DepartmentBudgetRepository`
  - `get_po_repo(db) -> PurchaseOrderRepository`
  - `get_config_repo(db) -> CompanyProcurementConfigRepository`
  - `get_budget_checker(db) -> BudgetChecker` (convenience factory)

### 10. Budget endpoints
- [x] Add budget endpoints to department router or create new budget router:
  - `PUT /api/v1/departments/{id}/budget` — set budget (admin)
  - `GET /api/v1/departments/{id}/budget` — get budget + spending (admin)
  - `GET /api/v1/budgets/summary` — all departments summary (admin)
  - Response format: `{"data": {...}}`
- [x] Create `adapters/http/api/budgets/__init__.py` if using separate router
- [x] Register budget router in `app.py` if separate

---

## Phase 5: Frontend

### 11. Budget frontend changes
- [x] Edit `web/app/src/pages/admin/DepartmentsPage.tsx`
  - Add budget columns to department table: Allocated, Spent, Remaining
  - Color coding: green (< 80%), yellow (80-100%), red (> 100%)
  - "Set Budget" button per department → modal with amount input
  - Fetch budget data alongside departments
- [x] Edit `web/app/src/pages/admin/PurchaseOrderFormPage.tsx`
  - When department is selected, show remaining budget below department picker
  - Format: "Department budget remaining: $X,XXX.XX of $Y,YYY.YY"
- [x] Edit `web/app/src/locales/en.ts` — add ~20 budget keys
- [x] Edit `web/app/src/locales/es.ts` — add ~20 budget keys

---

## Phase 6: Tests

### 12. Unit tests
- [x] Create `tests/unit/procurement_bc/budget/application/services/test_budget_checker.py`
  - check_approval: warn mode, over budget → allowed with warning
  - check_approval: strict mode, over budget → not allowed
  - check_approval: under budget → allowed, no warning
  - check_approval: no budget set → allowed
  - compute_spending: sums PO totals in countable statuses
  - compute_spending: excludes DRAFT, SUBMITTED, CANCELLED
  - get_fiscal_year: start_month=1 (January), current=June → same year
  - get_fiscal_year: start_month=4 (April), current=March → previous year
  - get_fiscal_year: start_month=4 (April), current=April → current year
  - check_threshold: cross from 79% to 81% → True
  - check_threshold: already at 85%, goes to 90% → False (already past)
  - check_threshold: stays at 70% → False
- [x] Create `tests/unit/procurement_bc/budget/application/commands/test_set_budget.py`
  - Set new budget, update existing budget, negative amount → error
- [x] Create `tests/unit/procurement_bc/purchase_order/application/commands/test_approve_with_budget.py`
  - Approve with strict enforcement → blocked
  - Approve with warn enforcement → warning
  - Approve without budget → succeeds
  - Approve triggers threshold notification
- [x] Create `tests/unit/company_bc/department/application/commands/test_delete_with_pos.py`
  - Delete blocked by open POs
  - Delete allowed when all POs are terminal
- ~14 unit tests

### 13. Integration tests
- [x] Create `tests/integration/test_budgets_endpoints.py`
  - PUT set budget → 200
  - GET budget → 200 with spending
  - GET summary → 200 with all departments
  - Negative budget amount → 422
  - Non-admin → 403
- [x] Edit `tests/integration/test_purchase_orders_endpoints.py`
  - Approve PO with strict enforcement over budget → 409
  - Approve PO with warn enforcement over budget → 200 with warning
- [x] Edit `tests/integration/test_departments_endpoints.py`
  - Delete department with open POs → 409
- ~8 integration tests

---

## Phase 7: Verification

### 14. Verify
- [x] Lint passes: `make lint`
- [x] Unit tests pass: `make test`
- [x] Integration tests pass: `make test-integration`
- [x] Frontend builds: `cd web/app && npm run build`
- [x] TypeScript compiles: `cd web/app && npx tsc --noEmit`
- [x] Budget enforcement works end-to-end: set budget → create PO → approve → check enforcement

---

## Dependency Graph

```
BudgetChecker (1) — depends on F0 repos
  └── SetBudgetCommand (2) — depends on F0 budget repo
  └── GetBudgetQuery (3) — depends on BudgetChecker
  └── GetSummaryQuery (4) — depends on BudgetChecker
  └── ApprovePO integration (5) — depends on BudgetChecker + F3 approve handler
  └── DeleteDept integration (6) — depends on F0 PO repo
        └── Notifications (7) — depends on integration points
              └── Schemas (8) + Deps (9) — depend on services
                    └── Endpoints (10) — depends on schemas + commands + queries
                          └── Frontend (11) — depends on API
                                └── Tests (12-13) — after all code
```

## Execution Order

**Batch 1:** Task 1 (BudgetChecker service)
**Batch 2 (Parallel):** Tasks 2-4 (command + queries)
**Batch 3 (Parallel):** Tasks 5-6 (handler integrations)
**Batch 4:** Task 7 (notifications)
**Batch 5 (Parallel):** Tasks 8-9 (schemas + deps)
**Batch 6:** Task 10 (endpoints)
**Batch 7:** Task 11 (frontend)
**Batch 8 (Parallel):** Tasks 12-13 (tests)
**Batch 9:** Task 14 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (unit + integration)
- [x] mypy passes
- [x] Frontend builds
- [x] Budget CRUD working
- [x] Enforcement modes working (warn + strict)
- [x] 80% threshold alert fires
- [x] Department deletion blocked by open POs
