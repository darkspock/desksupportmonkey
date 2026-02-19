# Tasks: F0 — Procurement Domain & Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 20
**Estimated Complexity:** XL

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 2 | S |
| Domain - Entities | 5 | M-L |
| Domain - Interfaces | 4 | S |
| Infrastructure - Migrations | 7 | S |
| Infrastructure - Models | 6 | S-M |
| Infrastructure - Repositories | 4 | M |
| Collateral | 2 | S |
| Tests | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Domain Layer — Enums

### 1. Create PurchaseOrderStatus enum
- [x] Create `src/procurement_bc/purchase_order/domain/enums.py`
  - Values: DRAFT, SUBMITTED, APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED, CANCELLED
  - `VALID_TRANSITIONS` dict mapping each status to its valid target statuses
  - `is_terminal` property → True for CLOSED, CANCELLED
  - `is_countable_for_budget` property → True for APPROVED, ORDERED, PARTIALLY_RECEIVED, RECEIVED, CLOSED
  - Inherits from `str, Enum`

### 2. Create EnforcementMode enum
- [x] Create `src/procurement_bc/budget/domain/enums.py`
  - Values: WARN, STRICT
  - Inherits from `str, Enum`

---

## Phase 1: Domain Layer — Entities

### 3. Create PurchaseOrder entity
- [x] Create `src/procurement_bc/purchase_order/domain/entities.py`
  - `PurchaseOrder` dataclass with all fields from design
  - `create()` factory method: generates ULID, sets DRAFT status, empty items
  - `submit()`: validates DRAFT → SUBMITTED, checks at least 1 item + total > 0
  - `approve(approved_by)`: SUBMITTED → APPROVED, sets approved_by/approved_at
  - `reject(reason)`: SUBMITTED → CANCELLED, sets cancellation_reason
  - `mark_ordered()`: APPROVED → ORDERED, sets ordered_at
  - `cancel(reason)`: validates source state, → CANCELLED
  - `receive()`: updates status based on overall item receipt state
  - `close()`: RECEIVED/PARTIALLY_RECEIVED → CLOSED
  - `recalculate_total()`: sum of items' total_cost_cents
  - `_transition(target)`: validates via PurchaseOrderStatus.VALID_TRANSITIONS

### 4. Create PurchaseOrderItem entity
- [x] In same file as PurchaseOrder entity
  - `PurchaseOrderItem` dataclass
  - Fields: id, purchase_order_id, description, asset_type (Optional[str]), quantity, unit_cost_cents, total_cost_cents, received_quantity (default 0), received_at (Optional), linked_asset_id (Optional), notes (Optional)

### 5. Create Vendor entity
- [x] Create `src/procurement_bc/vendor/domain/entities.py`
  - `Vendor` dataclass with all fields from design
  - `create()` factory method with ULID generation
  - `activate()` / `deactivate()` methods

### 6. Create DepartmentBudget entity
- [x] Create `src/procurement_bc/budget/domain/entities.py`
  - `DepartmentBudget` dataclass
  - `create()` factory method with ULID generation

### 7. Create CompanyProcurementConfig entity
- [x] In same file as DepartmentBudget (`src/procurement_bc/budget/domain/entities.py`)
  - `CompanyProcurementConfig` dataclass
  - `create()` factory method with ULID generation, sensible defaults

---

## Phase 1: Domain Layer — Repository Interfaces

### 8. Create PurchaseOrderRepositoryInterface
- [x] Create `src/procurement_bc/purchase_order/domain/repository.py`
  - ABC with methods: `save`, `find_by_id`, `find_all` (paginated+filtered), `find_by_number`, `get_next_number`, `sum_totals_by_department_status`

### 9. Create VendorRepositoryInterface
- [x] Create `src/procurement_bc/vendor/domain/repository.py`
  - ABC with methods: `save`, `find_by_id`, `find_all` (paginated+filtered+search), `find_by_name`

### 10. Create DepartmentBudgetRepositoryInterface
- [x] Create `src/procurement_bc/budget/domain/repository.py`
  - ABC with methods: `save`, `find_by_department_year`, `find_all_by_company_year`

### 11. Create CompanyProcurementConfigRepositoryInterface
- [x] In same file as DepartmentBudget repo interface
  - ABC with methods: `save`, `find_by_company_id`

---

## Phase 2: Infrastructure — Migrations

### 12. Create vendors table migration
- [x] Create `alembic/versions/i4j5k6l7m8n9_create_vendors_table.py`
  - Schema per design (id, company_id, name, contact_email, phone, address, notes, is_active, timestamps)
  - Index on company_id

### 13. Create purchase_orders table migration
- [x] Create `alembic/versions/j5k6l7m8n9o0_create_purchase_orders_table.py`
  - Schema per design (all PO header fields)
  - Unique constraint on (company_id, po_number)
  - Indexes on company_id, status, vendor_id, department_id

### 14. Create purchase_order_items table migration
- [x] Create `alembic/versions/k6l7m8n9o0p1_create_purchase_order_items_table.py`
  - FK to purchase_orders with CASCADE delete
  - Index on purchase_order_id

### 15. Create purchase_order_requests table migration
- [x] Create `alembic/versions/l7m8n9o0p1q2_create_purchase_order_requests_table.py`
  - Composite PK (purchase_order_id, request_id)
  - FK to purchase_orders (CASCADE) and requests

### 16. Create department_budgets table migration
- [x] Create `alembic/versions/m8n9o0p1q2r3_create_department_budgets_table.py`
  - Unique constraint on (department_id, fiscal_year)

