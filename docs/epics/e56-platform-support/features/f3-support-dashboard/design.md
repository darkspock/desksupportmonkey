# Solution Design: F3 — Support Dashboard

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-04
**Bounded Context:** `support_bc` (reuses F2 entities), frontend-heavy feature

## Summary

F3 is a **frontend-first feature** that builds the support team dashboard UI on top of F2's existing backend endpoints. The backend already provides all 6 super admin endpoints (`GET /api/v1/support-tickets`, `GET /stats`, `GET /{id}`, `POST /{id}/messages`, `PATCH /{id}/status`, `PATCH /{id}/priority`). F3 adds:

1. **Minor backend extension** — add `company_id` filter + `sort_by`/`sort_order` params to the list endpoint, and enrich the list response with `company_id`/`created_by_email`
2. **Frontend** — two new pages (SupportDashboardPage + SupportTicketDetailPage), new hooks for the super admin API, routing, nav, i18n

## Architecture Decision

**Frontend-only with minimal backend augmentation.** The alternative was to create a fully separate backend "dashboard" query with a denormalized response, but this adds unnecessary duplication since F2's endpoints already do everything. The only gaps are the company filter and the list item enrichment — both trivial additions.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Super admin router | `adapters/http/api/support/router.py` | Yes | Add `company_id` filter + `sort_by`/`sort_order` params to list; enrich `_to_list_item` with `company_id`/`created_by_email` |
| Ticket list item schema | `adapters/http/api/support/schemas.py` | Yes | Add `company_id`, `created_by_email` optional fields to `TicketListItemResponse` |
| `ListAllTicketsQuery` | `src/support_bc/ticket/application/queries/list_all_tickets.py` | Yes | Add `company_id`, `sort_by`, `sort_order` fields |
| Repository `find_all` | `src/support_bc/ticket/infrastructure/repository.py` | Yes | Add `company_id` filter + `order_by` support |
| Repository interface | `src/support_bc/ticket/domain/repository.py` | Yes | Add `company_id`, `sort_by`, `sort_order` params to `find_all` |
| `TicketStatusBadge` | `web/app/src/components/support/TicketStatusBadge.tsx` | Yes — reuse directly | None |
| `useTickets.ts` hooks | `web/app/src/hooks/useTickets.ts` | Partially | Add new hooks for super admin API (separate from customer hooks) |
| Router | `web/app/src/router.tsx` | Modify | Add 2 routes for dashboard pages |
| Nav config | `web/app/src/config/navSections.ts` | Modify | Add platform support tickets nav entry |
| Locale files | `web/app/src/locales/{en,es}.ts` | Modify | Add dashboard-specific i18n keys |

## Implementation Plan

### 1. Backend Changes (Minimal)

#### 1.1 Repository Interface — Add Parameters

**File:** `src/support_bc/ticket/domain/repository.py`

Add `company_id`, `sort_by`, `sort_order` to `find_all()`:

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
```

#### 1.2 Repository Implementation — Add Filtering & Sorting

**File:** `src/support_bc/ticket/infrastructure/repository.py`

In `find_all()`:
- Add `company_id` filter: `if company_id: query = query.where(SupportTicketModel.company_id == company_id)`
- Add `sort_by` support: map column names (`reference`, `subject`, `status`, `priority`, `category`, `created_at`, `updated_at`) to model columns, apply `order_by` with `asc`/`desc` based on `sort_order`
- Default sort: `created_at DESC` (existing behavior)
- Allowed `sort_by` values: `reference`, `subject`, `status`, `priority`, `category`, `created_at`, `updated_at`
- Allowed `sort_order` values: `asc`, `desc` (default `desc`)

#### 1.3 Query — Add Parameters

**File:** `src/support_bc/ticket/application/queries/list_all_tickets.py`

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

Pass all params through to repository in handler.

#### 1.4 Schema — Enrich List Item

**File:** `adapters/http/api/support/schemas.py`

Add to `TicketListItemResponse`:
```python
company_id: Optional[str] = None
created_by_email: Optional[str] = None
```

#### 1.5 Router — Add Params & Enrichment

**File:** `adapters/http/api/support/router.py`

In `list_all_tickets()`:
- Add query params: `company_id`, `sort_by`, `sort_order`
- Pass to query handler
- Enrich list items with `company_id` and `created_by_email` (batch-fetch users for the page)

Update `_to_list_item()` to accept optional `users` dict and populate `company_id` and `created_by_email`.

### 2. Frontend — New Hooks

#### 2.1 Support Admin Hooks

**File:** `web/app/src/hooks/useSupportAdmin.ts` (NEW)

Separate hooks for the super admin API (`/support-tickets` not `/my/support-tickets`):

```typescript
// Types
interface SupportAdminTicket extends SupportTicket {
  company_id: string | null;
  created_by_email: string | null;
}

