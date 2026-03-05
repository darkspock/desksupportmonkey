# Implementation Tasks: F2 — Support Ticket System

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 27
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain — Enums | 1 | S |
| Domain — Exceptions | 1 | S |
| Domain — Entities | 1 | M |
| Domain — Repository Interface | 1 | S |
| Infrastructure — Models | 1 | S |
| Infrastructure — Migration | 1 | S |
| Infrastructure — Repository | 1 | L |
| Application — Commands | 5 | M each |
| Application — Queries | 4 | S-M each |
| Infrastructure — Celery Tasks | 2 | M each |
| Infrastructure — Email Templates | 1 | S |
| HTTP — Schemas | 1 | S |
| HTTP — Customer Router | 1 | L |
| HTTP — Super Admin Router | 1 | L |
| Configuration & Registration | 1 | S |
| Tests — Unit | 2 | M-L |
| Tests — Integration | 1 | L |
| Frontend — Components & Pages | 1 | L |
| Frontend — i18n | 1 | S |
| Collateral — HelpPanel + AIChatWidget | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Create Ticket Enums

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create all ticket enums and the valid transitions map in a single file.

**File:** `src/support_bc/ticket/domain/enums.py`

**Implementation:**
```python
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
    TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
    TicketStatus.IN_PROGRESS: [TicketStatus.WAITING_ON_CUSTOMER, TicketStatus.RESOLVED, TicketStatus.CLOSED],
    TicketStatus.WAITING_ON_CUSTOMER: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
    TicketStatus.RESOLVED: [TicketStatus.OPEN, TicketStatus.CLOSED],
    TicketStatus.CLOSED: [],
}
```

**Also create `__init__.py` files:**
- `src/support_bc/ticket/__init__.py`
- `src/support_bc/ticket/domain/__init__.py`

**Acceptance Criteria:**
- [x] `TicketStatus` with 5 values (open, in_progress, waiting_on_customer, resolved, closed)
- [x] `TicketPriority` with 4 values (low, medium, high, urgent)
- [x] `TicketCategory` with 6 values (bug_report, feature_request, billing, how_to, account_access, other)
- [x] `VALID_TICKET_TRANSITIONS` dict with correct transition map per design
- [x] All enums inherit from `str, Enum`
- [x] Package `__init__.py` files created

---

### TASK-002: Create Ticket Domain Exceptions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create domain-specific exceptions for the ticket subdomain.

**File:** `src/support_bc/ticket/domain/exceptions.py`

**Implementation:**
```python
class TicketNotFoundError(Exception):
    pass

class InvalidTicketTransitionError(Exception):
    pass

class TicketReopenWindowExpiredError(Exception):
    pass
```

**Acceptance Criteria:**
- [x] `TicketNotFoundError` — ticket not found or access denied
- [x] `InvalidTicketTransitionError` — invalid state machine transition
- [x] `TicketReopenWindowExpiredError` — reopen attempted after 7-day window
- [x] All inherit from `Exception`

---

### TASK-003: Create SupportTicket and TicketMessage Entities

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**Description:**
Create the two domain entities with factory methods and state machine logic exactly as specified in the design document.

**File:** `src/support_bc/ticket/domain/entities.py`

**SupportTicket must include:**
- All fields: `id`, `reference`, `company_id`, `created_by`, `category`, `subject`, `description`, `status`, `priority`, `ai_conversation_summary`, `resolved_at`, `closed_at`, `created_at`, `updated_at`
- `REOPEN_WINDOW_DAYS = 7` class constant
- `create()` factory method — validates subject/description not empty, strips whitespace, defaults status to OPEN, priority to MEDIUM, reference to empty string (set by repo)
- `change_status(new_status)` — validates via `VALID_TICKET_TRANSITIONS`, sets `resolved_at` on RESOLVED, `closed_at` on CLOSED
- `reopen()` — validates status is RESOLVED, checks 7-day window from `resolved_at`, resets to OPEN, clears `resolved_at`
- `change_priority(new_priority)` — direct mutation

**TicketMessage must include:**
- All fields: `id`, `ticket_id`, `author_id`, `body`, `is_from_platform`, `created_at`
- `create()` factory method — validates body not empty, strips whitespace, defaults `is_from_platform` to False

**Acceptance Criteria:**
- [x] `SupportTicket` dataclass with all fields from design
- [x] `SupportTicket.create()` with validation (empty subject/description → ValueError)
- [x] `SupportTicket.change_status()` with `VALID_TICKET_TRANSITIONS` enforcement
- [x] `SupportTicket.change_status()` sets `resolved_at` when transitioning to RESOLVED
- [x] `SupportTicket.change_status()` sets `closed_at` when transitioning to CLOSED
- [x] `SupportTicket.reopen()` validates RESOLVED status + 7-day window
- [x] `SupportTicket.reopen()` resets status to OPEN and clears `resolved_at`
- [x] `SupportTicket.change_priority()` mutates priority
- [x] `TicketMessage` dataclass with all fields from design
- [x] `TicketMessage.create()` with validation (empty body → ValueError)
- [x] Uses ULID for ID generation

---

### TASK-004: Create SupportTicketRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Create the repository interface (port) in the domain layer with all methods specified in the design.

**File:** `src/support_bc/ticket/domain/repository.py`