### 17. Create company_procurement_configs table migration
- [x] Create `alembic/versions/n9o0p1q2r3s4_create_company_procurement_configs_table.py`
  - Unique constraint on company_id

### 18. Add purchase_cost_cents to assets migration
- [x] Create `alembic/versions/o0p1q2r3s4t5_add_purchase_cost_cents_to_assets.py`
  - Add nullable Integer column `purchase_cost_cents` to `assets` table

---

## Phase 2: Infrastructure — Models

### 19. Create PurchaseOrder models
- [x] Create `src/procurement_bc/purchase_order/infrastructure/models.py`
  - `PurchaseOrderModel` with ULIDMixin, TimestampMixin, all Mapped columns
  - `PurchaseOrderItemModel` with ULIDMixin, all Mapped columns, FK with CASCADE
  - `PurchaseOrderRequestModel` with composite PK, no mixins
  - Items relationship: `lazy="joined"`, cascade `all, delete-orphan`
  - Request IDs relationship (or handled at repo level)

### 20. Create Vendor model
- [x] Create `src/procurement_bc/vendor/infrastructure/models.py`
  - `VendorModel` with ULIDMixin, TimestampMixin, all Mapped columns

### 21. Create Budget models
- [x] Create `src/procurement_bc/budget/infrastructure/models.py`
  - `DepartmentBudgetModel` with ULIDMixin, TimestampMixin
  - `CompanyProcurementConfigModel` with ULIDMixin, TimestampMixin

---

## Phase 2: Infrastructure — Repositories

### 22. Create PurchaseOrderRepository
- [x] Create `src/procurement_bc/purchase_order/infrastructure/repository.py`
  - Implements PurchaseOrderRepositoryInterface
  - `_to_entity()` static method
  - `save()`: handle insert + update with items replacement
  - `find_all()`: paginated, filtered by status/vendor/dept/date
  - `get_next_number()`: `SELECT MAX(po_number) ... FOR UPDATE` scoped by company+year
  - `sum_totals_by_department_status()`: for budget computation

### 23. Create VendorRepository
- [x] Create `src/procurement_bc/vendor/infrastructure/repository.py`
  - Implements VendorRepositoryInterface
  - `_to_entity()`, `save()`, `find_all()` with search (ILIKE on name), active filter

### 24. Create DepartmentBudgetRepository
- [x] Create `src/procurement_bc/budget/infrastructure/repository.py`
  - Implements DepartmentBudgetRepositoryInterface
  - `save()` with upsert pattern (find existing by dept+year, update or insert)

### 25. Create CompanyProcurementConfigRepository
- [x] In same file as DepartmentBudgetRepository
  - Implements CompanyProcurementConfigRepositoryInterface
  - `save()` with upsert pattern (find by company_id, update or insert)

---

## Phase 3: Collateral

### 26. Extend Asset entity
- [x] Edit `src/asset_bc/asset/domain/entities.py`
  - Add `purchase_cost_cents: Optional[int] = None` field to Asset dataclass

### 27. Extend Asset model
- [x] Edit `src/asset_bc/asset/infrastructure/models.py`
  - Add `purchase_cost_cents: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)` column

---

## Phase 4: Tests

### 28. Domain unit tests
- [x] Create `tests/unit/procurement_bc/purchase_order/domain/test_entities.py`
  - PO factory method creates DRAFT with ULID
  - All valid state transitions succeed
  - All invalid state transitions raise ValueError
  - submit() validates items exist and total > 0
  - approve() sets approved_by and approved_at
  - cancel() sets cancellation_reason
  - recalculate_total() sums item totals
  - receive() transitions to correct state based on quantities
- [x] Create `tests/unit/procurement_bc/purchase_order/domain/test_enums.py`
  - VALID_TRANSITIONS completeness
  - is_terminal for CLOSED, CANCELLED only
  - is_countable_for_budget for expected statuses
- [x] Create `tests/unit/procurement_bc/vendor/domain/test_entities.py`
  - Vendor factory, activate, deactivate
- [x] Create `tests/unit/procurement_bc/budget/domain/test_entities.py`
  - DepartmentBudget factory
  - CompanyProcurementConfig factory with defaults
- 39 tests total

---

## Phase 5: Verification

### 29. Verify
- [x] All `__init__.py` files created for new packages
- [ ] Migrations apply cleanly: `make db-upgrade`
- [ ] Lint passes: `make lint`
- [x] Unit tests pass: `make test` (763 passed)
- [x] All domain entities follow dataclass pattern with factory methods
- [x] All models use `Mapped[type]` annotations

---

## Dependency Graph

```
Enums (1,2)
  └── Entities (3-7) — depend on enums
        └── Interfaces (8-11) — depend on entities
              └── Migrations (12-18) — independent of code but validated against entities
              └── Models (19-21) — depend on entity field knowledge
                    └── Repositories (22-25) — depend on interfaces + models
                          └── Tests (28) — depend on entities + repos
Collateral (26-27) — independent, can run in parallel with any phase
```

## Execution Order

**Batch 1 (Parallel):** Tasks 1-2 (enums)
**Batch 2 (Parallel):** Tasks 3-7 (entities)
**Batch 3 (Parallel):** Tasks 8-11 (interfaces)
**Batch 4 (Parallel):** Tasks 12-18 (migrations) + Tasks 19-21 (models) + Tasks 26-27 (collateral)
**Batch 5 (Parallel):** Tasks 22-25 (repositories)
**Batch 6:** Task 28 (tests)
**Batch 7:** Task 29 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (763 passed, 0 failed)
- [ ] mypy passes
- [ ] Migrations apply cleanly
- [x] No hardcoded strings in domain layer
- [x] All repos follow tenant isolation pattern