interface TicketStats {
  open: number;
  in_progress: number;
  waiting_on_customer: number;
  resolved: number;
  closed: number;
  total: number;
}

// Hooks
useSupportTickets(params: {
  page: number;
  status?: string;
  priority?: string;
  category?: string;
  search?: string;
  company_id?: string;
  sort_by?: string;
  sort_order?: string;
})

useSupportTicketStats()

useSupportTicketDetail(ticketId: string)

useAddPlatformMessage(ticketId: string)

useChangeTicketStatus(ticketId: string)

useChangeTicketPriority(ticketId: string)
```

### 3. Frontend — Pages

#### 3.1 SupportDashboardPage

**File:** `web/app/src/pages/support/SupportDashboardPage.tsx` (NEW)

Layout:
```
┌────────────────────────────────────────────────────────┐
│ Support Tickets                                        │
│                                                        │
│ ┌──────┐ ┌──────────┐ ┌──────────────────┐ ┌────────┐│
│ │ Open │ │In Progress│ │Waiting on Customer│ │Resolved││
│ │  12  │ │    5     │ │       3          │ │   8    ││
│ └──────┘ └──────────┘ └──────────────────┘ └────────┘│
│                                                        │
│ Filters: [Status ▾] [Priority ▾] [Category ▾]         │
│ Search:  [_______________________________] 🔍          │
│                                                        │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Ref  │ Company │ Creator │ Subject │ Cat │ Status │ ││
│ │──────│─────────│─────────│─────────│─────│────────│ ││
│ │SUP-1 │ Acme    │ j@a.com │ Login.. │ Bug │ Open   │ ││
│ │SUP-2 │ Beta    │ k@b.com │ Billi.. │ Bil │ InProg │ ││
│ └──────────────────────────────────────────────────────┘│
│                           ‹ 1 2 3 ... ›                │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Summary stat cards at top (clickable to filter by that status)
- Dropdowns: status, priority, category
- Text search (subject/reference) with debounce
- Sortable columns (click header to toggle asc/desc)
- Table columns: Reference, Company, Creator Email, Subject, Category, Status, Priority, Created, Updated
- Row click → navigate to `/platform/support-tickets/{id}` (detail page)
- Pagination (20/page)

#### 3.2 SupportTicketDetailPage

**File:** `web/app/src/pages/support/SupportTicketDetailPage.tsx` (NEW)

Layout:
```
┌────────────────────────────────────────────────────────┐
│ ← Back to Dashboard                                    │
│                                                        │
│ SUP-0001 — Login issues                         [Open] │
│ Company: Acme Corp • Creator: john@acme.com            │
│ Category: Bug Report • Priority: [Medium ▾]            │
│                                                        │
│ ┌──────────────────────────────────────────────────────┐│
│ │ Description:                                        ││
│ │ Lorem ipsum dolor sit amet...                       ││
│ └──────────────────────────────────────────────────────┘│
│                                                        │
│ ── Conversation ──────────────────────────────────────  │
│ [Customer] john@acme.com — Mar 2, 2026                 │
│   I can't log in to my account...                      │
│                                                        │
│ [Platform] admin@dsm — Mar 2, 2026                     │
│   We've reset your credentials...                      │
│                                                        │
│ ┌──────────────────────────────────────────────────────┐│
│ │ [Type a response...                        ] [Send] ││
│ └──────────────────────────────────────────────────────┘│
│                                                        │
│ Actions: [Set Waiting] [Resolve] [Close]               │
└────────────────────────────────────────────────────────┘
```

