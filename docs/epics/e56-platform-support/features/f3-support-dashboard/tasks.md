# Implementation Tasks: F3 — Support Dashboard

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-04
**Total Tasks:** 14
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Backend — Domain Interface | 1 | S |
| Backend — Infrastructure Repository | 1 | S |
| Backend — Application Query | 1 | S |
| Backend — HTTP Schema | 1 | S |
| Backend — HTTP Router | 1 | M |
| Backend — Tests | 1 | M |
| Frontend — Hooks | 1 | M |
| Frontend — SupportDashboardPage | 1 | L |
| Frontend — SupportTicketDetailPage | 1 | L |
| Frontend — Routes + Navigation | 1 | S |
| Frontend — i18n | 1 | S |
| Frontend — Missing i18n Keys (F2) | 1 | S |
| Verification | 1 | S |
| Final Checklist | 1 | S |

---

## Phase 1: Backend — Domain Layer

### TASK-001: Add Parameters to Repository Interface `find_all()`

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add `company_id`, `sort_by`, and `sort_order` optional parameters to the `find_all()` abstract method in the repository interface.

**File:** `src/support_bc/ticket/domain/repository.py`

**Implementation:**
```python
@abstractmethod
def find_all(
    self,
    page: int,
    page_size: int,
    status: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    company_id: Optional[str] = None,        # NEW
    sort_by: Optional[str] = None,           # NEW
    sort_order: Optional[str] = None,        # NEW
) -> tuple[list[SupportTicket], int]:
    """List all tickets (super admin). Paginated with filters."""
    ...
```

**Acceptance Criteria:**
- [x] `company_id: Optional[str] = None` added
- [x] `sort_by: Optional[str] = None` added
- [x] `sort_order: Optional[str] = None` added
- [x] Backward compatible — all new params have defaults

---

## Phase 2: Backend — Infrastructure Layer

### TASK-002: Implement Company Filter + Sorting in Repository

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Update `find_all()` in the repository implementation to support the new `company_id` filter and `sort_by`/`sort_order` sorting.

**File:** `src/support_bc/ticket/infrastructure/repository.py`

**Implementation:**
In `find_all()`, after existing filters:
```python
if company_id:
    query = query.where(SupportTicketModel.company_id == company_id)

# Sorting — whitelist allowed columns to prevent SQL injection
ALLOWED_SORT_COLUMNS = {
    'reference': SupportTicketModel.reference,
    'subject': SupportTicketModel.subject,
    'status': SupportTicketModel.status,
    'priority': SupportTicketModel.priority,
    'category': SupportTicketModel.category,
    'created_at': SupportTicketModel.created_at,
    'updated_at': SupportTicketModel.updated_at,
}

if sort_by and sort_by in ALLOWED_SORT_COLUMNS:
    col = ALLOWED_SORT_COLUMNS[sort_by]
    query = query.order_by(col.asc() if sort_order == 'asc' else col.desc())
else:
    query = query.order_by(SupportTicketModel.created_at.desc())
```

**Acceptance Criteria:**
- [x] `company_id` filter works when provided
- [x] `sort_by` maps to whitelisted model columns only
- [x] `sort_order` supports `asc` and `desc` (default `desc`)
- [x] Default sort is `created_at DESC` when no `sort_by` provided
- [x] Invalid `sort_by` values are silently ignored (falls back to default)
- [x] Existing behavior unchanged when new params are not passed

---

## Phase 3: Backend — Application Layer

### TASK-003: Update ListAllTicketsQuery with New Parameters

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `company_id`, `sort_by`, and `sort_order` fields to the query dataclass and pass them through to the repository in the handler.

**File:** `src/support_bc/ticket/application/queries/list_all_tickets.py`

**Implementation:**
```python
@dataclass
class ListAllTicketsQuery(Query):
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    search: Optional[str] = None
    company_id: Optional[str] = None    # NEW
    sort_by: Optional[str] = None       # NEW
    sort_order: Optional[str] = None    # NEW
```