**Methods (exactly as in design):**
- `save(ticket: SupportTicket) -> SupportTicket` — insert or update; on insert, assigns reference via sequence
- `find_by_id(ticket_id: str, company_id: str) -> Optional[SupportTicket]` — company-scoped
- `find_by_id_any_company(ticket_id: str) -> Optional[SupportTicket]` — for super admin
- `find_all(page, page_size, status?, category?, priority?, search?) -> tuple[list[SupportTicket], int]` — super admin list
- `find_by_company(company_id, page, page_size, status?, category?) -> tuple[list[SupportTicket], int]` — company list
- `find_by_created_by(user_id, company_id, page, page_size, status?) -> tuple[list[SupportTicket], int]` — user's tickets
- `find_resolved_older_than_days(days: int) -> list[SupportTicket]` — for auto-close
- `find_stale_older_than_days(days: int) -> list[SupportTicket]` — for auto-close
- `save_message(message: TicketMessage) -> TicketMessage`
- `find_messages(ticket_id: str) -> list[TicketMessage]` — ordered by created_at ASC
- `has_unread_platform_messages(ticket_id: str, last_read_at?) -> bool`
- `count_by_status() -> dict[str, int]` — for super admin dashboard stats

**Acceptance Criteria:**
- [x] ABC class with all 12 abstract methods from design
- [x] Uses domain entities in signatures (not models)
- [x] Proper type hints with `Optional` and `tuple`

---

## Phase 2: Infrastructure Layer

### TASK-005: Create SQLAlchemy Models

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create SQLAlchemy 2.0 models for `support_tickets` and `ticket_messages` tables.

**File:** `src/support_bc/ticket/infrastructure/models.py`

**Also create `__init__.py` files:**
- `src/support_bc/ticket/infrastructure/__init__.py`

**SupportTicketModel:**
- Inherits `ULIDMixin`, `TimestampMixin`, `Base`
- Table: `support_tickets`
- Columns: `reference` (String 20, unique), `company_id` (FK companies.id), `created_by` (FK users.id), `category` (String 30), `subject` (String 255), `description` (Text), `status` (String 30, default "open"), `priority` (String 20, default "medium"), `ai_conversation_summary` (Text, nullable), `resolved_at` (DateTime TZ, nullable), `closed_at` (DateTime TZ, nullable)
- Indexes: `(company_id, status)`, `(company_id, created_by)`, `(status, priority)`

**TicketMessageModel:**
- Inherits `ULIDMixin`, `Base`
- Table: `ticket_messages`
- Columns: `ticket_id` (FK support_tickets.id), `author_id` (FK users.id), `body` (Text), `is_from_platform` (Boolean, default false), `created_at` (DateTime TZ, default now())
- Index: `(ticket_id)`

**Acceptance Criteria:**
- [x] SQLAlchemy 2.0 style: `Mapped[]` + `mapped_column()`
- [x] All columns, types, and defaults match design DDL
- [x] All 3 indexes on `SupportTicketModel`
- [x] 1 index on `TicketMessageModel`
- [x] Foreign keys to `companies`, `users`, `support_tickets`

---

### TASK-006: Create Alembic Migration

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Generate Alembic migration for `support_tickets` and `ticket_messages` tables, including the `support_ticket_ref_seq` PostgreSQL sequence.

**File:** `alembic/versions/XXX_create_support_ticket_tables.py`

**Must include:**
1. `CREATE SEQUENCE support_ticket_ref_seq START 1;`
2. `support_tickets` table with all columns, FKs, defaults
3. `ticket_messages` table with all columns, FKs, defaults
4. All indexes from design
5. Reversible `downgrade()` — drop tables + sequence

**Run:** `make db-migrate` to auto-generate, then verify/adjust to include the sequence.

**Acceptance Criteria:**
- [x] Migration creates `support_ticket_ref_seq` sequence
- [x] Migration creates `support_tickets` table with all columns
- [x] Migration creates `ticket_messages` table with all columns
- [x] All indexes created
- [x] `downgrade()` drops tables and sequence
- [x] Migration applies successfully (`make db-upgrade`)

---

### TASK-007: Create SupportTicketRepository

**Phase:** Infrastructure
**Complexity:** L
**Dependencies:** TASK-004, TASK-005

**Description:**
Implement the `SupportTicketRepositoryInterface` with SQLAlchemy. Follow the `RequestRepository` patterns (upsert, `_to_entity`, pagination, filtering).

**File:** `src/support_bc/ticket/infrastructure/repository.py`

**Key implementation details from design:**
- `save()` — upsert pattern: check existing by ID; on insert call `nextval('support_ticket_ref_seq')` for reference; on update only change `status`, `priority`, `resolved_at`, `closed_at`; flush + refresh
- `find_by_id()` — filter by `id` + `company_id`
- `find_by_id_any_company()` — filter by `id` only (no company scoping)
- `find_all()` — paginated with optional filters (status, category, priority, search via `ilike` on subject/reference); order by `created_at DESC`
- `find_by_company()` — paginated + filtered by company_id
- `find_by_created_by()` — paginated + filtered by user_id + company_id
- `find_resolved_older_than_days(days)` — status=resolved AND `resolved_at < now() - interval`
- `find_stale_older_than_days(days)` — status in (open, in_progress, waiting_on_customer) AND `updated_at < now() - interval`
- `save_message()` — insert with flush + refresh
- `find_messages(ticket_id)` — ordered by `created_at ASC`
- `has_unread_platform_messages()` — check if `is_from_platform=True` messages exist newer than `last_read_at`
- `count_by_status()` — group by status, return dict
- `_to_entity()` — static method converting model → domain entity
- `_message_to_entity()` — static method converting model → domain `TicketMessage`

**Acceptance Criteria:**
- [x] Implements `SupportTicketRepositoryInterface`
- [x] `save()` does upsert with sequence-based reference generation on insert
- [x] `_to_entity()` correctly maps all fields including enum conversion
- [x] `_message_to_entity()` correctly maps message fields
- [x] All `find_*` methods return domain entities (not models)
- [x] Pagination methods return `(list[Entity], total_count)` tuple
- [x] `find_all()` supports search via `ilike` on subject and reference
- [x] `find_resolved_older_than_days()` and `find_stale_older_than_days()` use correct date arithmetic

---

## Phase 3: Application Layer — Commands

### TASK-008: Create CreateTicketCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create command and handler for ticket creation.

