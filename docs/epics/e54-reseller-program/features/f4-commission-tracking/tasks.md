# Implementation Tasks: F4 — Commission Tracking

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 20
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain Layer | 3 | S each |
| Infrastructure Layer | 3 | S–M |
| Application Layer | 6 | S–M |
| Collateral (Dispatcher + Dashboard) | 3 | M |
| HTTP Layer | 2 | S each |
| Tests | 2 | S–M |
| Frontend | 1 | M |

---

## Phase 1: Domain Layer

### TASK-001: Create `CommissionStatus` Enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create the commission status enum with all lifecycle states.

**File:** `src/reseller_bc/commission/domain/enums.py`

**Implementation:**
```python
from enum import Enum


class CommissionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CLAWED_BACK = "clawed_back"
```

**Acceptance Criteria:**
- [x]Enum with 4 values: `PENDING`, `CONFIRMED`, `PAID`, `CLAWED_BACK`
- [x]Inherits from `str, Enum` for JSON serialization
- [x]`__init__.py` files created for `src/reseller_bc/commission/` and `src/reseller_bc/commission/domain/`

---

### TASK-002: Create `ResellerCommission` Entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the commission entity with factory methods for creation, clawback creation, and status transition methods.

**File:** `src/reseller_bc/commission/domain/entities.py`

**Implementation:**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.reseller_bc.commission.domain.enums import CommissionStatus


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

**Acceptance Criteria:**
- [x]`@dataclass` with all 12 fields from design
- [x]`create()` factory: calculates `commission_amount_cents = payment_amount_cents * commission_pct // 100`, status starts `PENDING`
- [x]`create_clawback()` factory: negative amounts, status `CLAWED_BACK`
- [x]`confirm()` method: sets status to `CONFIRMED`
- [x]`clawback()` method: sets status to `CLAWED_BACK`

---

### TASK-003: Create `ResellerCommissionRepositoryInterface`

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Create the repository interface (port) defining all data access methods needed by commands, queries, and the Celery task.

**File:** `src/reseller_bc/commission/domain/repository.py`

**Implementation:**
```python
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.reseller_bc.commission.domain.entities import ResellerCommission


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

**Acceptance Criteria:**
- [x]ABC interface with 9 abstract methods exactly as specified in design
- [x]Uses domain entity types in signatures
- [x]No infrastructure dependencies

---

## Phase 2: Infrastructure Layer

### TASK-004: Create `ResellerCommissionModel` + Alembic Migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the SQLAlchemy model for the `reseller_commissions` table and its Alembic migration.

**File (model):** `src/reseller_bc/commission/infrastructure/models.py`
**File (migration):** `alembic/versions/XXXX_add_reseller_commissions_table.py`

**Model:**
```python
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.base import Base
from core.mixins import ULIDMixin


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

**Schema (migration):**
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

**Acceptance Criteria:**
- [x]Model uses `ULIDMixin`, `Base`
- [x]SQLAlchemy 2.0 style: `Mapped[type]` + `mapped_column()`
- [x]3 foreign keys: `resellers.id`, `reseller_clients.id`, `companies.id`
- [x]4 indexes: `reseller_id`, `company_id`, `stripe_invoice_id`, `status`
- [x]`stripe_invoice_id` NOT unique (clawback records reuse the same invoice ID)
- [x]Migration reversible (`upgrade` + `downgrade`)
- [x]`__init__.py` files created for `src/reseller_bc/commission/infrastructure/`
- [x]`make db-upgrade` succeeds

---

### TASK-005: Create `ResellerCommissionRepository`

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Implement the commission repository following the same pattern as `ResellerClientRepository` (upsert by ID, `select()` queries, aggregate `func.sum()`).

**File:** `src/reseller_bc/commission/infrastructure/repository.py`

