# Implementation Tasks: F5 — Payout Requests

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 22
**Estimated Complexity:** S-M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Interfaces | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Collateral - Commission Changes | 2 | S |
| Application - DTOs | 1 | S |
| Application - Commands | 2 | M |
| Application - Queries | 1 | M |
| Collateral - Dashboard Update | 1 | S |
| HTTP - Schemas & Mappers | 1 | S |
| HTTP - Reseller Endpoints | 1 | M |
| HTTP - Admin Endpoints | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Frontend - Reseller Page | 1 | M |
| Frontend - Admin Page | 1 | M |
| Configuration | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create PayoutStatus Enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create the `PayoutStatus` enum and `__init__.py` files for the payout subdomain directory structure.

**Files:**
- `src/reseller_bc/payout/__init__.py`
- `src/reseller_bc/payout/domain/__init__.py`
- `src/reseller_bc/payout/domain/enums.py`

**Implementation:**
```python
from enum import Enum

class PayoutStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
```

**Acceptance Criteria:**
- [x] Enum with 4 values: `requested`, `approved`, `paid`, `rejected`
- [x] Inherits from `str, Enum`
- [x] All `__init__.py` files created for `payout/`, `payout/domain/`, `payout/infrastructure/`, `payout/application/`, `payout/application/commands/`, `payout/application/queries/`

---

### TASK-002: Create Payout Domain Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create all domain exceptions for the payout subdomain.

**File:** `src/reseller_bc/payout/domain/exceptions.py`

**Implementation:**
```python
class InvalidPayoutAmountException(Exception):
    def __init__(self, amount: int):
        super().__init__(f"Payout amount must be positive, got: {amount}")

class InvalidPayoutTransitionException(Exception):
    def __init__(self, from_status: str, to_status: str):
        super().__init__(f"Cannot transition payout from '{from_status}' to '{to_status}'")

class InsufficientBalanceException(Exception):
    def __init__(self, balance: int, min_payout: int):
        super().__init__(f"Insufficient balance: {balance} cents (minimum: {min_payout} cents)")

class PayoutAlreadyPendingException(Exception):
    def __init__(self, reseller_id: str):
        super().__init__(f"Reseller {reseller_id} already has a pending/approved payout")

class PayoutNotFoundException(Exception):
    def __init__(self, payout_id: str):
        super().__init__(f"Payout not found: {payout_id}")
```

**Acceptance Criteria:**
- [x] 5 exception classes as specified in design
- [x] Each has descriptive error message with context

---

### TASK-003: Create ResellerPayout Entity

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**Description:**
Create the `ResellerPayout` dataclass entity with factory method and state transition methods.

**File:** `src/reseller_bc/payout/domain/entities.py`

**Implementation:**
As specified in design — `@dataclass` with fields: `id`, `reseller_id`, `amount_cents`, `status`, `requested_at`, `processed_at`, `processed_by`, `payment_reference`, `notes`.

Methods:
- `create(reseller_id, amount_cents, id=None)` — factory, sets `status=REQUESTED`, validates `amount_cents > 0`
- `approve(processed_by)` — `REQUESTED → APPROVED`, sets `processed_at` and `processed_by`
- `reject(processed_by, notes=None)` — `REQUESTED → REJECTED`, sets `processed_at`, `processed_by`, `notes`
- `mark_paid(payment_reference)` — `APPROVED → PAID`, sets `payment_reference` and `processed_at`

**Acceptance Criteria:**
- [x] All 9 fields from design
- [x] `create()` factory validates `amount_cents > 0`, raises `InvalidPayoutAmountException`
- [x] `approve()` only from `REQUESTED`, raises `InvalidPayoutTransitionException` otherwise
- [x] `reject()` only from `REQUESTED`, raises `InvalidPayoutTransitionException` otherwise
- [x] `mark_paid()` only from `APPROVED`, raises `InvalidPayoutTransitionException` otherwise
- [x] Uses `ulid.new()` for ID generation
- [x] Uses `datetime.utcnow()` for timestamps