Update handler to pass all params:
```python
return self.ticket_repo.find_all(
    page=query.page,
    page_size=query.page_size,
    status=query.status,
    category=query.category,
    priority=query.priority,
    search=query.search,
    company_id=query.company_id,
    sort_by=query.sort_by,
    sort_order=query.sort_order,
)
```

**Acceptance Criteria:**
- [x] 3 new fields added to `ListAllTicketsQuery`
- [x] Handler passes all 3 new params to `find_all()`
- [x] Backward compatible — defaults are `None`

---

## Phase 4: Backend — HTTP Layer

### TASK-004: Add Fields to TicketListItemResponse Schema

**Phase:** HTTP — Schema
**Complexity:** S
**Dependencies:** None

**Description:**
Add `company_id` and `created_by_email` optional fields to `TicketListItemResponse`.

**File:** `adapters/http/api/support/schemas.py`

**Implementation:**
```python
class TicketListItemResponse(BaseModel):
    id: str
    reference: str
    category: str
    subject: str
    status: str
    priority: str
    has_unread: bool = False
    company_id: Optional[str] = None         # NEW
    created_by_email: Optional[str] = None   # NEW
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
```

**Acceptance Criteria:**
- [x] `company_id: Optional[str] = None` added
- [x] `created_by_email: Optional[str] = None` added
- [x] Backward compatible — existing responses still valid

---

### TASK-005: Add Query Params + User Enrichment to List Router

**Phase:** HTTP — Router
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Update the `list_all_tickets()` endpoint to accept `company_id`, `sort_by`, `sort_order` query params. Update `_to_list_item()` to include `company_id` and `created_by_email` by batch-fetching users.

**File:** `adapters/http/api/support/router.py`

**Implementation:**

1. Add query params to `list_all_tickets()`:
```python
@router.get("")
def list_all_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    ticket_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),       # NEW
    sort_by: Optional[str] = Query(None),           # NEW
    sort_order: Optional[str] = Query(None),        # NEW
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
```

2. Pass new params to query handler.

3. After getting tickets, batch-fetch users for the page:
```python
# Enrich list items with creator email
creator_ids = list({t.created_by for t in tickets})
user_repo = UserRepository(db)
users = {u.id: u for u in [user_repo.find_by_id(uid) for uid in creator_ids] if u}
```

4. Update `_to_list_item()` to accept `users` dict parameter:
```python
def _to_list_item(ticket: SupportTicket, users: dict | None = None) -> dict:
    creator = users.get(ticket.created_by) if users else None
    return TicketListItemResponse(
        id=ticket.id,
        reference=ticket.reference,
        category=ticket.category.value,
        subject=ticket.subject,
        status=ticket.status.value,
        priority=ticket.priority.value,
        company_id=ticket.company_id,
        created_by_email=creator.email if creator else None,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    ).model_dump(mode="json")
```

5. Update list call site: `[_to_list_item(t, users) for t in tickets]`

**Acceptance Criteria:**
- [x] `company_id` query param filters by company
- [x] `sort_by` query param controls sort column
- [x] `sort_order` query param controls asc/desc
- [x] List items include `company_id` field
- [x] List items include `created_by_email` from batch-fetched users
- [x] No N+1 queries — users batch-fetched once per page
- [x] Existing behavior unchanged when new params are not provided

---

## Phase 5: Backend — Tests

### TASK-006: Unit + Integration Tests for New Parameters

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Add tests covering the new `company_id`, `sort_by`, `sort_order` functionality.

**Unit tests** — `tests/unit/support_bc/ticket/test_list_all_tickets.py` (NEW):
- Test query handler passes `company_id`, `sort_by`, `sort_order` to repo
- Test query handler works with `None` values (backward compat)

**Integration tests** — Add to `tests/integration/test_support_ticket_endpoints.py`:
- `test_list_all_with_company_filter`: Create tickets for 2 companies, filter by one, verify only matching tickets returned
- `test_list_all_with_sort_by_created_at_asc`: Verify ascending sort
- `test_list_all_with_sort_by_priority`: Verify sort by priority column
- `test_list_all_with_invalid_sort_by`: Verify falls back to default sort
- `test_list_all_response_includes_company_id`: Verify `company_id` in response items
- `test_list_all_response_includes_created_by_email`: Verify `created_by_email` in response items

