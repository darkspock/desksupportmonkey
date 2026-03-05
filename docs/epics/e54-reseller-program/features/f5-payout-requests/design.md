# Solution Design: F5 — Payout Requests

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `reseller_bc`
**Subdomain:** `payout`

## Summary

F5 adds a manual payout request/approval workflow for resellers. A reseller requests a payout of their available commission balance; a super admin reviews, approves, and marks it as paid with a payment reference. The design creates a new `payout` subdomain under `reseller_bc`, following the exact same patterns established by F4's `commission` subdomain: flat dataclass entity, simple enum, abstract repository interface, SQLAlchemy model with `ULIDMixin`, command/query handlers in same-file pairs, DTOs as dataclasses, and explicit mappers in the HTTP layer.

## Architecture Decision

**Approach:** New `payout` subdomain within existing `reseller_bc`, mirroring F4's commission subdomain pattern.

**Why:**
- The payout entity belongs to the reseller bounded context (it's a reseller-owned financial record)
- Following the identical flat-dataclass pattern from F4 commission ensures consistency and reduces cognitive load
- The payout workflow is simple enough (4 states, 3 transitions) to not require domain events
- Cross-subdomain interaction is minimal: payout only reads from commission repo (available balance) and writes commission status to `PAID` when a payout completes

**Key design decisions:**
1. **One active payout guard** — prevent creating a new payout request while one is in `requested` or `approved` status. This simplifies balance calculation and prevents double-payout scenarios.
2. **`mark_as_paid()` method added to `ResellerCommission`** — backward-compatible domain method for the `CONFIRMED → PAID` transition, called by `ProcessPayoutCommandHandler` when marking a payout as paid.
3. **Batch commission update** — when marking a payout as paid, update all `CONFIRMED` commissions for that reseller to `PAID` in a single repository method, not in a loop.
4. **Admin payout routes at `/api/v1/admin/payouts`** — flat list (not nested under resellers) since admins need a global view of all pending payouts, with optional `?reseller_id=` filter.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `ResellerCommission` entity | `src/reseller_bc/commission/domain/entities.py` | Yes | Add `mark_as_paid()` method |
| `CommissionStatus` enum | `src/reseller_bc/commission/domain/enums.py` | Yes (has `PAID`) | None |
| Commission repo interface | `src/reseller_bc/commission/domain/repository.py` | Yes | Add `mark_confirmed_as_paid_for_reseller(reseller_id)` |
| Commission repo impl | `src/reseller_bc/commission/infrastructure/repository.py` | Yes | Add `mark_confirmed_as_paid_for_reseller(reseller_id)` impl |
| `GetAvailableBalanceQuery` | `src/reseller_bc/commission/application/queries/get_available_balance.py` | Yes — reused directly in payout handler | None |
| `Reseller` entity | `src/reseller_bc/reseller/domain/entities.py` | Yes (`min_payout_cents` field) | None |
| `require_active_reseller()` | `adapters/http/api/reseller/dependencies.py` | Yes | None |
| `require_role(UserRole.SUPER_ADMIN)` | `adapters/http/api/auth/dependencies.py` | Yes | None |
| Dashboard query handler | `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | Yes | Add optional `payout_repo` for pending payout sum |
| Dashboard DTO | `src/reseller_bc/reseller/application/dtos.py` | Yes (`pending_payout_cents` already exists) | None |
| Reseller schemas | `adapters/http/api/reseller/schemas.py` | Yes | Add payout schemas |
| Reseller mappers | `adapters/http/api/reseller/mappers.py` | Yes | Add `PayoutMapper` |
| Reseller router | `adapters/http/api/reseller/routers.py` | Yes | Add payout endpoints |
| Admin reseller router | `adapters/http/api/admin/reseller_routers.py` | Yes | Add admin payout endpoints |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| `ResellerPayout` | `src/reseller_bc/payout/domain/entities.py` | Payout request dataclass with `create()`, `approve()`, `reject()`, `mark_paid()` factory/transition methods |

**`ResellerPayout` entity definition:**

```python
@dataclass
class ResellerPayout:
    id: str
    reseller_id: str
    amount_cents: int
    status: PayoutStatus
    requested_at: Optional[datetime]
    processed_at: Optional[datetime]
    processed_by: Optional[str]       # super admin user ID
    payment_reference: Optional[str]
    notes: Optional[str]

    @classmethod
    def create(cls, reseller_id: str, amount_cents: int, id: Optional[str] = None) -> "ResellerPayout":
        if amount_cents <= 0:
            raise InvalidPayoutAmountException(amount_cents)
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            amount_cents=amount_cents,
            status=PayoutStatus.REQUESTED,
            requested_at=datetime.utcnow(),
            processed_at=None,
            processed_by=None,
            payment_reference=None,
            notes=None,
        )

    def approve(self, processed_by: str) -> None:
        if self.status != PayoutStatus.REQUESTED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.APPROVED.value)
        self.status = PayoutStatus.APPROVED
        self.processed_at = datetime.utcnow()
        self.processed_by = processed_by

    def reject(self, processed_by: str, notes: Optional[str] = None) -> None:
        if self.status != PayoutStatus.REQUESTED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.REJECTED.value)
        self.status = PayoutStatus.REJECTED
        self.processed_at = datetime.utcnow()
        self.processed_by = processed_by
        self.notes = notes

    def mark_paid(self, payment_reference: str) -> None:
        if self.status != PayoutStatus.APPROVED:
            raise InvalidPayoutTransitionException(self.status.value, PayoutStatus.PAID.value)
        self.status = PayoutStatus.PAID
        self.payment_reference = payment_reference
        self.processed_at = datetime.utcnow()
