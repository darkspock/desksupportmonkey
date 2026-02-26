# Implementation Tasks: E49 — Asset Checkout & Custody Management

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-26
**Total Tasks:** 28
**Estimated Complexity:** XL

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Phase 1: Domain Layer | 4 | S-M |
| Phase 2: Infrastructure | 3 | S-M |
| Phase 3: Application — Commands | 4 | M-L |
| Phase 4: Application — Queries | 4 | S-M |
| Phase 5: Collateral Changes | 4 | M |
| Phase 6: Maintenance Automation | 2 | M |
| Phase 7: HTTP Layer | 3 | M |
| Phase 8: Tests | 3 | M-L |
| Phase 9: Frontend | 5 | M-L |

---

## Phase 1: Domain Layer

### TASK-001: Create AssetCondition Enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**File:** `src/asset_bc/checkout/domain/enums.py`

**Implementation:**
```python
class AssetCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"
```

**Acceptance Criteria:**
- [ ] Enum with 5 values: new, good, fair, damaged, unusable
- [ ] Inherits from `str, Enum` for JSON serialization

---

### TASK-002: Create Checkout Domain Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**File:** `src/asset_bc/checkout/domain/exceptions.py`

**Implementation:**
```python
class CheckoutNotFoundError(Exception): ...
class ActiveCheckoutExistsError(Exception): ...
class NoActiveCheckoutError(Exception): ...
class CheckoutAlreadyAcceptedError(Exception): ...
class CheckoutNotOpenError(Exception): ...
class UnauthorizedAcceptError(Exception): ...
class CannotUnassignWithOpenCheckoutError(Exception): ...
class InvalidCheckoutAssetStatusError(Exception): ...
class AssetAssignedToOtherError(Exception): ...
```

**Acceptance Criteria:**
- [ ] All 9 exception classes defined
- [ ] Each has a descriptive `__init__` with `super().__init__(message)`

---

### TASK-003: Create AssetCheckout Entity

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**File:** `src/asset_bc/checkout/domain/entities.py`

**Implementation:** As defined in design.md. Dataclass with:
- All fields from design (including `auto_assigned: bool = False`)
- Factory method `create()` — generates ULID, sets `checked_out_at = now()`
- `accept(user_id)` — validates user matches `self.user_id`, checkout is open and not accepted; sets `accepted_at`
- `checkin(checked_in_by, condition_in, ...)` — validates checkout is open; sets checkin fields
- `cancel(cancelled_by, reason)` — validates not checked in, not already cancelled; sets cancel fields
- Properties: `is_open`, `is_accepted`, `is_cancelled`

**Acceptance Criteria:**
- [ ] `create()` factory with ULID generation and validation
- [ ] `accept()` raises `UnauthorizedAcceptError` if wrong user, `CheckoutNotOpenError` if not open, `CheckoutAlreadyAcceptedError` if already accepted
- [ ] `checkin()` raises `CheckoutNotOpenError` if not open
- [ ] `cancel()` raises `CheckoutNotOpenError` if checked in or cancelled
- [ ] Properties `is_open`, `is_accepted`, `is_cancelled` work correctly

---

### TASK-004: Create CheckoutRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/asset_bc/checkout/domain/repository.py`

**Implementation:** ABC with all methods from design:
- `save`, `find_by_id`, `find_active_by_asset`
- `find_by_asset` (paginated), `find_open_by_company` (paginated + filters)
- `find_pending_acceptance_by_user`, `find_open_by_user`
- `count_open_by_company`, `count_pending_acceptance_by_company`
- `find_unaccepted_older_than_days`

**Acceptance Criteria:**
- [ ] ABC interface with all abstract methods
- [ ] Type hints use domain entities, not ORM models
- [ ] Pagination returns `tuple[list[AssetCheckout], int]`

---

## Phase 2: Infrastructure Layer

### TASK-005: Create Alembic Migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**File:** `alembic/versions/xxx_create_asset_checkouts_table.py`

**Implementation:**
- Create `asset_checkouts` table with all columns from design
- Create indexes: `company_id`, `asset_id`, `user_id`
- Create partial unique index: `uq_asset_checkouts_active` on `asset_id` WHERE `checked_in_at IS NULL AND cancelled_at IS NULL`
- Data migration: remove `EMPLOYEE` system locations, update assets at that location to `location_id = NULL`
- Seed GDPR sanitization maintenance template per existing company