**Acceptance Criteria:**
- [x] Unit tests for query handler with new params
- [x] Integration test for `company_id` filter
- [x] Integration test for `sort_by` + `sort_order`
- [x] Integration test for invalid `sort_by` fallback
- [x] Integration test for `company_id` in list response
- [x] Integration test for `created_by_email` in list response
- [x] All tests pass (`make test` and `make test-integration`)

---

## Phase 6: Frontend — Hooks

### TASK-007: Create useSupportAdmin Hooks

**Phase:** Frontend — Hooks
**Complexity:** M
**Dependencies:** TASK-005 (backend API ready)

**Description:**
Create React Query hooks for the super admin support ticket API (`/support-tickets` not `/my/support-tickets`).

**File:** `web/app/src/hooks/useSupportAdmin.ts` (NEW)

**Implementation:**

Types:
```typescript
export interface SupportAdminTicket {
  id: string;
  reference: string;
  category: string;
  subject: string;
  status: string;
  priority: string;
  has_unread: boolean;
  company_id: string | null;
  created_by_email: string | null;
  created_at: string | null;
  updated_at: string | null;
  resolved_at: string | null;
}

export interface TicketStats {
  open: number;
  in_progress: number;
  waiting_on_customer: number;
  resolved: number;
  closed: number;
  total: number;
}
```

Hooks (6 total):
- `useSupportTickets(params)` — `GET /support-tickets` with page, status, priority, category, search, company_id, sort_by, sort_order
- `useSupportTicketStats()` — `GET /support-tickets/stats`
- `useSupportTicketDetail(ticketId)` — `GET /support-tickets/{id}` (reuse `TicketDetail` type from `useTickets.ts`)
- `useAddPlatformMessage(ticketId)` — `POST /support-tickets/{id}/messages` with cache invalidation
- `useChangeTicketStatus(ticketId)` — `PATCH /support-tickets/{id}/status` with cache invalidation
- `useChangeTicketPriority(ticketId)` — `PATCH /support-tickets/{id}/priority` with cache invalidation

All mutation hooks should invalidate both `support-admin-tickets` and `support-admin-ticket-{id}` queries on success.

**Acceptance Criteria:**
- [x] 6 hooks created
- [x] `useSupportTickets` accepts all filter/sort params as dynamic queryKey
- [x] `useSupportTicketStats` fetches stats
- [x] `useSupportTicketDetail` fetches detail by ID
- [x] `useAddPlatformMessage` sends message + invalidates caches
- [x] `useChangeTicketStatus` changes status + invalidates caches
- [x] `useChangeTicketPriority` changes priority + invalidates caches
- [x] Uses `/support-tickets` base path (not `/my/support-tickets`)
- [x] TypeScript compiles clean

---

## Phase 7: Frontend — Pages

### TASK-008: Create SupportDashboardPage

**Phase:** Frontend — Page
**Complexity:** L
**Dependencies:** TASK-007

**Description:**
Create the main support team dashboard page with summary stats, filters, sortable table, and pagination.

**File:** `web/app/src/pages/support/SupportDashboardPage.tsx` (NEW)

**Features per design:**
- 4 summary stat cards at top: Open, In Progress, Waiting on Customer, Resolved — clickable to filter
- Filter row: status dropdown, priority dropdown, category dropdown
- Search input with debounce (300ms) for subject/reference
- Sortable table with columns: Reference, Company, Creator, Subject, Category, Status, Priority, Created, Updated
- Column headers clickable for sort (toggle asc/desc)
- Row click → navigate to `/platform/support-tickets/{id}`
- Pagination (20/page)
- Empty state when no tickets
- Uses `TicketStatusBadge` from F2 (`../../components/support/TicketStatusBadge`)

