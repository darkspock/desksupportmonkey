# Solution Design: F1 — Shipment Lifecycle & Notifications

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `shipping_bc`
**Depends on:** F0 (complete)

## Summary

F1 delivers the full shipment lifecycle: create, dispatch, in_transit, deliver, fail, cancel, update tracking, create return, modify items (DRAFT only), list, get, asset shipment history, my/shipments (employee), and dashboard summary. It adds 16 API endpoints, 5 notification event types, a `ShipmentEventFactory`, and cross-BC asset status updates on delivery.

## Architecture Decision

All commands and queries follow the existing CQRS pattern: `Command`/`CommandHandler` and `Query`/`QueryHandler` from `src.framework.application`. Events use the existing `EventBus` + `DomainEvent` pattern. Cross-BC asset updates follow E14's `ReceiptAssetService` pattern — a service class isolates the dependency on `asset_bc`.

### Existing Code Reuse

| Component | Location | Reuse |
|-----------|----------|-------|
| Command/CommandHandler | `src/framework/application/command_bus.py` | Inherit |
| Query/QueryHandler | `src/framework/application/query_bus.py` | Inherit |
| EventBus | `src/notification_bc/notification/application/services/event_bus.py` | Use as-is |
| DomainEvent | `src/notification_bc/notification/domain/events.py` | Use as-is |
| EventType | `src/notification_bc/notification/domain/enums.py` | Add 5 values |
| TargetResolver | `src/notification_bc/notification/application/services/target_resolver.py` | Add 5 resolvers |
| get_event_bus | `adapters/http/api/dependencies.py` | Use as-is |
| AssetRepository | `src/asset_bc/asset/infrastructure/repository.py` | Inject for cross-BC |
| ReceiptAssetService pattern | `src/procurement_bc/` | Pattern reuse |

## Implementation Plan

### 1. Application Layer — Commands

#### 1.1 CreateShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/create_shipment.py`

```python
@dataclass
class CreateShipmentCommand(Command):
    company_id: str
    direction: str  # "outbound" | "inbound"
    destination_type: str  # "employee_home" | "office" | "vendor"
    destination_address_id: str
    created_by: str
    asset_ids: list[str]
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
```

Handler logic:
1. Validate `direction` and `destination_type` are valid enum values
2. For each asset_id, check `shipment_repo.find_active_by_asset_id()` — if any active shipment exists, raise ValueError
3. Create `Shipment.create(...)` with `ShipmentItem.create(...)` for each asset
4. Save and return shipment ID

#### 1.2 DispatchShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/dispatch_shipment.py`

```python
@dataclass
class DispatchShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
```

Handler: load shipment, update carrier/tracking fields if provided, call `dispatch()`, save.

#### 1.3 MarkInTransitCommand

**File:** `src/shipping_bc/shipment/application/commands/mark_in_transit.py`

```python
@dataclass
class MarkInTransitCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
```

Handler: load shipment, call `mark_in_transit()`, save.

#### 1.4 DeliverShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/deliver_shipment.py`

```python
@dataclass
class DeliverShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    notes: Optional[str] = None
```

Handler:
1. Load shipment, call `deliver()`
2. If notes provided, update shipment.notes
3. Save shipment
4. Cross-BC asset side effects via `DeliveryAssetService`:
   - Outbound to employee_home → mark each asset ASSIGNED (to recipient_user_id)
   - Inbound (return from repair) → mark each asset IN_STOCK
   - Outbound to office → no asset change (relocated, stays IN_STOCK)
   - Outbound to vendor → no asset change (stays IN_REPAIR)

#### 1.5 FailShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/fail_shipment.py`

```python
@dataclass
class FailShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    reason: str
```

Handler: load shipment, call `fail(reason)`, save.

#### 1.6 CancelShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/cancel_shipment.py`

```python
@dataclass
class CancelShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    reason: str
```

Handler: load shipment, call `cancel(reason)`, save.

#### 1.7 UpdateShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/update_shipment.py`

```python
@dataclass
class UpdateShipmentCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    notes: Optional[str] = None
```