**File:** `src/support_bc/ticket/application/commands/create_ticket.py`

**Also create `__init__.py` files:**
- `src/support_bc/ticket/application/__init__.py`
- `src/support_bc/ticket/application/commands/__init__.py`

**Command fields:** `company_id`, `created_by`, `category`, `subject`, `description`, `ai_conversation_summary` (optional)

**Handler:**
- Constructor: `ticket_repo: SupportTicketRepositoryInterface`
- Result container: `self.created_ticket: SupportTicket | None = None`
- `handle()`: calls `SupportTicket.create()`, then `repo.save()`, stores result in `self.created_ticket`
- Returns `None` (CQRS)

**Acceptance Criteria:**
- [x] `CreateTicketCommand` dataclass extends `Command`
- [x] `CreateTicketCommandHandler` extends `CommandHandler[CreateTicketCommand]`
- [x] Handler stores created ticket in `self.created_ticket` (result container pattern)
- [x] Delegates creation to `SupportTicket.create()` factory
- [x] Saves via repository

---

### TASK-009: Create AddTicketMessageCommand + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create command and handler for adding messages to tickets with auto-status-transition logic.

**File:** `src/support_bc/ticket/application/commands/add_message.py`

**Command fields:** `ticket_id`, `author_id`, `body`, `is_from_platform` (default False), `company_id` (None for super admin)

**Handler logic (from design):**
1. Find ticket — company-scoped if `company_id` set, unscoped if None
2. Raise `TicketNotFoundError` if not found
3. Raise `InvalidTicketTransitionError` if ticket is CLOSED
4. Auto-transition:
   - Platform responds to OPEN ticket → IN_PROGRESS
   - Customer responds to WAITING_ON_CUSTOMER → IN_PROGRESS
5. Save ticket (for status change)
6. Create message via `TicketMessage.create()` and save

**Acceptance Criteria:**
- [x] Company-scoped lookup for regular users, unscoped for super admin
- [x] Raises `TicketNotFoundError` if ticket not found
- [x] Raises `InvalidTicketTransitionError` if ticket is CLOSED
- [x] Auto-transitions OPEN → IN_PROGRESS on platform message
- [x] Auto-transitions WAITING_ON_CUSTOMER → IN_PROGRESS on customer message
- [x] Creates and saves `TicketMessage` entity

---

### TASK-010: Create ChangeTicketStatusCommand + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create command and handler for changing ticket status (super admin operation).

**File:** `src/support_bc/ticket/application/commands/change_status.py`

**Command fields:** `ticket_id`, `new_status`

**Handler:** Finds ticket (unscoped — super admin), calls `ticket.change_status()`, saves.

**Acceptance Criteria:**
- [x] Uses `find_by_id_any_company()` (no company scoping)
- [x] Raises `TicketNotFoundError` if not found
- [x] Delegates to entity's `change_status()` for validation
- [x] Saves updated ticket

---

### TASK-011: Create ReopenTicketCommand + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create command and handler for reopening a resolved ticket (customer operation).

**File:** `src/support_bc/ticket/application/commands/reopen_ticket.py`

**Command fields:** `ticket_id`, `company_id`

**Handler:** Finds ticket (company-scoped), calls `ticket.reopen()`, saves.

**Acceptance Criteria:**
- [x] Uses `find_by_id()` with company scoping (customer operation)
- [x] Raises `TicketNotFoundError` if not found
- [x] Delegates to entity's `reopen()` for validation (status + 7-day window)
- [x] Saves updated ticket

---

### TASK-012: Create ChangeTicketPriorityCommand + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create command and handler for changing ticket priority (super admin operation).

**File:** `src/support_bc/ticket/application/commands/change_priority.py`

**Command fields:** `ticket_id`, `new_priority`

**Handler:** Finds ticket (unscoped — super admin), calls `ticket.change_priority()`, saves.

**Acceptance Criteria:**
- [x] Uses `find_by_id_any_company()` (no company scoping)
- [x] Raises `TicketNotFoundError` if not found
- [x] Delegates to entity's `change_priority()`
- [x] Saves updated ticket

---

## Phase 3: Application Layer — Queries

### TASK-013: Create ListMyTicketsQuery + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create query and handler for listing the current user's tickets.

**File:** `src/support_bc/ticket/application/queries/list_my_tickets.py`

**Also create `__init__.py` files:**
- `src/support_bc/ticket/application/queries/__init__.py`

**Query fields:** `user_id`, `company_id`, `page` (default 1), `page_size` (default 20), `status` (optional)

**Handler:** Delegates to `repo.find_by_created_by()`. Returns `tuple[list[SupportTicket], int]`.

**Acceptance Criteria:**
- [x] `ListMyTicketsQuery` dataclass extends `Query`
- [x] `ListMyTicketsQueryHandler` extends `QueryHandler[ListMyTicketsQuery, tuple]`
- [x] Delegates to repository with all filter params
- [x] Returns `(list[SupportTicket], total_count)`

---

### TASK-014: Create GetTicketDetailQuery + Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create query and handler for fetching ticket detail including messages.

**File:** `src/support_bc/ticket/application/queries/get_ticket_detail.py`

**DTO:** `TicketDetail` dataclass with `ticket: SupportTicket` and `messages: list[TicketMessage]`

**Query fields:** `ticket_id`, `company_id` (None for super admin)

**Handler:**
1. Find ticket — company-scoped or unscoped based on `company_id`
2. Raise `TicketNotFoundError` if not found
3. Fetch messages via `repo.find_messages()`
4. Return `TicketDetail(ticket=ticket, messages=messages)`

**Acceptance Criteria:**
- [x] `TicketDetail` dataclass with ticket + messages
- [x] Company-scoped for regular users, unscoped for super admin
- [x] Raises `TicketNotFoundError` if not found
- [x] Returns ticket with chronological messages

---

