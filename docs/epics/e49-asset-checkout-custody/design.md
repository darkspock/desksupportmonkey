# E49: Asset Checkout & Custody Management — Technical Design

**Date:** 2026-02-26
**Requirements:** [requirements.md](requirements.md)

## Bounded Context

Extend existing `asset_bc` under `src/asset_bc/checkout/`. The checkout concept is tightly coupled to assets — it uses the same repository infrastructure, same asset entity, and directly mutates asset state. A separate BC would require cross-BC commands for every checkout/checkin operation.

Structure:
```
src/asset_bc/checkout/
  domain/
    entities.py      — AssetCheckout
    enums.py         — AssetCondition
    exceptions.py    — CheckoutNotFoundError, ActiveCheckoutExistsError, etc.
    repository.py    — CheckoutRepositoryInterface
  application/
    commands/
      create_checkout.py
      checkin_asset.py
      cancel_checkout.py
      accept_checkout.py
    queries/
      get_current_checkout.py
      list_asset_checkouts.py
      list_company_checkouts.py
      list_my_equipment.py
    ports.py         — AssetLookup, UserLookup, MaintenanceLookup
  infrastructure/
    models.py        — AssetCheckoutModel
    repository.py    — CheckoutRepository
```

## Domain Layer

### Entities

#### AssetCheckout

```python
@dataclass
class AssetCheckout:
    id: str
    company_id: str
    asset_id: str
    user_id: str                          # Employee receiving the asset
    checked_out_by: str                   # Technician performing handover
    checked_out_at: datetime
    condition_out: AssetCondition
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None
    accepted_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    condition_in: Optional[AssetCondition] = None
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    maintenance_id: Optional[str] = None   # Link to GDPR maintenance created on checkin
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        company_id: str,
        asset_id: str,
        user_id: str,
        checked_out_by: str,
        condition_out: AssetCondition,
        condition_out_notes: Optional[str] = None,
        notes_out: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "AssetCheckout": ...

    def accept(self, user_id: str) -> None:
        """Employee confirms receipt. Raises if not the assigned user or already accepted/closed."""
        ...

    def checkin(
        self,
        checked_in_by: str,
        condition_in: AssetCondition,
        condition_in_notes: Optional[str] = None,
        notes_in: Optional[str] = None,
    ) -> None:
        """Close the checkout (return asset). Raises if not open."""
        ...

    def cancel(self, cancelled_by: str, reason: Optional[str] = None) -> None:
        """Cancel the checkout. Raises if already checked in or already cancelled."""
        ...

    @property
    def is_open(self) -> bool:
        return self.checked_in_at is None and self.cancelled_at is None

    @property
    def is_accepted(self) -> bool:
        return self.accepted_at is not None

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None
```

### Enums

#### AssetCondition

```python
class AssetCondition(str, Enum):
    NEW = "new"
    GOOD = "good"
    FAIR = "fair"
    DAMAGED = "damaged"
    UNUSABLE = "unusable"
```

File: `src/asset_bc/checkout/domain/enums.py`

### Exceptions

File: `src/asset_bc/checkout/domain/exceptions.py`

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

### Repository Interface

File: `src/asset_bc/checkout/domain/repository.py`

```python
class CheckoutRepositoryInterface(ABC):

    @abstractmethod
    def save(self, checkout: AssetCheckout) -> AssetCheckout: ...

    @abstractmethod
    def find_by_id(self, checkout_id: str, company_id: str) -> Optional[AssetCheckout]: ...

    @abstractmethod
    def find_active_by_asset(self, asset_id: str, company_id: str) -> Optional[AssetCheckout]: ...

    @abstractmethod
    def find_by_asset(
        self, asset_id: str, company_id: str,
        page: int = 1, page_size: int = 20,
    ) -> tuple[list[AssetCheckout], int]: ...

    @abstractmethod
    def find_open_by_company(
        self, company_id: str,
        page: int = 1, page_size: int = 20,
        user_id: Optional[str] = None,
        asset_id: Optional[str] = None,
    ) -> tuple[list[AssetCheckout], int]: ...

    @abstractmethod
    def find_pending_acceptance_by_user(
        self, user_id: str, company_id: str,
    ) -> list[AssetCheckout]: ...

    @abstractmethod
    def find_open_by_user(
        self, user_id: str, company_id: str,
    ) -> list[AssetCheckout]: ...

    @abstractmethod
    def count_open_by_company(self, company_id: str) -> int: ...

    @abstractmethod
    def count_pending_acceptance_by_company(self, company_id: str) -> int: ...

    @abstractmethod
    def find_unaccepted_older_than_days(
        self, company_id: str, days: int,
    ) -> list[AssetCheckout]: ...
```

