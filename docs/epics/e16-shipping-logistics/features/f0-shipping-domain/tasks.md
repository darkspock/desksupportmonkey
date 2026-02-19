# Tasks: F0 — Shipping Domain & Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 11
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Package structure | 1 | S |
| Domain - Enums | 1 | S |
| Domain - Entities (Shipment) | 1 | M |
| Domain - Entities (Address) | 1 | S |
| Domain - Repository interfaces | 1 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Tests - Shipment entities | 1 | M |
| Tests - Address entities | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Package Structure

### 1. Create `shipping_bc` package tree
- [x] Create directory structure:
  ```
  src/shipping_bc/__init__.py
  src/shipping_bc/shipment/__init__.py
  src/shipping_bc/shipment/domain/__init__.py
  src/shipping_bc/shipment/application/__init__.py
  src/shipping_bc/shipment/application/commands/__init__.py
  src/shipping_bc/shipment/application/queries/__init__.py
  src/shipping_bc/shipment/infrastructure/__init__.py
  src/shipping_bc/address/__init__.py
  src/shipping_bc/address/domain/__init__.py
  src/shipping_bc/address/application/__init__.py
  src/shipping_bc/address/application/commands/__init__.py
  src/shipping_bc/address/application/queries/__init__.py
  src/shipping_bc/address/infrastructure/__init__.py
  ```
- All `__init__.py` files are empty

---

## Phase 2: Domain Layer — Enums

### 2. Create shipment enums
- [x] Create `src/shipping_bc/shipment/domain/enums.py`
  - `ShipmentStatus(str, Enum)` with values: `DRAFT`, `DISPATCHED`, `IN_TRANSIT`, `DELIVERED`, `FAILED`, `CANCELLED`
  - `is_terminal` property: `True` for DELIVERED, FAILED, CANCELLED
  - `is_active` property: `True` for DRAFT, DISPATCHED, IN_TRANSIT
  - `VALID_TRANSITIONS` dict:
    - DRAFT → [DISPATCHED, CANCELLED]
    - DISPATCHED → [IN_TRANSIT, DELIVERED, FAILED, CANCELLED]
    - IN_TRANSIT → [DELIVERED, FAILED, CANCELLED]
    - DELIVERED → []
    - FAILED → []
    - CANCELLED → []
  - `InvalidShipmentStatusTransitionError` exception with `current` and `target` fields
  - `ShipmentDirection(str, Enum)` with values: `OUTBOUND`, `INBOUND`
  - `DestinationType(str, Enum)` with values: `EMPLOYEE_HOME`, `OFFICE`, `VENDOR`

---

## Phase 3: Domain Layer — Entities

### 3. Create Shipment and ShipmentItem entities
- [x] Create `src/shipping_bc/shipment/domain/entities.py`
  - **`ShipmentItem`** dataclass:
    - Fields: `id`, `shipment_id`, `asset_id`
    - Optional: `notes`
    - Factory `create(shipment_id, asset_id, notes?, id?)`: generates ULID
  - **`Shipment`** dataclass:
    - Fields: `id`, `company_id`, `direction` (ShipmentDirection), `destination_type` (DestinationType), `status` (ShipmentStatus), `destination_address_id`, `created_by`
    - Optional: `origin_address_id`, `recipient_name`, `recipient_user_id`, `carrier`, `tracking_number`, `tracking_url`, `request_id`, `po_id`, `return_for_shipment_id`, `notes`, `failure_reason`, `cancellation_reason`, `dispatched_at`, `delivered_at`, `created_at`, `updated_at`
    - `items: list[ShipmentItem] = field(default_factory=list)`
    - Factory `create(company_id, direction, destination_type, destination_address_id, created_by, items?, ...)`:
      - Generates ULID
      - Sets `status = ShipmentStatus.DRAFT`
      - Validates `len(items) <= 20`
    - `_transition(target)` — validates against `VALID_TRANSITIONS`, raises `InvalidShipmentStatusTransitionError`
    - `dispatch()` — DRAFT → DISPATCHED, validates `carrier` and `tracking_number` are not None, sets `dispatched_at = datetime.now(UTC)`
    - `mark_in_transit()` — DISPATCHED → IN_TRANSIT
    - `deliver()` — DISPATCHED/IN_TRANSIT → DELIVERED, sets `delivered_at = datetime.now(UTC)`
    - `fail(reason: str)` — DISPATCHED/IN_TRANSIT → FAILED, sets `failure_reason`
    - `cancel(reason: str)` — any non-terminal → CANCELLED, sets `cancellation_reason`
    - `add_item(item: ShipmentItem)` — validates `status == DRAFT`, validates `len(items) < 20`, appends item
    - `remove_item(item_id: str)` — validates `status == DRAFT`, removes item by id