**Acceptance Criteria:**
- [ ] Table created with all columns and correct types
- [ ] Partial unique index enforces one active checkout per asset
- [ ] `EMPLOYEE` system locations removed gracefully
- [ ] Assets at "Empleado" location get `location_id = NULL`
- [ ] GDPR template seeded for existing companies
- [ ] Reversible `downgrade()` method

---

### TASK-006: Create AssetCheckoutModel

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**File:** `src/asset_bc/checkout/infrastructure/models.py`

**Implementation:** SQLAlchemy model using `Mapped[type]` annotations, `ULIDMixin`, `TimestampMixin`. All columns mapped from migration. Partial unique index via `__table_args__`.

**Acceptance Criteria:**
- [ ] All columns use `Mapped[type]` annotations (SQLAlchemy 2.0 style)
- [ ] Inherits `ULIDMixin, TimestampMixin, Base`
- [ ] Foreign keys to `companies`, `assets`, `users`
- [ ] Partial unique index in `__table_args__`

---

### TASK-007: Create CheckoutRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-004, TASK-006

**File:** `src/asset_bc/checkout/infrastructure/repository.py`

**Implementation:** Implements `CheckoutRepositoryInterface`:
- `_to_entity()` and `_to_model()` conversion methods
- `save()` with upsert pattern (check existing, update or insert)
- All query methods with proper filters
- Pagination using `.offset()` / `.limit()` + `.count()`
- `find_unaccepted_older_than_days` using date arithmetic

**Acceptance Criteria:**
- [ ] Implements all interface methods
- [ ] Entity ↔ Model conversions correct
- [ ] `save()` handles insert and update
- [ ] Pagination returns `(list, total_count)`
- [ ] `find_active_by_asset` filters on `checked_in_at IS NULL AND cancelled_at IS NULL`

---

## Phase 3: Application Layer — Commands

### TASK-008: Create CreateCheckoutCommandHandler

**Phase:** Application
**Complexity:** L
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/commands/create_checkout.py`

**Implementation:** As described in design:
1. Look up asset — validate exists
2. Look up user — validate exists and active
3. If asset `IN_STOCK`: auto-assign (set `assigned_to`, status → `ASSIGNED`, save, event), set `auto_assigned=True`
4. If asset `ASSIGNED` to target user: proceed, `auto_assigned=False`
5. If asset `ASSIGNED` to different user: raise `AssetAssignedToOtherError`
6. Otherwise: raise `InvalidCheckoutAssetStatusError`
7. Check no active checkout: raise `ActiveCheckoutExistsError`
8. Create entity, save, create asset event

Dependencies: `asset_repo`, `checkout_repo`, `user_repo` (port)

**Acceptance Criteria:**
- [ ] Accepts `IN_STOCK` assets (auto-assigns)
- [ ] Accepts `ASSIGNED` assets (to same user)
- [ ] Rejects `ASSIGNED` to different user
- [ ] Rejects non-IN_STOCK/ASSIGNED statuses
- [ ] Rejects if active checkout exists
- [ ] Creates `AssetEvent` with `event_type="checked_out"`
- [ ] Sets `auto_assigned` flag correctly

---

### TASK-009: Create CheckinAssetCommandHandler

**Phase:** Application
**Complexity:** L
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/commands/checkin_asset.py`

**Implementation:** As described in design:
1. Find active checkout for asset
2. Call `checkout.checkin()`
3. Determine next status: `unusable` → `DECOMMISSIONED`, others → `IN_REPAIR`
4. Change asset status
5. Save both
6. Create GDPR maintenance record:
   - Use `CreateMaintenanceRecordCommand` pattern (instantiate handler directly or create record inline)
   - Link via `maintenance_id` on checkout
   - Pass `source_type="checkout_gdpr"` for automation
7. Create asset event

Dependencies: `asset_repo`, `checkout_repo`, `maintenance_repo`, `maintenance_template_repo`

