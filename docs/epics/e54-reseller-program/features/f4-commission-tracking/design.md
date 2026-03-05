# Solution Design: F4 — Commission Tracking

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `reseller_bc` (new subdomain: `commission`)

## Summary

Commission tracking creates a new `commission` subdomain within `reseller_bc` that automatically generates commission records when reseller-attributed companies make Stripe payments. The feature hooks into the existing `StripeWebhookDispatcher` (in `company_bc`) by extending the `invoice.payment_succeeded` handler and adding a new `charge.refunded` handler. A daily Celery beat task transitions commissions from `pending` → `confirmed` after 30 days. The dashboard query is updated to return real financial data, and new reseller/admin API endpoints expose commission lists and balance calculation.

## Architecture Decision

**Approach: Extend dispatcher + separate reseller_bc commands**

The `StripeWebhookDispatcher` in `company_bc` is the single entry point for Stripe events. Rather than creating a separate webhook endpoint or listener in `reseller_bc`, we extend the dispatcher to call `reseller_bc` commands after its existing billing handlers. This keeps webhook idempotency centralized.

**Key decisions:**
1. **Commission creation in `reseller_bc`, triggered from `company_bc`** — The dispatcher calls a reseller_bc command handler directly (cross-BC call). This follows the existing pattern where the dispatcher already instantiates handlers from `company_bc.application.commands`.
2. **Dispatcher receives extra repos** — The dispatcher's constructor gains optional `ResellerClientRepository` and `ResellerCommissionRepository` parameters (backward-compatible: default `None`). The billing router passes them from dependencies.
3. **No domain events** — The dispatcher calls commission commands synchronously (not via event bus). This avoids introducing event infrastructure just for this feature, consistent with how the dispatcher already works.
4. **Commission entity owns calculation** — `ResellerCommission.create()` factory calculates `commission_amount_cents = payment_amount_cents * commission_pct // 100` (integer division, rounds down).

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `StripeWebhookDispatcher` | `src/company_bc/company/application/services/stripe_webhook_dispatcher.py` | Yes — extend | Add commission hooks to `invoice.payment_succeeded` and new `charge.refunded` block |
| `ResellerClientRepository` | `src/reseller_bc/client/infrastructure/repository.py` | Yes — as-is | `find_by_company_id()` already exists |
| `Reseller.commission_pct` | `src/reseller_bc/reseller/domain/entities.py` | Yes — read only | No changes needed |
| `ResellerRepository` | `src/reseller_bc/reseller/infrastructure/repository.py` | Yes — as-is | `get_by_id()` already exists |
| `ResellerDashboardDto` | `src/reseller_bc/reseller/application/dtos.py` | Yes — as-is | Already has `total_commissions_cents`, `available_balance_cents`, `pending_payout_cents` (currently hardcoded to 0) |
| `GetResellerDashboardQueryHandler` | `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | Yes — modify | Replace hardcoded 0s with real commission data |
| Celery beat config | `core/celery.py` | Yes — extend | Add `confirm-commissions` schedule |
| Celery task pattern | `core/tasks/reseller.py` | Pattern reference | Follow same `SessionLocal` + try/except/finally pattern |
| Billing webhook router | `adapters/http/api/billing/routers.py` | Yes — modify | Pass reseller repos to dispatcher |
| Reseller router | `adapters/http/api/reseller/routers.py` | Yes — extend | Add `GET /reseller/commissions` endpoint |
| Admin reseller router | `adapters/http/api/admin/reseller_routers.py` | Yes — extend | Add `GET /admin/resellers/{id}/commissions` endpoint |
| Reseller schemas | `adapters/http/api/reseller/schemas.py` | Yes — extend | Add commission response schemas |
| Reseller mappers | `adapters/http/api/reseller/mappers.py` | Yes — extend | Add commission mapper |
| Dashboard frontend | `web/app/src/pages/reseller/ResellerDashboardPage.tsx` | Yes — as-is | Already displays `total_commissions_cents`, `available_balance_cents` from API |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| `ResellerCommission` | `src/reseller_bc/commission/domain/entities.py` | Commission record per client payment |

**`ResellerCommission` entity:**

```python
@dataclass
class ResellerCommission:
    id: str
    reseller_id: str
    reseller_client_id: str
    company_id: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    stripe_invoice_id: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    status: CommissionStatus
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        reseller_id: str,
        reseller_client_id: str,
        company_id: str,
        payment_amount_cents: int,
        commission_pct: int,
        stripe_invoice_id: str,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        id: Optional[str] = None,
    ) -> "ResellerCommission":
        commission_amount = payment_amount_cents * commission_pct // 100
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            reseller_client_id=reseller_client_id,
            company_id=company_id,
            payment_amount_cents=payment_amount_cents,
            commission_pct=commission_pct,
            commission_amount_cents=commission_amount,
            stripe_invoice_id=stripe_invoice_id,
            period_start=period_start,
            period_end=period_end,
            status=CommissionStatus.PENDING,
            created_at=datetime.utcnow(),
        )

    @classmethod
    def create_clawback(
        cls,
        original: "ResellerCommission",
        id: Optional[str] = None,
    ) -> "ResellerCommission":
        """Create negative commission for paid-then-refunded scenario."""
        return cls(
            id=id or str(ulid.new()),
            reseller_id=original.reseller_id,
            reseller_client_id=original.reseller_client_id,
            company_id=original.company_id,
            payment_amount_cents=-original.payment_amount_cents,
            commission_pct=original.commission_pct,
            commission_amount_cents=-original.commission_amount_cents,
            stripe_invoice_id=original.stripe_invoice_id,
            period_start=original.period_start,
            period_end=original.period_end,
            status=CommissionStatus.CLAWED_BACK,
            created_at=datetime.utcnow(),
        )

    def confirm(self) -> None:
        self.status = CommissionStatus.CONFIRMED

    def clawback(self) -> None:
        self.status = CommissionStatus.CLAWED_BACK