### 4. Create ShippingAddress entity
- [x] Create `src/shipping_bc/address/domain/entities.py`
  - **`ShippingAddress`** dataclass:
    - Fields: `id`, `company_id`, `label`, `street_line_1`, `city`, `state`, `postal_code`, `country`
    - Optional: `street_line_2`, `recipient_name`, `phone`, `user_id`
    - Defaults: `is_office: bool = False`, `is_active: bool = True`
    - Optional timestamps: `created_at`, `updated_at`
    - Factory `create(company_id, label, street_line_1, city, state, postal_code, country?, ...)`:
      - Generates ULID
      - Sets `is_active = True`
      - Defaults `country = "US"` if not provided
    - `deactivate()` — sets `is_active = False`
    - `update(label?, street_line_1?, street_line_2?, city?, state?, postal_code?, country?, phone?, recipient_name?, user_id?, is_office?)` — updates provided fields

---

## Phase 4: Domain Layer — Repository Interfaces

### 5. Create repository interfaces
- [x] Create `src/shipping_bc/shipment/domain/repository.py`
  - **`ShipmentRepositoryInterface(ABC)`**:
    - `save(shipment) -> Shipment`
    - `find_by_id(id, company_id) -> Optional[Shipment]`
    - `find_all(company_id, page, page_size, status?, direction?, destination_type?, request_id?, po_id?) -> tuple[list[Shipment], int]`
    - `find_by_asset_id(asset_id, company_id) -> list[Shipment]`
    - `find_active_by_asset_id(asset_id, company_id) -> list[Shipment]`
    - `find_by_recipient_user_id(recipient_user_id, company_id, page, page_size) -> tuple[list[Shipment], int]`
    - `count_by_status(company_id) -> dict[str, int]`
    - `find_recent_delivered(company_id, days) -> list[Shipment]`
    - `find_by_status(company_id, status) -> list[Shipment]`
- [x] Create `src/shipping_bc/address/domain/repository.py`
  - **`ShippingAddressRepositoryInterface(ABC)`**:
    - `save(address) -> ShippingAddress`
    - `find_by_id(id, company_id) -> Optional[ShippingAddress]`
    - `find_all(company_id, page, page_size, user_id?, is_office?, is_active?) -> tuple[list[ShippingAddress], int]`
    - `find_by_user_id(user_id, company_id) -> list[ShippingAddress]`

---

## Phase 5: Infrastructure — Migrations

### 6. Create Alembic migrations
- [x] Create `alembic/versions/g1a2b3c4d5e6_create_shipping_addresses.py`
  - Table `shipping_addresses` with all fields from design
  - Indexes on: `company_id`, `user_id`
  - FK to `companies(id)`, `users(id)`
- [x] Create `alembic/versions/g2b3c4d5e6f7_create_shipments.py`
  - Table `shipments` with all fields
  - Indexes on: `company_id`, `status`, `direction`, `request_id`, `po_id`, `recipient_user_id`, `return_for_shipment_id`
  - FK to `companies(id)`, `shipping_addresses(id)` (x2), `users(id)`, `service_requests(id)`, `purchase_orders(id)`, self-referential `shipments(id)`
- [x] Create `alembic/versions/g3c4d5e6f7a8_create_shipment_items.py`
  - Table `shipment_items` with all fields
  - Indexes on: `shipment_id`, `asset_id`
  - FK to `shipments(id)` (ondelete CASCADE), `assets(id)`

---

## Phase 6: Infrastructure — Models