### Ports

File: `src/asset_bc/checkout/application/ports.py`

```python
class CheckoutAssetLookup(ABC):
    """Port to look up asset data from the asset subdomain."""
    @abstractmethod
    def find_by_id(self, asset_id: str, company_id: str) -> Optional[Any]: ...

class CheckoutUserLookup(ABC):
    """Port to look up user data."""
    @abstractmethod
    def find_by_id_and_company(self, user_id: str, company_id: str) -> Optional[Any]: ...
```

---

## Application Layer

### Commands

#### CreateCheckoutCommand

File: `src/asset_bc/checkout/application/commands/create_checkout.py`

```python
@dataclass
class CreateCheckoutCommand(Command):
    checkout_id: str
    company_id: str
    asset_id: str
    user_id: str                    # Employee
    performed_by: str               # Technician
    condition_out: str              # AssetCondition value
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None
```

Handler logic:
1. Look up asset via `AssetRepositoryInterface.find_by_id()`
2. If asset is `IN_STOCK`: auto-assign (set `assigned_to`, status → `ASSIGNED`, save, create "assigned" event)
3. If asset is `ASSIGNED` to target `user_id`: proceed
4. If asset is `ASSIGNED` to a different user: raise `AssetAssignedToOtherError`
5. Otherwise: raise `InvalidCheckoutAssetStatusError`
6. Check no active checkout exists via `CheckoutRepositoryInterface.find_active_by_asset()`
7. Create `AssetCheckout.create()`
8. Save checkout
9. Create `AssetEvent` with `event_type="checked_out"`

Dependencies: `asset_repo: AssetRepositoryInterface`, `checkout_repo: CheckoutRepositoryInterface`, `user_repo: UserLookup`

#### CheckinAssetCommand

File: `src/asset_bc/checkout/application/commands/checkin_asset.py`

```python
@dataclass
class CheckinAssetCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    condition_in: str
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None
```

Handler logic:
1. Find active checkout for asset
2. Call `checkout.checkin()`
3. Determine next asset status based on `condition_in`:
   - `unusable` → `DECOMMISSIONED`
   - `good`/`fair`/`damaged` → `IN_REPAIR`
4. Change asset status via `asset.change_status()`
5. Save checkout and asset
6. Auto-create GDPR sanitization maintenance record via `CreateMaintenanceRecordCommand`:
   - Title: "GDPR Sanitization — {asset.brand} {asset.model}"
   - Use company's GDPR template if available
   - Link via `maintenance_id` on checkout
7. Create `AssetEvent` with `event_type="checked_in"`

Dependencies: `asset_repo`, `checkout_repo`, `maintenance_repo`, `maintenance_template_repo`

#### CancelCheckoutCommand

File: `src/asset_bc/checkout/application/commands/cancel_checkout.py`

```python
@dataclass
class CancelCheckoutCommand(Command):
    asset_id: str
    company_id: str
    performed_by: str
    reason: Optional[str] = None
```

Handler logic:
1. Find active checkout for asset
2. Call `checkout.cancel()`
3. Determine pre-checkout state:
   - If checkout auto-assigned (asset was `IN_STOCK`): unassign asset back to `IN_STOCK`
   - If checkout was for already-assigned asset: keep `ASSIGNED`
4. Save checkout and asset
5. Create `AssetEvent` with `event_type="checkout_cancelled"`

Design decision: To know if auto-assigned, add `auto_assigned: bool` field to `AssetCheckout` (set `True` when checkout triggers auto-assign in create handler).

Add field to entity:
```python
auto_assigned: bool = False
```

#### AcceptCheckoutCommand

File: `src/asset_bc/checkout/application/commands/accept_checkout.py`