```

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| `PayoutStatus` | `src/reseller_bc/payout/domain/enums.py` | `requested`, `approved`, `paid`, `rejected` |

#### Exceptions

| Exception | File Path | When Raised |
|-----------|-----------|-------------|
| `InvalidPayoutAmountException` | `src/reseller_bc/payout/domain/exceptions.py` | `amount_cents <= 0` |
| `InvalidPayoutTransitionException` | `src/reseller_bc/payout/domain/exceptions.py` | Invalid state transition (e.g., `rejected → paid`) |
| `InsufficientBalanceException` | `src/reseller_bc/payout/domain/exceptions.py` | Balance < `min_payout_cents` |
| `PayoutAlreadyPendingException` | `src/reseller_bc/payout/domain/exceptions.py` | Already has a `requested`/`approved` payout |
| `PayoutNotFoundException` | `src/reseller_bc/payout/domain/exceptions.py` | Payout ID not found |

#### Repository Interface

| Interface | File Path | Methods |
|-----------|-----------|---------|
| `ResellerPayoutRepositoryInterface` | `src/reseller_bc/payout/domain/repository.py` | `save`, `find_by_id`, `find_by_reseller_id` (paginated), `count_by_reseller_id`, `find_active_by_reseller_id`, `find_all` (paginated, optional reseller_id filter), `count_all`, `sum_requested_and_approved_by_reseller_id` |

**Interface methods:**

```python
class ResellerPayoutRepositoryInterface(ABC):
    @abstractmethod
    def save(self, payout: ResellerPayout) -> None: ...

    @abstractmethod
    def find_by_id(self, payout_id: str) -> Optional[ResellerPayout]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerPayout]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_active_by_reseller_id(self, reseller_id: str) -> Optional[ResellerPayout]: ...
    # "Active" = status in (requested, approved)

    @abstractmethod
    def find_all(self, offset: int = 0, limit: int = 50, reseller_id: Optional[str] = None) -> list[ResellerPayout]: ...

    @abstractmethod
    def count_all(self, reseller_id: Optional[str] = None) -> int: ...

    @abstractmethod
    def sum_requested_and_approved_by_reseller_id(self, reseller_id: str) -> int: ...