---

### TASK-004: Create ResellerPayoutRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Create the abstract repository interface (port) for payout persistence.

**File:** `src/reseller_bc/payout/domain/repository.py`

**Implementation:**
ABC interface with 8 abstract methods:
- `save(payout: ResellerPayout) -> None`
- `find_by_id(payout_id: str) -> Optional[ResellerPayout]`
- `find_by_reseller_id(reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerPayout]`
- `count_by_reseller_id(reseller_id: str) -> int`
- `find_active_by_reseller_id(reseller_id: str) -> Optional[ResellerPayout]` (status in `requested`, `approved`)
- `find_all(offset: int = 0, limit: int = 50, reseller_id: Optional[str] = None) -> list[ResellerPayout]`
- `count_all(reseller_id: Optional[str] = None) -> int`
- `sum_requested_and_approved_by_reseller_id(reseller_id: str) -> int`

**Acceptance Criteria:**
- [x] ABC class with all 8 `@abstractmethod` methods
- [x] Method signatures exactly match design
- [x] Imports `ResellerPayout` entity

---

## Phase 2: Infrastructure Layer

### TASK-005: Create ResellerPayoutModel

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the SQLAlchemy 2.0-style model for the `reseller_payouts` table.

**Files:**
- `src/reseller_bc/payout/infrastructure/__init__.py`
- `src/reseller_bc/payout/infrastructure/models.py`

**Implementation:**
```python
class ResellerPayoutModel(ULIDMixin, Base):
    __tablename__ = "reseller_payouts"

    reseller_id: Mapped[str] = mapped_column(String(26), ForeignKey("resellers.id"), nullable=False, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="requested", index=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    processed_by: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
```

**Acceptance Criteria:**
- [x] Uses `ULIDMixin, Base`
- [x] SQLAlchemy 2.0 `Mapped[]` + `mapped_column()` style
- [x] Indexes on `reseller_id` and `status`
- [x] FK to `resellers.id`
- [x] `Text` type for `notes` column

---

### TASK-006: Create Alembic Migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Create Alembic migration for the `reseller_payouts` table.

**File:** `alembic/versions/e9f0g1h2i3j4_add_reseller_payouts_table.py`

**Schema:**
```sql
CREATE TABLE reseller_payouts (
    id VARCHAR(26) PRIMARY KEY,
    reseller_id VARCHAR(26) NOT NULL REFERENCES resellers(id),
    amount_cents INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'requested',
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMP NULL,
    processed_by VARCHAR(26) NULL,
    payment_reference VARCHAR(255) NULL,
    notes TEXT NULL
);
CREATE INDEX ix_reseller_payouts_reseller_id ON reseller_payouts(reseller_id);
CREATE INDEX ix_reseller_payouts_status ON reseller_payouts(status);
```

**Acceptance Criteria:**
- [x] `down_revision = "d8e9f0g1h2i3"` (chains after F4 commission migration)
- [x] All columns from design
- [x] 2 indexes: `reseller_id`, `status`
- [x] FK to `resellers.id`
- [x] Reversible `downgrade()` drops indexes then table

---

### TASK-007: Create ResellerPayoutRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-004, TASK-005

**Description:**
Implement the repository adapter using SQLAlchemy.

**File:** `src/reseller_bc/payout/infrastructure/repository.py`

**Implementation:**
- `save()` — upsert pattern (check existing by ID, update or insert + flush)
- `find_by_id()` — select by ID, return entity or None
- `find_by_reseller_id()` — paginated select with order by `requested_at DESC`
- `count_by_reseller_id()` — COUNT query
- `find_active_by_reseller_id()` — select where `status IN ('requested', 'approved')` LIMIT 1
- `find_all()` — paginated select, optional `reseller_id` filter, order by `requested_at DESC`
- `count_all()` — COUNT with optional `reseller_id` filter
- `sum_requested_and_approved_by_reseller_id()` — SUM of `amount_cents` where status in (requested, approved)
- `_to_entity()` — static method converting model to entity