```python
@dataclass
class AcceptCheckoutCommand(Command):
    asset_id: str
    company_id: str
    user_id: str      # The employee accepting (from auth)
```

Handler logic:
1. Find active checkout for asset
2. Validate `command.user_id == checkout.user_id` (only assigned employee)
3. Call `checkout.accept(command.user_id)`
4. Save checkout
5. Create `AssetEvent` with `event_type="checkout_accepted"`

### Queries

#### GetCurrentCheckoutQuery

File: `src/asset_bc/checkout/application/queries/get_current_checkout.py`

```python
@dataclass
class GetCurrentCheckoutQuery(Query):
    asset_id: str
    company_id: str

class GetCurrentCheckoutQueryHandler(QueryHandler[GetCurrentCheckoutQuery, Optional[AssetCheckout]]):
    def handle(self, query) -> Optional[AssetCheckout]:
        return self.checkout_repo.find_active_by_asset(query.asset_id, query.company_id)
```

#### ListAssetCheckoutsQuery

File: `src/asset_bc/checkout/application/queries/list_asset_checkouts.py`

Returns paginated checkout history for a single asset.

#### ListCompanyCheckoutsQuery

File: `src/asset_bc/checkout/application/queries/list_company_checkouts.py`

Returns paginated open checkouts company-wide with optional filters (user_id, asset_id).

#### ListMyEquipmentQuery

File: `src/asset_bc/checkout/application/queries/list_my_equipment.py`

Returns current employee's open checkouts + pending acceptance items.

---

## Infrastructure Layer

### SQLAlchemy Model

File: `src/asset_bc/checkout/infrastructure/models.py`

```python
class AssetCheckoutModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "asset_checkouts"

    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), index=True)
    asset_id: Mapped[str] = mapped_column(String(26), ForeignKey("assets.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    checked_out_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"))
    checked_out_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    condition_out: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_out_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes_out: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    checked_in_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
    condition_in: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    condition_in_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes_in: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("users.id"), nullable=True)
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    maintenance_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
    auto_assigned: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
```

Partial unique index for one-active-checkout-per-asset:
```python
__table_args__ = (
    Index(
        "uq_asset_checkouts_active",
        "asset_id",
        unique=True,
        postgresql_where=text("checked_in_at IS NULL AND cancelled_at IS NULL"),
    ),
)
```

### Repository Implementation

File: `src/asset_bc/checkout/infrastructure/repository.py`

Implements `CheckoutRepositoryInterface` using SQLAlchemy. Follows same patterns as `AssetRepository`:
- `_to_entity()` / `_to_model()` conversion methods
- `.flush()` + `.refresh()` for fresh data on save

### Migration

File: `alembic/versions/xxx_create_asset_checkouts_table.py`

```sql
CREATE TABLE asset_checkouts (
    id                  VARCHAR(26) PRIMARY KEY,
    company_id          VARCHAR(26) NOT NULL REFERENCES companies(id),
    asset_id            VARCHAR(26) NOT NULL REFERENCES assets(id),
    user_id             VARCHAR(26) NOT NULL REFERENCES users(id),
    checked_out_by      VARCHAR(26) NOT NULL REFERENCES users(id),
    checked_out_at      TIMESTAMP NOT NULL,
    condition_out       VARCHAR(20) NOT NULL,
    condition_out_notes TEXT,
    notes_out           TEXT,
    accepted_at         TIMESTAMP,
    checked_in_at       TIMESTAMP,
    checked_in_by       VARCHAR(26) REFERENCES users(id),
    condition_in        VARCHAR(20),
    condition_in_notes  TEXT,
    notes_in            TEXT,
    cancelled_at        TIMESTAMP,
    cancelled_by        VARCHAR(26) REFERENCES users(id),
    cancel_reason       TEXT,
    maintenance_id      VARCHAR(26),
    auto_assigned       BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMP DEFAULT now(),
    updated_at          TIMESTAMP
);

CREATE INDEX ix_asset_checkouts_company ON asset_checkouts(company_id);
CREATE INDEX ix_asset_checkouts_asset ON asset_checkouts(asset_id);
CREATE INDEX ix_asset_checkouts_user ON asset_checkouts(user_id);
CREATE UNIQUE INDEX uq_asset_checkouts_active
    ON asset_checkouts(asset_id)
    WHERE checked_in_at IS NULL AND cancelled_at IS NULL;
```