Handler: load shipment, update mutable fields (only non-None values), save.

#### 1.8 CreateReturnShipmentCommand

**File:** `src/shipping_bc/shipment/application/commands/create_return_shipment.py`

```python
@dataclass
class CreateReturnShipmentCommand(Command):
    original_shipment_id: str
    company_id: str
    created_by: str
    destination_address_id: str
    asset_ids: list[str]
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
```

Handler:
1. Load original shipment, validate it exists and belongs to company
2. Create new shipment with `direction=INBOUND`, `return_for_shipment_id=original.id`
3. Origin = original's destination, destination = provided address
4. Validate asset conflicts (same as create)
5. Save and return new shipment ID

#### 1.9 ModifyShipmentItemsCommand

**File:** `src/shipping_bc/shipment/application/commands/modify_shipment_items.py`

```python
@dataclass
class ModifyShipmentItemsCommand(Command):
    shipment_id: str
    company_id: str
    performed_by: str
    add_asset_ids: list[str] = field(default_factory=list)
    remove_item_ids: list[str] = field(default_factory=list)
```

Handler:
1. Load shipment
2. For removals: call `shipment.remove_item(item_id)` for each
3. For additions: validate asset conflict, call `shipment.add_item(ShipmentItem.create(...))`
4. Save

### 2. Application Layer — Queries

#### 2.1 ListShipmentsQuery

**File:** `src/shipping_bc/shipment/application/queries/list_shipments.py`

```python
@dataclass
class ListShipmentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    direction: Optional[str] = None
    destination_type: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
```

Handler: delegates to `shipment_repo.find_all(...)`, returns paginated list.

#### 2.2 GetShipmentQuery

**File:** `src/shipping_bc/shipment/application/queries/get_shipment.py`

```python
@dataclass
class GetShipmentQuery(Query):
    shipment_id: str
    company_id: str
```

Handler: `find_by_id()`, raise if not found.

#### 2.3 ShipmentsByAssetQuery

**File:** `src/shipping_bc/shipment/application/queries/shipments_by_asset.py`

```python
@dataclass
class ShipmentsByAssetQuery(Query):
    asset_id: str
    company_id: str
```

Handler: delegates to `shipment_repo.find_by_asset_id(...)`.

#### 2.4 MyShipmentsQuery

**File:** `src/shipping_bc/shipment/application/queries/my_shipments.py`

```python
@dataclass
class MyShipmentsQuery(Query):
    recipient_user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
```

Handler: delegates to `shipment_repo.find_by_recipient_user_id(...)`.

#### 2.5 ShipmentDashboardQuery

**File:** `src/shipping_bc/shipment/application/queries/shipment_dashboard.py`

```python
@dataclass
class ShipmentDashboardQuery(Query):
    company_id: str
```

Handler:
1. `count_by_status()` → active counts (draft, dispatched, in_transit)
2. `find_recent_delivered(company_id, 7)` → recent deliveries
3. `find_by_status(company_id, "failed")` → failed count
4. Return dashboard summary dict

### 3. Cross-BC Service

#### 3.1 DeliveryAssetService

**File:** `src/shipping_bc/shipment/application/services/delivery_asset_service.py`

```python
class DeliveryAssetService:
    def __init__(self, asset_repo: AssetRepositoryInterface):
        self.asset_repo = asset_repo

    def update_assets_on_delivery(self, shipment: Shipment) -> None:
        if shipment.direction == ShipmentDirection.OUTBOUND:
            if shipment.destination_type == DestinationType.EMPLOYEE_HOME:
                self._assign_assets(shipment)
            # OFFICE and VENDOR: no asset change
        elif shipment.direction == ShipmentDirection.INBOUND:
            self._mark_assets_in_stock(shipment)

    def _assign_assets(self, shipment: Shipment) -> None:
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(item.asset_id, shipment.company_id)
            if asset:
                asset.assign(shipment.recipient_user_id)
                self.asset_repo.save(asset)

    def _mark_assets_in_stock(self, shipment: Shipment) -> None:
        for item in shipment.items:
            asset = self.asset_repo.find_by_id(item.asset_id, shipment.company_id)
            if asset:
                asset.change_status(AssetStatus.IN_STOCK)
                self.asset_repo.save(asset)
```