**Acceptance Criteria:**
- [x] Implements `ResellerPayoutRepositoryInterface`
- [x] Session-based, follows F4 commission repo patterns
- [x] `save()` uses upsert with `flush()` (not `commit()`)
- [x] `find_active_by_reseller_id()` checks both `requested` and `approved` statuses
- [x] `find_all()` supports optional `reseller_id` filter
- [x] `sum_requested_and_approved_by_reseller_id()` uses `func.coalesce(..., 0)`

---

## Phase 3: Collateral — Commission Changes

### TASK-008: Add mark_as_paid() to ResellerCommission Entity

**Phase:** Collateral
**Complexity:** S
**Dependencies:** None (existing file)

**Description:**
Add a `mark_as_paid()` domain method to the `ResellerCommission` entity for the `CONFIRMED → PAID` transition.

**File:** `src/reseller_bc/commission/domain/entities.py`

**Implementation:**
```python
def mark_as_paid(self) -> None:
    self.status = CommissionStatus.PAID
```

**Acceptance Criteria:**
- [x] New method `mark_as_paid()` sets status to `CommissionStatus.PAID`
- [x] Existing `confirm()` and `clawback()` methods unchanged

---

### TASK-009: Add mark_confirmed_as_paid_for_reseller() to Commission Repository

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-008

**Description:**
Add a batch update method to the commission repository interface and implementation that transitions all `CONFIRMED` commissions for a reseller to `PAID` in a single query.

**Files:**
- `src/reseller_bc/commission/domain/repository.py` — add abstract method
- `src/reseller_bc/commission/infrastructure/repository.py` — add implementation

**Interface addition:**
```python
@abstractmethod
def mark_confirmed_as_paid_for_reseller(self, reseller_id: str) -> int: ...
```

**Implementation:**
```python
def mark_confirmed_as_paid_for_reseller(self, reseller_id: str) -> int:
    result = self.session.execute(
        update(ResellerCommissionModel)
        .where(
            ResellerCommissionModel.reseller_id == reseller_id,
            ResellerCommissionModel.status == CommissionStatus.CONFIRMED.value,
        )
        .values(status=CommissionStatus.PAID.value)
    )
    self.session.flush()
    return result.rowcount
```

**Acceptance Criteria:**
- [x] Abstract method added to `ResellerCommissionRepositoryInterface`
- [x] Implementation uses batch `UPDATE ... WHERE` (not loop)
- [x] Returns count of updated rows
- [x] Uses `flush()` (not `commit()`)

---

## Phase 4: Application Layer

### TASK-010: Create Payout DTOs

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create DTOs for payout data transfer.

**File:** `src/reseller_bc/payout/application/dtos.py`

**Implementation:**
```python
@dataclass
class PayoutDto:
    id: str
    reseller_id: str
    reseller_name: str
    amount_cents: int
    status: str
    requested_at: Optional[datetime]
    processed_at: Optional[datetime]
    processed_by: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]

@dataclass
class PayoutListDto:
    items: list[PayoutDto]
    total: int
```

**Acceptance Criteria:**
- [x] `PayoutDto` with 10 fields as specified in design
- [x] `PayoutListDto` with `items` and `total`
- [x] Both are `@dataclass`

---

### TASK-011: Create RequestPayoutCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003, TASK-004, TASK-009, TASK-010

**Description:**
Create the command and handler for reseller payout requests. Command and handler in the SAME file.

**File:** `src/reseller_bc/payout/application/commands/request_payout.py`

**Handler logic (from design):**
1. Load reseller → verify exists
2. Check reseller not suspended → raise `ResellerSuspendedException`
3. Check no active payout → raise `PayoutAlreadyPendingException`
4. Calculate available balance: `confirmed - paid + clawbacks`
5. Compare against `reseller.min_payout_cents` → raise `InsufficientBalanceException`
6. Create `ResellerPayout.create(reseller_id, balance, id)`
7. Save payout