**Implementation details:**
- `save()` — upsert: check `select().where(id)`, update existing or `session.add()` new, `session.flush()`
- `find_by_stripe_invoice_id()` — `select().where(stripe_invoice_id).first()`, returns the FIRST match (for idempotency in create; clawback uses the original)
- `find_by_reseller_id(offset, limit)` — paginated, ordered by `created_at desc`
- `count_by_reseller_id()` — `select(func.count())`
- `find_pending_before(before)` — `where(status == "pending", created_at <= before)`
- `sum_confirmed_by_reseller_id()` — `select(func.coalesce(func.sum(commission_amount_cents), 0)).where(reseller_id, status == "confirmed")`
- `sum_clawbacks_by_reseller_id()` — same pattern, `status == "clawed_back"`
- `sum_paid_by_reseller_id()` — same pattern, `status == "paid"`
- `sum_all_commissions_by_reseller_id()` — SUM where status IN (pending, confirmed, paid) — excludes clawback negative records
- `_to_entity()` — model → entity conversion using `CommissionStatus(model.status)`

**Acceptance Criteria:**
- [x]Implements `ResellerCommissionRepositoryInterface`
- [x]All 9 interface methods implemented
- [x]`_to_entity()` static method for model → entity conversion
- [x]Uses `func.coalesce(..., 0)` for SUM queries (avoid NULL when no records)
- [x]Follows `ResellerClientRepository` patterns (upsert, session.flush)

---

### TASK-006: Add `CompanyRepository.find_by_ids()` Batch Method

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** None

**Description:**
Add a `find_by_ids(ids: list[str]) -> list[Company]` batch method to the company repository to avoid N+1 queries in the commission list query. Add it to both the interface and implementation.

**Files:**
- `src/company_bc/company/domain/repository.py` — Add abstract method
- `src/company_bc/company/infrastructure/repository.py` — Add implementation

**Implementation:**
```python
# In repository interface:
@abstractmethod
def find_by_ids(self, ids: list[str]) -> list[Company]: ...

# In repository implementation:
def find_by_ids(self, ids: list[str]) -> list[Company]:
    if not ids:
        return []
    models = self.session.execute(
        select(CompanyModel).where(CompanyModel.id.in_(ids))
    ).scalars().all()
    return [self._to_entity(m) for m in models]
```

**Acceptance Criteria:**
- [x]Abstract method added to `CompanyRepositoryInterface`
- [x]Implementation uses `WHERE id IN (...)` query
- [x]Returns empty list for empty input
- [x]Returns domain entities (not models)

---

## Phase 3: Application Layer

### TASK-007: Create `CommissionDto` and `CommissionListDto`

**Phase:** Application
**Complexity:** S
**Dependencies:** None

**Description:**
Create the DTOs for commission data transfer between application and HTTP layers.

**File:** `src/reseller_bc/commission/application/dtos.py`

**Implementation:**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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

**Acceptance Criteria:**
- [x]Both DTOs are `@dataclass`
- [x]`CommissionDto` has all 12 fields from design
- [x]`CommissionListDto` has `items` (list) and `total` (int)
- [x]`__init__.py` file created for `src/reseller_bc/commission/application/`

---

### TASK-008: Create `CreateCommissionCommand` + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-002, TASK-003

**Description:**
Create the command and handler that creates a commission when a Stripe payment is received. Fails silently on all validation failures (no reseller client, demo account, already processed, orphaned client).

**File:** `src/reseller_bc/commission/application/commands/create_commission.py`

**Implementation:**
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.client.domain.repository import ResellerClientRepositoryInterface
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface
from src.reseller_bc.reseller.domain.repository import ResellerRepositoryInterface


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
        self.commission_repo = commission_repo
        self.client_repo = client_repo
        self.reseller_repo = reseller_repo

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

**Acceptance Criteria:**
- [x]Inherits from `Command` / `CommandHandler`
- [x]Command + Handler in SAME file
- [x]`handle()` returns `None` (CQRS)
- [x]Finds `ResellerClient` by `company_id` — returns silently if not found
- [x]Skips demo accounts (`client.is_demo`)
- [x]Idempotency: checks `find_by_stripe_invoice_id` — returns silently if exists
- [x]Gets `Reseller` for `commission_pct` — returns silently if not found
- [x]Creates `ResellerCommission` via factory method, saves via repo