### 4. HTTP Layer

#### 4.1 Router

**File:** `adapters/http/api/shipments/routers.py`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/shipments` | technician+ | Create shipment |
| GET | `/api/v1/shipments` | technician+ | List shipments |
| GET | `/api/v1/shipments/{id}` | technician+ | Get detail |
| PATCH | `/api/v1/shipments/{id}` | technician+ | Update tracking/notes |
| POST | `/api/v1/shipments/{id}/dispatch` | technician+ | Dispatch |
| POST | `/api/v1/shipments/{id}/in-transit` | technician+ | Mark in transit |
| POST | `/api/v1/shipments/{id}/deliver` | technician+ | Mark delivered |
| POST | `/api/v1/shipments/{id}/fail` | technician+ | Mark failed |
| POST | `/api/v1/shipments/{id}/cancel` | technician+ | Cancel |
| POST | `/api/v1/shipments/{id}/return` | technician+ | Create return |
| GET | `/api/v1/shipments/by-asset/{asset_id}` | technician+ | Asset history |
| PATCH | `/api/v1/shipments/{id}/items` | technician+ | Modify items (DRAFT) |

**Additional endpoints on existing routers:**

| Method | Path | Router | Auth | Description |
|--------|------|--------|------|-------------|
| GET | `/api/v1/my/shipments` | my/routers.py | any auth | Employee's own |
| GET | `/api/v1/dashboard/shipments` | dashboard/routers.py | admin+ | Dashboard summary |

#### 4.2 Schemas

**File:** `adapters/http/api/shipments/schemas.py`

```python
class CreateShipmentRequest(BaseModel):
    direction: str
    destination_type: str
    destination_address_id: str
    asset_ids: list[str]
    origin_address_id: Optional[str] = None
    recipient_name: Optional[str] = None
    recipient_user_id: Optional[str] = None
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    request_id: Optional[str] = None
    po_id: Optional[str] = None
    notes: Optional[str] = None

