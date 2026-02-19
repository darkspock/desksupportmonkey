# Solution Design: F4 — Budget Allocation & Enforcement

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc.budget`

## Summary

Department budget management and enforcement. Set/view budgets, compute spending, enforce limits on PO approval (warn/strict modes), fire 80% threshold alerts. Budget display on departments page. Hooks into F3's approve handler for enforcement.

## Architecture Decision

Budget allocation is a simple upsert command. Spending is computed at query time (sum of PO totals in countable statuses) — not stored, to avoid staleness. The BudgetChecker service is a domain service injected into the PO approval flow. In strict mode, it raises an exception before approval; in warn mode, it returns a warning included in the response. The 80% threshold alert uses the existing notification pub/sub.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| DepartmentBudget entity + repo | `src/procurement_bc/budget/` (F0) | Yes | None |
| CompanyProcurementConfig entity + repo | `src/procurement_bc/budget/` (F0) | Yes | None |
| PO repository | `src/procurement_bc/purchase_order/` (F0) | Yes | Use count_by_department_status |
| ApprovePurchaseOrderCommandHandler | F3 | — | Inject BudgetChecker |
| Notification subscriber/resolver | `src/notification_bc/` | Template | Add budget.threshold_reached |
| DeleteDepartmentCommandHandler | `src/company_bc/department/` | — | Add PO count check |

## Implementation Plan

### 1. Application Layer

#### Services

| Service | File Path | Description |
|---------|-----------|-------------|
| BudgetChecker | `src/procurement_bc/budget/application/services/budget_checker.py` | Compute spending, check enforcement, detect threshold |

```python
class BudgetCheckResult:
    allowed: bool
    warning: Optional[str]  # None if no warning
    remaining_cents: int
    spent_cents: int
    allocated_cents: int

class BudgetChecker:
    def __init__(
        self,
        budget_repo: DepartmentBudgetRepositoryInterface,
        po_repo: PurchaseOrderRepositoryInterface,
        config_repo: CompanyProcurementConfigRepositoryInterface,
    ):
        ...

    def check_approval(
        self, company_id: str, department_id: str, po_total_cents: int
    ) -> BudgetCheckResult:
        # 1. Get config (enforcement mode)
        # 2. Get budget for department + current fiscal year
        # 3. Compute spending from POs in countable statuses
        # 4. Check if po_total_cents + spent > allocated
        # 5. Return result based on enforcement mode

    def compute_spending(
        self, company_id: str, department_id: str, fiscal_year: int
    ) -> int:
        # Sum of PO totals in APPROVED/ORDERED/PARTIALLY_RECEIVED/RECEIVED/CLOSED
        # for the given department and fiscal year

    def get_fiscal_year(self, start_month: int) -> int:
        # Given start_month and current date, return fiscal year integer

    def check_threshold(
        self, company_id: str, department_id: str, spent_before: int, spent_after: int, allocated: int
    ) -> bool:
        # Return True if threshold was crossed (80%)
```

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| SetDepartmentBudgetCommand | SetDepartmentBudgetCommandHandler | Upsert budget for department + fiscal year |

```python
@dataclass
class SetDepartmentBudgetCommand(Command):
    company_id: str
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    currency: str
    performed_by: str = ""
```

Handler: validates amount >= 0, upserts via repository.

#### Queries

| Query | Handler | Description |
|-------|---------|-------------|
| GetDepartmentBudgetQuery | GetDepartmentBudgetQueryHandler | Budget + spending for a department |
| GetBudgetSummaryQuery | GetBudgetSummaryQueryHandler | All departments' budgets for a fiscal year |

```python
@dataclass
class GetDepartmentBudgetQuery(Query):
    company_id: str
    department_id: str
    fiscal_year: Optional[int] = None  # defaults to current

@dataclass
class GetBudgetSummaryQuery(Query):
    company_id: str
    fiscal_year: Optional[int] = None  # defaults to current