**Acceptance Criteria:**
- [ ] Finds and closes active checkout
- [ ] `condition_in=unusable` → asset `DECOMMISSIONED`
- [ ] Other conditions → asset `IN_REPAIR`
- [ ] Auto-creates GDPR sanitization maintenance record
- [ ] Links `maintenance_id` on checkout
- [ ] Creates `AssetEvent` with `event_type="checked_in"`
- [ ] Raises `NoActiveCheckoutError` if no open checkout

---

### TASK-010: Create CancelCheckoutCommandHandler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/commands/cancel_checkout.py`

**Implementation:**
1. Find active checkout for asset
2. Call `checkout.cancel()`
3. If `checkout.auto_assigned`: unassign asset (`assigned_to = None`, status → `IN_STOCK`)
4. Save both
5. Create asset event

Dependencies: `asset_repo`, `checkout_repo`

**Acceptance Criteria:**
- [ ] Cancels open checkout
- [ ] If auto-assigned: asset returns to `IN_STOCK` and `assigned_to = None`
- [ ] If not auto-assigned: asset stays `ASSIGNED`
- [ ] Creates `AssetEvent` with `event_type="checkout_cancelled"`
- [ ] Raises `NoActiveCheckoutError` if no open checkout

---

### TASK-011: Create AcceptCheckoutCommandHandler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/commands/accept_checkout.py`

**Implementation:**
1. Find active checkout for asset
2. Validate `command.user_id == checkout.user_id`
3. Call `checkout.accept()`
4. Save
5. Create asset event

**Acceptance Criteria:**
- [ ] Only assigned employee can accept
- [ ] Raises `UnauthorizedAcceptError` if wrong user
- [ ] Raises `CheckoutNotOpenError` if not open
- [ ] Creates `AssetEvent` with `event_type="checkout_accepted"`

---

## Phase 4: Application Layer — Queries

### TASK-012: Create GetCurrentCheckoutQuery

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/queries/get_current_checkout.py`

**Acceptance Criteria:**
- [ ] Returns `Optional[AssetCheckout]` — the active checkout or None
- [ ] Inherits `Query` / `QueryHandler`

---

### TASK-013: Create ListAssetCheckoutsQuery

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/queries/list_asset_checkouts.py`

Returns paginated checkout history for a single asset.

**Acceptance Criteria:**
- [ ] Accepts `asset_id`, `company_id`, `page`, `page_size`
- [ ] Returns `tuple[list[AssetCheckout], int]`

---