**Acceptance Criteria:**
- [x] Summary stat cards show counts from `useSupportTicketStats()`
- [x] Clicking a stat card filters the table by that status
- [x] Status, priority, category dropdown filters work
- [x] Search input debounces and filters by subject/reference
- [x] Table columns are sortable (click header toggles asc/desc)
- [x] Table shows: reference, company_id, created_by_email, subject, category, status badge, priority, created_at, updated_at
- [x] Row click navigates to detail page
- [x] Pagination with page controls
- [x] Empty state displayed when no tickets match
- [x] Reuses `TicketStatusBadge` component
- [x] All text uses i18n keys

---

### TASK-009: Create SupportTicketDetailPage

**Phase:** Frontend — Page
**Complexity:** L
**Dependencies:** TASK-007

**Description:**
Create the support team's ticket detail page with conversation view, response form, and status/priority management.

**File:** `web/app/src/pages/support/SupportTicketDetailPage.tsx` (NEW)

**Features per design:**
- Back link → `/platform/support-tickets`
- Ticket header: reference + subject + status badge
- Metadata: company_id, created_by_email, category
- Priority: dropdown (inline changeable via `useChangeTicketPriority`)
- Description section
- Conversation thread: messages ordered chronologically, customer vs platform styling
- Add response form: textarea + send button (via `useAddPlatformMessage`)
- Status action buttons (context-dependent per current status):
  - From `open`: In Progress, Waiting on Customer, Resolve, Close
  - From `in_progress`: Waiting on Customer, Resolve, Close
  - From `waiting_on_customer`: In Progress, Resolve, Close
  - From `resolved`: Close
  - From `closed`: no actions
- Loading and error states

**Acceptance Criteria:**
- [x] Back link navigates to dashboard
- [x] Ticket metadata displayed: reference, subject, company, creator email, category
- [x] Status badge shown using `TicketStatusBadge`
- [x] Priority dropdown allows changing priority
- [x] Description section rendered
- [x] Conversation thread shows messages with customer/platform distinction
- [x] Add response textarea + send button works
- [x] Status action buttons are context-dependent (only valid transitions shown)
- [x] Status change triggers mutation + page refresh
- [x] Priority change triggers mutation (silent — no notification shown)
- [x] Loading and error states handled
- [x] All text uses i18n keys

---

## Phase 8: Frontend — Configuration

### TASK-010: Add Routes for Dashboard Pages

**Phase:** Frontend — Routing
**Complexity:** S
**Dependencies:** TASK-008, TASK-009

**Description:**
Add lazy-loaded routes for the two dashboard pages and add navigation entry.

**File:** `web/app/src/router.tsx`

Add 2 routes in the super admin section (near existing `overview`, `companies`, `resellers`):
```typescript
const SupportDashboardPage = lazy(() => import('./pages/support/SupportDashboardPage'));
const SupportTicketDetailPage = lazy(() => import('./pages/support/SupportTicketDetailPage'));

// In routes array:
{
  path: 'platform/support-tickets',
  element: <RequireRole roles={['super_admin']}><S><SupportDashboardPage /></S></RequireRole>,
},
{
  path: 'platform/support-tickets/:id',
  element: <RequireRole roles={['super_admin']}><S><SupportTicketDetailPage /></S></RequireRole>,
},
```

**File:** `web/app/src/config/navSections.ts`

Add entry in the "Platform" section (`nav.section_platform`):
```typescript
{ to: '/platform/support-tickets', labelKey: 'nav.platform_support_tickets', roles: ['super_admin'] },
```

**Acceptance Criteria:**
- [x] 2 lazy-loaded routes added for `super_admin` role
- [x] `/platform/support-tickets` loads SupportDashboardPage
- [x] `/platform/support-tickets/:id` loads SupportTicketDetailPage
- [x] Navigation entry added in Platform section
- [x] Route paths use `/platform/support-tickets` prefix (not `/support/tickets`)

---

### TASK-011: Add i18n Keys for Dashboard

**Phase:** Frontend — i18n
**Complexity:** S
**Dependencies:** None

**Description:**
Add all dashboard-specific i18n keys to English and Spanish locale files.

**Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

**Keys to add (35 keys):**