---

### TASK-009: Create `ClawbackCommissionCommand` + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-003

**Description:**
Create the command and handler that claws back a commission when a charge is refunded. If the commission was already paid, also creates a negative commission record.

**File:** `src/reseller_bc/commission/application/commands/clawback_commission.py`

**Implementation:**
```python
from dataclasses import dataclass

from src.framework.application.command_bus import Command, CommandHandler
from src.reseller_bc.commission.domain.entities import ResellerCommission
from src.reseller_bc.commission.domain.enums import CommissionStatus
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface


@dataclass
class ClawbackCommissionCommand(Command):
    stripe_invoice_id: str


class ClawbackCommissionCommandHandler(CommandHandler[ClawbackCommissionCommand]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        self.commission_repo = commission_repo

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

**Acceptance Criteria:**
- [x]Inherits from `Command` / `CommandHandler`
- [x]Command + Handler in SAME file
- [x]`handle()` returns `None`
- [x]Finds commission by `stripe_invoice_id` — returns silently if not found
- [x]Skips if already `CLAWED_BACK`
- [x]If `PAID`: creates negative commission record via `create_clawback()`
- [x]Marks original as `CLAWED_BACK` via `commission.clawback()`

---

### TASK-010: Create `ListCommissionsQuery` + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-003, TASK-006, TASK-007

**Description:**
Create the query and handler that returns a paginated list of commissions for a reseller, enriched with company names (batch-loaded to avoid N+1).

**File:** `src/reseller_bc/commission/application/queries/list_commissions.py`

**Implementation:** (as specified in design — see design.md §3 Queries → `ListCommissionsQuery`)

**Acceptance Criteria:**
- [x]Inherits from `Query` / `QueryHandler`
- [x]Query + Handler in SAME file
- [x]Returns `CommissionListDto`
- [x]Uses `commission_repo.find_by_reseller_id()` with pagination
- [x]Batch-loads company names via `company_repo.find_by_ids()` (no N+1)
- [x]Maps entities to `CommissionDto` items

---

### TASK-011: Create `GetAvailableBalanceQuery` + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Create the query and handler that calculates the available balance for a reseller: `confirmed − paid + clawbacks` (clawbacks are negative).

**File:** `src/reseller_bc/commission/application/queries/get_available_balance.py`

**Implementation:**
```python
from dataclasses import dataclass

from src.framework.application.query_bus import Query, QueryHandler
from src.reseller_bc.commission.domain.repository import ResellerCommissionRepositoryInterface


@dataclass
class GetAvailableBalanceQuery(Query):
    reseller_id: str


class GetAvailableBalanceQueryHandler(QueryHandler[GetAvailableBalanceQuery, int]):
    def __init__(self, commission_repo: ResellerCommissionRepositoryInterface):
        self.commission_repo = commission_repo

    def handle(self, query: GetAvailableBalanceQuery) -> int:
        confirmed = self.commission_repo.sum_confirmed_by_reseller_id(query.reseller_id)
        paid = self.commission_repo.sum_paid_by_reseller_id(query.reseller_id)
        clawbacks = self.commission_repo.sum_clawbacks_by_reseller_id(query.reseller_id)
        return confirmed - paid + clawbacks
```

**Acceptance Criteria:**
- [x]Inherits from `Query` / `QueryHandler`
- [x]Returns `int` (cents)
- [x]Formula: `confirmed − paid + clawbacks` (clawbacks are negative values, so adding reduces)
- [x]Uses 3 separate SUM repo methods

---

### TASK-012: Create `confirm_commissions` Celery Task + Beat Schedule

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Create the daily Celery beat task that transitions commissions from `pending` → `confirmed` after 30 days. Register in beat schedule.

**File (task):** `core/tasks/commission.py`
**File (schedule):** `core/celery.py`

**Task implementation:**
```python
import logging
from datetime import datetime, timedelta

