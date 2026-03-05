# Solution Design: F2 — Support Ticket System

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `support_bc` (existing — new subdomain `ticket`)

## Summary

A full-lifecycle support ticket system where admins and technicians can submit tickets to the DSM Control platform team, track their status, and exchange messages. The backend follows the same DDD + CQRS patterns as the request_bc (state machine, event log via messages, repository with filtering/pagination). A Celery beat task auto-closes resolved tickets after 7 days and stale tickets after 30 days. Email notifications are sent via Brevo (3 templates). The frontend provides creation, listing, and detail/conversation pages.

The ticket system is scoped to **platform support** (users contacting the DSM Control team), not internal IT helpdesk requests — those are handled by the existing request_bc.

## Architecture Decision

**Approach chosen:** DDD entity with state machine + CQRS commands/queries

- **New subdomain within `support_bc`** — `src/support_bc/ticket/` sits alongside `ai_assistant/`. This keeps all platform-support features in one bounded context.
- **State machine via enum transitions** — Same pattern as `ServiceRequest.change_status()` with `VALID_STATUS_TRANSITIONS` dict. Simpler than a workflow engine; 5 statuses with well-defined transitions.
- **Reference generation via DB sequence** — PostgreSQL sequence (`support_ticket_ref_seq`) ensures unique, monotonic references across concurrent requests. The format is `SUP-{seq:04d}` (e.g., `SUP-0001`). The repository calls `nextval()` during `save()`.
- **Separate email task** — New Celery task `send_support_ticket_email` handles 3 template variants (ticket_created, response_received, ticket_resolved). Follows the existing `send_request_notification_email` pattern with retry + backoff.
- **No EventBus integration** — F2 uses direct email dispatch (not the notification_bc EventBus). Support tickets are platform-level, not company-internal. In-app notifications can be added in a future iteration.
- **Super admin endpoints defined here, UI in F3** — The API endpoints for the support team (`/api/v1/support-tickets/*`) are defined in F2 since they share entities. F3 builds the dashboard UI on top of them.

**Alternative considered: Reuse request_bc** — Rejected because support tickets have different semantics (platform → user, not user → IT team), different state machine, different roles (SUPER_ADMIN manages, not TECHNICIAN), and different access patterns (cross-company for super admin).

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| State machine pattern | `src/request_bc/request/domain/entities.py` → `change_status()` | Pattern only | Same VALID_STATUS_TRANSITIONS approach, different states |
| Factory method pattern | `ServiceRequest.create()` | Pattern only | Same validation + defaults approach |
| Repository with pagination | `src/request_bc/request/infrastructure/repository.py` | Pattern only | Same `find_all()` with filters + `(items, total)` return |
| SQLAlchemy 2.0 model | `src/request_bc/request/infrastructure/models.py` | Pattern only | Same `Mapped[]` + `mapped_column()` + mixins |
| Celery beat task | `core/celery.py` + `core/tasks/` | Pattern + config | Add new beat entry; follow existing task patterns |
| Email service | `core/email.py` | Yes | Reuse `get_email_service()` directly |
| Email Celery task | `core/tasks/email_notifications.py` | Pattern only | New task `send_support_ticket_email` with 3 variants |
| Jinja2 templates | `templates/email/request_comment.html` | Pattern only | New templates with similar structure |
| PaginationMeta | `adapters/http/schemas/responses.py` | Yes | Reuse directly |
| Auth dependencies | `adapters/http/api/auth/dependencies.py` | Yes | Reuse `require_role(UserRole.TECHNICIAN)` and `require_role(UserRole.SUPER_ADMIN)` |
| `/my` router pattern | `adapters/http/api/my/routers.py` | Pattern only | New router file for customer-facing endpoints |
| Help panel | `web/app/src/components/help/HelpPanel.tsx` | Modify | Add "Contact Support" link |
| AppLayout | `web/app/src/components/layout/AppLayout.tsx` | Reference | Check where to add nav links |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| `SupportTicket` | `src/support_bc/ticket/domain/entities.py` | Main entity with state machine, factory method, reopen validation |
| `TicketMessage` | Same file | Conversation message with `is_from_platform` flag |