**Dependencies (constructor):**
- `payout_repo: ResellerPayoutRepositoryInterface`
- `commission_repo: ResellerCommissionRepositoryInterface`
- `reseller_repo: ResellerRepositoryInterface`

**Acceptance Criteria:**
- [x] `RequestPayoutCommand(Command)` with fields: `id`, `reseller_id`
- [x] `RequestPayoutCommandHandler(CommandHandler[RequestPayoutCommand])`
- [x] `handle()` returns `None`
- [x] Raises `ResellerNotFoundException` if reseller not found
- [x] Raises `ResellerSuspendedException` if suspended
- [x] Raises `PayoutAlreadyPendingException` if active payout exists
- [x] Raises `InsufficientBalanceException` if balance < min_payout_cents
- [x] Calculates balance inline: `confirmed - paid + clawbacks`
- [x] Creates payout with `amount_cents = balance`

---

### TASK-012: Create ProcessPayoutCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003, TASK-004, TASK-009

**Description:**
Create the command and handler for super admin payout processing (approve/reject/mark_paid). Command and handler in the SAME file.

**File:** `src/reseller_bc/payout/application/commands/process_payout.py`

**Handler logic (from design):**
1. Find payout by ID → raise `PayoutNotFoundException` if not found
2. Based on `action`:
   - `"approve"` → call `payout.approve(processed_by)`
   - `"reject"` → call `payout.reject(processed_by, notes)`
   - `"mark_paid"` → validate `payment_reference` present, call `payout.mark_paid(payment_reference)`, then call `commission_repo.mark_confirmed_as_paid_for_reseller(payout.reseller_id)`
   - Unknown → raise `ValueError`
3. Save payout

**Dependencies (constructor):**
- `payout_repo: ResellerPayoutRepositoryInterface`
- `commission_repo: ResellerCommissionRepositoryInterface`

**Acceptance Criteria:**
- [x] `ProcessPayoutCommand(Command)` with fields: `payout_id`, `action`, `processed_by`, `payment_reference` (optional), `notes` (optional)
- [x] `ProcessPayoutCommandHandler(CommandHandler[ProcessPayoutCommand])`
- [x] `handle()` returns `None`
- [x] Supports 3 actions: `approve`, `reject`, `mark_paid`
- [x] `mark_paid` requires `payment_reference`, raises `ValueError` if missing
- [x] `mark_paid` calls `commission_repo.mark_confirmed_as_paid_for_reseller()`
- [x] Entity transition methods raise `InvalidPayoutTransitionException` for invalid transitions

---

### TASK-013: Create ListPayoutsQuery + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004, TASK-010

**Description:**
Create the query and handler for listing payouts (both reseller and admin scope). Query and handler in the SAME file.

**File:** `src/reseller_bc/payout/application/queries/list_payouts.py`

**Handler logic (from design):**
1. If `reseller_id` provided: use `find_by_reseller_id` + `count_by_reseller_id`
2. If `reseller_id` is None: use `find_all` + `count_all` (admin view)
3. Batch-load reseller names by ID
4. Map to `PayoutDto` list → return `PayoutListDto`

**Dependencies (constructor):**
- `payout_repo: ResellerPayoutRepositoryInterface`
- `reseller_repo: ResellerRepositoryInterface`

**Acceptance Criteria:**
- [x] `ListPayoutsQuery(Query)` with fields: `reseller_id` (optional), `offset`, `limit`
- [x] `ListPayoutsQueryHandler(QueryHandler[ListPayoutsQuery, PayoutListDto])`
- [x] Scopes by `reseller_id` when provided, lists all when `None`
- [x] Batch-loads reseller names (not N+1)
- [x] Returns `PayoutListDto`

---

### TASK-014: Update Dashboard Query Handler

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-007