from core.celery import celery_app

logger = logging.getLogger(__name__)


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

**Beat schedule entry (add to `core/celery.py`):**
```python
"confirm-commissions": {
    "task": "core.tasks.commission.confirm_commissions",
    "schedule": crontab(hour=4, minute=0),  # Daily at 04:00 UTC
},
```

**Acceptance Criteria:**
- [x]Task uses `SessionLocal` + try/except/finally pattern (same as `expire_demo_accounts`)
- [x]Cutoff = `utcnow() - 30 days`
- [x]Calls `find_pending_before()` then `confirm()` + `save()` for each
- [x]`session.commit()` after all updates
- [x]Registered in `beat_schedule` at 04:00 UTC daily
- [x]Returns dict with `confirmed` count

---

## Phase 4: Collateral Changes

### TASK-013: Extend `StripeWebhookDispatcher` + Billing Router Dependencies

**Phase:** Collateral
**Complexity:** M
**Dependencies:** TASK-008, TASK-009

**Description:**
Modify the Stripe webhook dispatcher to:
1. Accept optional reseller repos in constructor (backward-compatible)
2. Add commission creation after `invoice.payment_succeeded` billing handler
3. Add `charge.refunded` handler for clawbacks

Also update the billing router to pass the reseller repos to the dispatcher, and add dependency functions.

**Files:**
- `src/company_bc/company/application/services/stripe_webhook_dispatcher.py`
- `adapters/http/api/billing/routers.py`
- `adapters/http/api/billing/dependencies.py`

**Dispatcher changes:**

Constructor gains 3 optional params:
```python
def __init__(
    self,
    company_repo: CompanyRepositoryInterface,
    client_repo: Optional[ResellerClientRepositoryInterface] = None,
    commission_repo: Optional[ResellerCommissionRepositoryInterface] = None,
    reseller_repo: Optional[ResellerRepositoryInterface] = None,
) -> None:
```

In `_route()`, extend `invoice.payment_succeeded` block — after existing `RestoreBillingCommand`, add:
```python
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

Add new `charge.refunded` block (before the `else: logger.debug` at the end):
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

**Billing router:** Update `stripe_webhook` endpoint to pass reseller repos:
```python
from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository
from src.reseller_bc.reseller.infrastructure.repository import ResellerRepository