class DispatchShipmentRequest(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None

class FailShipmentRequest(BaseModel):
    reason: str

class CancelShipmentRequest(BaseModel):
    reason: str

class DeliverShipmentRequest(BaseModel):
    notes: Optional[str] = None

class UpdateShipmentRequest(BaseModel):
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    notes: Optional[str] = None

class CreateReturnRequest(BaseModel):
    destination_address_id: str
    asset_ids: list[str]
    carrier: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class ModifyItemsRequest(BaseModel):
    add_asset_ids: list[str] = []
    remove_item_ids: list[str] = []

class ShipmentItemResponse(BaseModel):
    id: str
    shipment_id: str
    asset_id: str
    notes: Optional[str] = None

class ShipmentResponse(BaseModel):
    id: str
    company_id: str
    direction: str
    destination_type: str
    status: str
    origin_address_id: Optional[str]
    destination_address_id: str
    recipient_name: Optional[str]
    recipient_user_id: Optional[str]
    carrier: Optional[str]
    tracking_number: Optional[str]
    tracking_url: Optional[str]
    request_id: Optional[str]
    po_id: Optional[str]
    return_for_shipment_id: Optional[str]
    notes: Optional[str]
    failure_reason: Optional[str]
    cancellation_reason: Optional[str]
    created_by: str
    dispatched_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    items: list[ShipmentItemResponse] = []
    item_count: int = 0

class ShipmentDashboardResponse(BaseModel):
    active_by_status: dict[str, int]
    recent_deliveries: list[ShipmentResponse]
    failed_count: int
```

#### 4.3 Dependencies

**File:** `adapters/http/api/shipments/dependencies.py`

```python
def get_shipment_repo(db = Depends(get_db)):
    return ShipmentRepository(db)

def get_delivery_asset_service(db = Depends(get_db)):
    from src.asset_bc.asset.infrastructure.repository import AssetRepository
    return DeliveryAssetService(AssetRepository(db))
```

### 5. Notification Integration

#### 5.1 EventType additions

**File:** `src/notification_bc/notification/domain/enums.py` — Add:

```python
SHIPMENT_CREATED = "shipment.created"
SHIPMENT_DISPATCHED = "shipment.dispatched"
SHIPMENT_DELIVERED = "shipment.delivered"
SHIPMENT_FAILED = "shipment.failed"
SHIPMENT_CANCELLED = "shipment.cancelled"
```

#### 5.2 TargetResolver additions

Add 5 resolver methods to existing `TargetResolver`:
- `SHIPMENT_CREATED` → notify recipient_user_id (if set)
- `SHIPMENT_DISPATCHED` → notify recipient_user_id
- `SHIPMENT_DELIVERED` → notify recipient_user_id (outbound) or created_by (inbound)
- `SHIPMENT_FAILED` → notify created_by
- `SHIPMENT_CANCELLED` → notify recipient_user_id (if already dispatched)

### 6. App Registration

**File:** `app.py` — Add:
```python
from adapters.http.api.shipments.routers import router as shipments_router
app.include_router(shipments_router)
```

## Testing Strategy

### Unit Tests (~25 tests)

**`tests/unit/shipping_bc/shipment/application/commands/test_create.py`:**
- Create with valid data saves shipment in DRAFT
- Create validates asset conflict (active shipment exists)
- Create with invalid direction raises ValueError
- Create return links via return_for_shipment_id

**`tests/unit/shipping_bc/shipment/application/commands/test_dispatch.py`:**
- Dispatch sets carrier and tracking, transitions to DISPATCHED
- Dispatch without carrier raises ValueError
- Dispatch from DELIVERED raises error

**`tests/unit/shipping_bc/shipment/application/commands/test_deliver.py`:**
- Deliver from DISPATCHED → DELIVERED
- Deliver from IN_TRANSIT → DELIVERED
- Deliver calls DeliveryAssetService for outbound employee_home
- Deliver does NOT call service for outbound office

**`tests/unit/shipping_bc/shipment/application/commands/test_transitions.py`:**
- MarkInTransit from DISPATCHED → IN_TRANSIT
- Fail from DISPATCHED/IN_TRANSIT → FAILED with reason
- Cancel from DRAFT/DISPATCHED → CANCELLED with reason
- Cancel from DELIVERED raises error

**`tests/unit/shipping_bc/shipment/application/commands/test_items.py`:**
- ModifyItems adds assets in DRAFT
- ModifyItems removes items in DRAFT
- ModifyItems in DISPATCHED raises error
- ModifyItems validates asset conflict

**`tests/unit/shipping_bc/shipment/application/queries/test_queries.py`:**
- List returns paginated results with filters
- Get returns shipment or raises not found
- ShipmentsByAsset returns history
- MyShipments returns recipient's shipments
- Dashboard returns counts and lists

### Integration Tests (~18 tests)

**`tests/integration/test_shipments_endpoints.py`:**
- POST create → 201
- GET list → 200 with pagination
- GET detail → 200 with items
- PATCH update → 200
- POST dispatch → 200
- POST in-transit → 200
- POST deliver → 200
- POST fail → 200
- POST cancel → 200
- POST return → 201
- GET by-asset → 200
- PATCH items → 200
- GET my/shipments → 200
- GET dashboard/shipments → 200
- Create with active asset conflict → 409
- Dispatch without tracking → 422
- Invalid state transition → 409
- Deliver updates asset status (cross-BC)

## Implementation Order

1. Notification enums (add 5 EventType values)
2. TargetResolver additions (5 methods)
3. DeliveryAssetService (cross-BC)
4. Commands (create, dispatch, in_transit, deliver, fail, cancel, update, return, modify_items)
5. Queries (list, get, by_asset, my_shipments, dashboard)
6. Schemas + Dependencies
7. Router + App registration
8. My/shipments endpoint on my/routers.py
9. Dashboard endpoint on dashboard/routers.py
10. Unit tests
11. Integration tests
12. Verification