**Description:**
Update `GetResellerDashboardQueryHandler` to accept optional `payout_repo` and compute `pending_payout_cents` from `sum_requested_and_approved_by_reseller_id`.

**File:** `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py`

**Changes:**
1. Add optional `payout_repo: Optional[ResellerPayoutRepositoryInterface] = None` to `__init__`
2. If `payout_repo` is not None: compute `pending_payout_cents = payout_repo.sum_requested_and_approved_by_reseller_id(reseller.id)`
3. Replace hardcoded `pending_payout_cents=0` with computed value

**Acceptance Criteria:**
- [x] `payout_repo` parameter is optional (default `None`) for backward compatibility
- [x] When provided, computes real `pending_payout_cents`
- [x] When `None`, keeps `pending_payout_cents=0` (backward compatible)

---

## Phase 5: HTTP Layer

### TASK-015: Add Payout Schemas and Mapper

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-010

**Description:**
Add payout-related schemas and mapper to the existing reseller HTTP layer files.

**Files:**
- `adapters/http/api/reseller/schemas.py` — add `PayoutResponse`, `PayoutListResponse`, `ProcessPayoutRequest`
- `adapters/http/api/reseller/mappers.py` — add `PayoutMapper` class

**Schemas:**
```python
class PayoutResponse(BaseModel):
    id: str
    reseller_id: str
    reseller_name: str
    amount_cents: int
    status: str
    requested_at: Optional[str]
    processed_at: Optional[str]
    processed_by: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]

class PayoutListResponse(BaseModel):
    items: list[PayoutResponse]
    total: int

class ProcessPayoutRequest(BaseModel):
    action: str = Field(pattern=r"^(approve|reject|mark_paid)$")
    payment_reference: Optional[str] = None
    notes: Optional[str] = None
```

**Mapper:**
```python
class PayoutMapper:
    @staticmethod
    def dto_to_response(dto: PayoutDto) -> PayoutResponse: ...

    @staticmethod
    def dto_to_list_response(dto: PayoutListDto) -> PayoutListResponse: ...
```

**Acceptance Criteria:**
- [x] 3 new schemas added to existing `schemas.py`
- [x] `ProcessPayoutRequest.action` validates regex: `approve|reject|mark_paid`
- [x] `PayoutMapper` added to existing `mappers.py`
- [x] Mapper converts `datetime` to `.isoformat()` strings

---

### TASK-016: Add Reseller Payout Endpoints

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-011, TASK-013, TASK-015

**Description:**
Add payout endpoints to the existing reseller router and update the dashboard endpoint to pass `payout_repo`.

**File:** `adapters/http/api/reseller/routers.py`

**Endpoints:**

1. `POST /api/v1/reseller/payouts` (status 201)
   - Auth: `require_active_reseller()`
   - Create `RequestPayoutCommand` with generated ULID
   - Catch `InsufficientBalanceException` → 400
   - Catch `PayoutAlreadyPendingException` → 409
   - Catch `ResellerSuspendedException` → 403
   - Return created payout via `ListPayoutsQuery` for single item

2. `GET /api/v1/reseller/payouts`
   - Auth: `get_current_reseller`
   - Query with `reseller_id`, `offset`, `limit`
   - Return `PayoutListResponse`

3. Update `get_dashboard` endpoint to pass `payout_repo` to handler

**Acceptance Criteria:**
- [x] `POST /reseller/payouts` creates payout, returns 201
- [x] `POST /reseller/payouts` returns 400 for insufficient balance
- [x] `POST /reseller/payouts` returns 409 for already pending payout
- [x] Suspended reseller gets 403 from `require_active_reseller()`
- [x] `GET /reseller/payouts` returns paginated payout history
- [x] Dashboard endpoint updated to pass `payout_repo`

---

### TASK-017: Create Admin Payout Endpoints

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-012, TASK-013, TASK-015