---

## HTTP Layer

### Endpoints

File: `adapters/http/api/checkouts/routers.py`

| Method | Route | Role | Handler |
|--------|-------|------|---------|
| POST | `/api/v1/assets/{asset_id}/checkout` | TECHNICIAN | CreateCheckoutCommandHandler |
| POST | `/api/v1/assets/{asset_id}/checkin` | TECHNICIAN | CheckinAssetCommandHandler |
| POST | `/api/v1/assets/{asset_id}/checkout/cancel` | TECHNICIAN | CancelCheckoutCommandHandler |
| POST | `/api/v1/assets/{asset_id}/checkout/accept` | EMPLOYEE | AcceptCheckoutCommandHandler |
| GET | `/api/v1/assets/{asset_id}/checkouts` | TECHNICIAN | ListAssetCheckoutsQueryHandler |
| GET | `/api/v1/assets/{asset_id}/checkout/current` | ANY | GetCurrentCheckoutQueryHandler |
| GET | `/api/v1/checkouts` | TECHNICIAN | ListCompanyCheckoutsQueryHandler |

File: `adapters/http/api/my/routers.py` (extend existing)

| Method | Route | Role | Handler |
|--------|-------|------|---------|
| GET | `/api/v1/my/equipment` | EMPLOYEE | ListMyEquipmentQueryHandler |
| POST | `/api/v1/my/equipment/{asset_id}/accept` | EMPLOYEE | AcceptCheckoutCommandHandler |

### Schemas

File: `adapters/http/api/checkouts/schemas.py`

```python
class CreateCheckoutRequest(BaseModel):
    user_id: str = Field(min_length=1)
    condition_out: str = Field(min_length=1)
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None

class CheckinRequest(BaseModel):
    condition_in: str = Field(min_length=1)
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None

class CancelCheckoutRequest(BaseModel):
    reason: Optional[str] = None

class CheckoutResponse(BaseModel):
    id: str
    company_id: str
    asset_id: str
    user_id: str
    user_email: Optional[str] = None
    checked_out_by: str
    checked_out_at: datetime
    condition_out: str
    condition_out_notes: Optional[str] = None
    notes_out: Optional[str] = None
    accepted_at: Optional[datetime] = None
    checked_in_at: Optional[datetime] = None
    checked_in_by: Optional[str] = None
    condition_in: Optional[str] = None
    condition_in_notes: Optional[str] = None
    notes_in: Optional[str] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    maintenance_id: Optional[str] = None
    auto_assigned: bool = False
    status: str     # Derived: "open", "accepted", "checked_in", "cancelled"
    created_at: Optional[datetime] = None

class MyEquipmentResponse(BaseModel):
    open_checkouts: list[CheckoutResponse]
    pending_acceptance: list[CheckoutResponse]
```

### Dependencies

File: `adapters/http/api/checkouts/dependencies.py`

```python
def get_checkout_repo(db: Session = Depends(get_db)) -> CheckoutRepository:
    return CheckoutRepository(db)
```

---

## Collateral Changes

### Files to Modify

| File | Change | Description |
|------|--------|-------------|
| `src/asset_bc/asset/domain/enums.py` | Remove `EMPLOYEE` from `SystemLocation` | No longer needed; checkout tracks custody |
| `src/asset_bc/asset/application/commands/assign_asset.py` | Remove auto-location move to "Empleado" | Lines 54-92: remove employee_loc lookup and location_changed event |
| `src/asset_bc/asset/application/commands/unassign_asset.py` | Remove auto-location move + add open checkout guard | Remove warehouse auto-move; add `checkout_repo` dependency to check for open checkouts |
| `src/company_bc/company/application/commands/create_company.py` | Remove EMPLOYEE location seeding, add GDPR template seeding | Modify system location loop; add maintenance template creation |
| `adapters/http/api/assets/routers.py` | Import and catch `CannotUnassignWithOpenCheckoutError` | Add to unassign endpoint's try/catch |
| `app.py` | Register checkout router | `application.include_router(checkout_router)` |
| `adapters/http/api/my/routers.py` | Add equipment endpoints | `/my/equipment`, `/my/equipment/{id}/accept` |

