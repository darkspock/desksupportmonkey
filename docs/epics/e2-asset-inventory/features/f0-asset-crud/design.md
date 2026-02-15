# Design: F0 - Asset CRUD + Event Sourcing

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-15

---

## Architecture Overview

F0 introduces the `asset_bc` bounded context with two entities (Asset, AssetEvent) and full CRUD with event sourcing.

```
NEW FILES:
src/asset_bc/
├── asset/
│   ├── domain/
│   │   ├── entities.py           # Asset, AssetEvent dataclasses
│   │   ├── enums.py              # AssetType, AssetStatus + transitions
│   │   └── repository.py         # AssetRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_asset.py
│   │   │   ├── update_asset.py
│   │   │   └── change_asset_status.py
│   │   └── queries/
│   │       ├── list_assets.py
│   │       ├── get_asset.py
│   │       └── get_asset_history.py
│   └── infrastructure/
│       ├── models.py             # AssetModel, AssetEventModel
│       └── repository.py         # AssetRepository

adapters/http/api/assets/
├── routers.py
└── schemas.py

MODIFIED FILES:
core/models_registry.py           # Add AssetModel, AssetEventModel
app.py                            # Register assets router
```

---

## Domain Layer

### AssetType Enum

```python
class AssetType(str, Enum):
    LAPTOP = "laptop"
    MONITOR = "monitor"
    KEYBOARD = "keyboard"
    MOUSE = "mouse"
    HEADSET = "headset"
    DOCKING_STATION = "docking_station"
    OTHER = "other"
```

### AssetStatus Enum + Transitions

```python
class AssetStatus(str, Enum):
    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    IN_REPAIR = "in_repair"
    DECOMMISSIONED = "decommissioned"

VALID_TRANSITIONS: dict[AssetStatus, list[AssetStatus]] = {
    AssetStatus.IN_STOCK: [AssetStatus.IN_REPAIR, AssetStatus.DECOMMISSIONED],
    AssetStatus.ASSIGNED: [AssetStatus.IN_REPAIR, AssetStatus.DECOMMISSIONED],
    AssetStatus.IN_REPAIR: [AssetStatus.IN_STOCK, AssetStatus.DECOMMISSIONED],
    AssetStatus.DECOMMISSIONED: [],
}
```

Note: `in_stock <-> assigned` transitions are handled by assign/unassign in F1, not the generic status change.

### Asset Entity

```python
@dataclass
class Asset:
    id: str
    company_id: str
    type: AssetType
    brand: str
    model: str
    serial_number: str
    status: AssetStatus
    assigned_to: Optional[str] = None
    department_id: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, company_id, type, brand, model, serial_number, ...): ...
    def update(self, brand=None, model=None, ...): ...
    def change_status(self, new_status: AssetStatus): ...
```

### AssetEvent Entity

```python
@dataclass
class AssetEvent:
    id: str
    asset_id: str
    event_type: str
    data: dict
    performed_by: str
    created_at: Optional[datetime] = None

    @classmethod
    def create(cls, asset_id, event_type, data, performed_by): ...
```

### AssetRepositoryInterface

```python
class AssetRepositoryInterface(ABC):
    def save(self, asset: Asset) -> Asset: ...
    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Asset]: ...
    def find_by_serial_number(self, serial_number: str, company_id: str) -> Optional[Asset]: ...
    def find_all(self, company_id, page, page_size, ...) -> tuple[list[Asset], int]: ...
    def save_event(self, event: AssetEvent) -> AssetEvent: ...
    def find_events(self, asset_id: str) -> list[AssetEvent]: ...
```

---

## Infrastructure Layer

### AssetModel

```python
class AssetModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "assets"
    company_id = Column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    type = Column(String(30), nullable=False)
    brand = Column(String(255), nullable=False)
    model = Column(String(255), nullable=False)
    serial_number = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, server_default="in_stock")
    assigned_to = Column(String(26), ForeignKey("users.id"), nullable=True, index=True)
    department_id = Column(String(26), ForeignKey("departments.id"), nullable=True, index=True)
    purchase_date = Column(Date, nullable=True)
    warranty_expiration = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("company_id", "serial_number", name="uq_asset_company_serial"),
    )
```

### AssetEventModel

```python
class AssetEventModel(ULIDMixin, Base):
    __tablename__ = "asset_events"
    asset_id = Column(String(26), ForeignKey("assets.id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    data = Column(JSON, nullable=False)
    performed_by = Column(String(26), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
```

No TimestampMixin — events are immutable (no updated_at).

---

## Application Layer

### CreateAssetCommand
1. Validate serial_number unique in company -> `SerialNumberExistsError`
2. Create Asset entity
3. Save asset
4. Create AssetEvent (type=created, data=asset fields)
5. Return asset

### UpdateAssetCommand
1. Find asset by id + company_id -> `AssetNotFoundError`
2. Update mutable fields (brand, model, notes, purchase_date, warranty_expiration)
3. Save asset
4. Create AssetEvent (type=updated, data=changed fields)
5. Return asset

### ChangeAssetStatusCommand
1. Find asset -> `AssetNotFoundError`
2. Validate transition via state machine -> `InvalidStatusTransitionError`
3. Change status
4. If decommissioned, clear assigned_to
5. Save asset
6. Create AssetEvent (type=status_changed, data={old_status, new_status})
7. Return asset

---

## HTTP Layer

### Schemas

```python
class CreateAssetRequest(BaseModel):
    type: str
    brand: str = Field(min_length=1, max_length=255)
    model: str = Field(min_length=1, max_length=255)
    serial_number: str = Field(min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None

class UpdateAssetRequest(BaseModel):
    brand: Optional[str] = Field(None, min_length=1, max_length=255)
    model: Optional[str] = Field(None, min_length=1, max_length=255)
    purchase_date: Optional[date] = None
    warranty_expiration: Optional[date] = None
    notes: Optional[str] = None

class ChangeStatusRequest(BaseModel):
    status: str

class AssetResponse(BaseModel):
    id, company_id, type, brand, model, serial_number, status,
    assigned_to, department_id, purchase_date, warranty_expiration,
    notes, created_at, updated_at

class AssetEventResponse(BaseModel):
    id, asset_id, event_type, data, performed_by, created_at
```

---

## Decisions

1. **Dual-write pattern**: Asset table stores current state (for fast reads), AssetEvent table stores history (for audit). We don't derive state from events — this is pragmatic event sourcing.
2. **Status transitions for assign/unassign excluded**: The generic `change_status` endpoint only handles in_repair/decommissioned transitions. Assignment transitions are in F1 commands with their own business logic.
3. **Decommission clears assignment**: If an asset is decommissioned while assigned, the assignment is automatically cleared and an unassigned event is recorded.
4. **Event data as JSON**: Flexible schema per event type. Domain layer creates properly structured dicts.