**Description:**
Create a new admin payout router with endpoints for super admin payout management, and register it in `app.py`.

**Files:**
- `adapters/http/api/admin/payout_routers.py` — new file
- `app.py` — register new router

**Endpoints:**

1. `GET /api/v1/admin/payouts`
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Optional `reseller_id` query param for filtering
   - Returns paginated `PayoutListResponse`

2. `PATCH /api/v1/admin/payouts/{payout_id}`
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Body: `ProcessPayoutRequest`
   - Catch `PayoutNotFoundException` → 404
   - Catch `InvalidPayoutTransitionException` → 422
   - Catch `ValueError` → 422
   - Return updated payout

**Acceptance Criteria:**
- [x] New router at `adapters/http/api/admin/payout_routers.py`
- [x] Prefix: `/api/v1/admin/payouts`, tag: `admin-payouts`
- [x] `GET /` lists all payouts, supports `?reseller_id=` filter
- [x] `PATCH /{payout_id}` processes payout (approve/reject/mark_paid)
- [x] All domain exceptions caught and mapped to HTTP status codes
- [x] Router registered in `app.py` via `include_router`

---

## Phase 6: Tests

### TASK-018: Unit Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-003, TASK-011, TASK-012, TASK-013

**Description:**
Create unit tests for the payout entity and all command/query handlers.

**Files:**
- `tests/unit/reseller_bc/payout/domain/test_payout_entity.py`
- `tests/unit/reseller_bc/payout/application/test_request_payout.py`
- `tests/unit/reseller_bc/payout/application/test_process_payout.py`
- `tests/unit/reseller_bc/payout/application/test_list_payouts.py`

**Entity tests:**
- `test_create_payout_sets_requested_status` — happy path
- `test_create_payout_with_zero_amount_raises` — `InvalidPayoutAmountException`
- `test_create_payout_with_negative_amount_raises` — `InvalidPayoutAmountException`
- `test_approve_from_requested` — sets `APPROVED`, `processed_at`, `processed_by`
- `test_approve_from_non_requested_raises` — `InvalidPayoutTransitionException`
- `test_reject_from_requested` — sets `REJECTED`, `notes`
- `test_reject_from_non_requested_raises` — `InvalidPayoutTransitionException`
- `test_mark_paid_from_approved` — sets `PAID`, `payment_reference`
- `test_mark_paid_from_non_approved_raises` — `InvalidPayoutTransitionException`

**RequestPayoutCommand tests:**
- `test_request_payout_success` — happy path
- `test_request_payout_reseller_not_found` — `ResellerNotFoundException`
- `test_request_payout_reseller_suspended` — `ResellerSuspendedException`
- `test_request_payout_already_pending` — `PayoutAlreadyPendingException`
- `test_request_payout_insufficient_balance` — `InsufficientBalanceException`

**ProcessPayoutCommand tests:**
- `test_approve_payout` — happy path
- `test_reject_payout_with_notes` — sets notes
- `test_mark_paid_transitions_commissions` — calls `mark_confirmed_as_paid_for_reseller`
- `test_mark_paid_without_reference_raises` — `ValueError`
- `test_process_payout_not_found` — `PayoutNotFoundException`
- `test_invalid_action_raises` — `ValueError`

**ListPayoutsQuery tests:**
- `test_list_payouts_by_reseller` — scoped list
- `test_list_all_payouts` — admin view (reseller_id=None)

**Acceptance Criteria:**
- [x] All test files created with `__init__.py` files in directories
- [x] Uses mock repositories (unittest.mock)
- [x] All happy paths and error paths covered
- [x] At least 22 test cases total

---

### TASK-019: Integration Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-016, TASK-017

**Description:**
Create integration tests for the payout HTTP endpoints.

**File:** `tests/integration/test_reseller_payout_endpoints.py`