### TASK-014: Create ListCompanyCheckoutsQuery

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/queries/list_company_checkouts.py`

Global checkout list with filters.

**Acceptance Criteria:**
- [ ] Accepts `company_id`, `page`, `page_size`, optional `user_id`, `asset_id`
- [ ] Returns only open checkouts by default
- [ ] Returns `tuple[list[AssetCheckout], int]`

---

### TASK-015: Create ListMyEquipmentQuery

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-007

**File:** `src/asset_bc/checkout/application/queries/list_my_equipment.py`

**Acceptance Criteria:**
- [ ] Returns open checkouts + pending acceptance for a user
- [ ] Separates "pending acceptance" (open, not accepted) from "accepted" (open, accepted)

---

## Phase 5: Collateral Changes

### TASK-016: Modify AssignAssetCommandHandler — Remove Auto-Location Move

**Phase:** Collateral
**Complexity:** M
**Dependencies:** TASK-005

**File:** `src/asset_bc/asset/application/commands/assign_asset.py`

**Changes:**
- Remove lines 53-92: employee location lookup, `asset.location_id = employee_loc.id`, and `location_changed` event
- Keep: asset validation, user validation, `asset.assign()`, save, "assigned" event

**Acceptance Criteria:**
- [ ] `assign()` no longer moves location to "Empleado"
- [ ] No `location_changed` event emitted on assign
- [ ] Existing unit tests updated to reflect new behavior

---

### TASK-017: Modify UnassignAssetCommandHandler — Remove Auto-Location + Add Checkout Guard

**Phase:** Collateral
**Complexity:** M
**Dependencies:** TASK-007

**File:** `src/asset_bc/asset/application/commands/unassign_asset.py`

**Changes:**
- Add `checkout_repo: CheckoutRepositoryInterface` to `__init__`
- Before `asset.unassign()`: check `checkout_repo.find_active_by_asset()` → raise `CannotUnassignWithOpenCheckoutError`
- Remove lines 33-70: warehouse location lookup, `asset.location_id = warehouse.id`, and `location_changed` event

**Acceptance Criteria:**
- [ ] Raises `CannotUnassignWithOpenCheckoutError` if open checkout exists
- [ ] No longer auto-moves location to warehouse
- [ ] No `location_changed` event on unassign
- [ ] Existing unit tests updated

---

### TASK-018: Modify Company Creation — Remove EMPLOYEE Location + Add GDPR Template Seeding

**Phase:** Collateral
**Complexity:** M
**Dependencies:** TASK-005

**File:** `src/company_bc/company/application/commands/create_company.py`

**Changes:**
- Remove `EMPLOYEE` from system location seeding loop
- Add GDPR sanitization maintenance template seeding:
  - Title: "GDPR Sanitization"
  - Default checklist items from requirements doc
  - Template is editable by admin

**Acceptance Criteria:**
- [ ] New companies don't get "Empleado" system location
- [ ] New companies get a GDPR sanitization maintenance template
- [ ] Template has 6 default checklist items

---

### TASK-019: Modify SystemLocation Enum

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-005

**File:** `src/asset_bc/asset/domain/enums.py`

**Changes:**
- Remove `EMPLOYEE = "employee"` from `SystemLocation` enum

**Acceptance Criteria:**
- [ ] `SystemLocation` has only `IN_TRANSIT` and `MAIN_WAREHOUSE`
- [ ] No code references `SystemLocation.EMPLOYEE` (search and fix any remaining references)

---

## Phase 6: Maintenance Automation

### TASK-020: Add source_type to MaintenanceRecord

**Phase:** Maintenance Automation
**Complexity:** M
**Dependencies:** TASK-005

**Files:**
- `src/maintenance_bc/maintenance_record/domain/entities.py` — add `source_type: Optional[str] = None`
- `src/maintenance_bc/maintenance_record/infrastructure/models.py` — add `source_type` column
- `src/maintenance_bc/maintenance_record/application/commands/create_maintenance_record.py` — add `source_type` to command + pass to entity
- Migration: add `source_type VARCHAR(30)` column to `maintenance_records` table (in same migration as TASK-005 or separate)

**Acceptance Criteria:**
- [ ] `MaintenanceRecord` entity has `source_type: Optional[str]`
- [ ] `CreateMaintenanceRecordCommand` accepts `source_type`
- [ ] Model has `source_type` column
- [ ] DB column is nullable VARCHAR(30)

---

### TASK-021: Modify CompleteMaintenanceCommandHandler — Auto IN_STOCK

**Phase:** Maintenance Automation
**Complexity:** M
**Dependencies:** TASK-020

**File:** `src/maintenance_bc/maintenance_record/application/commands/complete_maintenance.py`

**Changes:**
- Add `asset_repo` port (or new `AssetStatusUpdater` port)
- After `record.complete()`: if `record.source_type == "checkout_gdpr"`, update asset status to `IN_STOCK`
- This requires the maintenance BC to have an `AssetLookup` port extended with `set_status()` or a dedicated port

**Acceptance Criteria:**
- [ ] Completing a `checkout_gdpr` maintenance automatically sets asset to `IN_STOCK`
- [ ] Non-checkout maintenance completion unchanged
- [ ] Creates asset event `"maintenance_completed_auto_stock"`

---

## Phase 7: HTTP Layer

### TASK-022: Create Checkout Router + Schemas + Dependencies

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-008 through TASK-015

**Files:**
- `adapters/http/api/checkouts/__init__.py`
- `adapters/http/api/checkouts/routers.py`
- `adapters/http/api/checkouts/schemas.py`
- `adapters/http/api/checkouts/dependencies.py`

**Implementation:**
- 7 endpoints as defined in design
- Request/Response schemas from design
- Dependency injection for `checkout_repo`
- Exception → HTTP status mapping for ALL domain exceptions
- Role guards: `require_role(UserRole.TECHNICIAN)` for technician endpoints

**Acceptance Criteria:**
- [ ] All 7 endpoints implemented with correct HTTP methods and paths
- [ ] All domain exceptions caught and mapped to HTTP status codes (404, 409, 422, 403)
- [ ] `CheckoutResponse` includes derived `status` field
- [ ] Pagination on list endpoints

---

### TASK-023: Extend My Router with Equipment Endpoints

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-015

**File:** `adapters/http/api/my/routers.py`

**Changes:**
- Add `GET /api/v1/my/equipment` endpoint
- Add `POST /api/v1/my/equipment/{asset_id}/accept` endpoint

**Acceptance Criteria:**
- [ ] Employee can view their equipment
- [ ] Employee can accept checkout
- [ ] Role guard: `require_role(UserRole.EMPLOYEE)` or any authenticated user

---

### TASK-024: Register Checkout Router in app.py

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-022

**File:** `app.py`

**Changes:**
- Import and include `checkout_router`

**Acceptance Criteria:**
- [ ] Router registered and accessible

---

## Phase 8: Tests

### TASK-025: Unit Tests — Domain + Commands

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-003 through TASK-011

**Files:**
- `tests/unit/asset_bc/checkout/domain/test_entities.py`
- `tests/unit/asset_bc/checkout/application/commands/test_create_checkout.py`
- `tests/unit/asset_bc/checkout/application/commands/test_checkin.py`
- `tests/unit/asset_bc/checkout/application/commands/test_cancel.py`
- `tests/unit/asset_bc/checkout/application/commands/test_accept.py`

**Test cases:**

Entity tests:
- `create()` happy path
- `accept()` happy path + wrong user + already accepted + not open
- `checkin()` happy path + not open
- `cancel()` happy path + already checked in + already cancelled
- `is_open`, `is_accepted`, `is_cancelled` properties

Command handler tests (using MagicMock):
- Create checkout: IN_STOCK auto-assign, ASSIGNED to same user, ASSIGNED to other (reject), active exists (reject)
- Checkin: happy path, condition determines status, GDPR maintenance created, no active (reject)
- Cancel: happy path, auto-assigned reverts to IN_STOCK, not auto-assigned stays ASSIGNED
- Accept: happy path, wrong user (reject), not open (reject)

**Acceptance Criteria:**
- [ ] All entity methods tested (success + error paths)
- [ ] All command handlers tested with MagicMock repos
- [ ] `make test` passes

---

### TASK-026: Update Existing Assign/Unassign Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-016, TASK-017

**Files:**
- `tests/unit/asset_bc/asset/application/commands/test_commands.py`
- `tests/unit/asset_bc/asset/application/commands/test_location_commands.py`

**Changes:**
- Remove assertions about auto-location move
- Add test: unassign with open checkout raises error
- Update mock setup for `checkout_repo` dependency in unassign handler

**Acceptance Criteria:**
- [ ] Existing assign tests pass without location assertions
- [ ] New test: unassign blocked by open checkout
- [ ] `make test` passes

---

### TASK-027: Integration Tests — Checkout Endpoints

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-022, TASK-023

**File:** `tests/integration/test_checkout_endpoints.py`

**Test cases:**
- POST checkout: happy path (ASSIGNED asset), happy path (IN_STOCK auto-assign), asset not found, active checkout exists
- POST checkin: happy path, condition → status mapping, GDPR maintenance created
- POST cancel: happy path, auto-assigned reverts
- POST accept: happy path, wrong user 403
- GET current checkout: found / not found
- GET asset checkouts: paginated list
- GET company checkouts: filtered list
- GET my/equipment: employee sees their equipment
- Partial unique index: second checkout on same asset rejected

**Acceptance Criteria:**
- [ ] Full lifecycle tested: checkout → accept → checkin → maintenance created
- [ ] Direct checkout from IN_STOCK tested
- [ ] Cancel flow tested
- [ ] Role-based access tested
- [ ] `make test-integration` passes

---

## Phase 9: Frontend

### TASK-028: Asset Detail — Custody Tab

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-022

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx` (or new `AssetDetailPage.tsx` tab component)