```

Return types include computed `spent_cents` and `remaining_cents`.

### 2. Budget Enforcement Integration

Modify `ApprovePurchaseOrderCommandHandler` (from F3):
1. Inject `BudgetChecker`
2. Before calling `po.approve()`, call `budget_checker.check_approval(...)`
3. If strict mode and not allowed → raise `BudgetExceededException`
4. If warn mode and not allowed → proceed but set warning flag
5. After approval: check if 80% threshold was crossed → emit `budget.threshold_reached`

### 3. Department Delete Constraint

Modify `DeleteDepartmentCommandHandler` in `src/company_bc/department/application/commands/delete_department.py`:
- Before deactivation, check if department has POs in non-terminal status (not CLOSED, not CANCELLED)
- If yes → raise `DepartmentHasOpenPOsError`
- Follows existing pattern: department already blocks deletion when users are assigned

### 4. Notifications

| Event | Targets | Content |
|-------|---------|---------|
| `budget.threshold_reached` | Department manager + all admins | Department name, utilization %, allocated, spent |

### 5. HTTP Layer

#### Endpoints

| Method | Route | Role | Description |
|--------|-------|------|-------------|
| PUT | `/api/v1/departments/{id}/budget` | admin | Set/update budget for fiscal year |
| GET | `/api/v1/departments/{id}/budget` | admin | Get budget + spending for department |
| GET | `/api/v1/budgets/summary` | admin | All departments budget summary |

#### Schemas

```python
class BudgetSetRequest(BaseModel):
    fiscal_year: Optional[int] = None  # defaults to current
    allocated_amount_cents: int = Field(ge=0)

class BudgetResponse(BaseModel):
    id: Optional[str]
    department_id: str
    department_name: str
    fiscal_year: int
    allocated_amount_cents: int
    spent_cents: int
    remaining_cents: int
    utilization_pct: float
    currency: str

class BudgetSummaryResponse(BaseModel):
    fiscal_year: int
    total_allocated_cents: int
    total_spent_cents: int
    departments: list[BudgetResponse]
```

### 6. Frontend Changes

| Page | Change | Description |
|------|--------|-------------|
| DepartmentsPage | Edit | Add budget columns (allocated/spent/remaining), "Set Budget" action |
| PurchaseOrderFormPage | Edit | Show department remaining budget when dept is selected |

- i18n: ~20 keys (EN + ES)

### 7. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/procurement_bc/purchase_order/application/commands/approve_po.py` | Edit | Inject BudgetChecker, add enforcement |
| `src/company_bc/department/application/commands/delete_department.py` | Edit | Add PO count check |
| `src/notification_bc/notification/domain/enums.py` | Edit | Add budget.threshold_reached |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit | Handle budget event |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit | Resolve budget event targets |
| `adapters/http/api/departments/routers.py` | Edit | Add budget endpoints |
| `web/app/src/pages/admin/DepartmentsPage.tsx` | Edit | Budget columns |
| `web/app/src/pages/admin/PurchaseOrderFormPage.tsx` | Edit | Remaining budget display |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | BudgetChecker.check_approval (warn mode, strict mode, no budget) | High |
| Unit | BudgetChecker.compute_spending | High |
| Unit | BudgetChecker.check_threshold (cross, no cross, already over) | High |
| Unit | BudgetChecker.get_fiscal_year (various months) | Medium |
| Unit | SetDepartmentBudgetCommandHandler (create + update) | High |
| Unit | GetDepartmentBudgetQueryHandler (with spending) | Medium |
| Unit | GetBudgetSummaryQueryHandler | Medium |
| Unit | ApprovePO with budget enforcement (strict block, warn allow) | High |
| Unit | DeleteDepartment blocked by open POs | Medium |
| Integration | Budget CRUD endpoints | High |
| Integration | Budget summary endpoint | Medium |
| Integration | PO approval with strict budget enforcement | High |
| Integration | Department delete blocked by POs | Medium |

~22 tests total (14 unit + 8 integration).

## Implementation Order

1. [ ] Application: BudgetChecker service
2. [ ] Application: SetDepartmentBudgetCommand + handler
3. [ ] Application: GetDepartmentBudgetQuery + handler
4. [ ] Application: GetBudgetSummaryQuery + handler
5. [ ] Integration: Modify ApprovePO handler for budget enforcement
6. [ ] Integration: Modify DeleteDepartment handler for PO check
7. [ ] Notifications: budget.threshold_reached event
8. [ ] HTTP: Budget schemas
9. [ ] HTTP: Budget endpoints (on departments router + budgets router)
10. [ ] Frontend: DepartmentsPage budget columns, PO form budget display, i18n
11. [ ] Tests: Unit tests
12. [ ] Tests: Integration tests

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Budget computation performance (many POs) | Low | Medium | Indexed query on department_id + status + date |
| Race condition: two POs approved simultaneously exceed budget | Low | Medium | In strict mode, the check runs inside the request transaction |
| Fiscal year edge cases | Medium | Low | Comprehensive unit tests for boundary months |