```

### 2. Application Layer

#### DTOs

| DTO | File Path | Description |
|-----|-----------|-------------|
| `PayoutDto` | `src/reseller_bc/payout/application/dtos.py` | Single payout record |
| `PayoutListDto` | `src/reseller_bc/payout/application/dtos.py` | Paginated list with total |

```python
@dataclass
class PayoutDto:
    id: str
    reseller_id: str
    reseller_name: str          # denormalized for admin view
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

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `RequestPayoutCommand` | `RequestPayoutCommandHandler` | `src/reseller_bc/payout/application/commands/request_payout.py` | Creates payout with current available balance |
| `ProcessPayoutCommand` | `ProcessPayoutCommandHandler` | `src/reseller_bc/payout/application/commands/process_payout.py` | Approve/reject/mark-paid transitions |

**`RequestPayoutCommand` handler logic:**

1. Load reseller from repo → verify exists, is not suspended
2. Check no active payout exists (`find_active_by_reseller_id`) → raise `PayoutAlreadyPendingException` if found
3. Calculate available balance (reuse `GetAvailableBalanceQueryHandler` formula inline: `confirmed - paid + clawbacks`)
4. Compare balance against `reseller.min_payout_cents` → raise `InsufficientBalanceException` if below
5. Create `ResellerPayout.create(reseller_id, amount_cents)`
6. Save payout

```python
@dataclass
class RequestPayoutCommand(Command):
    id: str
    reseller_id: str

class RequestPayoutCommandHandler(CommandHandler[RequestPayoutCommand]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        commission_repo: ResellerCommissionRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        ...

    def handle(self, command: RequestPayoutCommand) -> None:
        reseller = self.reseller_repo.get_by_id(command.reseller_id)
        if reseller is None:
            raise ResellerNotFoundException(command.reseller_id)
        if reseller.status == ResellerStatus.SUSPENDED:
            raise ResellerSuspendedException(command.reseller_id)

        # Guard: one active payout at a time
        active = self.payout_repo.find_active_by_reseller_id(command.reseller_id)
        if active is not None:
            raise PayoutAlreadyPendingException(command.reseller_id)

        # Calculate available balance
        confirmed = self.commission_repo.sum_confirmed_by_reseller_id(command.reseller_id)
        paid = self.commission_repo.sum_paid_by_reseller_id(command.reseller_id)
        clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(command.reseller_id)
        balance = confirmed - paid + clawbacks

        if balance < reseller.min_payout_cents:
            raise InsufficientBalanceException(balance, reseller.min_payout_cents)

        payout = ResellerPayout.create(
            reseller_id=command.reseller_id,
            amount_cents=balance,
            id=command.id,
        )
        self.payout_repo.save(payout)
```

**`ProcessPayoutCommand` handler logic:**

```python
@dataclass
class ProcessPayoutCommand(Command):
    payout_id: str
    action: str               # "approve" | "reject" | "mark_paid"
    processed_by: str         # super admin user ID
    payment_reference: Optional[str] = None
    notes: Optional[str] = None

class ProcessPayoutCommandHandler(CommandHandler[ProcessPayoutCommand]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        commission_repo: ResellerCommissionRepositoryInterface,
    ):
        ...

    def handle(self, command: ProcessPayoutCommand) -> None:
        payout = self.payout_repo.find_by_id(command.payout_id)
        if payout is None:
            raise PayoutNotFoundException(command.payout_id)

        if command.action == "approve":
            payout.approve(processed_by=command.processed_by)
        elif command.action == "reject":
            payout.reject(processed_by=command.processed_by, notes=command.notes)
        elif command.action == "mark_paid":
            if not command.payment_reference:
                raise ValueError("payment_reference is required for mark_paid")
            payout.mark_paid(payment_reference=command.payment_reference)
            # Transition confirmed commissions to paid
            self.commission_repo.mark_confirmed_as_paid_for_reseller(payout.reseller_id)
        else:
            raise ValueError(f"Unknown action: {command.action}")

        self.payout_repo.save(payout)
```

#### Queries

| Query | Handler | File Path | Description |
|-------|---------|-----------|-------------|
| `ListPayoutsQuery` | `ListPayoutsQueryHandler` | `src/reseller_bc/payout/application/queries/list_payouts.py` | Paginated payout list (reseller or admin scope) |