```python
# src/support_bc/ticket/domain/entities.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from src.support_bc.ticket.domain.enums import (
    TicketCategory,
    TicketPriority,
    TicketStatus,
    VALID_TICKET_TRANSITIONS,
)
from src.support_bc.ticket.domain.exceptions import (
    InvalidTicketTransitionError,
    TicketReopenWindowExpiredError,
)
from ulid import ULID


@dataclass
class SupportTicket:
    id: str
    reference: str  # SUP-NNNN
    company_id: str
    created_by: str
    category: TicketCategory
    subject: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    ai_conversation_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    REOPEN_WINDOW_DAYS = 7

    @classmethod
    def create(
        cls,
        company_id: str,
        created_by: str,
        category: str,
        subject: str,
        description: str,
        ai_conversation_summary: Optional[str] = None,
        id: Optional[str] = None,
    ) -> "SupportTicket":
        subject = subject.strip()
        description = description.strip()
        if not subject:
            raise ValueError("Subject is required")
        if not description:
            raise ValueError("Description is required")

        return cls(
            id=id or str(ULID()),
            reference="",  # Set by repository after sequence nextval
            company_id=company_id,
            created_by=created_by,
            category=TicketCategory(category),
            subject=subject,
            description=description,
            status=TicketStatus.OPEN,
            priority=TicketPriority.MEDIUM,
            ai_conversation_summary=ai_conversation_summary,
        )

    def change_status(self, new_status: TicketStatus) -> None:
        allowed = VALID_TICKET_TRANSITIONS.get(self.status, [])
        if new_status not in allowed:
            raise InvalidTicketTransitionError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        if new_status == TicketStatus.RESOLVED:
            self.resolved_at = datetime.now(timezone.utc)
        if new_status == TicketStatus.CLOSED:
            self.closed_at = datetime.now(timezone.utc)
        self.status = new_status

    def reopen(self) -> None:
        if self.status != TicketStatus.RESOLVED:
            raise InvalidTicketTransitionError("Only resolved tickets can be reopened")
        if self.resolved_at:
            days_since = (datetime.now(timezone.utc) - self.resolved_at).days
            if days_since > self.REOPEN_WINDOW_DAYS:
                raise TicketReopenWindowExpiredError(
                    "This ticket can no longer be reopened"
                )
        self.status = TicketStatus.OPEN
        self.resolved_at = None

    def change_priority(self, new_priority: TicketPriority) -> None:
        self.priority = new_priority


@dataclass
class TicketMessage:
    id: str
    ticket_id: str
    author_id: str
    body: str
    is_from_platform: bool
    created_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        ticket_id: str,
        author_id: str,
        body: str,
        is_from_platform: bool = False,
        id: Optional[str] = None,
    ) -> "TicketMessage":
        body = body.strip()
        if not body:
            raise ValueError("Message body is required")
        return cls(
            id=id or str(ULID()),
            ticket_id=ticket_id,
            author_id=author_id,
            body=body,
            is_from_platform=is_from_platform,
        )
```

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| `TicketStatus` | `src/support_bc/ticket/domain/enums.py` | open, in_progress, waiting_on_customer, resolved, closed |
| `TicketPriority` | Same file | low, medium, high, urgent |
| `TicketCategory` | Same file | bug_report, feature_request, billing, how_to, account_access, other |
| `VALID_TICKET_TRANSITIONS` | Same file | Dict mapping current → allowed next states |

```python
# src/support_bc/ticket/domain/enums.py
from enum import Enum


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_ON_CUSTOMER = "waiting_on_customer"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, Enum):
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"
    BILLING = "billing"
    HOW_TO = "how_to"
    ACCOUNT_ACCESS = "account_access"
    OTHER = "other"


VALID_TICKET_TRANSITIONS: dict[TicketStatus, list[TicketStatus]] = {
    TicketStatus.OPEN: [
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    ],
    TicketStatus.IN_PROGRESS: [
        TicketStatus.WAITING_ON_CUSTOMER,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    ],
    TicketStatus.WAITING_ON_CUSTOMER: [
        TicketStatus.IN_PROGRESS,
        TicketStatus.RESOLVED,
        TicketStatus.CLOSED,
    ],
    TicketStatus.RESOLVED: [
        TicketStatus.OPEN,  # reopen (within 7 days)
        TicketStatus.CLOSED,
    ],
    TicketStatus.CLOSED: [],  # terminal state
}
```

#### Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| `TicketNotFoundError` | `src/support_bc/ticket/domain/exceptions.py` | Ticket not found or access denied |
| `InvalidTicketTransitionError` | Same file | Invalid state machine transition |
| `TicketReopenWindowExpiredError` | Same file | Reopen attempted after 7-day window |

```python
# src/support_bc/ticket/domain/exceptions.py
class TicketNotFoundError(Exception):
    pass

class InvalidTicketTransitionError(Exception):
    pass

class TicketReopenWindowExpiredError(Exception):
    pass
```

#### Repository Interface

| Interface | File Path | Description |
|-----------|-----------|-------------|
| `SupportTicketRepositoryInterface` | `src/support_bc/ticket/domain/repository.py` | ABC with CRUD + query methods |

```python
# src/support_bc/ticket/domain/repository.py
from abc import ABC, abstractmethod
from typing import Optional

from src.support_bc.ticket.domain.entities import SupportTicket, TicketMessage


class SupportTicketRepositoryInterface(ABC):

    @abstractmethod
    def save(self, ticket: SupportTicket) -> SupportTicket:
        """Insert or update. On insert, assigns reference via sequence."""
        ...

    @abstractmethod
    def find_by_id(self, ticket_id: str, company_id: str) -> Optional[SupportTicket]:
        ...

    @abstractmethod
    def find_by_id_any_company(self, ticket_id: str) -> Optional[SupportTicket]:
        """For super admin — no company scoping."""
        ...

    @abstractmethod
    def find_all(
        self,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List all tickets (super admin). Paginated with filters."""
        ...

    @abstractmethod
    def find_by_company(
        self,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List tickets for a company. Paginated with filters."""
        ...

    @abstractmethod
    def find_by_created_by(
        self,
        user_id: str,
        company_id: str,
        page: int,
        page_size: int,
        status: Optional[str] = None,
    ) -> tuple[list[SupportTicket], int]:
        """List tickets created by user. Paginated."""
        ...

    @abstractmethod
    def find_resolved_older_than_days(self, days: int) -> list[SupportTicket]:
        """For auto-close: resolved tickets older than N days."""
        ...

    @abstractmethod
    def find_stale_older_than_days(self, days: int) -> list[SupportTicket]:
        """For auto-close: active tickets with updated_at older than N days."""
        ...

    @abstractmethod
    def save_message(self, message: TicketMessage) -> TicketMessage:
        ...

    @abstractmethod
    def find_messages(self, ticket_id: str) -> list[TicketMessage]:
        """Ordered by created_at ASC."""
        ...

    @abstractmethod
    def has_unread_platform_messages(self, ticket_id: str, last_read_at: Optional[str] = None) -> bool:
        """Check if there are platform messages newer than the user's last visit."""
        ...

    @abstractmethod
    def count_by_status(self) -> dict[str, int]:
        """For super admin dashboard stats."""
        ...
```

### 2. Infrastructure Layer

#### Models

| Model | File Path | Table |
|-------|-----------|-------|
| `SupportTicketModel` | `src/support_bc/ticket/infrastructure/models.py` | `support_tickets` |
| `TicketMessageModel` | Same file | `ticket_messages` |