### Data Migration

In the same Alembic migration:
1. Create `asset_checkouts` table
2. Remove `EMPLOYEE` system locations: update assets at that location to `location_id = NULL`
3. Seed GDPR sanitization maintenance template per existing company

### Breaking Changes

| Change | Impact | Mitigation |
|--------|--------|------------|
| `EMPLOYEE` location removal | Assets previously at "Empleado" lose that location | Migration sets `location_id = NULL`; frontend filters that used "Empleado" will return empty |
| Assign no longer auto-moves | Technicians accustomed to assign = location change | Clear in release notes; checkout is the new handover mechanism |

---

## Maintenance → IN_STOCK Automation

### Approach

Modify `CompleteMaintenanceCommandHandler` to check if the maintenance was created by a checkout (via `maintenance_id` link), and if so, transition the asset to `IN_STOCK`.

File to modify: `src/maintenance_bc/maintenance_record/application/commands/complete_maintenance.py`

Add:
1. New port: `AssetStatusUpdater` — allows maintenance BC to trigger asset status change
2. After `record.complete()`, check if record has a `source_checkout_id` tag
3. If yes, call `asset_status_updater.set_in_stock(asset_id, company_id)`

Alternative (simpler): Add a `source_type` field to `MaintenanceRecord` (e.g., `"checkout_gdpr"`). On completion, if `source_type == "checkout_gdpr"`, update asset status.

**Chosen approach:** Add `source_type: Optional[str]` to `MaintenanceRecord` + `CreateMaintenanceRecordCommand`. When checkin creates maintenance, pass `source_type="checkout_gdpr"`. On completion, if `source_type == "checkout_gdpr"`, use `AssetLookup` port (already exists) extended with a `set_status()` method.

---

## Frontend

### Asset Detail Page — Custody Tab

New tab in asset detail showing:
- Current checkout status (who has it, since when, accepted or pending)
- Checkout/Checkin/Cancel buttons for technicians
- Checkout history table (paginated)

### My Equipment Page

New page `/my/equipment`:
- Pending acceptance banner with "Confirm Receipt" button
- List of currently checked-out equipment with details

### Dashboard Widget

Add to existing dashboard:
- Open checkouts count
- Pending acceptances count

### Nav/Router Changes

| File | Change |
|------|--------|
| `web/app/src/router.tsx` | Add `/my/equipment` route |
| `web/app/src/components/layout/Sidebar.tsx` | Add "My Equipment" under employee section |
| `web/app/src/locales/en.ts` | Add checkout i18n keys |
| `web/app/src/locales/es.ts` | Add checkout i18n keys |

---

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | AssetCheckout entity methods | HIGH | `tests/unit/asset_bc/checkout/domain/test_entities.py` |
| Unit | CreateCheckoutCommandHandler | HIGH | `tests/unit/asset_bc/checkout/application/commands/test_create_checkout.py` |
| Unit | CheckinAssetCommandHandler | HIGH | `tests/unit/asset_bc/checkout/application/commands/test_checkin.py` |
| Unit | CancelCheckoutCommandHandler | HIGH | `tests/unit/asset_bc/checkout/application/commands/test_cancel.py` |
| Unit | AcceptCheckoutCommandHandler | HIGH | `tests/unit/asset_bc/checkout/application/commands/test_accept.py` |
| Unit | Modified assign/unassign | HIGH | Update existing tests |
| Integration | Checkout lifecycle endpoints | HIGH | `tests/integration/test_checkout_endpoints.py` |
| Integration | Global checkouts endpoint | MEDIUM | Same file |
| Integration | My equipment endpoint | MEDIUM | Same file |

---

## Implementation Order

1. Domain: enums, entities, exceptions, repository interface
2. Infrastructure: migration, model, repository
3. Application: commands (create, checkin, cancel, accept)
4. Application: queries (current, list, company-wide, my equipment)
5. Collateral: modify assign/unassign, company seeding
6. Maintenance automation: modify complete_maintenance + add source_type
7. HTTP: router, schemas, dependencies, register in app.py
8. Unit tests
9. Integration tests
10. Frontend: asset detail custody tab, my equipment page, dashboard widget, i18n