**Test scenarios:**
- `test_request_payout_success` — POST creates payout with 201
- `test_request_payout_insufficient_balance` — POST returns 400
- `test_request_payout_already_pending` — POST returns 409
- `test_request_payout_suspended_reseller` — POST returns 403
- `test_list_reseller_payouts` — GET returns payout history
- `test_admin_list_all_payouts` — GET admin view returns all payouts
- `test_admin_approve_payout` — PATCH approve transitions to approved
- `test_admin_reject_payout` — PATCH reject with notes
- `test_admin_mark_paid` — PATCH mark_paid transitions commissions
- `test_admin_non_super_admin_forbidden` — non-admin gets 403

**Acceptance Criteria:**
- [x] At least 10 integration tests
- [x] Tests both reseller and admin endpoints
- [x] Tests authentication and authorization
- [x] Tests error cases (400, 403, 404, 409, 422)
- [x] Uses test database with proper setup/teardown

---

## Phase 7: Frontend

### TASK-020: Create PayoutsPage.tsx

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-016

**Description:**
Create the reseller payout history page with "Request Payout" button and payout table. Also add the route, nav link, and i18n keys.

**Files:**
- `web/app/src/pages/reseller/PayoutsPage.tsx` — new page
- `web/app/src/router.tsx` — add route
- `web/app/src/components/layout/ResellerLayout.tsx` — add nav item
- `web/app/src/locales/en.ts` — add payout i18n keys
- `web/app/src/locales/es.ts` — add payout i18n keys (Spanish)

**Components:**
- Available balance display (from dashboard API)
- "Request Payout" button — disabled when `available_balance_cents < min_payout_cents`, calls `POST /reseller/payouts`
- Payout history table: amount, status badge, requested date, processed date, payment reference, notes
- Status badges: yellow=requested, blue=approved, green=paid, red=rejected (same pattern as `CommissionsPage`)
- Pagination (same pattern as `CommissionsPage`)

**Nav item:**
Add between "Commissions" and "Profile" in `ResellerLayout.tsx` `navItems` array.

**i18n keys (en):**
- `reseller.nav.payouts`, `reseller.payouts.title`, `reseller.payouts.subtitle`
- `reseller.payouts.empty`, `reseller.payouts.request_button`, `reseller.payouts.request_button_disabled`
- `reseller.payouts.col_amount`, `reseller.payouts.col_status`, `reseller.payouts.col_requested`
- `reseller.payouts.col_processed`, `reseller.payouts.col_reference`, `reseller.payouts.col_notes`
- `reseller.payouts.status_requested`, `reseller.payouts.status_approved`, `reseller.payouts.status_paid`, `reseller.payouts.status_rejected`
- `reseller.payouts.balance_label`, `reseller.payouts.threshold_label`

**Acceptance Criteria:**
- [x] PayoutsPage displays payout history in a table
- [x] "Request Payout" button shows available balance and is disabled when below threshold
- [x] Status badges with correct colors
- [x] Pagination works
- [x] Route added at `/reseller/payouts`
- [x] Nav item added to sidebar
- [x] i18n keys added for both en and es

---

### TASK-021: Create Admin Payout Management Page

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-017

**Description:**
Create the super admin payout management page with approve/reject/mark-paid actions.

**Files:**
- `web/app/src/pages/superadmin/PayoutManagementPage.tsx` — new page (or add to existing `ResellersPage`)
- `web/app/src/router.tsx` — add route
- `web/app/src/locales/en.ts` — add admin payout i18n keys
- `web/app/src/locales/es.ts` — add admin payout i18n keys (Spanish)

**Components:**
- Payout request table with: reseller name, amount, status badge, requested date, processed date, reference, notes
- Action buttons per row:
  - `requested` status → "Approve" and "Reject" buttons
  - `approved` status → "Mark as Paid" button (opens modal/form for payment reference)
  - `paid`/`rejected` → no actions
- Reject modal with notes text area
- Mark as Paid modal with payment reference input
- Optional filter by reseller