```

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| `CommissionStatus` | `src/reseller_bc/commission/domain/enums.py` | `PENDING`, `CONFIRMED`, `PAID`, `CLAWED_BACK` |

```python
class CommissionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CLAWED_BACK = "clawed_back"
```

#### Repository Interface

| Interface | File Path |
|-----------|-----------|
| `ResellerCommissionRepositoryInterface` | `src/reseller_bc/commission/domain/repository.py` |

```python
class ResellerCommissionRepositoryInterface(ABC):
    @abstractmethod
    def save(self, commission: ResellerCommission) -> None: ...

    @abstractmethod
    def find_by_stripe_invoice_id(self, stripe_invoice_id: str) -> Optional[ResellerCommission]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerCommission]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_pending_before(self, before: datetime) -> list[ResellerCommission]: ...

    @abstractmethod
    def sum_confirmed_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_clawbacks_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_paid_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def sum_all_commissions_by_reseller_id(self, reseller_id: str) -> int: ...
```

### 2. Infrastructure Layer

#### Model

| Model | File Path | Table |
|-------|-----------|-------|
| `ResellerCommissionModel` | `src/reseller_bc/commission/infrastructure/models.py` | `reseller_commissions` |

```python
class ResellerCommissionModel(ULIDMixin, Base):
    __tablename__ = "reseller_commissions"

    reseller_id: Mapped[str] = mapped_column(String(26), ForeignKey("resellers.id"), nullable=False, index=True)
    reseller_client_id: Mapped[str] = mapped_column(String(26), ForeignKey("reseller_clients.id"), nullable=False)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    payment_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    commission_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    commission_amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    stripe_invoice_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