```python
# src/support_bc/ticket/infrastructure/models.py
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from src.framework.infrastructure.database.mixins import TimestampMixin, ULIDMixin


class SupportTicketModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "support_tickets"

    reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), server_default="open", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), server_default="medium", nullable=False)
    ai_conversation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_support_tickets_company_status", "company_id", "status"),
        Index("ix_support_tickets_created_by", "company_id", "created_by"),
        Index("ix_support_tickets_status_priority", "status", "priority"),
    )


class TicketMessageModel(ULIDMixin, Base):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[str] = mapped_column(String(26), ForeignKey("support_tickets.id"), nullable=False)
    author_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_from_platform: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_ticket_messages_ticket_id", "ticket_id"),
    )
```

#### Repository

| Interface | Implementation | File Path |
|-----------|----------------|-----------|
| `SupportTicketRepositoryInterface` | `SupportTicketRepository` | `src/support_bc/ticket/infrastructure/repository.py` |

The repository follows the same patterns as `RequestRepository`:
- `save()` does upsert with `flush()` + `refresh()`
- On insert, calls `SELECT nextval('support_ticket_ref_seq')` to assign reference
- `_to_entity()` static method converts model → domain entity
- All `find_*` methods return domain entities
- Pagination returns `(list[Entity], total_count)` tuple

```python
# src/support_bc/ticket/infrastructure/repository.py (key methods)
class SupportTicketRepository(SupportTicketRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, ticket: SupportTicket) -> SupportTicket:
        existing = self.session.get(SupportTicketModel, ticket.id)
        if existing:
            existing.status = ticket.status.value
            existing.priority = ticket.priority.value
            existing.resolved_at = ticket.resolved_at
            existing.closed_at = ticket.closed_at
            self.session.flush()
            self.session.refresh(existing)
            return self._to_entity(existing)
        else:
            # Generate reference from sequence
            seq = self.session.execute(text("SELECT nextval('support_ticket_ref_seq')")).scalar()
            reference = f"SUP-{seq:04d}"

            model = SupportTicketModel(
                id=ticket.id,
                reference=reference,
                company_id=ticket.company_id,
                created_by=ticket.created_by,
                category=ticket.category.value,
                subject=ticket.subject,
                description=ticket.description,
                status=ticket.status.value,
                priority=ticket.priority.value,
                ai_conversation_summary=ticket.ai_conversation_summary,
            )
            self.session.add(model)
            self.session.flush()
            self.session.refresh(model)
            return self._to_entity(model)

    def find_by_company(self, company_id, page, page_size, status=None, category=None):
        query = select(SupportTicketModel).where(
            SupportTicketModel.company_id == company_id
        )
        if status:
            query = query.where(SupportTicketModel.status == status)
        if category:
            query = query.where(SupportTicketModel.category == category)
        total = self.session.execute(
            select(func.count()).select_from(query.subquery())
        ).scalar() or 0
        query = query.order_by(SupportTicketModel.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        models = self.session.execute(query).scalars().all()
        return [self._to_entity(m) for m in models], total

    @staticmethod
    def _to_entity(model: SupportTicketModel) -> SupportTicket:
        return SupportTicket(
            id=model.id,
            reference=model.reference,
            company_id=model.company_id,
            created_by=model.created_by,
            category=TicketCategory(model.category),
            subject=model.subject,
            description=model.description,
            status=TicketStatus(model.status),
            priority=TicketPriority(model.priority),
            ai_conversation_summary=model.ai_conversation_summary,
            resolved_at=model.resolved_at,
            closed_at=model.closed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

#### Migrations

| Migration | Description |
|-----------|-------------|
| `create_support_ticket_tables` | Create `support_tickets`, `ticket_messages` tables, sequence `support_ticket_ref_seq`, and indexes |

```sql
-- Key DDL
CREATE SEQUENCE support_ticket_ref_seq START 1;