| Key | English | Spanish |
|-----|---------|---------|
| `nav.platform_support_tickets` | Support Tickets | Tickets de Soporte |
| `support_dashboard.title` | Support Tickets | Tickets de Soporte |
| `support_dashboard.subtitle` | Manage support tickets across all companies | Gestiona tickets de soporte de todas las empresas |
| `support_dashboard.stat_open` | Open | Abiertos |
| `support_dashboard.stat_in_progress` | In Progress | En Progreso |
| `support_dashboard.stat_waiting` | Waiting on Customer | Esperando al Cliente |
| `support_dashboard.stat_resolved` | Resolved | Resueltos |
| `support_dashboard.filter_status` | Status | Estado |
| `support_dashboard.filter_priority` | Priority | Prioridad |
| `support_dashboard.filter_category` | Category | Categoría |
| `support_dashboard.filter_all` | All | Todos |
| `support_dashboard.search_placeholder` | Search by subject or reference... | Buscar por asunto o referencia... |
| `support_dashboard.col_reference` | Reference | Referencia |
| `support_dashboard.col_company` | Company | Empresa |
| `support_dashboard.col_creator` | Creator | Creador |
| `support_dashboard.col_subject` | Subject | Asunto |
| `support_dashboard.col_category` | Category | Categoría |
| `support_dashboard.col_status` | Status | Estado |
| `support_dashboard.col_priority` | Priority | Prioridad |
| `support_dashboard.col_created` | Created | Creado |
| `support_dashboard.col_updated` | Updated | Actualizado |
| `support_dashboard.empty` | No support tickets found | No se encontraron tickets de soporte |
| `support_dashboard.back_to_list` | Back to Dashboard | Volver al Panel |
| `support_dashboard.description` | Description | Descripción |
| `support_dashboard.conversation` | Conversation | Conversación |
| `support_dashboard.add_response` | Add Response | Agregar Respuesta |
| `support_dashboard.response_placeholder` | Type your response... | Escribe tu respuesta... |
| `support_dashboard.send_response` | Send Response | Enviar Respuesta |
| `support_dashboard.actions` | Actions | Acciones |
| `support_dashboard.set_in_progress` | Set In Progress | Establecer En Progreso |
| `support_dashboard.set_waiting` | Set Waiting on Customer | Establecer Esperando al Cliente |
| `support_dashboard.resolve` | Resolve | Resolver |
| `support_dashboard.close_ticket` | Close Ticket | Cerrar Ticket |
| `support_dashboard.response_sent` | Response sent | Respuesta enviada |
| `support_dashboard.status_changed` | Status changed | Estado cambiado |
| `support_dashboard.priority_changed` | Priority changed | Prioridad cambiada |

**Acceptance Criteria:**
- [x] All 35 keys added to `en.ts`
- [x] All 35 keys added to `es.ts` with correct Spanish translations
- [x] Keys follow `support_dashboard.*` naming convention
- [x] Nav key follows `nav.*` convention

---

### TASK-012: Fix Missing F2 i18n Keys

**Phase:** Frontend — i18n fix
**Complexity:** S
**Dependencies:** None

**Description:**
Add 16 i18n keys that are referenced by the F2 frontend code but missing from locale files. These were identified during the exploration phase.

**Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

**Keys to add:**

| Key | English | Spanish |
|-----|---------|---------|
| `support_ticket.ai_summary_attached` | AI conversation summary attached | Resumen de conversación con IA adjunto |
| `support_ticket.all_statuses` | All Statuses | Todos los Estados |
| `support_ticket.category_label` | Category | Categoría |
| `support_ticket.closed_notice` | This ticket is closed and cannot receive new messages | Este ticket está cerrado y no puede recibir nuevos mensajes |
| `support_ticket.create_subtitle` | Describe your issue and we'll get back to you | Describe tu problema y te responderemos |
| `support_ticket.created_by` | Created by | Creado por |
| `support_ticket.description_placeholder` | Describe your issue in detail... | Describe tu problema en detalle... |
| `support_ticket.no_messages` | No messages yet | Sin mensajes aún |
| `support_ticket.platform_team` | Support Team | Equipo de Soporte |
| `support_ticket.priority_label` | Priority | Prioridad |
| `support_ticket.resolved_at` | Resolved at | Resuelto el |
| `support_ticket.send_message` | Send Message | Enviar Mensaje |
| `support_ticket.status_label` | Status | Estado |
| `support_ticket.subject_placeholder` | Brief description of your issue | Breve descripción de tu problema |
| `support_ticket.submit` | Submit Ticket | Enviar Ticket |
| `support_ticket.subtitle` | Contact our support team | Contacta a nuestro equipo de soporte |