**Features:**
- Back link to dashboard
- Ticket metadata: reference, subject, status badge, company, creator email, category
- Priority dropdown (changeable inline)
- Description section
- Conversation thread (reuse message display pattern from F2's TicketDetailPage)
- Add response form (textarea + send button)
- Status action buttons (context-dependent based on current status):
  - From `open`: In Progress, Waiting on Customer, Resolve, Close
  - From `in_progress`: Waiting on Customer, Resolve, Close
  - From `waiting_on_customer`: In Progress, Resolve, Close
  - From `resolved`: Close
  - From `closed`: (none)
- Status changes trigger email notifications (handled by backend)

### 4. Frontend — Routing

**File:** `web/app/src/router.tsx`

Add 2 routes in the super admin section:
```typescript
{
  path: 'platform/support-tickets',
  element: <RequireRole roles={['super_admin']}><S><SupportDashboardPage /></S></RequireRole>,
},
{
  path: 'platform/support-tickets/:id',
  element: <RequireRole roles={['super_admin']}><S><SupportTicketDetailPage /></S></RequireRole>,
},
```

**Path rationale:** `/platform/support-tickets` (not `/support/tickets`) to distinguish from the customer-facing ticket pages which live at `/support/tickets`. The "platform" prefix groups it with other super admin pages.

### 5. Frontend — Navigation

**File:** `web/app/src/config/navSections.ts`

Add entry in the "Platform" section (alongside overview, companies, resellers):
```typescript
{ to: '/platform/support-tickets', labelKey: 'nav.platform_support_tickets', roles: ['super_admin'] },
```

### 6. Frontend — i18n

**Files:** `web/app/src/locales/en.ts`, `web/app/src/locales/es.ts`

New keys (prefix `support_dashboard.`):
```
nav.platform_support_tickets

support_dashboard.title
support_dashboard.subtitle
support_dashboard.stat_open
support_dashboard.stat_in_progress
support_dashboard.stat_waiting
support_dashboard.stat_resolved
support_dashboard.filter_status
support_dashboard.filter_priority
support_dashboard.filter_category
support_dashboard.filter_all
support_dashboard.search_placeholder
support_dashboard.col_reference
support_dashboard.col_company
support_dashboard.col_creator
support_dashboard.col_subject
support_dashboard.col_category
support_dashboard.col_status
support_dashboard.col_priority
support_dashboard.col_created
support_dashboard.col_updated
support_dashboard.empty
support_dashboard.back_to_list
support_dashboard.description
support_dashboard.conversation
support_dashboard.add_response
support_dashboard.response_placeholder
support_dashboard.send_response
support_dashboard.actions
support_dashboard.set_in_progress
support_dashboard.set_waiting
support_dashboard.resolve
support_dashboard.close_ticket
support_dashboard.change_priority
support_dashboard.response_sent
support_dashboard.status_changed
support_dashboard.priority_changed
support_dashboard.company_label
support_dashboard.creator_label
support_dashboard.category_label
support_dashboard.priority_label
```

### 7. Collateral Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `src/support_bc/ticket/domain/repository.py` | Modify | Add `company_id`, `sort_by`, `sort_order` to `find_all()` |
| `src/support_bc/ticket/infrastructure/repository.py` | Modify | Implement company filter + sorting in `find_all()` |
| `src/support_bc/ticket/application/queries/list_all_tickets.py` | Modify | Add new params to query + handler |
| `adapters/http/api/support/router.py` | Modify | Add query params + user enrichment on list |
| `adapters/http/api/support/schemas.py` | Modify | Add `company_id`, `created_by_email` to list item |
| `web/app/src/router.tsx` | Modify | Add 2 lazy-loaded routes |
| `web/app/src/config/navSections.ts` | Modify | Add platform support tickets nav entry |
| `web/app/src/locales/en.ts` | Modify | Add ~35 dashboard i18n keys |
| `web/app/src/locales/es.ts` | Modify | Add ~35 dashboard i18n keys (Spanish) |

### Breaking Changes

None. All backend changes are additive (new optional params with backward-compatible defaults).

## Database Schema

No new tables or migrations. F3 reuses F2's `support_tickets` and `ticket_messages` tables.

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | Updated query handler (new params) | Medium |
| Unit | Repository `find_all` with company filter + sorting | Medium |
| Integration | List endpoint with company_id, sort_by, sort_order params | High |
| Integration | List response includes company_id + created_by_email | High |
| Frontend | TypeScript compilation | High |

## Implementation Order

1. [ ] Backend: Add params to repository interface
2. [ ] Backend: Implement company filter + sorting in repository
3. [ ] Backend: Update query + handler
4. [ ] Backend: Update schema (list item enrichment)
5. [ ] Backend: Update router (new params + user enrichment)
6. [ ] Backend: Tests (unit + integration for new params)
7. [ ] Frontend: useSupportAdmin hooks
8. [ ] Frontend: SupportDashboardPage
9. [ ] Frontend: SupportTicketDetailPage
10. [ ] Frontend: Routes + navigation
11. [ ] Frontend: i18n (en + es)
12. [ ] Verification: TypeScript compiles, tests pass

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| User enrichment on list (N+1 query) | Medium | Medium | Batch-fetch users for the page results only |
| Sort column SQL injection | Low | High | Whitelist allowed column names in repository |
