# Solution Design: F0 — Shipping Domain & Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `shipping_bc`

## Summary

F0 creates the entire `shipping_bc` bounded context foundation: 2 subdomains (`shipment` and `address`), 5 domain entities (`Shipment`, `ShipmentItem`, `ShippingAddress`), 3 enums (`ShipmentStatus`, `ShipmentDirection`, `DestinationType`), 2 repository interfaces, 3 SQLAlchemy models, 3 Alembic migrations, and 2 repository implementations. No API endpoints or frontend — pure domain + infrastructure.

## Architecture Decision

New bounded context `shipping_bc` with two subdomains: `shipment` (Shipment + ShipmentItem) and `address` (ShippingAddress). Follows the same DDD structure as `procurement_bc` and `appointment_bc`. ShipmentItem is a child entity of Shipment (same pattern as PurchaseOrderItem).

### Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ULIDMixin | `core/mixins.py` | Yes | None |
| TimestampMixin | `core/mixins.py` | Yes | None |
| Base (SQLAlchemy) | `core/base.py` | Yes | None |
| PO enum pattern | `src/procurement_bc/purchase_order/domain/enums.py` | Pattern reuse | Adapt for ShipmentStatus |
| PO entity pattern | `src/procurement_bc/purchase_order/domain/entities.py` | Pattern reuse | Adapt for Shipment+ShipmentItem parent-child |
| PO repo pattern | `src/procurement_bc/purchase_order/infrastructure/repository.py` | Pattern reuse | Adapt for Shipment with items cascade |

## Implementation Plan

### 1. Domain Layer

#### 1.1 Enums

**File:** `src/shipping_bc/shipment/domain/enums.py`

**`ShipmentStatus`** — `str, Enum` with 6 values:

| Value | Description | Terminal |
|-------|-------------|----------|
| `DRAFT` | Shipment created, not yet dispatched | No |
| `DISPATCHED` | Picked up by carrier, tracking assigned | No |
| `IN_TRANSIT` | Confirmed in transit (optional intermediate) | No |
| `DELIVERED` | Delivered to destination | Yes |
| `FAILED` | Lost, damaged, or returned to sender | Yes |
| `CANCELLED` | Cancelled before delivery | Yes |

**`VALID_TRANSITIONS`** dict:

```python
VALID_TRANSITIONS = {
    DRAFT: [DISPATCHED, CANCELLED],
    DISPATCHED: [IN_TRANSIT, DELIVERED, FAILED, CANCELLED],
    IN_TRANSIT: [DELIVERED, FAILED, CANCELLED],
    DELIVERED: [],
    FAILED: [],
    CANCELLED: [],
}
```

**`ShipmentDirection`** — `str, Enum`:
- `OUTBOUND = "outbound"`
- `INBOUND = "inbound"`

**`DestinationType`** — `str, Enum`:
- `EMPLOYEE_HOME = "employee_home"`
- `OFFICE = "office"`
- `VENDOR = "vendor"`

**`InvalidShipmentStatusTransitionError`** — Exception with `current` and `target` status.

#### 1.2 Entities

**File:** `src/shipping_bc/shipment/domain/entities.py`

**`ShipmentItem`** — Child entity:

```python
@dataclass
class ShipmentItem:
    id: str
    shipment_id: str
    asset_id: str
    notes: Optional[str] = None
```

Factory method `create(shipment_id, asset_id, notes?, id?)`:
- Generates ULID if no id provided

**`Shipment`** — Main entity with state machine:

```python
@dataclass
class Shipment:
    id: str
    company_id: str
    direction: ShipmentDirection
    destination_type: DestinationType
    status: ShipmentStatus
    destination_address_id: str
    created_by: str
    origin_address_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_user_id: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
    return_for_shipment_id: Optional[str] = None
    notes: Optional[str] = None
    failure_reason: Optional[str] = None
    cancellation_reason: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: list[ShipmentItem] = field(default_factory=list)
```

Factory method `create(company_id, direction, destination_type, destination_address_id, created_by, ...)`:
- Generates ULID
- Sets initial status to `DRAFT`
- Validates `items` count <= 20

State machine methods:
- `dispatch()` — DRAFT → DISPATCHED, validates `carrier` and `tracking_number` are set, sets `dispatched_at`
- `mark_in_transit()` — DISPATCHED → IN_TRANSIT
- `deliver()` — DISPATCHED/IN_TRANSIT → DELIVERED, sets `delivered_at`
- `fail(reason: str)` — DISPATCHED/IN_TRANSIT → FAILED, sets `failure_reason`
- `cancel(reason: str)` — any non-terminal → CANCELLED, sets `cancellation_reason`

Item management:
- `add_item(item: ShipmentItem)` — validates status is DRAFT, validates items count < 20
- `remove_item(item_id: str)` — validates status is DRAFT, removes item by id

All use `_transition(target)` pattern from PO entity.

**File:** `src/shipping_bc/address/domain/entities.py`

**`ShippingAddress`** — Address entity:

```python
@dataclass
class ShippingAddress:
    id: str
    company_id: str
    label: str
    street_line_1: str
    city: str
    state: str
    postal_code: str
    country: str
    street_line_2: Optional[str] = None
    recipient_name: Optional[str] = None
    phone: Optional[str] = None
    user_id: Optional[str] = None
    is_office: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

Factory method `create(company_id, label, street_line_1, city, state, postal_code, country, ...)`:
- Generates ULID
- Sets `is_active = True`
- Defaults `country = "US"` if not provided

Methods:
- `deactivate()` — sets `is_active = False`
- `update(label?, street_line_1?, ...)` — updates mutable fields

#### 1.3 Repository Interfaces

**File:** `src/shipping_bc/shipment/domain/repository.py`

**`ShipmentRepositoryInterface(ABC)`:**
- `save(shipment) -> Shipment`
- `find_by_id(id, company_id) -> Optional[Shipment]`
- `find_all(company_id, page, page_size, status?, direction?, destination_type?, request_id?, po_id?) -> tuple[list[Shipment], int]`
- `find_by_asset_id(asset_id, company_id) -> list[Shipment]` — shipments containing this asset
- `find_active_by_asset_id(asset_id, company_id) -> list[Shipment]` — active (DRAFT/DISPATCHED/IN_TRANSIT) shipments for asset conflict check
- `find_by_recipient_user_id(recipient_user_id, company_id, page, page_size) -> tuple[list[Shipment], int]` — for my/shipments
- `count_by_status(company_id) -> dict[str, int]` — dashboard counts
- `find_recent_delivered(company_id, days) -> list[Shipment]` — recent deliveries
- `find_by_status(company_id, status) -> list[Shipment]` — e.g., failed shipments

**File:** `src/shipping_bc/address/domain/repository.py`

**`ShippingAddressRepositoryInterface(ABC)`:**
- `save(address) -> ShippingAddress`
- `find_by_id(id, company_id) -> Optional[ShippingAddress]`
- `find_all(company_id, page, page_size, user_id?, is_office?, is_active?) -> tuple[list[ShippingAddress], int]`
- `find_by_user_id(user_id, company_id) -> list[ShippingAddress]`
- `delete(id, company_id) -> bool` — not used (soft-delete via deactivate)

### 2. Infrastructure Layer

#### 2.1 Migrations

**Migration 1: `create_shipping_addresses`** (first, because shipments FK to it)

```sql
CREATE TABLE shipping_addresses (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    label VARCHAR(100) NOT NULL,
    recipient_name VARCHAR(200),
    street_line_1 VARCHAR(300) NOT NULL,
    street_line_2 VARCHAR(300),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20) NOT NULL,
    country VARCHAR(2) NOT NULL DEFAULT 'US',
    phone VARCHAR(30),
    user_id VARCHAR(26) REFERENCES users(id),
    is_office BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX ix_shipping_addresses_company_id ON shipping_addresses(company_id);