CREATE TABLE support_tickets (
    id VARCHAR(26) PRIMARY KEY,
    reference VARCHAR(20) NOT NULL UNIQUE,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    created_by VARCHAR(26) NOT NULL REFERENCES users(id),
    category VARCHAR(30) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'open',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    ai_conversation_summary TEXT,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_support_tickets_company_status ON support_tickets (company_id, status);
CREATE INDEX ix_support_tickets_created_by ON support_tickets (company_id, created_by);
CREATE INDEX ix_support_tickets_status_priority ON support_tickets (status, priority);

CREATE TABLE ticket_messages (
    id VARCHAR(26) PRIMARY KEY,
    ticket_id VARCHAR(26) NOT NULL REFERENCES support_tickets(id),
    author_id VARCHAR(26) NOT NULL REFERENCES users(id),
    body TEXT NOT NULL,
    is_from_platform BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_ticket_messages_ticket_id ON ticket_messages (ticket_id);
```

### 3. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `CreateTicketCommand` | `CreateTicketCommandHandler` | `src/support_bc/ticket/application/commands/create_ticket.py` | Creates ticket, assigns reference, sends emails |
| `AddTicketMessageCommand` | `AddTicketMessageCommandHandler` | `src/support_bc/ticket/application/commands/add_message.py` | Adds message, auto-transitions status, sends email |
| `ChangeTicketStatusCommand` | `ChangeTicketStatusCommandHandler` | `src/support_bc/ticket/application/commands/change_status.py` | Changes status (super admin), sends resolved email |
| `ReopenTicketCommand` | `ReopenTicketCommandHandler` | `src/support_bc/ticket/application/commands/reopen_ticket.py` | Reopens resolved ticket within 7-day window |
| `ChangeTicketPriorityCommand` | `ChangeTicketPriorityCommandHandler` | `src/support_bc/ticket/application/commands/change_priority.py` | Changes priority (super admin) |

```python
# src/support_bc/ticket/application/commands/create_ticket.py
@dataclass
class CreateTicketCommand(Command):
    company_id: str
    created_by: str
    category: str
    subject: str
    description: str
    ai_conversation_summary: str | None = None

class CreateTicketCommandHandler(CommandHandler[CreateTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo
        self.created_ticket: SupportTicket | None = None  # Result container

    def handle(self, command: CreateTicketCommand) -> None:
        ticket = SupportTicket.create(
            company_id=command.company_id,
            created_by=command.created_by,
            category=command.category,
            subject=command.subject,
            description=command.description,
            ai_conversation_summary=command.ai_conversation_summary,
        )
        self.created_ticket = self.ticket_repo.save(ticket)
```

```python
# src/support_bc/ticket/application/commands/add_message.py
@dataclass
class AddTicketMessageCommand(Command):
    ticket_id: str
    author_id: str
    body: str
    is_from_platform: bool = False
    company_id: str | None = None  # None for super admin

class AddTicketMessageCommandHandler(CommandHandler[AddTicketMessageCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: AddTicketMessageCommand) -> None:
        # Find ticket (company-scoped for regular users, unscoped for super admin)
        if command.company_id:
            ticket = self.ticket_repo.find_by_id(command.ticket_id, command.company_id)
        else:
            ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)

        if not ticket:
            raise TicketNotFoundError("Ticket not found")

        if ticket.status == TicketStatus.CLOSED:
            raise InvalidTicketTransitionError("Cannot add messages to a closed ticket")

        # Auto-transition based on who is messaging
        if command.is_from_platform and ticket.status == TicketStatus.OPEN:
            ticket.change_status(TicketStatus.IN_PROGRESS)
        elif command.is_from_platform and ticket.status != TicketStatus.WAITING_ON_CUSTOMER:
            pass  # No status change needed
        elif not command.is_from_platform and ticket.status == TicketStatus.WAITING_ON_CUSTOMER:
            ticket.change_status(TicketStatus.IN_PROGRESS)

        self.ticket_repo.save(ticket)

        message = TicketMessage.create(
            ticket_id=command.ticket_id,
            author_id=command.author_id,
            body=command.body,
            is_from_platform=command.is_from_platform,
        )
        self.ticket_repo.save_message(message)
```

```python
# src/support_bc/ticket/application/commands/change_status.py
@dataclass
class ChangeTicketStatusCommand(Command):
    ticket_id: str
    new_status: str

class ChangeTicketStatusCommandHandler(CommandHandler[ChangeTicketStatusCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ChangeTicketStatusCommand) -> None:
        ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.change_status(TicketStatus(command.new_status))
        self.ticket_repo.save(ticket)
```

```python
# src/support_bc/ticket/application/commands/reopen_ticket.py
@dataclass
class ReopenTicketCommand(Command):
    ticket_id: str
    company_id: str

class ReopenTicketCommandHandler(CommandHandler[ReopenTicketCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ReopenTicketCommand) -> None:
        ticket = self.ticket_repo.find_by_id(command.ticket_id, command.company_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.reopen()  # Validates status + 7-day window
        self.ticket_repo.save(ticket)
```

```python
# src/support_bc/ticket/application/commands/change_priority.py
@dataclass
class ChangeTicketPriorityCommand(Command):
    ticket_id: str
    new_priority: str

class ChangeTicketPriorityCommandHandler(CommandHandler[ChangeTicketPriorityCommand]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, command: ChangeTicketPriorityCommand) -> None:
        ticket = self.ticket_repo.find_by_id_any_company(command.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        ticket.change_priority(TicketPriority(command.new_priority))
        self.ticket_repo.save(ticket)
```

#### Queries

| Query | Handler | File Path | Return Type |
|-------|---------|-----------|-------------|
| `ListMyTicketsQuery` | `ListMyTicketsQueryHandler` | `src/support_bc/ticket/application/queries/list_my_tickets.py` | `tuple[list[SupportTicket], int]` |
| `GetTicketDetailQuery` | `GetTicketDetailQueryHandler` | `src/support_bc/ticket/application/queries/get_ticket_detail.py` | `TicketDetail` (ticket + messages) |
| `ListAllTicketsQuery` | `ListAllTicketsQueryHandler` | `src/support_bc/ticket/application/queries/list_all_tickets.py` | `tuple[list[SupportTicket], int]` |
| `GetTicketStatsQuery` | `GetTicketStatsQueryHandler` | `src/support_bc/ticket/application/queries/get_ticket_stats.py` | `dict[str, int]` |

```python
# src/support_bc/ticket/application/queries/get_ticket_detail.py
@dataclass
class TicketDetail:
    ticket: SupportTicket
    messages: list[TicketMessage]

@dataclass
class GetTicketDetailQuery(Query):
    ticket_id: str
    company_id: str | None = None  # None for super admin

class GetTicketDetailQueryHandler(QueryHandler[GetTicketDetailQuery, TicketDetail]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, query: GetTicketDetailQuery) -> TicketDetail:
        if query.company_id:
            ticket = self.ticket_repo.find_by_id(query.ticket_id, query.company_id)
        else:
            ticket = self.ticket_repo.find_by_id_any_company(query.ticket_id)
        if not ticket:
            raise TicketNotFoundError("Ticket not found")
        messages = self.ticket_repo.find_messages(query.ticket_id)
        return TicketDetail(ticket=ticket, messages=messages)
```

```python
# src/support_bc/ticket/application/queries/list_my_tickets.py
@dataclass
class ListMyTicketsQuery(Query):
    user_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: str | None = None

class ListMyTicketsQueryHandler(QueryHandler[ListMyTicketsQuery, tuple[list[SupportTicket], int]]):
    def __init__(self, ticket_repo: SupportTicketRepositoryInterface):
        self.ticket_repo = ticket_repo

    def handle(self, query: ListMyTicketsQuery) -> tuple[list[SupportTicket], int]:
        return self.ticket_repo.find_by_created_by(
            user_id=query.user_id,
            company_id=query.company_id,
            page=query.page,
            page_size=query.page_size,
            status=query.status,
        )
```

#### Celery Beat Task

| Task | Schedule | File Path | Description |
|------|----------|-----------|-------------|
| `auto_close_stale_tickets` | Every hour | `core/tasks/support_tickets.py` | Auto-close resolved (7 days) and stale (30 days) tickets |

```python
# core/tasks/support_tickets.py
import logging
from core.celery import celery_app
from core.database import SessionLocal

logger = logging.getLogger(__name__)

@celery_app.task(name="core.tasks.support_tickets.auto_close_stale_tickets")
def auto_close_stale_tickets():
    """Auto-close resolved tickets (>7 days) and stale active tickets (>30 days)."""
    from src.support_bc.ticket.infrastructure.repository import SupportTicketRepository
    from src.support_bc.ticket.domain.enums import TicketStatus

    session = SessionLocal()
    try:
        repo = SupportTicketRepository(session)
        closed_count = 0

        # 1. Close resolved tickets older than 7 days
        resolved_tickets = repo.find_resolved_older_than_days(7)
        for ticket in resolved_tickets:
            ticket.change_status(TicketStatus.CLOSED)
            repo.save(ticket)
            closed_count += 1

        # 2. Close stale active tickets older than 30 days
        stale_tickets = repo.find_stale_older_than_days(30)
        for ticket in stale_tickets:
            ticket.change_status(TicketStatus.CLOSED)
            repo.save(ticket)
            closed_count += 1

        session.commit()
        logger.info("Auto-closed %d support tickets", closed_count)
        return closed_count
    except Exception:
        session.rollback()
        logger.exception("Failed to auto-close stale tickets")
        raise
    finally:
        session.close()
```

#### Email Task

| Task | File Path | Description |
|------|-----------|-------------|
| `send_support_ticket_email` | `core/tasks/support_ticket_emails.py` | Send ticket emails with 3 variants |

```python
# core/tasks/support_ticket_emails.py
import logging
from jinja2 import Environment, FileSystemLoader
from core.celery import celery_app
from core.config import settings
from core.email import get_email_service

logger = logging.getLogger(__name__)

_env = Environment(loader=FileSystemLoader("templates/email"))
_env.globals["brand_name"] = settings.BRAND_NAME
_env.globals["frontend_url"] = settings.FRONTEND_URL

@celery_app.task(
    name="core.tasks.support_ticket_emails.send_support_ticket_email",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    retry_backoff=True,
    retry_backoff_max=600,
)
def send_support_ticket_email(
    self,
    to_email: str,
    to_name: str,
    ticket_reference: str,
    ticket_subject: str,
    variant: str,  # "ticket_created" | "response_received" | "ticket_resolved"
    message_body: str = "",
    responder_name: str = "",
):
    try:
        template = _env.get_template(f"support_{variant}.html")
        html = template.render(
            to_name=to_name,
            ticket_reference=ticket_reference,
            ticket_subject=ticket_subject,
            message_body=message_body,
            responder_name=responder_name,
            ticket_url=f"{settings.FRONTEND_URL}/support/tickets",
        )

        subject_map = {
            "ticket_created": f"[{settings.BRAND_NAME}] Ticket {ticket_reference}: {ticket_subject}",
            "response_received": f"[{settings.BRAND_NAME}] New response on {ticket_reference}: {ticket_subject}",
            "ticket_resolved": f"[{settings.BRAND_NAME}] Ticket resolved: {ticket_reference}",
        }
        subject = subject_map.get(variant, f"[{settings.BRAND_NAME}] Support ticket update")

        email_service = get_email_service()
        email_service.send(to_email, subject, html)
        logger.info("Sent %s email for %s to %s", variant, ticket_reference, to_email)
    except Exception as exc:
        logger.exception("Failed to send %s email for %s", variant, ticket_reference)
        raise self.retry(exc=exc)
```

### 4. HTTP Layer

#### Endpoints

**Customer-facing (`/api/v1/my/support-tickets`)**

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| `POST` | `/api/v1/my/support-tickets` | Create support ticket | TECHNICIAN+ |
| `GET` | `/api/v1/my/support-tickets` | List my tickets (paginated) | TECHNICIAN+ |
| `GET` | `/api/v1/my/support-tickets/{id}` | Get ticket detail + messages | TECHNICIAN+ |
| `POST` | `/api/v1/my/support-tickets/{id}/messages` | Add message to ticket | TECHNICIAN+ |
| `POST` | `/api/v1/my/support-tickets/{id}/reopen` | Reopen resolved ticket | TECHNICIAN+ |
| `POST` | `/api/v1/my/support-tickets/{id}/rating` | Submit rating (reserved for F4) | TECHNICIAN+ |

**Super admin (`/api/v1/support-tickets`)**

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| `GET` | `/api/v1/support-tickets` | List all tickets (paginated, filtered) | SUPER_ADMIN |
| `GET` | `/api/v1/support-tickets/{id}` | Get ticket detail + messages | SUPER_ADMIN |
| `POST` | `/api/v1/support-tickets/{id}/messages` | Add platform response | SUPER_ADMIN |
| `PATCH` | `/api/v1/support-tickets/{id}/status` | Change ticket status | SUPER_ADMIN |
| `PATCH` | `/api/v1/support-tickets/{id}/priority` | Change ticket priority | SUPER_ADMIN |
| `GET` | `/api/v1/support-tickets/stats` | Dashboard stats | SUPER_ADMIN |

#### Router Files

| Router | File Path | Prefix |
|--------|-----------|--------|
| Customer router | `adapters/http/api/my/support_router.py` | `/api/v1/my/support-tickets` |
| Super admin router | `adapters/http/api/support/router.py` | `/api/v1/support-tickets` |
| Dependencies | `adapters/http/api/support/dependencies.py` | — |

```python
# adapters/http/api/my/support_router.py (customer-facing, key endpoints)
router = APIRouter(prefix="/api/v1/my/support-tickets", tags=["my-support-tickets"])

@router.post("", status_code=201)
def create_ticket(
    body: CreateTicketRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = CreateTicketCommandHandler(ticket_repo=ticket_repo)
    handler.handle(CreateTicketCommand(
        company_id=current_user.company_id,
        created_by=current_user.id,
        category=body.category,
        subject=body.subject,
        description=body.description,
        ai_conversation_summary=body.ai_conversation_summary,
    ))
    db.commit()

    ticket = handler.created_ticket
    # Send confirmation email to creator
    send_support_ticket_email.delay(
        to_email=current_user.email,
        to_name=current_user.name or current_user.email,
        ticket_reference=ticket.reference,
        ticket_subject=ticket.subject,
        variant="ticket_created",
    )
    # Send notification to support team
    send_support_ticket_email.delay(
        to_email="support@dsmcontrol.com",
        to_name="Support Team",
        ticket_reference=ticket.reference,
        ticket_subject=ticket.subject,
        variant="ticket_created",
    )
    return {"data": _to_response(ticket)}

@router.get("")
def list_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    handler = ListMyTicketsQueryHandler(ticket_repo=ticket_repo)
    tickets, total = handler.handle(ListMyTicketsQuery(
        user_id=current_user.id,
        company_id=current_user.company_id,
        page=page,
        page_size=page_size,
        status=status,
    ))
    return {
        "data": [_to_list_item(t) for t in tickets],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }

@router.get("/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    db: Session = Depends(get_db),
):
    ticket_repo = SupportTicketRepository(db)
    user_repo = UserRepository(db)
    handler = GetTicketDetailQueryHandler(ticket_repo=ticket_repo)
    try:
        detail = handler.handle(GetTicketDetailQuery(
            ticket_id=ticket_id,
            company_id=current_user.company_id,
        ))
    except TicketNotFoundError:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Enrich messages with author info
    author_ids = {m.author_id for m in detail.messages}
    author_ids.add(detail.ticket.created_by)
    users = {u.id: u for u in [user_repo.find_by_id(uid) for uid in author_ids] if u}

    return {"data": _to_detail_response(detail, users)}
```

#### Schemas

```python
# adapters/http/api/support/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CreateTicketRequest(BaseModel):
    category: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    ai_conversation_summary: Optional[str] = None

class AddMessageRequest(BaseModel):
    body: str = Field(..., min_length=1, max_length=10000)

class ChangeStatusRequest(BaseModel):
    status: str = Field(..., min_length=1)

class ChangePriorityRequest(BaseModel):
    priority: str = Field(..., min_length=1)

class TicketListItemResponse(BaseModel):
    id: str
    reference: str
    category: str
    subject: str
    status: str
    priority: str
    has_unread: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

class TicketDetailResponse(BaseModel):
    id: str
    reference: str
    company_id: str
    created_by: str
    created_by_name: Optional[str] = None
    created_by_email: Optional[str] = None
    category: str
    subject: str
    description: str
    status: str
    priority: str
    ai_conversation_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: list["TicketMessageResponse"] = []

class TicketMessageResponse(BaseModel):
    id: str
    author_id: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    body: str
    is_from_platform: bool
    created_at: Optional[datetime] = None

class TicketStatsResponse(BaseModel):
    open: int = 0
    in_progress: int = 0
    waiting_on_customer: int = 0
    resolved: int = 0
    closed: int = 0
    total: int = 0
```

### 5. Frontend Components

#### Component Structure

```
web/app/src/
├── pages/
│   └── support/
│       ├── MyTicketsPage.tsx          # List page with filters/sort
│       ├── TicketDetailPage.tsx       # Detail + conversation thread
│       └── CreateTicketPage.tsx       # Creation form
├── components/
│   └── support/
│       ├── TicketStatusBadge.tsx      # Status pill component
│       ├── AIChatWidget.tsx           # (existing F1) — enable escalation button
│       └── AIChatMessage.tsx          # (existing F1)
├── hooks/
│   └── useTickets.ts                  # (new) List + detail data hooks
└── locales/
    ├── en.ts                          # Add support_ticket.* keys
    └── es.ts                          # Add support_ticket.* keys (Spanish)
```

#### MyTicketsPage.tsx

- Route: `/support/tickets`
- Lists tickets created by the current user
- Columns: reference, subject, category, status (badge), priority, created date, updated date
- Filters: status dropdown
- Sorting: clickable column headers
- Empty state: "No support tickets yet"
- "Create Ticket" button in header

#### TicketDetailPage.tsx

- Route: `/support/tickets/:id`
- Shows ticket info: reference, subject, category, status badge, priority, dates
- Chronological conversation thread (messages)
- Each message: author name, role badge (customer/support), timestamp, body
- Message input at bottom (disabled if ticket is closed)
- "Reopen" button (visible only if status is resolved and within 7 days)
- Back link to list

#### CreateTicketPage.tsx

- Route: `/support/tickets/new`
- Form fields: category (select), subject (text input), description (textarea)
- Categories: Bug Report, Feature Request, Billing, How To, Account Access, Other
- Submit creates ticket and navigates to detail page
- Optional: pre-fill from AI conversation summary (via URL query param)

#### TicketStatusBadge.tsx

- Renders a colored pill/badge for ticket status
- Colors: open=blue, in_progress=yellow, waiting_on_customer=orange, resolved=green, closed=gray

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `core/celery.py` | Add beat entry | Add `auto-close-support-tickets` schedule (every hour) |
| `core/tasks/__init__.py` | Add import | Export `auto_close_stale_tickets` and `send_support_ticket_email` |
| `core/models_registry.py` | Add imports | Import `SupportTicketModel`, `TicketMessageModel` |
| `app.py` | Add routers | Include `support_router` and `my_support_router` |
| `web/app/src/components/help/HelpPanel.tsx` | Add link | "Contact Support" link → `/support/tickets/new` |
| `web/app/src/components/support/AIChatWidget.tsx` | Enable button | Enable "Create support ticket" escalation button → navigate to create page |
| `web/app/src/App.tsx` (or router config) | Add routes | `/support/tickets`, `/support/tickets/new`, `/support/tickets/:id` |
| `web/app/src/locales/en.ts` | Add keys | ~25 `support_ticket.*` i18n keys |
| `web/app/src/locales/es.ts` | Add keys | Same keys in Spanish |
| Navigation sidebar/header | Add link | "Support Tickets" nav item for ADMIN/TECHNICIAN |

#### Email Templates to Create

| Template | File Path | Description |
|----------|-----------|-------------|
| `support_ticket_created.html` | `templates/email/support_ticket_created.html` | Ticket created confirmation |
| `support_response_received.html` | `templates/email/support_response_received.html` | New response notification |
| `support_ticket_resolved.html` | `templates/email/support_ticket_resolved.html` | Ticket resolved notification |

#### Breaking Changes

None — all new tables, endpoints, and routes. No existing functionality is modified.

## State Machine

```
          ┌──────────────────────────────────────────┐
          │                                          │
          ▼                                          │
       [OPEN] ──────► [IN_PROGRESS] ◄──────────┐    │
          │               │    │                │    │
          │               │    │                │    │
          │               ▼    │                │    │
          │    [WAITING_ON_CUSTOMER]─────────────┘    │
          │               │                          │
          │               │                          │
          ▼               ▼                          │
       [RESOLVED] ───────────────────────────────────┘
          │                  (reopen within 7 days)
          │
          ▼
       [CLOSED]  (terminal — auto-close after 7 days resolved
                  or 30 days stale on any active status)
```

**Transition triggers:**
- `OPEN → IN_PROGRESS`: Platform responds (auto on first message)
- `IN_PROGRESS → WAITING_ON_CUSTOMER`: Platform sets status
- `WAITING_ON_CUSTOMER → IN_PROGRESS`: Customer responds (auto on message)
- `* → RESOLVED`: Platform resolves (manual)
- `RESOLVED → OPEN`: Customer reopens (within 7 days)
- `RESOLVED → CLOSED`: Auto-close (7 days) or manual
- `OPEN/IN_PROGRESS/WAITING_ON_CUSTOMER → CLOSED`: Auto-close (30 days stale)

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `support_bc` (existing) | Same BC | New `ticket` subdomain alongside `ai_assistant` |
| `Company` entity | Cross-BC read | FK reference in `support_tickets.company_id` |
| `User` entity | Cross-BC read | FK reference in `created_by`, `author_id`; user enrichment in responses |
| Celery + Redis | Infrastructure | Already running; add beat schedule + email task |
| Brevo | External service | Already integrated via `core/email.py` |
| PostgreSQL sequences | Database | `support_ticket_ref_seq` for reference generation |

## Testing Strategy

| Test Type | Scope | File Path | Priority |
|-----------|-------|-----------|----------|
| Unit | `SupportTicket` entity — create, state transitions, reopen window | `tests/unit/support_bc/ticket/test_entities.py` | High |
| Unit | `TicketMessage` entity — create, validation | Same file | High |
| Unit | `CreateTicketCommandHandler` — creates ticket with reference | `tests/unit/support_bc/ticket/test_create_ticket.py` | High |
| Unit | `AddTicketMessageCommandHandler` — auto-transitions, closed check | `tests/unit/support_bc/ticket/test_add_message.py` | High |
| Unit | `ReopenTicketCommandHandler` — 7-day window, status check | `tests/unit/support_bc/ticket/test_reopen_ticket.py` | High |
| Unit | `ChangeTicketStatusCommandHandler` — valid transitions | `tests/unit/support_bc/ticket/test_change_status.py` | Medium |
| Unit | `auto_close_stale_tickets` — closes correct tickets | `tests/unit/core/test_support_ticket_tasks.py` | High |
| Integration | Customer endpoints — create, list, detail, message, reopen | `tests/integration/test_support_ticket_endpoints.py` | High |
| Integration | Super admin endpoints — list all, change status/priority, message | Same file | High |
| Integration | Auth — EMPLOYEE 403, TECHNICIAN 200, SUPER_ADMIN 200 | Same file | High |
| Integration | Tenant isolation — cross-company access denied | Same file | High |

### Key Test Scenarios

1. **Create ticket:** Verify reference generation (SUP-NNNN format), default status OPEN, default priority MEDIUM
2. **State transitions:** All valid transitions succeed; invalid transitions raise `InvalidTicketTransitionError`
3. **Reopen within window:** Ticket at 6 days resolved → reopen succeeds
4. **Reopen after window:** Ticket at 8 days resolved → `TicketReopenWindowExpiredError`
5. **Auto-transition on message:** Platform responds to OPEN ticket → auto IN_PROGRESS; customer responds to WAITING → auto IN_PROGRESS
6. **Closed ticket rejection:** Cannot add message to CLOSED ticket
7. **Auto-close task:** Resolved tickets >7 days are closed; stale active tickets >30 days are closed; tickets within window are untouched
8. **Tenant isolation:** Company A user cannot see Company B tickets
9. **Role access:** EMPLOYEE gets 403, TECHNICIAN gets 200, ADMIN gets 200, SUPER_ADMIN gets 200 on admin endpoints
10. **Email dispatch:** Create ticket → 2 emails queued (creator + support team); platform response → email to creator

## Implementation Order

1. [ ] Domain: Enums (`TicketStatus`, `TicketPriority`, `TicketCategory`, `VALID_TICKET_TRANSITIONS`)
2. [ ] Domain: Exceptions (`TicketNotFoundError`, `InvalidTicketTransitionError`, `TicketReopenWindowExpiredError`)
3. [ ] Domain: Entities (`SupportTicket`, `TicketMessage`) with factory methods and state machine
4. [ ] Domain: Repository interface (`SupportTicketRepositoryInterface`)
5. [ ] Infrastructure: SQLAlchemy models (`SupportTicketModel`, `TicketMessageModel`)
6. [ ] Infrastructure: Alembic migration (tables + sequence + indexes)
7. [ ] Infrastructure: Repository implementation (`SupportTicketRepository`)
8. [ ] Application: Commands (`CreateTicket`, `AddMessage`, `ChangeStatus`, `ReopenTicket`, `ChangePriority`)
9. [ ] Application: Queries (`ListMyTickets`, `GetTicketDetail`, `ListAllTickets`, `GetTicketStats`)
10. [ ] Infrastructure: Celery auto-close task (`auto_close_stale_tickets`)
11. [ ] Infrastructure: Email task (`send_support_ticket_email`) + 3 Jinja2 templates
12. [ ] HTTP: Schemas (`CreateTicketRequest`, `TicketListItemResponse`, `TicketDetailResponse`, etc.)
13. [ ] HTTP: Customer router (`/my/support-tickets`) — 6 endpoints
14. [ ] HTTP: Super admin router (`/support-tickets`) — 6 endpoints
15. [ ] HTTP: Register routers in `app.py`
16. [ ] Configuration: Celery beat schedule, models registry, task exports
17. [ ] Tests: Unit tests — entities, commands, queries, Celery task
18. [ ] Tests: Integration tests — all endpoints, auth, tenant isolation
19. [ ] Frontend: `TicketStatusBadge` component
20. [ ] Frontend: `useTickets` hook
21. [ ] Frontend: `MyTicketsPage`, `TicketDetailPage`, `CreateTicketPage`
22. [ ] Frontend: Route registration + navigation links
23. [ ] Frontend: i18n keys (en.ts + es.ts)
24. [ ] Collateral: Enable AI chat escalation button, add "Contact Support" to HelpPanel

## Folder Structure (New Files)

```
src/support_bc/ticket/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities.py              # SupportTicket, TicketMessage
│   ├── enums.py                 # TicketStatus, TicketPriority, TicketCategory
│   ├── exceptions.py            # TicketNotFoundError, InvalidTicketTransitionError, TicketReopenWindowExpiredError
│   └── repository.py            # SupportTicketRepositoryInterface (ABC)
├── application/
│   ├── __init__.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── create_ticket.py     # CreateTicketCommand + Handler
│   │   ├── add_message.py       # AddTicketMessageCommand + Handler
│   │   ├── change_status.py     # ChangeTicketStatusCommand + Handler
│   │   ├── reopen_ticket.py     # ReopenTicketCommand + Handler
│   │   └── change_priority.py   # ChangeTicketPriorityCommand + Handler
│   └── queries/
│       ├── __init__.py
│       ├── list_my_tickets.py   # ListMyTicketsQuery + Handler
│       ├── get_ticket_detail.py # GetTicketDetailQuery + Handler
│       ├── list_all_tickets.py  # ListAllTicketsQuery + Handler
│       └── get_ticket_stats.py  # GetTicketStatsQuery + Handler
└── infrastructure/
    ├── __init__.py
    ├── models.py                # SupportTicketModel, TicketMessageModel
    └── repository.py            # SupportTicketRepository

adapters/http/api/
├── my/
│   └── support_router.py       # 6 customer-facing endpoints
└── support/
    ├── __init__.py
    ├── router.py                # 6 super admin endpoints
    ├── dependencies.py          # Repository injection
    └── schemas.py               # Request/response models

core/tasks/
├── support_tickets.py           # auto_close_stale_tickets
└── support_ticket_emails.py     # send_support_ticket_email

templates/email/
├── support_ticket_created.html
├── support_response_received.html
└── support_ticket_resolved.html

web/app/src/
├── pages/support/
│   ├── MyTicketsPage.tsx
│   ├── TicketDetailPage.tsx
│   └── CreateTicketPage.tsx
├── components/support/
│   └── TicketStatusBadge.tsx
└── hooks/
    └── useTickets.ts

tests/
├── unit/support_bc/ticket/
│   ├── __init__.py
│   ├── test_entities.py
│   ├── test_create_ticket.py
│   ├── test_add_message.py
│   ├── test_reopen_ticket.py
│   ├── test_change_status.py
│   └── test_support_ticket_tasks.py
└── integration/
    └── test_support_ticket_endpoints.py
```

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Sequence gaps in reference numbers | Low | Low | PostgreSQL sequences can have gaps on rollback; acceptable for support tickets |
| Email delivery failures | Low | Medium | Celery retry with exponential backoff (3 retries, max 600s) |
| Race condition on auto-close + reopen | Very Low | Medium | Auto-close checks resolved_at timestamp; reopen clears resolved_at — no window for conflict |
| High ticket volume overwhelming support email | Low | Low | Not expected for platform support; can add pagination/batching later |
| Super admin endpoints exposed before F3 UI | Low | Low | Endpoints require SUPER_ADMIN role; no UI to accidentally discover |

## Open Technical Questions

None — all decisions are resolved.