```python
@dataclass
class ListPayoutsQuery(Query):
    reseller_id: Optional[str] = None  # None = all (admin)
    offset: int = 0
    limit: int = 50

class ListPayoutsQueryHandler(QueryHandler[ListPayoutsQuery, PayoutListDto]):
    def __init__(
        self,
        payout_repo: ResellerPayoutRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        ...

    def handle(self, query: ListPayoutsQuery) -> PayoutListDto:
        if query.reseller_id:
            payouts = self.payout_repo.find_by_reseller_id(
                query.reseller_id, query.offset, query.limit
            )
            total = self.payout_repo.count_by_reseller_id(query.reseller_id)
        else:
            payouts = self.payout_repo.find_all(query.offset, query.limit)
            total = self.payout_repo.count_all()

        # Batch-load reseller names
        reseller_ids = list({p.reseller_id for p in payouts})
        resellers = {}
        for rid in reseller_ids:
            r = self.reseller_repo.get_by_id(rid)
            if r:
                resellers[rid] = r

        items = [
            PayoutDto(
                id=p.id,
                reseller_id=p.reseller_id,
                reseller_name=resellers[p.reseller_id].name if p.reseller_id in resellers else "Unknown",
                amount_cents=p.amount_cents,
                status=p.status.value,
                requested_at=p.requested_at,
                processed_at=p.processed_at,
                processed_by=p.processed_by,
                payment_reference=p.payment_reference,
                notes=p.notes,
            )
            for p in payouts
        ]
        return PayoutListDto(items=items, total=total)
```

### 3. Infrastructure Layer

#### Repository

| Interface | Implementation | Table |
|-----------|----------------|-------|
| `ResellerPayoutRepositoryInterface` | `ResellerPayoutRepository` | `reseller_payouts` |

**File paths:**
- Interface: `src/reseller_bc/payout/domain/repository.py`
- Implementation: `src/reseller_bc/payout/infrastructure/repository.py`
- Model: `src/reseller_bc/payout/infrastructure/models.py`

**`ResellerPayoutModel`:**

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

**Repository `find_active_by_reseller_id` implementation:**

```python
def find_active_by_reseller_id(self, reseller_id: str) -> Optional[ResellerPayout]:
    model = self.session.execute(
        select(ResellerPayoutModel)
        .where(
            ResellerPayoutModel.reseller_id == reseller_id,
            ResellerPayoutModel.status.in_([
                PayoutStatus.REQUESTED.value,
                PayoutStatus.APPROVED.value,
            ]),
        )
        .limit(1)
    ).scalar_one_or_none()
    return self._to_entity(model) if model else None
```

#### Migrations

| Migration | Description |
|-----------|-------------|
| `e9f0g1h2i3j4_add_reseller_payouts_table.py` | Create `reseller_payouts` table with indexes on `reseller_id` and `status`. `down_revision = "d8e9f0g1h2i3"` |

### 4. HTTP Layer

#### Schemas (add to `adapters/http/api/reseller/schemas.py`)

```python
# Payout schemas
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

#### Mapper (add to `adapters/http/api/reseller/mappers.py`)

```python
class PayoutMapper:
    @staticmethod
    def dto_to_response(dto: PayoutDto) -> PayoutResponse:
        return PayoutResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            reseller_name=dto.reseller_name,
            amount_cents=dto.amount_cents,
            status=dto.status,
            requested_at=dto.requested_at.isoformat() if dto.requested_at else None,
            processed_at=dto.processed_at.isoformat() if dto.processed_at else None,
            processed_by=dto.processed_by,
            payment_reference=dto.payment_reference,
            notes=dto.notes,
        )

    @staticmethod
    def dto_to_list_response(dto: PayoutListDto) -> PayoutListResponse:
        return PayoutListResponse(
            items=[PayoutMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )
```

#### Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| `POST` | `/api/v1/reseller/payouts` | `require_active_reseller()` | Request a payout (amount = available balance) |
| `GET` | `/api/v1/reseller/payouts` | `get_current_reseller` | List reseller's payout history |
| `GET` | `/api/v1/admin/payouts` | `require_role(SUPER_ADMIN)` | List all payout requests (optional `?reseller_id=` filter) |
| `PATCH` | `/api/v1/admin/payouts/{payout_id}` | `require_role(SUPER_ADMIN)` | Approve / reject / mark as paid |

**Reseller endpoints** (add to `adapters/http/api/reseller/routers.py`):

```python
@router.post("/payouts", status_code=201)
def request_payout(
    reseller: Reseller = Depends(require_active_reseller()),
    db: Session = Depends(get_db),
):
    ...
    handler = RequestPayoutCommandHandler(payout_repo, commission_repo, reseller_repo)
    payout_id = str(ulid.new())
    try:
        handler.handle(RequestPayoutCommand(id=payout_id, reseller_id=reseller.id))
    except InsufficientBalanceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PayoutAlreadyPendingException as e:
        raise HTTPException(status_code=409, detail=str(e))
    ...

@router.get("/payouts")
def list_payouts(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db),
):
    ...