CREATE INDEX ix_shipping_addresses_user_id ON shipping_addresses(user_id);
```

**Migration 2: `create_shipments`**

```sql
CREATE TABLE shipments (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    direction VARCHAR(20) NOT NULL,
    destination_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    origin_address_id VARCHAR(26) REFERENCES shipping_addresses(id),
    destination_address_id VARCHAR(26) NOT NULL REFERENCES shipping_addresses(id),
    recipient_name VARCHAR(200),
    recipient_user_id VARCHAR(26) REFERENCES users(id),
    carrier VARCHAR(100),
    tracking_number VARCHAR(100),
    tracking_url VARCHAR(500),
    request_id VARCHAR(26) REFERENCES service_requests(id),
    po_id VARCHAR(26) REFERENCES purchase_orders(id),
    return_for_shipment_id VARCHAR(26) REFERENCES shipments(id),
    notes TEXT,
    failure_reason TEXT,
    cancellation_reason TEXT,
    created_by VARCHAR(26) NOT NULL,
    dispatched_at TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX ix_shipments_company_id ON shipments(company_id);
CREATE INDEX ix_shipments_status ON shipments(status);
CREATE INDEX ix_shipments_direction ON shipments(direction);
CREATE INDEX ix_shipments_request_id ON shipments(request_id);
CREATE INDEX ix_shipments_po_id ON shipments(po_id);
CREATE INDEX ix_shipments_recipient_user_id ON shipments(recipient_user_id);
CREATE INDEX ix_shipments_return_for ON shipments(return_for_shipment_id);
```

**Migration 3: `create_shipment_items`**

```sql
CREATE TABLE shipment_items (
    id VARCHAR(26) PRIMARY KEY,
    shipment_id VARCHAR(26) NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    asset_id VARCHAR(26) NOT NULL REFERENCES assets(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ix_shipment_items_shipment_id ON shipment_items(shipment_id);
CREATE INDEX ix_shipment_items_asset_id ON shipment_items(asset_id);
```

#### 2.2 SQLAlchemy Models

**File:** `src/shipping_bc/shipment/infrastructure/models.py`

- **`ShipmentModel(ULIDMixin, TimestampMixin, Base)`:**
  - `__tablename__ = "shipments"`
  - All fields with `Mapped[type]` annotations
  - FK to `companies.id`, `shipping_addresses.id` (x2), `users.id`, `service_requests.id`, `purchase_orders.id`, self-referential `shipments.id`
  - `items` relationship: `relationship("ShipmentItemModel", cascade="all, delete-orphan", lazy="joined")`

- **`ShipmentItemModel(ULIDMixin, Base)`:**
  - `__tablename__ = "shipment_items"`
  - FK to `shipments.id` (ondelete CASCADE), `assets.id`
  - `created_at` column (no TimestampMixin — no updated_at needed)

**File:** `src/shipping_bc/address/infrastructure/models.py`

- **`ShippingAddressModel(ULIDMixin, TimestampMixin, Base)`:**
  - `__tablename__ = "shipping_addresses"`
  - All fields with `Mapped[type]` annotations
  - FK to `companies.id`, optional `users.id`

#### 2.3 Repository Implementations

**File:** `src/shipping_bc/shipment/infrastructure/repository.py`

- **`ShipmentRepository(ShipmentRepositoryInterface)`:**
  - `__init__(self, session: Session)`
  - `save()`: upsert pattern — syncs items (clear + re-add for update)
  - `find_by_id()`: query with joined items
  - `find_all()`: paginated with filters
  - `find_by_asset_id()`: join with `shipment_items` on `asset_id`
  - `find_active_by_asset_id()`: filter `status IN ('draft', 'dispatched', 'in_transit')`
  - `find_by_recipient_user_id()`: paginated filter on `recipient_user_id`
  - `count_by_status()`: group by status, return dict
  - `find_recent_delivered()`: filter `status = 'delivered'` and `delivered_at >= now - days`
  - `find_by_status()`: simple filter
  - Private `_to_entity(model)` and `_to_item_entity(model)` mappers

**File:** `src/shipping_bc/address/infrastructure/repository.py`

- **`ShippingAddressRepository(ShippingAddressRepositoryInterface)`:**
  - `__init__(self, session: Session)`
  - `save()`: upsert pattern
  - `find_by_id()`: query by id + company_id
  - `find_all()`: paginated with filters (user_id, is_office, is_active)
  - `find_by_user_id()`: filter by user_id + company_id
  - Private `_to_entity(model)` mapper

### 3. Package Structure

```
src/shipping_bc/
├── __init__.py
├── shipment/
│   ├── __init__.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands/
│   │   │   └── __init__.py
│   │   ├── queries/
│   │   │   └── __init__.py
│   │   └── ports.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   ├── enums.py
│   │   └── repository.py
│   └── infrastructure/
│       ├── __init__.py
│       ├── models.py
│       └── repository.py
├── address/
│   ├── __init__.py
│   ├── application/
│   │   ├── __init__.py
│   │   ├── commands/
│   │   │   └── __init__.py
│   │   ├── queries/
│   │   │   └── __init__.py
│   │   └── ports.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py
│   │   └── repository.py
│   └── infrastructure/
│       ├── __init__.py
│       ├── models.py
│       └── repository.py
```

## Testing Strategy

### Unit Tests (~18 tests)

**`tests/unit/shipping_bc/shipment/domain/test_entities.py`:**
- Shipment.create() generates ULID and sets DRAFT status
- Shipment.create() validates items count <= 20
- dispatch() transitions DRAFT → DISPATCHED, sets dispatched_at
- dispatch() without carrier raises ValueError
- dispatch() without tracking_number raises ValueError
- dispatch() from DELIVERED raises InvalidShipmentStatusTransitionError
- mark_in_transit() from DISPATCHED → IN_TRANSIT
- mark_in_transit() from DRAFT raises error
- deliver() from DISPATCHED → DELIVERED, sets delivered_at
- deliver() from IN_TRANSIT → DELIVERED
- fail() from DISPATCHED → FAILED with reason
- fail() from IN_TRANSIT → FAILED
- cancel() from DRAFT → CANCELLED with reason
- cancel() from DISPATCHED → CANCELLED
- cancel() from DELIVERED raises error
- add_item() in DRAFT succeeds
- add_item() in DISPATCHED raises error
- remove_item() in DRAFT succeeds

**`tests/unit/shipping_bc/address/domain/test_entities.py`:**
- ShippingAddress.create() generates ULID and sets is_active
- deactivate() sets is_active to False
- update() modifies fields

## Implementation Order

1. Package structure (`__init__.py` files)
2. Enums (`ShipmentStatus`, `ShipmentDirection`, `DestinationType`, error)
3. Entities (`Shipment`, `ShipmentItem`, `ShippingAddress`)
4. Repository interfaces (2 ABC classes)
5. Migrations (3 Alembic migrations)
6. SQLAlchemy models (3 models)
7. Repository implementations (2 classes)
8. Unit tests (entities)
9. Verification (lint + tests)

## Risks

- **Parent-child cascade:** Shipment.items sync on save requires careful implementation in the repository. Follow PO repo's pattern of clearing and re-adding items on update.
- **Self-referential FK:** `return_for_shipment_id` references `shipments(id)`. Standard SQLAlchemy pattern, no issues expected.
- **Address FK ordering:** Migrations must create `shipping_addresses` before `shipments` (FK dependency).