### TASK-015: Create ListAllTicketsQuery + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create query and handler for listing all tickets (super admin).

**File:** `src/support_bc/ticket/application/queries/list_all_tickets.py`

**Query fields:** `page`, `page_size`, `status` (optional), `category` (optional), `priority` (optional), `search` (optional)

**Handler:** Delegates to `repo.find_all()`. Returns `tuple[list[SupportTicket], int]`.

**Acceptance Criteria:**
- [x] Supports all filter params from design (status, category, priority, search)
- [x] Delegates to repository
- [x] Returns paginated result tuple

---

### TASK-016: Create GetTicketStatsQuery + Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Create query and handler for dashboard statistics (super admin).

**File:** `src/support_bc/ticket/application/queries/get_ticket_stats.py`

**Query fields:** (none — global stats)

**Handler:** Delegates to `repo.count_by_status()`. Returns `dict[str, int]`.

**Acceptance Criteria:**
- [x] Returns dict with count per status
- [x] Delegates to repository's `count_by_status()`

---

## Phase 4: Infrastructure — Celery Tasks & Email

### TASK-017: Create Auto-Close Celery Task

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-007

**Description:**
Create the Celery beat task that auto-closes resolved and stale tickets.

**File:** `core/tasks/support_tickets.py`

**Implementation (from design):**
- `auto_close_stale_tickets()` decorated with `@celery_app.task`
- Creates `SessionLocal()` session
- Fetches resolved tickets older than 7 days via `find_resolved_older_than_days(7)`
- Fetches stale active tickets older than 30 days via `find_stale_older_than_days(30)`
- Calls `ticket.change_status(TicketStatus.CLOSED)` + `repo.save()` for each
- Commits, logs count
- Rollback on exception, close session in finally

**Acceptance Criteria:**
- [x] Task named `core.tasks.support_tickets.auto_close_stale_tickets`
- [x] Closes resolved tickets > 7 days
- [x] Closes stale active tickets > 30 days
- [x] Proper session lifecycle (commit/rollback/close)
- [x] Logs count of closed tickets
- [x] Re-raises exceptions for Celery error handling

---

### TASK-018: Create Email Task + 3 Jinja2 Templates

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** None (uses existing `core/email.py`)

**Description:**
Create the Celery task for sending support ticket emails and the 3 HTML email templates.

**Files:**
- `core/tasks/support_ticket_emails.py` — Celery task
- `templates/email/support_ticket_created.html`
- `templates/email/support_response_received.html`
- `templates/email/support_ticket_resolved.html`

**Task (from design):**
- `send_support_ticket_email` with `bind=True, max_retries=3, default_retry_delay=30, retry_backoff=True, retry_backoff_max=600`
- Params: `to_email`, `to_name`, `ticket_reference`, `ticket_subject`, `variant`, `message_body`, `responder_name`
- Uses Jinja2 `Environment` with `FileSystemLoader("templates/email")`
- 3 variants: `ticket_created`, `response_received`, `ticket_resolved`
- Subject lines per design's `subject_map`
- Uses `get_email_service().send()`
- Retries on exception

**Templates:** Follow existing `request_comment.html` pattern:
- Responsive, max-width 600px
- System fonts
- Brand name + ticket reference in header
- Color-coded CTAs
- `ticket_created`: Confirmation with ticket details, "View Tickets" button
- `response_received`: Shows responder name + message body in quote block
- `ticket_resolved`: Resolution notice with optional reopen info

**Acceptance Criteria:**
- [x] Celery task with retry + backoff configuration
- [x] Handles all 3 variants with correct subject lines
- [x] Uses `get_email_service()` from `core/email.py`
- [x] 3 HTML templates created following existing template patterns
- [x] Templates render with context vars: `to_name`, `ticket_reference`, `ticket_subject`, `message_body`, `responder_name`, `ticket_url`
- [x] Retry on exception with `self.retry(exc=exc)`

---

## Phase 5: HTTP Layer

### TASK-019: Create HTTP Schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Create Pydantic request/response schemas for the support ticket endpoints.

**File:** `adapters/http/api/support/schemas.py`

**Also create `__init__.py`:**
- `adapters/http/api/support/__init__.py`

**Request schemas:**
- `CreateTicketRequest` — category (required), subject (1-255), description (required), ai_conversation_summary (optional)
- `AddMessageRequest` — body (1-10000)
- `ChangeStatusRequest` — status (required)
- `ChangePriorityRequest` — priority (required)

**Response schemas:**
- `TicketListItemResponse` — id, reference, category, subject, status, priority, has_unread, created_at, updated_at, resolved_at
- `TicketDetailResponse` — all fields + created_by_name/email + messages list
- `TicketMessageResponse` — id, author_id, author_name, author_email, body, is_from_platform, created_at
- `TicketStatsResponse` — count per status + total

**Acceptance Criteria:**
- [x] All request schemas with proper Field validation (min_length, max_length)
- [x] All response schemas with Optional fields where needed
- [x] Schemas match design document exactly

---

### TASK-020: Create Customer-Facing Router

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-008, TASK-009, TASK-011, TASK-013, TASK-014, TASK-018, TASK-019

**Description:**
Create the customer-facing router with 6 endpoints at `/api/v1/my/support-tickets`.

**File:** `adapters/http/api/my/support_router.py`

**Also create:**
- `adapters/http/api/support/dependencies.py` — `get_ticket_repo(db)` dependency

**Endpoints (from design):**

1. `POST /api/v1/my/support-tickets` — Create ticket
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Creates ticket via `CreateTicketCommandHandler`
   - Sends 2 emails: creator confirmation + support@dsmcontrol.com notification
   - Returns `{"data": ticket_response}` with 201

2. `GET /api/v1/my/support-tickets` — List my tickets
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Query params: `page`, `page_size`, `status`
   - Uses `ListMyTicketsQueryHandler`
   - Returns `{"data": [...], "meta": PaginationMeta}`