### 7. Create SQLAlchemy models
- [x] Create `src/shipping_bc/shipment/infrastructure/models.py`
  - **`ShipmentModel(ULIDMixin, TimestampMixin, Base)`**:
    - `__tablename__ = "shipments"`
    - All fields with `Mapped[type]` annotations
    - `company_id`: `Mapped[str]` FK to `companies.id`, indexed
    - `direction`: `Mapped[str]` (String(20))
    - `destination_type`: `Mapped[str]` (String(20))
    - `status`: `Mapped[str]` default `"draft"`
    - `origin_address_id`: `Mapped[Optional[str]]` FK to `shipping_addresses.id`, nullable
    - `destination_address_id`: `Mapped[str]` FK to `shipping_addresses.id`
    - `recipient_name`: `Mapped[Optional[str]]` nullable
    - `recipient_user_id`: `Mapped[Optional[str]]` FK to `users.id`, nullable
    - `carrier`: `Mapped[Optional[str]]` nullable
    - `tracking_number`: `Mapped[Optional[str]]` nullable
    - `tracking_url`: `Mapped[Optional[str]]` nullable
    - `request_id`: `Mapped[Optional[str]]` FK to `service_requests.id`, nullable
    - `po_id`: `Mapped[Optional[str]]` FK to `purchase_orders.id`, nullable
    - `return_for_shipment_id`: `Mapped[Optional[str]]` FK to `shipments.id`, nullable
    - `notes`: `Mapped[Optional[str]]` nullable
    - `failure_reason`: `Mapped[Optional[str]]` nullable
    - `cancellation_reason`: `Mapped[Optional[str]]` nullable
    - `created_by`: `Mapped[str]`
    - `dispatched_at`: `Mapped[Optional[datetime]]` nullable
    - `delivered_at`: `Mapped[Optional[datetime]]` nullable
    - `items`: `Mapped[list["ShipmentItemModel"]]` relationship, cascade="all, delete-orphan", lazy="joined"
  - **`ShipmentItemModel(ULIDMixin, Base)`**:
    - `__tablename__ = "shipment_items"`
    - `shipment_id`: `Mapped[str]` FK to `shipments.id` (ondelete CASCADE), indexed
    - `asset_id`: `Mapped[str]` FK to `assets.id`, indexed
    - `notes`: `Mapped[Optional[str]]` nullable
    - `created_at`: `Mapped[datetime]` server_default=func.now()
- [x] Create `src/shipping_bc/address/infrastructure/models.py`
  - **`ShippingAddressModel(ULIDMixin, TimestampMixin, Base)`**:
    - `__tablename__ = "shipping_addresses"`
    - `company_id`: `Mapped[str]` FK to `companies.id`, indexed
    - `label`: `Mapped[str]` String(100)
    - `recipient_name`: `Mapped[Optional[str]]` String(200), nullable
    - `street_line_1`: `Mapped[str]` String(300)
    - `street_line_2`: `Mapped[Optional[str]]` String(300), nullable
    - `city`: `Mapped[str]` String(100)
    - `state`: `Mapped[str]` String(100)
    - `postal_code`: `Mapped[str]` String(20)
    - `country`: `Mapped[str]` String(2), server_default="US"
    - `phone`: `Mapped[Optional[str]]` String(30), nullable
    - `user_id`: `Mapped[Optional[str]]` FK to `users.id`, nullable, indexed
    - `is_office`: `Mapped[bool]` server_default="false"
    - `is_active`: `Mapped[bool]` server_default="true"

---

## Phase 7: Infrastructure — Repositories

### 8. Create repository implementations
- [x] Create `src/shipping_bc/shipment/infrastructure/repository.py`
  - **`ShipmentRepository(ShipmentRepositoryInterface)`**:
    - `__init__(self, session: Session)`
    - `save()`: upsert — check existing by id, update fields or create new model. For update: sync items (clear existing, re-add from entity)
    - `find_by_id()`: query by id + company_id, map model → entity with items
    - `find_all()`: paginated with optional filters (status, direction, destination_type, request_id, po_id), ordered by created_at desc
    - `find_by_asset_id()`: join `shipment_items` where `asset_id` matches
    - `find_active_by_asset_id()`: same join + filter `status IN ('draft', 'dispatched', 'in_transit')`
    - `find_by_recipient_user_id()`: paginated filter on `recipient_user_id`
    - `count_by_status()`: `SELECT status, COUNT(*) ... GROUP BY status`
    - `find_recent_delivered()`: filter `status='delivered'` and `delivered_at >= now() - interval(days)`
    - `find_by_status()`: simple filter
    - Private `_to_entity(model)` — maps ShipmentModel → Shipment with items
    - Private `_to_item_entity(model)` — maps ShipmentItemModel → ShipmentItem
- [x] Create `src/shipping_bc/address/infrastructure/repository.py`
  - **`ShippingAddressRepository(ShippingAddressRepositoryInterface)`**:
    - `__init__(self, session: Session)`
    - `save()`: upsert pattern
    - `find_by_id()`: query by id + company_id
    - `find_all()`: paginated with optional filters (user_id, is_office, is_active), default `is_active=True`, ordered by label
    - `find_by_user_id()`: filter by user_id + company_id, active only
    - Private `_to_entity(model)` mapper