# In stripe_webhook endpoint, get db session and instantiate:
dispatcher = StripeWebhookDispatcher(
    company_repo=company_repo,
    client_repo=ResellerClientRepository(db),
    commission_repo=ResellerCommissionRepository(db),
    reseller_repo=ResellerRepository(db),
)
```

**Acceptance Criteria:**
- [x]Dispatcher constructor backward-compatible (optional params default to `None`)
- [x]Commission creation only when all 3 reseller repos are present
- [x]Commission errors caught with `except Exception` — logged, never raised
- [x]`charge.refunded` handler skips if no `invoice` field in payload
- [x]`charge.refunded` errors caught with `except Exception` — logged, never raised
- [x]Billing router passes all repos to dispatcher
- [x]Existing billing handlers unchanged

---

### TASK-014: Update `GetResellerDashboardQueryHandler` with Real Commission Data

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-005, TASK-011

**Description:**
Update the dashboard query handler to accept a `ResellerCommissionRepository` and replace the hardcoded zeros with real financial data.

**File:** `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py`

**Changes:**
- Add `commission_repo: ResellerCommissionRepositoryInterface` to `__init__`
- Replace `total_commissions_cents=0` with `commission_repo.sum_all_commissions_by_reseller_id(reseller.id)`
- Replace `available_balance_cents=0` with result from `GetAvailableBalanceQueryHandler` or inline calculation
- `pending_payout_cents` stays 0 until F5

Also update the dashboard route in `adapters/http/api/reseller/routers.py` to pass `commission_repo` to the handler.

**Acceptance Criteria:**
- [x]`commission_repo` added as constructor param
- [x]`total_commissions_cents` returns real SUM from repo
- [x]`available_balance_cents` returns `confirmed − paid + clawbacks`
- [x]`pending_payout_cents` remains `0` (F5 scope)
- [x]Dashboard route updated to instantiate and pass `ResellerCommissionRepository`

---

### TASK-015: Add Commission Schemas + Mapper

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-007

**Description:**
Add commission response schemas and mapper to the reseller HTTP layer.

**File (schemas):** `adapters/http/api/reseller/schemas.py`
**File (mappers):** `adapters/http/api/reseller/mappers.py`

**Schemas to add:**
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

**Mapper to add:**
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

**Acceptance Criteria:**
- [x]`CommissionResponse` schema with all 11 fields
- [x]`CommissionListResponse` schema with `items` and `total`
- [x]`CommissionMapper.dto_to_response()` converts datetimes to ISO strings
- [x]`CommissionMapper.dto_to_list_response()` wraps list

---

## Phase 5: HTTP Layer

### TASK-016: Add `GET /reseller/commissions` + `GET /admin/resellers/{id}/commissions` Endpoints

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-010, TASK-015

**Description:**
Add the commission list endpoints to both the reseller router and the admin reseller router.

**File (reseller):** `adapters/http/api/reseller/routers.py`
**File (admin):** `adapters/http/api/admin/reseller_routers.py`

**Reseller endpoint:**
```python
@router.get("/commissions")
def list_commissions(
    offset: int = QueryParam(0, ge=0),
    limit: int = QueryParam(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db),
):
    from src.company_bc.company.infrastructure.repository import CompanyRepository
    from src.reseller_bc.client.infrastructure.repository import ResellerClientRepository
    from src.reseller_bc.commission.application.queries.list_commissions import (
        ListCommissionsQuery, ListCommissionsQueryHandler,
    )
    from src.reseller_bc.commission.infrastructure.repository import ResellerCommissionRepository

    handler = ListCommissionsQueryHandler(
        commission_repo=ResellerCommissionRepository(db),
        client_repo=ResellerClientRepository(db),
        company_repo=CompanyRepository(db),
    )
    dto = handler.handle(ListCommissionsQuery(
        reseller_id=reseller.id, offset=offset, limit=limit,
    ))
    return {"data": CommissionMapper.dto_to_list_response(dto).model_dump()}