```

**Note:** `stripe_invoice_id` is indexed but NOT unique — clawback records reuse the same invoice ID.

#### Repository Implementation

| Interface | Implementation | Table |
|-----------|----------------|-------|
| `ResellerCommissionRepositoryInterface` | `ResellerCommissionRepository` | `reseller_commissions` |

**File:** `src/reseller_bc/commission/infrastructure/repository.py`

Follows the same pattern as `ResellerClientRepository`:
- `save()` — upsert by ID
- `find_by_stripe_invoice_id()` — lookup for idempotency and clawback matching
- `find_by_reseller_id()` — paginated list ordered by `created_at desc`
- `count_by_reseller_id()` — total count
- `find_pending_before()` — for Celery confirmation task
- `sum_confirmed_by_reseller_id()` — SUM of `commission_amount_cents` WHERE `status = confirmed`
- `sum_clawbacks_by_reseller_id()` — SUM of `commission_amount_cents` WHERE `status = clawed_back` (negative values)
- `sum_paid_by_reseller_id()` — SUM of `commission_amount_cents` WHERE `status = paid`
- `sum_all_commissions_by_reseller_id()` — SUM for total earned (all statuses except clawed_back negative records)

#### Migration

| Migration | Description |
|-----------|-------------|
| `XXXX_add_reseller_commissions_table.py` | Create `reseller_commissions` table |

### 3. Application Layer

#### Commands

| Command | Handler | File | Description |
|---------|---------|------|-------------|
| `CreateCommissionCommand` | `CreateCommissionCommandHandler` | `src/reseller_bc/commission/application/commands/create_commission.py` | Creates commission from payment event |
| `ClawbackCommissionCommand` | `ClawbackCommissionCommandHandler` | `src/reseller_bc/commission/application/commands/clawback_commission.py` | Handles refund clawback |

**`CreateCommissionCommand`:**

```python
@dataclass
class CreateCommissionCommand(Command):
    stripe_invoice_id: str
    company_id: str
    payment_amount_cents: int
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

class CreateCommissionCommandHandler(CommandHandler[CreateCommissionCommand]):
    def __init__(
        self,
        commission_repo: ResellerCommissionRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
        reseller_repo: ResellerRepositoryInterface,
    ):
        ...

    def handle(self, command: CreateCommissionCommand) -> None:
        # 1. Find ResellerClient by company_id
        client = self.client_repo.find_by_company_id(command.company_id)
        if client is None:
            return  # Not a reseller client — skip

        # 2. Skip demo accounts
        if client.is_demo:
            return

        # 3. Idempotency: check if commission already exists for this invoice
        existing = self.commission_repo.find_by_stripe_invoice_id(command.stripe_invoice_id)
        if existing is not None:
            return  # Already processed

        # 4. Get reseller for commission_pct
        reseller = self.reseller_repo.get_by_id(client.reseller_id)
        if reseller is None:
            return  # Orphaned client — skip

        # 5. Create commission
        commission = ResellerCommission.create(
            reseller_id=reseller.id,
            reseller_client_id=client.id,
            company_id=command.company_id,
            payment_amount_cents=command.payment_amount_cents,
            commission_pct=reseller.commission_pct,
            stripe_invoice_id=command.stripe_invoice_id,
            period_start=command.period_start,
            period_end=command.period_end,
        )
        self.commission_repo.save(commission)
```

**`ClawbackCommissionCommand`:**

```python
@dataclass
class ClawbackCommissionCommand(Command):
    stripe_invoice_id: str