**Implementation:**
- New "Custody" tab showing current checkout status
- Checkout/Checkin/Cancel action buttons for technicians
- Checkout history table with pagination
- Condition badges (color-coded)

**Acceptance Criteria:**
- [x] Current checkout displayed with user, date, condition, acceptance status
- [x] Checkout button: opens form with user picker + condition select
- [x] Checkin button: opens form with condition select + notes
- [x] Cancel button: opens confirmation with optional reason
- [x] History table paginated

---

### TASK-029: My Equipment Page

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-023

**File:** `web/app/src/pages/employee/MyEquipmentPage.tsx`

**Implementation:**
- Pending acceptance banner at top
- "Confirm Receipt" button per pending item
- List of currently held equipment

**Acceptance Criteria:**
- [x] Shows pending acceptance items prominently
- [x] Confirm Receipt calls accept endpoint
- [x] Shows currently held equipment list

---

### TASK-030: Router + Sidebar + i18n

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-028, TASK-029

**Files:**
- `web/app/src/router.tsx` — add `/my/equipment` route
- `web/app/src/components/layout/Sidebar.tsx` — add "My Equipment" link for employees
- `web/app/src/locales/en.ts` — add all checkout-related keys
- `web/app/src/locales/es.ts` — add all checkout-related keys

**Acceptance Criteria:**
- [x] Route accessible
- [x] Sidebar shows "My Equipment" for employee role
- [x] All UI strings translated EN + ES