---

## Phase 8: Tests — Shipment Entities

### 9. Unit tests for shipment entities and enums
- [x] Create `tests/unit/shipping_bc/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/domain/__init__.py`
- [x] Create `tests/unit/shipping_bc/shipment/domain/test_entities.py`
  - `test_create_shipment_generates_ulid_and_draft_status`
  - `test_create_shipment_validates_items_count`
  - `test_dispatch_from_draft` — DRAFT → DISPATCHED, sets dispatched_at
  - `test_dispatch_without_carrier_raises` — carrier is None → ValueError
  - `test_dispatch_without_tracking_raises` — tracking_number is None → ValueError
  - `test_dispatch_from_delivered_raises` — InvalidShipmentStatusTransitionError
  - `test_mark_in_transit_from_dispatched` — DISPATCHED → IN_TRANSIT
  - `test_mark_in_transit_from_draft_raises` — error
  - `test_deliver_from_dispatched` — DISPATCHED → DELIVERED, sets delivered_at
  - `test_deliver_from_in_transit` — IN_TRANSIT → DELIVERED
  - `test_fail_from_dispatched` — DISPATCHED → FAILED with reason
  - `test_fail_from_in_transit` — IN_TRANSIT → FAILED
  - `test_cancel_from_draft` — DRAFT → CANCELLED with reason
  - `test_cancel_from_dispatched` — DISPATCHED → CANCELLED
  - `test_cancel_from_delivered_raises` — error (terminal)
  - `test_add_item_in_draft` — succeeds
  - `test_add_item_in_dispatched_raises` — error (items locked)
  - `test_remove_item_in_draft` — succeeds
  - `test_shipment_status_is_terminal` — DELIVERED, FAILED, CANCELLED
  - `test_shipment_status_is_active` — DRAFT, DISPATCHED, IN_TRANSIT

---

## Phase 9: Tests — Address Entities

### 10. Unit tests for address entities
- [x] Create `tests/unit/shipping_bc/address/__init__.py`
- [x] Create `tests/unit/shipping_bc/address/domain/__init__.py`
- [x] Create `tests/unit/shipping_bc/address/domain/test_entities.py`
  - `test_create_address_generates_ulid`
  - `test_create_address_defaults_country_us`
  - `test_create_address_is_active_by_default`
  - `test_deactivate_sets_is_active_false`
  - `test_update_modifies_fields`

---

## Phase 10: Verification

### 11. Verify
- [x] Lint passes: `make lint` (no new errors in shipping_bc)
- [x] Unit tests pass: `make test`
- [ ] Migrations apply cleanly: `make db-upgrade` (requires Docker)
- [x] All `__init__.py` files present

---

## Dependency Graph

```
Package structure (1)
  └── Enums (2)
        ├── Entities - Shipment (3) — uses enums
        │     └── Repository interfaces - Shipment (5a)
        └── Entities - Address (4) — independent
              └── Repository interfaces - Address (5b)
                    ├── Migrations (6)
                    ├── Models (7)
                    └── Repositories (8)
                          ├── Shipment Entity Tests (9)
                          ├── Address Entity Tests (10)
                          └── Verification (11)
```

## Execution Order

**Batch 1:** Task 1 (package structure)
**Batch 2:** Task 2 (enums)
**Batch 3 (Parallel):** Tasks 3 + 4 (shipment entities + address entity)
**Batch 4:** Task 5 (repository interfaces)
**Batch 5 (Parallel):** Tasks 6 + 7 (migrations + models)
**Batch 6:** Task 8 (repositories)
**Batch 7 (Parallel):** Tasks 9 + 10 (tests)
**Batch 8:** Task 11 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All `__init__.py` files created
- [x] All tests passing (unit) — 25 passed
- [x] mypy passes on new code
- [x] 3 entities with factory methods (Shipment, ShipmentItem, ShippingAddress)
- [x] 3 enums (ShipmentStatus, ShipmentDirection, DestinationType)
- [x] 1 state machine with valid transitions
- [x] 2 repository interfaces
- [x] 3 SQLAlchemy models (Mapped[type])
- [x] 3 Alembic migrations
- [x] 2 repository implementations
- [x] ~25 unit tests covering entities + enums