class ClawbackCommissionCommandHandler(CommandHandler[ClawbackCommissionCommand]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        ...

    def handle(self, command: ClawbackCommissionCommand) -> None:
        # 1. Find commission by stripe_invoice_id
        commission = self.commission_repo.find_by_stripe_invoice_id(command.stripe_invoice_id)
        if commission is None:
            return  # No commission for this invoice — skip

        # 2. If already clawed back, skip
        if commission.status == CommissionStatus.CLAWED_BACK:
            return

        # 3. If already paid, create negative record
        if commission.status == CommissionStatus.PAID:
            negative = ResellerCommission.create_clawback(commission)
            self.commission_repo.save(negative)

        # 4. Mark original as clawed_back
        commission.clawback()
        self.commission_repo.save(commission)
```

#### Queries

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| `ListCommissionsQuery` | `ListCommissionsQueryHandler` | `src/reseller_bc/commission/application/queries/list_commissions.py` | Paginated commission list for a reseller |
| `GetAvailableBalanceQuery` | `GetAvailableBalanceQueryHandler` | `src/reseller_bc/commission/application/queries/get_available_balance.py` | Calculate available balance |

**`ListCommissionsQuery`:**

```python
@dataclass
class ListCommissionsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50

class ListCommissionsQueryHandler(QueryHandler[ListCommissionsQuery, CommissionListDto]):
    def __init__(
        self,
        commission_repo: ResellerCommissionRepositoryInterface,
        client_repo: ResellerClientRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
    ):
        ...

    def handle(self, query: ListCommissionsQuery) -> CommissionListDto:
        commissions = self.commission_repo.find_by_reseller_id(
            query.reseller_id, query.offset, query.limit
        )
        total = self.commission_repo.count_by_reseller_id(query.reseller_id)

        # Batch-load company names to avoid N+1
        company_ids = list({c.company_id for c in commissions})
        companies = {c.id: c for c in self.company_repo.find_by_ids(company_ids)} if company_ids else {}

        items = []
        for c in commissions:
            company = companies.get(c.company_id)
            items.append(CommissionDto(
                id=c.id,
                reseller_id=c.reseller_id,
                company_id=c.company_id,
                company_name=company.name if company else "Unknown",
                payment_amount_cents=c.payment_amount_cents,
                commission_pct=c.commission_pct,
                commission_amount_cents=c.commission_amount_cents,
                stripe_invoice_id=c.stripe_invoice_id,
                period_start=c.period_start,
                period_end=c.period_end,
                status=c.status.value,
                created_at=c.created_at,
            ))
        return CommissionListDto(items=items, total=total)
```

**`GetAvailableBalanceQuery`:**

```python
@dataclass
class GetAvailableBalanceQuery(Query):
    reseller_id: str

class GetAvailableBalanceQueryHandler(QueryHandler[GetAvailableBalanceQuery, int]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        ...

    def handle(self, query: GetAvailableBalanceQuery) -> int:
        confirmed = self.commission_repo.sum_confirmed_by_reseller_id(query.reseller_id)
        paid = self.commission_repo.sum_paid_by_reseller_id(query.reseller_id)
        clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(query.reseller_id)
        return confirmed - paid + clawbacks  # clawbacks are negative, so adding reduces balance
```

#### DTOs

| DTO | File Path |
|-----|-----------|
| `CommissionDto` | `src/reseller_bc/commission/application/dtos.py` |
| `CommissionListDto` | `src/reseller_bc/commission/application/dtos.py` |

```python
@dataclass
class CommissionDto:
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    stripe_invoice_id: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    status: str
    created_at: Optional[datetime]

@dataclass
class CommissionListDto:
    items: list[CommissionDto]
    total: int
```

#### Celery Task

| Task | File Path | Schedule |
|------|-----------|----------|
| `confirm_commissions` | `core/tasks/commission.py` | Daily at 04:00 UTC |

```python
@celery_app.task(name="core.tasks.commission.confirm_commissions")
def confirm_commissions() -> dict:
    """Transition pending commissions to confirmed after 30 days."""
    from core.database import SessionLocal
    from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository

    session = SessionLocal()
    try:
        repo = ResellerCommissionRepository(session)
        cutoff = datetime.utcnow() - timedelta(days=30)
        pending = repo.find_pending_before(before=cutoff)
        confirmed_count = 0
        for commission in pending:
            commission.confirm()
            repo.save(commission)
            confirmed_count += 1
        session.commit()
        logger.info("Commission confirmation: confirmed=%d", confirmed_count)
        return {"confirmed": confirmed_count}
    except Exception as e:
        session.rollback()
        logger.error("Commission confirmation failed: %s", str(e))
        raise
    finally:
        session.close()
```

### 4. HTTP Layer

#### Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/api/v1/reseller/commissions` | Reseller JWT | Paginated commission list |
| GET | `/api/v1/admin/resellers/{reseller_id}/commissions` | SUPER_ADMIN | Commissions for a specific reseller |

**New schemas (in `adapters/http/api/reseller/schemas.py`):**

```python
class CommissionResponse(BaseModel):
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    period_start: Optional[str]
    period_end: Optional[str]
    status: str
    created_at: Optional[str]

class CommissionListResponse(BaseModel):
    items: list[CommissionResponse]
    total: int
```

**New mapper methods (in `adapters/http/api/reseller/mappers.py`):**

```python
class CommissionMapper:
    @staticmethod
    def dto_to_response(dto: CommissionDto) -> CommissionResponse:
        return CommissionResponse(
            id=dto.id,
            reseller_id=dto.reseller_id,
            company_id=dto.company_id,
            company_name=dto.company_name,
            payment_amount_cents=dto.payment_amount_cents,
            commission_pct=dto.commission_pct,
            commission_amount_cents=dto.commission_amount_cents,
            period_start=dto.period_start.isoformat() if dto.period_start else None,
            period_end=dto.period_end.isoformat() if dto.period_end else None,
            status=dto.status,
            created_at=dto.created_at.isoformat() if dto.created_at else None,
        )

    @staticmethod
    def dto_to_list_response(dto: CommissionListDto) -> CommissionListResponse:
        return CommissionListResponse(
            items=[CommissionMapper.dto_to_response(item) for item in dto.items],
            total=dto.total,
        )
```

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/company_bc/company/application/services/stripe_webhook_dispatcher.py` | **Extend** | Add optional reseller repos to constructor; add commission creation in `invoice.payment_succeeded` block; add `charge.refunded` handler |
| `adapters/http/api/billing/routers.py` | **Extend** | Pass `ResellerClientRepository` and `ResellerCommissionRepository` to `StripeWebhookDispatcher` constructor |
| `adapters/http/api/billing/dependencies.py` | **Extend** | Add `get_reseller_client_repo()` and `get_commission_repo()` dependency functions |
| `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | **Modify** | Accept `ResellerCommissionRepository`, replace hardcoded 0s with real balance data |
| `adapters/http/api/reseller/routers.py` | **Extend** | Add `GET /reseller/commissions` endpoint; update dashboard endpoint to pass commission repo |
| `adapters/http/api/admin/reseller_routers.py` | **Extend** | Add `GET /admin/resellers/{reseller_id}/commissions` endpoint |
| `adapters/http/api/reseller/schemas.py` | **Extend** | Add `CommissionResponse`, `CommissionListResponse` schemas |
| `adapters/http/api/reseller/mappers.py` | **Extend** | Add `CommissionMapper` class |
| `core/celery.py` | **Extend** | Add `confirm-commissions` to `beat_schedule` |
| `core/tasks/commission.py` | **New** | Celery task for commission confirmation |
| `web/app/src/pages/reseller/CommissionsPage.tsx` | **New** | Commission list page |
| `web/app/src/router.tsx` | **Extend** | Add `/reseller/commissions` route |
| `web/app/src/locales/en.ts` | **Extend** | Add commission-related i18n keys |
| `web/app/src/locales/es.ts` | **Extend** | Add commission-related i18n keys |

**Note:** `CompanyRepository.find_by_ids()` may need to be added if it doesn't exist. Check existing `find_by_id()` and add batch method.

#### Breaking Changes

None. All changes are additive:
- Dispatcher constructor gains optional params (backward-compatible)
- Dashboard DTO fields already exist (values change from 0 to real data)
- New API endpoints don't conflict with existing routes

### 6. Stripe Webhook Dispatcher Changes

**Critical integration point.** The dispatcher changes are:

```python
class StripeWebhookDispatcher:
    def __init__(
        self,
        company_repo: CompanyRepositoryInterface,
        client_repo: Optional[ResellerClientRepositoryInterface] = None,
        commission_repo: Optional[ResellerCommissionRepositoryInterface] = None,
        reseller_repo: Optional[ResellerRepositoryInterface] = None,
    ) -> None:
        self.company_repo = company_repo
        self.client_repo = client_repo
        self.commission_repo = commission_repo
        self.reseller_repo = reseller_repo
```

In `_route()`, after the existing `invoice.payment_succeeded` handler:

```python
elif event_type == "invoice.payment_succeeded":
    # Existing: restore billing
    RestoreBillingCommandHandler(self.company_repo).handle(
        RestoreBillingCommand(stripe_customer_id=obj["customer"])
    )
    # NEW: create commission if applicable
    if self.client_repo and self.commission_repo and self.reseller_repo:
        company = self.company_repo.find_by_stripe_customer_id(obj["customer"])
        if company:
            try:
                CreateCommissionCommandHandler(
                    commission_repo=self.commission_repo,
                    client_repo=self.client_repo,
                    reseller_repo=self.reseller_repo,
                ).handle(CreateCommissionCommand(
                    stripe_invoice_id=obj["id"],
                    company_id=company.id,
                    payment_amount_cents=obj["amount_paid"],
                    period_start=_unix_to_datetime(obj["period_start"]) if obj.get("period_start") else None,
                    period_end=_unix_to_datetime(obj["period_end"]) if obj.get("period_end") else None,
                ))
            except Exception:
                logger.warning("Commission creation failed for invoice=%s", obj["id"], exc_info=True)
```

New `charge.refunded` block:

```python
elif event_type == "charge.refunded":
    if self.commission_repo:
        invoice_id = obj.get("invoice")
        if invoice_id:
            try:
                ClawbackCommissionCommandHandler(
                    commission_repo=self.commission_repo,
                ).handle(ClawbackCommissionCommand(
                    stripe_invoice_id=invoice_id,
                ))
            except Exception:
                logger.warning("Commission clawback failed for charge=%s", obj.get("id"), exc_info=True)
```

## Database Schema

```sql
CREATE TABLE reseller_commissions (
    id              VARCHAR(26)     PRIMARY KEY,
    reseller_id     VARCHAR(26)     NOT NULL REFERENCES resellers(id),
    reseller_client_id VARCHAR(26)  NOT NULL REFERENCES reseller_clients(id),
    company_id      VARCHAR(26)     NOT NULL REFERENCES companies(id),
    payment_amount_cents INTEGER    NOT NULL,
    commission_pct  INTEGER         NOT NULL,
    commission_amount_cents INTEGER NOT NULL,
    stripe_invoice_id VARCHAR(255)  NOT NULL,
    period_start    TIMESTAMP       NULL,
    period_end      TIMESTAMP       NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending',
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_reseller_commissions_reseller_id ON reseller_commissions(reseller_id);
CREATE INDEX ix_reseller_commissions_company_id ON reseller_commissions(company_id);
CREATE INDEX ix_reseller_commissions_stripe_invoice_id ON reseller_commissions(stripe_invoice_id);
CREATE INDEX ix_reseller_commissions_status ON reseller_commissions(status);
```

## State Machine

```
                 ┌─────────────┐
                 │   PENDING   │ ← created on invoice.payment_succeeded
                 └──────┬──────┘
                        │
              30 days (Celery beat)
                        │
                 ┌──────▼──────┐
                 │  CONFIRMED  │ ← available for payout
                 └──────┬──────┘
                        │
               F5: payout approved
                        │
                 ┌──────▼──────┐
                 │    PAID     │ ← money sent to reseller
                 └─────────────┘

    Any status ──── charge.refunded ────→ CLAWED_BACK
    PAID + refund → CLAWED_BACK + negative commission record
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `StripeWebhookDispatcher` (E43) | Integration | Receives Stripe events; we extend it |
| `ResellerClient` (F2) | Domain | Links companies to resellers |
| `Reseller` (F1) | Domain | Provides `commission_pct` |
| `CompanyRepository` | Cross-BC read | Lookup company by `stripe_customer_id` for commission |
| Celery beat | Infrastructure | Scheduled commission confirmation task |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | `CreateCommissionCommandHandler` — all paths | High | `tests/unit/reseller_bc/commission/application/test_create_commission.py` |
| Unit | `ClawbackCommissionCommandHandler` — all paths | High | `tests/unit/reseller_bc/commission/application/test_clawback_commission.py` |
| Unit | `ResellerCommission.create()` — calculation | High | `tests/unit/reseller_bc/commission/domain/test_commission_entity.py` |
| Unit | `GetAvailableBalanceQueryHandler` | Medium | `tests/unit/reseller_bc/commission/application/test_get_available_balance.py` |
| Integration | `GET /reseller/commissions` | Medium | `tests/integration/test_reseller_commission_endpoints.py` |
| Integration | Commission creation via webhook flow | High | `tests/integration/test_commission_webhook.py` |
| Integration | `GET /admin/resellers/{id}/commissions` | Medium | `tests/integration/test_reseller_commission_endpoints.py` |

## Implementation Order

1. [ ] Domain: `CommissionStatus` enum
2. [ ] Domain: `ResellerCommission` entity
3. [ ] Domain: `ResellerCommissionRepositoryInterface`
4. [ ] Infrastructure: `ResellerCommissionModel`
5. [ ] Infrastructure: `ResellerCommissionRepository`
6. [ ] Infrastructure: Alembic migration
7. [ ] Application: `CreateCommissionCommand` + Handler
8. [ ] Application: `ClawbackCommissionCommand` + Handler
9. [ ] Application: `CommissionDto`, `CommissionListDto`
10. [ ] Application: `ListCommissionsQuery` + Handler
11. [ ] Application: `GetAvailableBalanceQuery` + Handler
12. [ ] Celery: `confirm_commissions` task + beat schedule
13. [ ] Collateral: Extend `StripeWebhookDispatcher` (+ billing router deps)
14. [ ] Collateral: Update `GetResellerDashboardQueryHandler` with real data
15. [ ] HTTP: Commission schemas + mapper
16. [ ] HTTP: `GET /reseller/commissions` endpoint
17. [ ] HTTP: `GET /admin/resellers/{id}/commissions` endpoint
18. [ ] Tests: Unit tests (entity, commands, queries)
19. [ ] Tests: Integration tests (endpoints, webhook flow)
20. [ ] Frontend: `CommissionsPage.tsx` + route + i18n

## Open Technical Questions

1. **`CompanyRepository.find_by_ids()`** — Does this batch method exist? If not, it needs to be added to avoid N+1 in the commission list query. (Check during implementation.)
2. **Stripe `charge.refunded` payload** — The `invoice` field on a refunded charge may be null for direct charges (not subscription-based). The handler gracefully handles this (skips if no `invoice` field).

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Duplicate commission records | Low | Medium | Idempotency check on `stripe_invoice_id` in handler + dispatcher-level `is_stripe_event_processed` |
| Celery task failure | Low | Low | Task is retried by Celery; pending commissions accumulate safely |
| `charge.refunded` without invoice ID | Medium | Low | Handler skips gracefully if `obj.get("invoice")` is None |
| Commission calculation off by 1 cent | Low | Low | Integer division (`//`) with explicit rounding-down documented in requirements |