**Acceptance Criteria:**
- [x] Admin payout page displays all payout requests
- [x] Approve/Reject/Mark-Paid action buttons visible based on status
- [x] Reject action accepts notes
- [x] Mark as Paid action requires payment reference
- [x] Route added under admin section (e.g., `/admin/payouts`)
- [x] i18n keys added for both en and es
- [x] Only accessible to `super_admin` role

---

## Phase 8: Configuration

### TASK-022: Register Payout Model in Test Configuration

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Import the `ResellerPayoutModel` in `tests/conftest.py` so the test database creates the table.

**File:** `tests/conftest.py`

**Change:**
Add import line alongside existing reseller model imports:
```python
import src.reseller_bc.payout.infrastructure.models  # noqa: F401
```

**Acceptance Criteria:**
- [x] `ResellerPayoutModel` imported in conftest.py
- [x] Test database creates `reseller_payouts` table

---

## Dependency Graph

```
TASK-001 (PayoutStatus enum)
├── TASK-002 (Exceptions) ──► TASK-003 (Entity) ──► TASK-004 (Repo Interface)
├── TASK-005 (Model) ──► TASK-006 (Migration)
│                    └──► TASK-007 (Repository) ◄── TASK-004
├── TASK-010 (DTOs)
│
TASK-008 (Commission mark_as_paid) ──► TASK-009 (Commission batch update)
│
TASK-003 + TASK-004 + TASK-009 + TASK-010 ──► TASK-011 (RequestPayoutCommand)
TASK-003 + TASK-004 + TASK-009 ──► TASK-012 (ProcessPayoutCommand)
TASK-004 + TASK-010 ──► TASK-013 (ListPayoutsQuery)
TASK-007 ──► TASK-014 (Dashboard update)
│
TASK-010 ──► TASK-015 (Schemas + Mapper)
TASK-011 + TASK-013 + TASK-015 ──► TASK-016 (Reseller endpoints)
TASK-012 + TASK-013 + TASK-015 ──► TASK-017 (Admin endpoints)
│
TASK-003..013 ──► TASK-018 (Unit tests)
TASK-016 + TASK-017 ──► TASK-019 (Integration tests)
TASK-016 ──► TASK-020 (PayoutsPage frontend)
TASK-017 ──► TASK-021 (Admin payout frontend)
TASK-005 ──► TASK-022 (conftest registration)
```

## Execution Order (Batches)

**Batch 1 (Parallel):** TASK-001, TASK-008
- PayoutStatus enum + directory structure
- Commission entity `mark_as_paid()` addition

**Batch 2 (Parallel):** TASK-002, TASK-005, TASK-009, TASK-010
- Payout exceptions
- ResellerPayoutModel
- Commission repo batch update method
- Payout DTOs

**Batch 3 (Parallel):** TASK-003, TASK-006, TASK-022
- ResellerPayout entity
- Alembic migration
- conftest registration

**Batch 4 (Parallel):** TASK-004, TASK-015
- Payout repository interface
- HTTP schemas + mapper

**Batch 5:** TASK-007
- Payout repository implementation

**Batch 6 (Parallel):** TASK-011, TASK-012, TASK-013, TASK-014
- RequestPayoutCommand + Handler
- ProcessPayoutCommand + Handler
- ListPayoutsQuery + Handler
- Dashboard update

**Batch 7 (Parallel):** TASK-016, TASK-017
- Reseller payout endpoints
- Admin payout endpoints

**Batch 8:** TASK-018
- Unit tests

**Batch 9:** TASK-019
- Integration tests

**Batch 10 (Parallel):** TASK-020, TASK-021
- Reseller PayoutsPage frontend
- Admin payout management frontend

## Final Checklist

- [x] All 22 tasks completed
- [x] All unit tests passing
- [x] All integration tests passing
- [x] TypeScript compiles clean (`npx tsc --noEmit`)
- [x] No regressions in existing tests
- [x] tasks.md checkboxes all marked `[x]`
- [x] slicing.md updated (F5 → Done)