```

**Admin endpoints** (add to `adapters/http/api/admin/reseller_routers.py` or create separate `payout_routers.py`):

Given the requirement specifies `/admin/payouts` (not nested under resellers), add a new router file `adapters/http/api/admin/payout_routers.py`:

```python
router = APIRouter(prefix="/api/v1/admin/payouts", tags=["admin-payouts"])

@router.get("/")
def list_all_payouts(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller_id: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ...

@router.patch("/{payout_id}")
def process_payout(
    payout_id: str,
    body: ProcessPayoutRequest,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    ...
    handler = ProcessPayoutCommandHandler(payout_repo, commission_repo)
    try:
        handler.handle(ProcessPayoutCommand(
            payout_id=payout_id,
            action=body.action,
            processed_by=current_user.id,
            payment_reference=body.payment_reference,
            notes=body.notes,
        ))
    except PayoutNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidPayoutTransitionException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    ...
```

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/reseller_bc/commission/domain/entities.py` | Add method | Add `mark_as_paid()` → sets `status = PAID` |
| `src/reseller_bc/commission/domain/repository.py` | Add method | Add `mark_confirmed_as_paid_for_reseller(reseller_id: str) -> int` |
| `src/reseller_bc/commission/infrastructure/repository.py` | Add method | Implement `mark_confirmed_as_paid_for_reseller()` — batch UPDATE |
| `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | Modify | Accept optional `payout_repo`, compute `pending_payout_cents` from `sum_requested_and_approved_by_reseller_id` |
| `adapters/http/api/reseller/routers.py` | Add endpoints | `POST /reseller/payouts`, `GET /reseller/payouts` + update dashboard to pass payout_repo |
| `adapters/http/api/reseller/schemas.py` | Add schemas | `PayoutResponse`, `PayoutListResponse`, `ProcessPayoutRequest` |
| `adapters/http/api/reseller/mappers.py` | Add mapper | `PayoutMapper` class |
| `core/main.py` | Add router | Include `payout_routers.router` |
| `tests/conftest.py` | Add import | Import `ResellerPayoutModel` for table creation |
| `web/app/src/router.tsx` | Add route | `{ path: 'payouts', element: <S><PayoutsPage /></S> }` |
| `web/app/src/components/layout/ResellerLayout.tsx` | Add nav item | "Payouts" nav link |
| `web/app/src/locales/en.ts` | Add keys | Payout i18n keys |
| `web/app/src/locales/es.ts` | Add keys | Payout i18n keys (Spanish) |

#### Breaking Changes

None. All changes are additive.

### 6. Frontend

#### New Pages

| Page | File Path | Description |
|------|-----------|-------------|
| `PayoutsPage` | `web/app/src/pages/reseller/PayoutsPage.tsx` | Payout history table + "Request Payout" button (disabled when balance < threshold). Shows: amount, status badge, requested date, payment reference, notes. |
| `PayoutManagementPage` | `web/app/src/pages/admin/resellers/PayoutManagementPage.tsx` | **Not needed as separate page** — integrate payout management into the existing super admin `ResellersPage` or add it as a section. Given the scope, a simpler approach: add a "Payouts" tab/section in the existing super admin reseller detail page. If the super admin UI is too small for F5, create a standalone page. |

**Simpler approach for admin UI:** Add payout list + action buttons directly into the existing `ResellersPage` as a tab, or create a minimal `PayoutManagementPage` following the same `CommissionsPage` pattern (table + action buttons for approve/reject/mark-paid).

#### Frontend components for PayoutsPage:

- Available balance display + "Request Payout" button
- Payout history table: amount, status badge (yellow=requested, blue=approved, green=paid, red=rejected), dates, payment reference
- Status badges follow same pattern as `CommissionsPage` (`statusConfig` map → className)

## Database Schema

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

## State Machine

```
                ┌──────────┐
                │ requested│
                └────┬─────┘
               ┌─────┴─────┐
               ▼            ▼
          ┌────────┐   ┌─────────┐
          │approved│   │ rejected│  (terminal)
          └────┬───┘   └─────────┘
               ▼
          ┌────────┐
          │  paid  │  (terminal — commissions marked as paid)
          └────────┘
```

**Transitions:**
- `requested → approved` — super admin approves
- `requested → rejected` — super admin rejects (reseller can immediately create a new request)
- `approved → paid` — super admin records payment reference + commissions bulk-updated to `PAID`

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F4 Commission Tracking | Required (Done) | Available balance calculation, commission status transitions |
| F1 Reseller Entity | Required (Done) | `min_payout_cents` field, reseller repo |
| Alembic migration chain | Required | `down_revision = "d8e9f0g1h2i3"` (F4's migration) |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | `ResellerPayout` entity (create, transitions, guards) | High | `tests/unit/reseller_bc/payout/domain/test_payout_entity.py` |
| Unit | `RequestPayoutCommandHandler` (happy path, insufficient balance, already pending, suspended) | High | `tests/unit/reseller_bc/payout/application/test_request_payout.py` |
| Unit | `ProcessPayoutCommandHandler` (approve, reject, mark_paid, not found, invalid transition) | High | `tests/unit/reseller_bc/payout/application/test_process_payout.py` |
| Unit | `ListPayoutsQueryHandler` | Medium | `tests/unit/reseller_bc/payout/application/test_list_payouts.py` |
| Integration | Reseller payout endpoints (request, list, admin process) | High | `tests/integration/test_reseller_payout_endpoints.py` |

## Implementation Order

1. [ ] Domain: `PayoutStatus` enum
2. [ ] Domain: Payout exceptions
3. [ ] Domain: `ResellerPayout` entity
4. [ ] Domain: `ResellerPayoutRepositoryInterface`
5. [ ] Infrastructure: `ResellerPayoutModel`
6. [ ] Infrastructure: Alembic migration
7. [ ] Infrastructure: `ResellerPayoutRepository`
8. [ ] Collateral: Add `mark_as_paid()` to `ResellerCommission` entity
9. [ ] Collateral: Add `mark_confirmed_as_paid_for_reseller()` to commission repo interface + impl
10. [ ] Application: `PayoutDto` / `PayoutListDto`
11. [ ] Application: `RequestPayoutCommand` + Handler
12. [ ] Application: `ProcessPayoutCommand` + Handler
13. [ ] Application: `ListPayoutsQuery` + Handler
14. [ ] Collateral: Update dashboard query handler (pending payout sum)
15. [ ] HTTP: Payout schemas + mapper
16. [ ] HTTP: Reseller payout endpoints
17. [ ] HTTP: Admin payout endpoints + router registration
18. [ ] Tests: Unit tests (entity, commands, queries)
19. [ ] Tests: Integration tests (endpoints)
20. [ ] Frontend: `PayoutsPage.tsx` + route + nav + i18n
21. [ ] Frontend: Admin payout management page + route + i18n
22. [ ] Configuration: Register payout model in `conftest.py`

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Race condition on concurrent payout requests | Low | Medium | `find_active_by_reseller_id` check + database-level constraint would be ideal, but the single-active-payout guard in the handler is sufficient given manual admin workflow |
| Commission status sync on mark_paid | Low | High | Batch UPDATE in single transaction; if it fails, payout status is also rolled back |
| Dashboard performance with payout repo | Low | Low | Single COUNT query via `sum_requested_and_approved_by_reseller_id`; negligible overhead |