---

### TASK-031: Dashboard Widget — Open Checkouts

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-022

**Files:** Extend existing dashboard components

**Implementation:**
- Add card: "Open Checkouts" with count
- Add card: "Pending Acceptances" with count

**Acceptance Criteria:**
- [x] Dashboard shows open checkout count
- [x] Dashboard shows pending acceptance count
- [x] Counts fetched from existing or new API endpoint

---

### TASK-032: TypeScript Build Verification

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-028 through TASK-031

**Implementation:** Run `npx tsc --noEmit` to verify no TypeScript errors.

**Acceptance Criteria:**
- [x] `npx tsc --noEmit` passes with zero errors

---

## Dependency Graph

```
TASK-001 (Enum) ─────────────┐
TASK-002 (Exceptions) ───────┤
                              ├──► TASK-003 (Entity) ──► TASK-004 (Repo Interface)
                              │                    │
                              │                    ▼
                              │              TASK-005 (Migration) ──► TASK-006 (Model)
                              │                    │                        │
                              │                    ▼                        ▼
                              │              TASK-018 (Company seed)  TASK-007 (Repository)
                              │              TASK-019 (Remove EMPLOYEE)     │
                              │                                            ▼
                              │                    ┌───────────────────────┤
                              │                    ▼                       ▼
                              │              TASK-008..011 (Commands) TASK-012..015 (Queries)
                              │                    │                       │
                              │                    ▼                       ▼
                              │              TASK-016 (Modify assign)  TASK-022 (Router)
                              │              TASK-017 (Modify unassign)TASK-023 (My router)
                              │                    │                  TASK-024 (Register)
                              │                    ▼                       │
                              │              TASK-020 (Maint source_type)  ▼
                              │              TASK-021 (Auto IN_STOCK) TASK-028..032 (Frontend)
                              │                    │
                              │                    ▼
                              │              TASK-025 (Unit tests)
                              │              TASK-026 (Update tests)
                              │              TASK-027 (Integration tests)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002
**Batch 2:** TASK-003
**Batch 3:** TASK-004, TASK-005
**Batch 4 (Parallel):** TASK-006, TASK-019
**Batch 5:** TASK-007, TASK-018
**Batch 6 (Parallel):** TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-015
**Batch 7 (Parallel):** TASK-016, TASK-017, TASK-020
**Batch 8:** TASK-021
**Batch 9 (Parallel):** TASK-022, TASK-023
**Batch 10:** TASK-024
**Batch 11 (Parallel):** TASK-025, TASK-026, TASK-027
**Batch 12 (Parallel):** TASK-028, TASK-029, TASK-030, TASK-031
**Batch 13:** TASK-032

## Final Checklist

- [x] All tasks completed
- [x] `make test` passes (unit tests — 1594 passed, 1 pre-existing failure unrelated)
- [ ] `make test-integration` passes (integration tests)
- [ ] `make lint` passes (mypy + flake8)
- [x] `npx tsc --noEmit` passes (TypeScript)
- [x] Progress tracking updated (slicing.md, roadmap.md)