```

**Admin endpoint:** Same pattern with `reseller_id` from path param and `require_role(UserRole.SUPER_ADMIN)`.

**Acceptance Criteria:**
- [x]Reseller: `GET /api/v1/reseller/commissions` with `get_current_reseller` auth
- [x]Suspended resellers can access (uses `get_current_reseller`, NOT `require_active_reseller`)
- [x]Admin: `GET /api/v1/admin/resellers/{reseller_id}/commissions` with `require_role(SUPER_ADMIN)`
- [x]Both support `offset` and `limit` query params
- [x]Return `{"data": CommissionListResponse}`

---

## Phase 6: Tests

### TASK-017: Unit Tests — Commission Entity, Commands, and Queries

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-002, TASK-008, TASK-009, TASK-011

**Description:**
Create unit tests covering entity logic and all command/query handler behaviors.

**Files:**
- `tests/unit/reseller_bc/commission/domain/test_commission_entity.py`
- `tests/unit/reseller_bc/commission/application/test_create_commission.py`
- `tests/unit/reseller_bc/commission/application/test_clawback_commission.py`
- `tests/unit/reseller_bc/commission/application/test_get_available_balance.py`

**Entity test cases:**
1. `create()` calculates `commission_amount_cents` correctly (e.g., 10000 * 20 // 100 = 2000)
2. `create()` sets status to `PENDING`
3. `create()` rounds down (e.g., 999 * 15 // 100 = 149, not 150)
4. `create_clawback()` produces negative amounts
5. `create_clawback()` status is `CLAWED_BACK`
6. `confirm()` sets status to `CONFIRMED`
7. `clawback()` sets status to `CLAWED_BACK`

**CreateCommission handler test cases:**
1. Valid: company has ResellerClient → commission created, `save` called
2. No ResellerClient → `save` NOT called
3. Demo account → `save` NOT called
4. Already processed (existing invoice) → `save` NOT called
5. Orphaned client (reseller not found) → `save` NOT called

**Clawback handler test cases:**
1. Pending commission → status set to `CLAWED_BACK`, `save` called once
2. Confirmed commission → status set to `CLAWED_BACK`, `save` called once
3. Paid commission → negative record created + original clawed back, `save` called twice
4. Already clawed back → no action, `save` NOT called
5. No commission found → no action, `save` NOT called

**GetAvailableBalance test cases:**
1. Returns `confirmed - paid + clawbacks`
2. All zeros → returns 0

**Acceptance Criteria:**
- [x]All entity test cases (7)
- [x]All CreateCommission test cases (5)
- [x]All Clawback test cases (5)
- [x]All GetAvailableBalance test cases (2)
- [x]Uses `MagicMock` for repos
- [x]`make test` passes

---

### TASK-018: Integration Tests — Commission Endpoints

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-016

**Description:**
Create integration tests for the commission endpoints and webhook commission flow.

**File:** `tests/integration/test_reseller_commission_endpoints.py`

**Test cases:**
1. `GET /reseller/commissions` — returns commissions for authenticated reseller
2. `GET /reseller/commissions` — empty list for reseller with no commissions
3. `GET /reseller/commissions` — suspended reseller can view (read-only)
4. `GET /admin/resellers/{id}/commissions` — super admin can view
5. `GET /admin/resellers/{id}/commissions` — non-admin gets 403

**Fixtures needed:**
- `reseller` fixture (active, with known JWT)
- `reseller_client` fixture (linked company)
- `commission` fixture (commission record for the reseller_client)

**Acceptance Criteria:**
- [x]All 5 test cases implemented
- [x]Uses real DB (test fixtures from conftest.py)
- [x]Verifies response structure (`items`, `total`)
- [x]Suspended reseller access confirmed
- [x]`make test-integration` passes

---

## Phase 7: Frontend

### TASK-019: Create `CommissionsPage.tsx` + Route + i18n

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-016

**Description:**
Create the reseller commissions page with a filterable/sortable table showing all commissions.

**Files:**
- `web/app/src/pages/reseller/CommissionsPage.tsx` — New page
- `web/app/src/router.tsx` — Add route
- `web/app/src/locales/en.ts` — Add commission i18n keys
- `web/app/src/locales/es.ts` — Add commission i18n keys

**CommissionsPage features:**
- Fetch `GET /reseller/commissions` with pagination
- Table columns: Company, Payment, Rate, Earned, Period, Status, Date
- Status badges: `pending` (yellow), `confirmed` (green), `paid` (blue), `clawed_back` (red with strikethrough)
- Clawed-back commissions clearly marked (red text, strikethrough on amount)
- Pagination controls (offset/limit)
- Format cents as dollars (`$XX.XX`)

**Acceptance Criteria:**
- [x]Table displays all commission fields
- [x]Clawed-back commissions clearly marked with visual distinction
- [x]Pagination working
- [x]i18n keys added for both `en.ts` and `es.ts`
- [x]Route registered in `router.tsx` at `/reseller/commissions`
- [x]Navigation link added to reseller layout/sidebar

---

## Dependency Graph

```
TASK-001 (Enum) ──┬──→ TASK-002 (Entity) ──→ TASK-003 (Interface) ──→ TASK-005 (Repo Impl)
                  │                                                      │
                  └──→ TASK-004 (Model+Migration) ──────────────────────┘
                                                                         │
TASK-006 (find_by_ids) ──────────────────────────────────────────────┐   │
                                                                     │   │