3. `GET /api/v1/my/support-tickets/{ticket_id}` — Get detail
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Uses `GetTicketDetailQueryHandler` with company scoping
   - Enriches messages with author user info (name, email)
   - Returns `{"data": detail_response}`

4. `POST /api/v1/my/support-tickets/{ticket_id}/messages` — Add message
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Uses `AddTicketMessageCommandHandler` with `is_from_platform=False`
   - Sends `response_received` email to support@dsmcontrol.com
   - Returns 201

5. `POST /api/v1/my/support-tickets/{ticket_id}/reopen` — Reopen
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Uses `ReopenTicketCommandHandler`
   - Maps `TicketReopenWindowExpiredError` → 409
   - Returns refreshed ticket

6. `POST /api/v1/my/support-tickets/{ticket_id}/rating` — Rating placeholder
   - Auth: `require_role(UserRole.TECHNICIAN)`
   - Returns 501 Not Implemented (reserved for F4)

**Helper functions:**
- `_to_response(ticket)` → dict for detail
- `_to_list_item(ticket)` → dict for list
- `_to_detail_response(detail, users_map)` → dict with enriched messages

**Error mapping:**
- `TicketNotFoundError` → 404
- `InvalidTicketTransitionError` → 409
- `TicketReopenWindowExpiredError` → 409
- `ValueError` → 422

**Acceptance Criteria:**
- [x] All 6 endpoints implemented per design
- [x] `require_role(UserRole.TECHNICIAN)` on all endpoints
- [x] Email dispatch on create (2 emails) and add message (1 email)
- [x] User enrichment on detail response (author name/email)
- [x] Proper error mapping to HTTP status codes
- [x] Rating endpoint returns 501 (reserved for F4)
- [x] Uses `PaginationMeta` from `adapters/http/schemas/responses.py`

---

### TASK-021: Create Super Admin Router

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-010, TASK-012, TASK-009, TASK-014, TASK-015, TASK-016, TASK-018, TASK-019

**Description:**
Create the super admin router with 6 endpoints at `/api/v1/support-tickets`.

**File:** `adapters/http/api/support/router.py`

**Endpoints (from design):**

1. `GET /api/v1/support-tickets` — List all tickets
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Query params: `page`, `page_size`, `status`, `category`, `priority`, `search`
   - Uses `ListAllTicketsQueryHandler`
   - Returns `{"data": [...], "meta": PaginationMeta}`

2. `GET /api/v1/support-tickets/stats` — Dashboard stats
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Uses `GetTicketStatsQueryHandler`
   - Returns `{"data": TicketStatsResponse}`
   - **Note:** Must be registered BEFORE `/{id}` to avoid path conflict

3. `GET /api/v1/support-tickets/{ticket_id}` — Get detail
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Uses `GetTicketDetailQueryHandler` with `company_id=None` (unscoped)
   - Enriches with user info

4. `POST /api/v1/support-tickets/{ticket_id}/messages` — Add platform response
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Uses `AddTicketMessageCommandHandler` with `is_from_platform=True`
   - Sends `response_received` email to ticket creator
   - Returns 201

5. `PATCH /api/v1/support-tickets/{ticket_id}/status` — Change status
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Uses `ChangeTicketStatusCommandHandler`
   - If new status is RESOLVED, sends `ticket_resolved` email to creator
   - Returns updated ticket

6. `PATCH /api/v1/support-tickets/{ticket_id}/priority` — Change priority
   - Auth: `require_role(UserRole.SUPER_ADMIN)`
   - Uses `ChangeTicketPriorityCommandHandler`
   - Returns updated ticket

**Acceptance Criteria:**
- [x] All 6 endpoints implemented per design
- [x] `require_role(UserRole.SUPER_ADMIN)` on all endpoints
- [x] `/stats` route registered before `/{id}` to avoid conflict
- [x] Platform messages have `is_from_platform=True`
- [x] Email on response (to creator) and on resolve (to creator)
- [x] Proper error mapping to HTTP status codes

---

## Phase 6: Configuration & Registration

### TASK-022: Register Routers, Beat Schedule, Models, Tasks

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-017, TASK-018, TASK-020, TASK-021

**Description:**
Wire everything together: register routers in `app.py`, add Celery beat schedule, register models, export tasks.

**Files to modify:**

1. **`app.py`** — Add router imports and `include_router()`:
   ```python
   from adapters.http.api.my.support_router import router as my_support_router
   from adapters.http.api.support.router import router as support_router
   application.include_router(my_support_router)
   application.include_router(support_router)
   ```

2. **`core/celery.py`** — Add beat schedule entry:
   ```python
   "auto-close-support-tickets": {
       "task": "core.tasks.support_tickets.auto_close_stale_tickets",
       "schedule": crontab(minute=0),  # Every hour
   },
   ```
   Also add `"core.tasks"` autodiscovery if not already covering new files.

3. **`core/tasks/__init__.py`** — Add imports:
   ```python
   from core.tasks.support_tickets import auto_close_stale_tickets
   from core.tasks.support_ticket_emails import send_support_ticket_email
   ```

4. **`core/models_registry.py`** — Add model imports:
   ```python
   from src.support_bc.ticket.infrastructure.models import SupportTicketModel  # noqa: F401
   from src.support_bc.ticket.infrastructure.models import TicketMessageModel  # noqa: F401
   ```

**Acceptance Criteria:**
- [x] Both routers registered in `app.py`
- [x] Celery beat schedule includes hourly auto-close task
- [x] Task exports in `core/tasks/__init__.py`
- [x] Models registered in `core/models_registry.py`
- [x] Celery autodiscovery covers new task files

---

## Phase 7: Tests

### TASK-023: Unit Tests — Entities + Commands

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-003, TASK-008, TASK-009, TASK-010, TASK-011, TASK-012, TASK-017