**Acceptance Criteria:**
- [x] All 16 missing keys added to `en.ts`
- [x] All 16 missing keys added to `es.ts` with correct Spanish translations
- [x] No more missing key warnings in frontend

---

## Phase 9: Verification

### TASK-013: Final Verification

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Run all verification steps to confirm the feature is complete.

**Steps:**
1. `npm run build` — TypeScript compiles clean
2. `make test` — Unit tests pass
3. `make test-integration` — Integration tests pass (if Docker is running)
4. Manual verification: navigate to `/platform/support-tickets` as super_admin

**Acceptance Criteria:**
- [x] TypeScript compiles clean (`tsc --noEmit`)
- [x] Frontend builds without errors (`npm run build`)
- [x] All unit tests pass (`make test`)
- [x] All integration tests pass (`make test-integration`)
- [x] Dashboard page loads and shows ticket table
- [x] Detail page loads and shows ticket conversation

---

## Phase 10: Final Checklist

### TASK-014: Mark Feature Complete

**Phase:** Documentation
**Complexity:** S
**Dependencies:** TASK-013

**Description:**
Update all tracking documents to mark F3 as complete.

**Files:**
- `docs/epics/e56-platform-support/features/f3-support-dashboard/tasks.md` — Mark all checkboxes
- `docs/epics/e56-platform-support/slicing.md` — Mark F3 as "Done"

**Acceptance Criteria:**
- [x] All task checkboxes marked in tasks.md
- [x] F3 marked as "Done" in slicing.md

---

## Dependency Graph

```
TASK-001 (Repo Interface)
    │
    ▼
TASK-002 (Repo Implementation)
    │
    ▼
TASK-003 (Query + Handler)
    │
    ├───────── TASK-004 (Schema) ── independent
    │             │
    ▼             ▼
TASK-005 (Router) ◄────────────┐
    │                           │
    ▼                           │
TASK-006 (Backend Tests)        │
    │                           │
    ▼                           │
TASK-007 (Frontend Hooks) ◄─────┘
    │
    ├──► TASK-008 (Dashboard Page)
    │
    └──► TASK-009 (Detail Page)
              │
              ▼
         TASK-010 (Routes + Nav) ◄── TASK-008
              │
              ▼
         TASK-013 (Verification) ◄── TASK-011, TASK-012
              │
              ▼
         TASK-014 (Mark Complete)

TASK-011 (i18n) ── independent (can be done any time)
TASK-012 (F2 missing keys) ── independent
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-004, TASK-011, TASK-012
> Domain interface change + schema change + i18n keys (all independent)

**Batch 2 (Sequential):** TASK-002, TASK-003, TASK-005
> Repository implementation → Query update → Router update (each depends on previous)

**Batch 3:** TASK-006
> Backend tests (depends on router being complete)

**Batch 4:** TASK-007
> Frontend hooks (depends on backend API being ready)

**Batch 5 (Parallel):** TASK-008, TASK-009
> Dashboard page + Detail page (both depend on hooks, independent of each other)

**Batch 6:** TASK-010
> Routes + navigation (depends on pages existing)

**Batch 7:** TASK-013
> Verification (depends on everything)

**Batch 8:** TASK-014
> Mark complete

## Final Checklist

- [x] All 14 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] TypeScript compiles clean
- [x] Frontend builds successfully
- [x] Dashboard page accessible at `/platform/support-tickets`
- [x] Detail page accessible at `/platform/support-tickets/:id`
- [x] Stat cards, filters, search, sorting, pagination all functional
- [x] Support team can respond, change status, change priority
- [x] All text available in English and Spanish
- [x] F3 marked as Done in slicing.md