TASK-007 (DTOs) ─────────────────────────────────────────┐           │   │
                                                          │           │   │
TASK-002 + TASK-003 ──→ TASK-008 (CreateCommission) ──────┤           │   │
                   └──→ TASK-009 (Clawback) ──────────────┤           │   │
                                                          │           │   │
TASK-003 + TASK-006 + TASK-007 ──→ TASK-010 (ListQuery) ──┤           │   │
                                                          │           │   │
TASK-003 ──→ TASK-011 (BalanceQuery) ─────────────────────┤           │   │
                                                          │           │   │
TASK-005 ──→ TASK-012 (Celery Task) ──────────────────────┤           │   │
                                                          │           │   │
TASK-008 + TASK-009 ──→ TASK-013 (Dispatcher) ────────────┤           │   │
                                                          │           │   │
TASK-005 + TASK-011 ──→ TASK-014 (Dashboard) ─────────────┤           │   │
                                                          │           │   │
TASK-007 ──→ TASK-015 (Schemas+Mapper) ───────────────────┤           │   │
                                                          │           │   │
TASK-010 + TASK-015 ──→ TASK-016 (Endpoints) ─────────────┤           │   │
                                                          │           │   │
TASK-002+008+009+011 ──→ TASK-017 (Unit Tests) ───────────┤           │   │
                                                          │           │   │
TASK-016 ──→ TASK-018 (Integration Tests) ────────────────┤           │   │
                                                          │           │   │
TASK-016 ──→ TASK-019 (Frontend) ─────────────────────────┘           │   │
```

## Execution Order

**Batch 1 (Parallel — no dependencies):**
- TASK-001: Create `CommissionStatus` enum
- TASK-006: Add `CompanyRepository.find_by_ids()`
- TASK-007: Create `CommissionDto` and `CommissionListDto`

**Batch 2 (Depends on Batch 1):**
- TASK-002: Create `ResellerCommission` entity (depends on TASK-001)
- TASK-004: Create `ResellerCommissionModel` + migration (depends on TASK-001)

**Batch 3 (Depends on Batch 2):**
- TASK-003: Create `ResellerCommissionRepositoryInterface` (depends on TASK-002)

**Batch 4 (Depends on Batch 3):**
- TASK-005: Create `ResellerCommissionRepository` (depends on TASK-003, TASK-004)
- TASK-008: Create `CreateCommissionCommand` + Handler (depends on TASK-002, TASK-003)
- TASK-009: Create `ClawbackCommissionCommand` + Handler (depends on TASK-002, TASK-003)
- TASK-011: Create `GetAvailableBalanceQuery` + Handler (depends on TASK-003)
- TASK-015: Add Commission schemas + mapper (depends on TASK-007)

**Batch 5 (Depends on Batch 4):**
- TASK-010: Create `ListCommissionsQuery` + Handler (depends on TASK-003, TASK-006, TASK-007)
- TASK-012: Create `confirm_commissions` Celery task (depends on TASK-005)
- TASK-013: Extend `StripeWebhookDispatcher` (depends on TASK-008, TASK-009)
- TASK-014: Update dashboard query with real data (depends on TASK-005, TASK-011)

**Batch 6 (Depends on Batch 5):**
- TASK-016: Add commission endpoints (depends on TASK-010, TASK-015)
- TASK-017: Unit tests (depends on TASK-002, TASK-008, TASK-009, TASK-011)

**Batch 7 (Depends on Batch 6):**
- TASK-018: Integration tests (depends on TASK-016)
- TASK-019: Frontend commissions page (depends on TASK-016)

## Final Checklist

- [x]All 19 tasks completed
- [x]All unit tests passing (`make test`)
- [x]All integration tests passing (`make test-integration`)
- [x]Existing tests still pass (backward compat)
- [x]mypy passes (`make lint`)
- [x]No breaking changes to existing APIs
- [x]Dashboard returns real commission data
- [x]Celery beat schedule registered