**Description:**
Create unit tests for domain entities, all command handlers, and the Celery auto-close task.

**Files:**
- `tests/unit/support_bc/ticket/__init__.py`
- `tests/unit/support_bc/ticket/test_entities.py`
- `tests/unit/support_bc/ticket/test_create_ticket.py`
- `tests/unit/support_bc/ticket/test_add_message.py`
- `tests/unit/support_bc/ticket/test_reopen_ticket.py`
- `tests/unit/support_bc/ticket/test_change_status.py`
- `tests/unit/core/test_support_ticket_tasks.py`

**test_entities.py — Key scenarios:**
- `SupportTicket.create()` with valid input → correct defaults (status=OPEN, priority=MEDIUM)
- `SupportTicket.create()` with empty subject → ValueError
- `SupportTicket.create()` with empty description → ValueError
- `SupportTicket.create()` strips whitespace from subject/description
- `change_status()` valid transitions succeed (test each allowed transition)
- `change_status()` invalid transitions raise `InvalidTicketTransitionError`
- `change_status()` to RESOLVED sets `resolved_at`
- `change_status()` to CLOSED sets `closed_at`
- `reopen()` on RESOLVED within 7 days succeeds → status OPEN, resolved_at None
- `reopen()` on RESOLVED after 7 days → `TicketReopenWindowExpiredError`
- `reopen()` on non-RESOLVED → `InvalidTicketTransitionError`
- `change_priority()` updates priority
- `TicketMessage.create()` with valid input
- `TicketMessage.create()` with empty body → ValueError

**test_create_ticket.py:**
- Handler stores created ticket in `self.created_ticket`
- Repository `save()` is called with correct entity

**test_add_message.py:**
- Platform message on OPEN ticket → auto IN_PROGRESS
- Customer message on WAITING_ON_CUSTOMER → auto IN_PROGRESS
- Message on CLOSED ticket → `InvalidTicketTransitionError`
- Ticket not found → `TicketNotFoundError`

**test_reopen_ticket.py:**
- Reopen within 7 days → success
- Reopen after 7 days → `TicketReopenWindowExpiredError`
- Ticket not found → `TicketNotFoundError`

**test_change_status.py:**
- Valid transition → success
- Ticket not found → `TicketNotFoundError`

**test_support_ticket_tasks.py:**
- Mock `SessionLocal`, `SupportTicketRepository`
- Verify resolved tickets > 7 days are closed
- Verify stale tickets > 30 days are closed
- Verify session commit on success
- Verify session rollback on exception

**Acceptance Criteria:**
- [x] All entity factory method tests (valid + invalid input)
- [x] All state machine transition tests (valid + invalid)
- [x] Reopen window validation tests (within + beyond 7 days)
- [x] All 5 command handler tests
- [x] Celery task tests with mocked session
- [x] All tests pass (`make test`)

---

### TASK-024: Integration Tests — All Endpoints

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-020, TASK-021, TASK-022

**Description:**
Create integration tests for all 12 HTTP endpoints (6 customer + 6 super admin).

**File:** `tests/integration/test_support_ticket_endpoints.py`

**Test scenarios (from design):**

