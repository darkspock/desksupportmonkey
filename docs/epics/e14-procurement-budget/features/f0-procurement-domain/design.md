# Solution Design: F0 — Procurement Domain & Infrastructure

**Requirement:** [requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `procurement_bc` (new)

## Summary

Create the entire `procurement_bc` bounded context — domain entities, enums, repository interfaces, SQLAlchemy models, Alembic migrations, and repository implementations. Extend the Asset entity with `purchase_cost_cents`. No API endpoints or frontend in this feature — pure domain and infrastructure foundation.

## Architecture Decision

A new `procurement_bc` bounded context with three subdomains (`purchase_order`, `vendor`, `budget`) follows the existing DDD pattern. Each subdomain gets its own entity, repository interface, model, and repository implementation. The PO state machine is implemented as entity behavior methods with a `VALID_TRANSITIONS` dict on the enum, matching the pattern used in request and asset status management.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ULIDMixin | `core/mixins.py` | Yes | None |
| TimestampMixin | `core/mixins.py` | Yes | None |
| Base (SQLAlchemy) | `core/database.py` | Yes | None |
| Command/CommandHandler | `src/framework/application/command_bus.py` | Yes | None |
| Query/QueryHandler | `src/framework/application/query_bus.py` | Yes | None |
| AssetType enum | `src/asset_bc/asset/domain/entities.py` | Yes (referenced by PO items) | None |
| Asset entity | `src/asset_bc/asset/domain/entities.py` | — | Add `purchase_cost_cents` field |
| Asset model | `src/asset_bc/asset/infrastructure/models.py` | — | Add `purchase_cost_cents` column |
| EquipmentProfile pattern | `src/company_bc/equipment_profile/` | Template for new BC | None |

## Implementation Plan

### 1. Domain Layer

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| PurchaseOrderStatus | `src/procurement_bc/purchase_order/domain/enums.py` | DRAFT, SUBMITTED, APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED, CANCELLED |
| EnforcementMode | `src/procurement_bc/budget/domain/enums.py` | WARN, STRICT |

**PurchaseOrderStatus** must include:
- `VALID_TRANSITIONS: dict[PurchaseOrderStatus, list[PurchaseOrderStatus]]` class attribute
- `is_terminal` property (CLOSED, CANCELLED)
- `is_countable_for_budget` property (APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED)

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| PurchaseOrder | `src/procurement_bc/purchase_order/domain/entities.py` | PO header with state machine methods |
| PurchaseOrderItem | `src/procurement_bc/purchase_order/domain/entities.py` | Line item within a PO |
| Vendor | `src/procurement_bc/vendor/domain/entities.py` | Equipment supplier |
| DepartmentBudget | `src/procurement_bc/budget/domain/entities.py` | Annual budget per department |
| CompanyProcurementConfig | `src/procurement_bc/budget/domain/entities.py` | Per-company procurement settings |

**PurchaseOrder entity:**
```python
@dataclass
class PurchaseOrder:
    id: str
    company_id: str
    po_number: str
    vendor_id: Optional[str]
    vendor_name: str
    department_id: str
    status: PurchaseOrderStatus
    total_amount_cents: int
    currency: str
    notes: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    ordered_at: Optional[datetime]
    cancellation_reason: Optional[str]
    created_by: str
    items: list[PurchaseOrderItem]
    request_ids: list[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "PurchaseOrder"  # factory, DRAFT status
    def submit(self) -> None                  # DRAFT → SUBMITTED
    def approve(self, approved_by: str) -> None  # SUBMITTED → APPROVED
    def reject(self, reason: str) -> None     # SUBMITTED → CANCELLED
    def mark_ordered(self) -> None            # APPROVED → ORDERED
    def cancel(self, reason: str) -> None     # DRAFT/SUBMITTED/APPROVED/ORDERED → CANCELLED
    def receive(self) -> None                 # Update status based on received quantities
    def close(self) -> None                   # RECEIVED/PARTIALLY_RECEIVED → CLOSED
    def recalculate_total(self) -> None       # Recompute total_amount_cents from items
    def _transition(self, target: PurchaseOrderStatus) -> None  # Validates via VALID_TRANSITIONS
```

**PurchaseOrderItem entity:**
```python
@dataclass
class PurchaseOrderItem:
    id: str
    purchase_order_id: str
    description: str
    asset_type: Optional[str]
    quantity: int
    unit_cost_cents: int
    total_cost_cents: int
    received_quantity: int
    received_at: Optional[datetime]
    linked_asset_id: Optional[str]
    notes: Optional[str]
```

**Vendor entity:**
```python
@dataclass
class Vendor:
    id: str
    company_id: str
    name: str
    contact_email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "Vendor"
    def activate(self) -> None
    def deactivate(self) -> None
```

**DepartmentBudget entity:**
```python
@dataclass
class DepartmentBudget:
    id: str
    company_id: str
    department_id: str
    fiscal_year: int
    allocated_amount_cents: int
    currency: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "DepartmentBudget"
```

**CompanyProcurementConfig entity:**
```python
@dataclass
class CompanyProcurementConfig:
    id: str
    company_id: str
    enforcement_mode: str  # "warn" or "strict"
    approval_threshold_cents: int
    po_number_prefix: str
    fiscal_year_start_month: int
    currency: str
    auto_create_assets: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    @classmethod
    def create(cls, ...) -> "CompanyProcurementConfig"
```

#### Repository Interfaces

| Interface | File Path | Key Methods |
|-----------|-----------|-------------|
| PurchaseOrderRepositoryInterface | `src/procurement_bc/purchase_order/domain/repository.py` | save, find_by_id, find_all, find_by_number, get_next_number, count_by_department_status |
| VendorRepositoryInterface | `src/procurement_bc/vendor/domain/repository.py` | save, find_by_id, find_all, find_by_name |
| DepartmentBudgetRepositoryInterface | `src/procurement_bc/budget/domain/repository.py` | save, find_by_department_year, find_all_by_company_year |
| CompanyProcurementConfigRepositoryInterface | `src/procurement_bc/budget/domain/repository.py` | save, find_by_company_id |

### 2. Infrastructure Layer

#### Repository Implementations

| Interface | Implementation | Table |
|-----------|----------------|-------|
| PurchaseOrderRepositoryInterface | PurchaseOrderRepository | purchase_orders + purchase_order_items + purchase_order_requests |
| VendorRepositoryInterface | VendorRepository | vendors |
| DepartmentBudgetRepositoryInterface | DepartmentBudgetRepository | department_budgets |
| CompanyProcurementConfigRepositoryInterface | CompanyProcurementConfigRepository | company_procurement_configs |

All repositories follow the EquipmentProfile pattern:
- Constructor takes `Session`
- `_to_entity()` static method for model → entity conversion
- Tenant isolation via `company_id` filter on all queries
- `.unique().scalar_one_or_none()` for single results
- Pagination with `.offset()` + `.limit()` + `func.count()`

**PurchaseOrderRepository** special methods:
- `get_next_number(company_id, year, prefix)` — uses `SELECT MAX(...) ... FOR UPDATE` for concurrency
- `find_all(...)` — filters by status, vendor_id, department_id, date range
- `count_by_department_status(company_id, department_id, fiscal_year_start, fiscal_year_end, statuses)` — for budget computation

#### Migrations

| Migration | Description |
|-----------|-------------|
| `create_vendors_table` | vendors table with company_id index |
| `create_purchase_orders_table` | purchase_orders table with indexes on company_id, status, vendor_id, department_id |
| `create_purchase_order_items_table` | purchase_order_items with FK to purchase_orders (CASCADE) |
| `create_purchase_order_requests_table` | join table (purchase_order_id, request_id) |
| `create_department_budgets_table` | department_budgets with unique constraint on (department_id, fiscal_year) |
| `create_company_procurement_configs_table` | company_procurement_configs with unique company_id |
| `add_purchase_cost_cents_to_assets` | Add nullable Integer column to assets table |

#### SQLAlchemy Models

All models use `Mapped[type]` annotations (SQLAlchemy 2.0), `ULIDMixin`, and `TimestampMixin`.

| Model | File Path | Table |
|-------|-----------|-------|
| PurchaseOrderModel | `src/procurement_bc/purchase_order/infrastructure/models.py` | purchase_orders |
| PurchaseOrderItemModel | `src/procurement_bc/purchase_order/infrastructure/models.py` | purchase_order_items |
| PurchaseOrderRequestModel | `src/procurement_bc/purchase_order/infrastructure/models.py` | purchase_order_requests |
| VendorModel | `src/procurement_bc/vendor/infrastructure/models.py` | vendors |
| DepartmentBudgetModel | `src/procurement_bc/budget/infrastructure/models.py` | department_budgets |
| CompanyProcurementConfigModel | `src/procurement_bc/budget/infrastructure/models.py` | company_procurement_configs |

### 3. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/asset_bc/asset/domain/entities.py` | Edit | Add `purchase_cost_cents: Optional[int] = None` field |
| `src/asset_bc/asset/infrastructure/models.py` | Edit | Add `purchase_cost_cents` Mapped column |

## Database Schema

```sql
CREATE TABLE vendors (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    name VARCHAR(200) NOT NULL,
    contact_email VARCHAR(254),
    phone VARCHAR(50),
    address TEXT,
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
CREATE INDEX ix_vendors_company_id ON vendors(company_id);

CREATE TABLE purchase_orders (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    po_number VARCHAR(30) NOT NULL,
    vendor_id VARCHAR(26) REFERENCES vendors(id),
    vendor_name VARCHAR(200) NOT NULL,
    department_id VARCHAR(26) NOT NULL REFERENCES departments(id),
    status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    total_amount_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    notes TEXT,
    approved_by VARCHAR(26),
    approved_at TIMESTAMP,
    ordered_at TIMESTAMP,
    cancellation_reason TEXT,
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(company_id, po_number)
);
CREATE INDEX ix_purchase_orders_company_id ON purchase_orders(company_id);
CREATE INDEX ix_purchase_orders_status ON purchase_orders(status);
CREATE INDEX ix_purchase_orders_vendor_id ON purchase_orders(vendor_id);
CREATE INDEX ix_purchase_orders_department_id ON purchase_orders(department_id);

CREATE TABLE purchase_order_items (
    id VARCHAR(26) PRIMARY KEY,
    purchase_order_id VARCHAR(26) NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    description VARCHAR(500) NOT NULL,
    asset_type VARCHAR(30),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_cost_cents INTEGER NOT NULL DEFAULT 0,
    total_cost_cents INTEGER NOT NULL DEFAULT 0,
    received_quantity INTEGER NOT NULL DEFAULT 0,
    received_at TIMESTAMP,
    linked_asset_id VARCHAR(26),
    notes TEXT
);
CREATE INDEX ix_purchase_order_items_po_id ON purchase_order_items(purchase_order_id);

CREATE TABLE purchase_order_requests (
    purchase_order_id VARCHAR(26) NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    request_id VARCHAR(26) NOT NULL REFERENCES requests(id),
    PRIMARY KEY (purchase_order_id, request_id)
);

CREATE TABLE department_budgets (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    department_id VARCHAR(26) NOT NULL REFERENCES departments(id),
    fiscal_year INTEGER NOT NULL,
    allocated_amount_cents INTEGER NOT NULL DEFAULT 0,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(department_id, fiscal_year)
);

CREATE TABLE company_procurement_configs (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id) UNIQUE,
    enforcement_mode VARCHAR(10) NOT NULL DEFAULT 'warn',
    approval_threshold_cents INTEGER NOT NULL DEFAULT 0,
    po_number_prefix VARCHAR(10) NOT NULL DEFAULT 'PO',
    fiscal_year_start_month INTEGER NOT NULL DEFAULT 1,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    auto_create_assets BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Asset extension
ALTER TABLE assets ADD COLUMN purchase_cost_cents INTEGER;
```

## State Machine

```
DRAFT → SUBMITTED → APPROVED → ORDERED → PARTIALLY_RECEIVED → RECEIVED → CLOSED
  ↓        ↓           ↓         ↓              ↓
CANCELLED CANCELLED CANCELLED CANCELLED      CLOSED
```

Valid transitions dict:
```python
VALID_TRANSITIONS = {
    DRAFT: [SUBMITTED, CANCELLED],
    SUBMITTED: [APPROVED, CANCELLED],
    APPROVED: [ORDERED, CANCELLED],
    ORDERED: [PARTIALLY_RECEIVED, RECEIVED, CANCELLED],
    PARTIALLY_RECEIVED: [PARTIALLY_RECEIVED, RECEIVED, CLOSED],
    RECEIVED: [CLOSED],
    CLOSED: [],
    CANCELLED: [],
}
```

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | PO state machine transitions (valid + invalid) | High |
| Unit | PO entity factory, recalculate_total | High |
| Unit | Vendor entity activate/deactivate | Medium |
| Unit | DepartmentBudget entity creation | Medium |
| Unit | PurchaseOrderStatus enum properties | Medium |

~20 unit tests total.

## Implementation Order

1. [ ] Domain: Enums (PurchaseOrderStatus, EnforcementMode)
2. [ ] Domain: Entities (PurchaseOrder, PurchaseOrderItem, Vendor, DepartmentBudget, CompanyProcurementConfig)
3. [ ] Domain: Repository interfaces (4 interfaces)
4. [ ] Infrastructure: Migrations (7 migrations)
5. [ ] Infrastructure: SQLAlchemy models (6 models)
6. [ ] Infrastructure: Repository implementations (4 repositories)
7. [ ] Collateral: Asset entity + model extension
8. [ ] Tests: Domain unit tests

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration order conflicts with concurrent work | Low | Medium | Run migrations in sequence, test with `make db-upgrade` |
| PO state machine complexity | Medium | Low | Comprehensive unit tests for all valid + invalid transitions |
| FOR UPDATE lock contention on PO numbering | Low | Medium | Scope per company+year reduces contention significantly |