**Customer endpoints:**
1. `POST /my/support-tickets` — 201 creates ticket with SUP-NNNN reference
2. `POST /my/support-tickets` — 422 on missing fields
3. `GET /my/support-tickets` — 200 returns paginated list (only user's tickets)
4. `GET /my/support-tickets` — filter by status works
5. `GET /my/support-tickets/{id}` — 200 returns detail + messages
6. `GET /my/support-tickets/{id}` — 404 for other company's ticket (tenant isolation)
7. `POST /my/support-tickets/{id}/messages` — 201 adds message
8. `POST /my/support-tickets/{id}/messages` — 409 on closed ticket
9. `POST /my/support-tickets/{id}/reopen` — 200 reopens resolved ticket
10. `POST /my/support-tickets/{id}/reopen` — 409 when window expired
11. `POST /my/support-tickets/{id}/rating` — 501 Not Implemented

**Super admin endpoints:**
12. `GET /support-tickets` — 200 lists all tickets cross-company
13. `GET /support-tickets` — filters work (status, category, priority, search)
14. `GET /support-tickets/stats` — 200 returns counts by status
15. `GET /support-tickets/{id}` — 200 returns detail (any company)
16. `POST /support-tickets/{id}/messages` — 201 adds platform message
17. `PATCH /support-tickets/{id}/status` — 200 changes status
18. `PATCH /support-tickets/{id}/status` — 409 on invalid transition
19. `PATCH /support-tickets/{id}/priority` — 200 changes priority

**Auth tests:**
20. All customer endpoints — 401 unauthenticated
21. All customer endpoints — 403 for EMPLOYEE role
22. All super admin endpoints — 403 for TECHNICIAN/ADMIN roles
23. All super admin endpoints — 200 for SUPER_ADMIN role

**Tenant isolation:**
24. User from company A cannot see company B tickets via `/my/support-tickets/{id}`

**Acceptance Criteria:**
- [x] All customer endpoints tested (create, list, detail, message, reopen, rating)
- [x] All super admin endpoints tested (list, stats, detail, message, status, priority)
- [x] Auth tests: 401, 403, 200 for correct roles
- [x] Tenant isolation verified
- [x] Invalid transitions return 409
- [x] Email dispatch mocked/verified
- [x] All tests pass (`make test-integration`)

---

## Phase 8: Frontend

### TASK-025: Create Frontend Pages, Components, and Hooks

**Phase:** Frontend
**Complexity:** L
**Dependencies:** TASK-020 (API must exist)

**Description:**
Create all frontend components for the support ticket system.

**Files to create:**
- `web/app/src/pages/support/MyTicketsPage.tsx`
- `web/app/src/pages/support/TicketDetailPage.tsx`
- `web/app/src/pages/support/CreateTicketPage.tsx`
- `web/app/src/components/support/TicketStatusBadge.tsx`
- `web/app/src/hooks/useTickets.ts`

**MyTicketsPage.tsx (`/support/tickets`):**
- Table listing user's tickets: reference, subject, category, status (badge), priority, created_at, updated_at
- Status filter dropdown (open, in_progress, waiting_on_customer, resolved, closed)
- Sortable column headers
- Pagination
- Empty state: "No support tickets yet"
- "Create Ticket" button → navigates to `/support/tickets/new`

**TicketDetailPage.tsx (`/support/tickets/:id`):**
- Ticket info header: reference, subject, category, status badge, priority, dates
- Chronological conversation thread (messages)
- Each message: author name, role badge (customer/support based on `is_from_platform`), timestamp, body
- Message input at bottom (textarea + send button, disabled if ticket is CLOSED)
- "Reopen" button visible only if status=resolved (call POST `/reopen`, handle 409)
- Back link to list

**CreateTicketPage.tsx (`/support/tickets/new`):**
- Form: category (select with 6 options), subject (text input, max 255), description (textarea)
- All fields required
- Optional: read `ai_summary` query param to pre-fill description
- Submit → POST `/my/support-tickets` → navigate to detail page on success
- Loading + error states

**TicketStatusBadge.tsx:**
- Renders colored pill/badge based on status value
- Colors: open=blue, in_progress=yellow, waiting_on_customer=orange, resolved=green, closed=gray

**useTickets.ts:**
- `useMyTickets(page, pageSize, status?)` — fetches list from `GET /my/support-tickets`
- `useTicketDetail(id)` — fetches detail from `GET /my/support-tickets/{id}`
- `useCreateTicket()` — mutation hook for `POST /my/support-tickets`
- `useAddMessage(ticketId)` — mutation hook for `POST /my/support-tickets/{id}/messages`
- `useReopenTicket(ticketId)` — mutation hook for `POST /my/support-tickets/{id}/reopen`

**Route registration:** Add routes in app router configuration:
- `/support/tickets` → `MyTicketsPage`
- `/support/tickets/new` → `CreateTicketPage`
- `/support/tickets/:id` → `TicketDetailPage`

**Navigation:** Add "Support Tickets" link in sidebar/nav for ADMIN/TECHNICIAN roles.

**Acceptance Criteria:**
- [x] MyTicketsPage with table, filters, pagination, empty state
- [x] TicketDetailPage with conversation thread, message input, reopen button
- [x] CreateTicketPage with validated form and category select
- [x] TicketStatusBadge with correct colors per status
- [x] useTickets hook with all 5 sub-hooks
- [x] Routes registered and navigable
- [x] Navigation link added for ADMIN/TECHNICIAN
- [x] TypeScript compiles clean

---

### TASK-026: Add i18n Keys (English + Spanish)

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None

**Description:**
Add ~25 i18n keys for the support ticket UI to both locale files.

**Files to modify:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys to add (prefix `support_ticket.*`):**
```
support_ticket.title: "Support Tickets" / "Tickets de Soporte"
support_ticket.create: "Create Ticket" / "Crear Ticket"
support_ticket.create_title: "Create Support Ticket" / "Crear Ticket de Soporte"
support_ticket.category: "Category" / "Categoría"
support_ticket.subject: "Subject" / "Asunto"
support_ticket.description: "Description" / "Descripción"
support_ticket.status: "Status" / "Estado"
support_ticket.priority: "Priority" / "Prioridad"
support_ticket.reference: "Reference" / "Referencia"
support_ticket.created_at: "Created" / "Creado"
support_ticket.updated_at: "Updated" / "Actualizado"
support_ticket.empty: "No support tickets yet" / "Aún no hay tickets de soporte"
support_ticket.detail_title: "Ticket Details" / "Detalles del Ticket"
support_ticket.conversation: "Conversation" / "Conversación"
support_ticket.add_message: "Add Message" / "Agregar Mensaje"
support_ticket.message_placeholder: "Type your message..." / "Escribe tu mensaje..."
support_ticket.send: "Send" / "Enviar"
support_ticket.reopen: "Reopen Ticket" / "Reabrir Ticket"
support_ticket.reopen_expired: "This ticket can no longer be reopened" / "Este ticket ya no puede ser reabierto"
support_ticket.created_success: "Ticket created successfully" / "Ticket creado exitosamente"
support_ticket.message_sent: "Message sent" / "Mensaje enviado"
support_ticket.reopened: "Ticket reopened" / "Ticket reabierto"
support_ticket.contact_support: "Contact Support" / "Contactar Soporte"
support_ticket.category_bug_report: "Bug Report" / "Reporte de Error"
support_ticket.category_feature_request: "Feature Request" / "Solicitud de Funcionalidad"
support_ticket.category_billing: "Billing" / "Facturación"
support_ticket.category_how_to: "How To" / "Cómo Hacer"
support_ticket.category_account_access: "Account Access" / "Acceso a Cuenta"
support_ticket.category_other: "Other" / "Otro"
support_ticket.closed_no_messages: "This ticket is closed and cannot receive new messages" / "Este ticket está cerrado y no puede recibir nuevos mensajes"
support_ticket.back_to_list: "Back to tickets" / "Volver a tickets"
```

**Acceptance Criteria:**
- [x] All keys added to `en.ts`
- [x] All keys added to `es.ts` with correct Spanish translations
- [x] Keys follow existing naming convention (`module.key_name`)
- [x] TypeScript compiles clean

---

## Phase 9: Collateral Changes

### TASK-027: Update HelpPanel + AIChatWidget + Navigation

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-025

**Description:**
Update existing components to integrate with the support ticket system.

**Files to modify:**

1. **`web/app/src/components/help/HelpPanel.tsx`**
   - Add "Contact Support" link in the footer section (before email link)
   - Link navigates to `/support/tickets/new`
   - Uses `Ticket` icon from lucide-react
   - Visible for ADMIN/TECHNICIAN roles

2. **`web/app/src/components/support/AIChatWidget.tsx`**
   - Enable the currently disabled "Create support ticket" button
   - On click: close AI chat panel, navigate to `/support/tickets/new?ai_summary=true`
   - Pass AI conversation summary via session storage or query param

**Acceptance Criteria:**
- [x] HelpPanel shows "Contact Support" link for ADMIN/TECHNICIAN
- [x] "Contact Support" navigates to `/support/tickets/new`
- [x] AIChatWidget escalation button is enabled and functional
- [x] Escalation navigates to ticket creation page
- [x] TypeScript compiles clean

---

## Dependency Graph

```
TASK-001 (Enums) ─────────────┐
TASK-002 (Exceptions) ────────┤
                               ├──► TASK-003 (Entities) ──► TASK-004 (Repo Interface) ──┐
                               │                                                         │
TASK-001 ──► TASK-005 (Models) ┤                                                         │
                               │                                                         │
                               ├──► TASK-006 (Migration) ──────────────────────────┐     │
                               │                                                    │     │
                               │    TASK-004 + TASK-005 ──► TASK-007 (Repository) ──┤     │
                               │                                                    │     │
                               │    TASK-004 ──► TASK-008 (CreateTicket Cmd) ───────┤     │
                               │    TASK-004 ──► TASK-009 (AddMessage Cmd) ─────────┤     │
                               │    TASK-004 ──► TASK-010 (ChangeStatus Cmd) ───────┤     │
                               │    TASK-004 ──► TASK-011 (ReopenTicket Cmd) ───────┤     │
                               │    TASK-004 ──► TASK-012 (ChangePriority Cmd) ─────┤     │
                               │    TASK-004 ──► TASK-013 (ListMyTickets Qry) ──────┤     │
                               │    TASK-004 ──► TASK-014 (GetTicketDetail Qry) ────┤     │
                               │    TASK-004 ──► TASK-015 (ListAllTickets Qry) ─────┤     │
                               │    TASK-004 ──► TASK-016 (GetTicketStats Qry) ─────┤     │
                               │                                                    │     │
                               │    TASK-007 ──► TASK-017 (Auto-close Task) ────────┤     │
                               │                 TASK-018 (Email Task) ─────────────┤     │
                               │                 TASK-019 (Schemas) ────────────────┤     │
                               │                                                    │     │
                               │    TASK-008..019 ──► TASK-020 (Customer Router) ───┤     │
                               │    TASK-008..019 ──► TASK-021 (Admin Router) ──────┤     │
                               │                                                    │     │
                               │    TASK-017..021 ──► TASK-022 (Configuration) ─────┤     │
                               │                                                    │     │
                               │    TASK-003..017 ──► TASK-023 (Unit Tests) ────────┤     │
                               │    TASK-020..022 ──► TASK-024 (Integration Tests) ─┤     │
                               │                                                    │     │
                               │    TASK-020 ──► TASK-025 (Frontend) ───────────────┤     │
                               │                 TASK-026 (i18n) ───────────────────┤     │
                               │    TASK-025 ──► TASK-027 (Collateral) ─────────────┘     │
```

## Execution Order

**Batch 1 (Parallel — no dependencies):**
- TASK-001: Enums
- TASK-002: Exceptions
- TASK-018: Email task + templates (depends only on existing `core/email.py`)
- TASK-019: HTTP Schemas
- TASK-026: i18n keys

**Batch 2 (Parallel — depends on Batch 1):**
- TASK-003: Entities (needs TASK-001, TASK-002)
- TASK-005: SQLAlchemy Models (needs TASK-001)

**Batch 3 (Parallel — depends on Batch 2):**
- TASK-004: Repository Interface (needs TASK-003)
- TASK-006: Alembic Migration (needs TASK-005)

**Batch 4 (Parallel — depends on Batch 3):**
- TASK-007: Repository Implementation (needs TASK-004, TASK-005)
- TASK-008: CreateTicketCommand (needs TASK-004)
- TASK-009: AddTicketMessageCommand (needs TASK-004)
- TASK-010: ChangeTicketStatusCommand (needs TASK-004)
- TASK-011: ReopenTicketCommand (needs TASK-004)
- TASK-012: ChangeTicketPriorityCommand (needs TASK-004)
- TASK-013: ListMyTicketsQuery (needs TASK-004)
- TASK-014: GetTicketDetailQuery (needs TASK-004)
- TASK-015: ListAllTicketsQuery (needs TASK-004)
- TASK-016: GetTicketStatsQuery (needs TASK-004)

**Batch 5 (Parallel — depends on Batch 4):**
- TASK-017: Auto-close Celery task (needs TASK-007)
- TASK-020: Customer router (needs TASK-008, 009, 011, 013, 014, 018, 019)
- TASK-021: Super admin router (needs TASK-009, 010, 012, 014, 015, 016, 018, 019)

**Batch 6 (Sequential — depends on Batch 5):**
- TASK-022: Configuration & Registration (needs TASK-017, 018, 020, 021)

**Batch 7 (Parallel — depends on Batch 4-6):**
- TASK-023: Unit tests (needs TASK-003, 008-012, 017)
- TASK-024: Integration tests (needs TASK-020, 021, 022)
- TASK-025: Frontend pages + hooks (needs TASK-020)

**Batch 8 (Sequential — depends on Batch 7):**
- TASK-027: Collateral changes (needs TASK-025)

---

## Final Checklist

- [x] All 27 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] TypeScript compiles clean
- [ ] mypy passes (`make lint`)
- [ ] flake8 passes (`make lint`)
- [x] Migration applies and rolls back cleanly
- [x] Celery beat task runs correctly
- [x] Email templates render correctly
- [x] All acceptance criteria from requirements.md verified
