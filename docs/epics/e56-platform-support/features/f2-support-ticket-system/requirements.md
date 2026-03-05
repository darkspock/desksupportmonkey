# Feature: Support Ticket System

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 2
**Dependencies:** None
**Complexity:** L

## Scope

### Included

- `SupportTicket` entity with full lifecycle state machine (open → in_progress → waiting_on_customer → resolved → closed)
- `TicketMessage` entity for conversation threads
- Human-readable reference numbers (`SUP-NNNN`)
- 6 customer-facing API endpoints (create, list, detail, message, reopen, rating placeholder route reserved for F4)
- Ticket creation from the UI (standalone + pre-filled from AI escalation when F1 is deployed)
- "My Support Tickets" list page with filters and status badges
- Ticket detail page with chronological conversation thread
- Both creator and support team can add messages to tickets
- State transitions: open → in_progress (on support response), waiting_on_customer → in_progress (on customer response), any active → resolved (by support team), resolved → open (reopen within 7 days)
- Auto-close: resolved tickets after 7 days, stale tickets (open/in_progress/waiting_on_customer) after 30 days inactive — Celery beat task
- Email notifications: ticket created (to creator + support@dsmcontrol.com), response received (to other party), ticket resolved (to creator)
- 3 Brevo email templates
- Database migration: `support_tickets`, `ticket_messages` tables with indexes
- Role-based access: ADMIN and TECHNICIAN can create/view/respond; support team endpoints reserved for F3
- Tenant isolation: users only see their own company's tickets
- i18n: all ticket UI text in English and Spanish
- "Contact Support" link added to help panel (E51) footer
- "Support" link added to user menu/navigation for ADMIN/TECHNICIAN

### Excluded (in other features)

- Support team dashboard (F3) — support team responds via F3's dashboard, not this feature's UI
- Satisfaction rating submission (F4) — the rating endpoint is reserved but not implemented
- AI chat widget (F1) — independent feature
- File attachments (future iteration)
- SLA tracking (future iteration)
- In-app notifications via notification_bc (future iteration — email-only in V1)

## User Value

When this feature is complete, admins and technicians can submit support tickets, track their status, and have back-and-forth conversations with the support team — all from within the app. They no longer need to send emails to a black-hole inbox with no visibility into resolution progress.

## Acceptance Criteria

- [ ] Ticket creation form accessible from "Contact Support" button (help panel, user menu)
- [ ] Form fields: category (required, 6 options), subject (required), description (required)
- [ ] Ticket receives auto-generated reference (`SUP-NNNN`)
- [ ] Creator receives email confirmation with ticket details
- [ ] Notification email sent to support@dsmcontrol.com
- [ ] "My Support Tickets" page lists user's tickets with reference, subject, category, status, priority, dates
- [ ] List filterable by status, sortable by columns
- [ ] Ticket detail page shows full conversation thread (chronological)
- [ ] Creator can add messages; messages display with author name, role badge, timestamp
- [ ] New messages trigger email notification to the other party
- [ ] Support team can respond (via F3's dashboard — endpoint exists in F2, UI in F3)
- [ ] State transitions work correctly per the state machine
- [ ] Creator can reopen a resolved ticket within 7 days
- [ ] Reopen after 7 days shows error: "This ticket can no longer be reopened"
- [ ] Celery beat auto-closes resolved tickets after 7 days
- [ ] Celery beat auto-closes stale tickets after 30 days of inactivity
- [ ] Tenant isolation: users cannot see tickets from other companies
- [ ] EMPLOYEE role gets 403 on all support ticket endpoints
- [ ] Badge/indicator shows unread responses from the support team
- [ ] All UI text available in English and Spanish

## Technical Scope

### Entities (owned by this feature)

- `SupportTicket` — full entity with state machine, all fields per epic spec
- `TicketMessage` — conversation message with `is_from_platform` flag

### Entities (used from dependencies)

- None (F2 is independent at the entity level; uses existing `User` and `Company` for FKs)

### Key Components

**Backend — Domain:**
- `src/support_bc/ticket/domain/entities.py` — `SupportTicket`, `TicketMessage` entities
- `src/support_bc/ticket/domain/enums.py` — `TicketStatus`, `TicketPriority`, `TicketCategory` enums
- `src/support_bc/ticket/domain/repository.py` — `SupportTicketRepositoryInterface`

**Backend — Infrastructure:**
- `src/support_bc/ticket/infrastructure/models.py` — SQLAlchemy models
- `src/support_bc/ticket/infrastructure/repository.py` — `SupportTicketRepository`
- Alembic migration: `support_tickets` + `ticket_messages` tables

**Backend — Application:**
- `src/support_bc/ticket/application/commands/` — `CreateTicket`, `AddMessage`, `ChangeStatus`, `ReopenTicket`
- `src/support_bc/ticket/application/queries/` — `ListMyTickets`, `GetTicketDetail`
- Celery beat task: `auto_close_stale_tickets`

**Backend — HTTP:**
- `adapters/http/api/my/support_router.py` — 6 customer-facing endpoints
- `adapters/http/api/support/router.py` — support team endpoints (used by F3, defined here for shared entity access)

**Frontend:**
- `web/app/src/pages/support/MyTicketsPage.tsx` — list page
- `web/app/src/pages/support/TicketDetailPage.tsx` — detail with conversation
- `web/app/src/pages/support/CreateTicketPage.tsx` — creation form
- `web/app/src/components/support/TicketStatusBadge.tsx` — status pill component
- Modify `HelpPanel.tsx` — add "Contact Support" link
- Modify sidebar/navigation — add "Support Tickets" link for ADMIN/TECHNICIAN

**Email:**
- 3 Brevo templates: ticket_created, response_received, ticket_resolved

## Notes

- The support team API endpoints (`/api/v1/support-tickets/*`) are defined as part of F2's backend but the dashboard UI is in F3. This avoids overlapping scope: F2 owns all entities and endpoints, F3 owns the support team UI.
- The `rating` endpoint route is reserved in F2 but the handler is implemented in F4.
- The auto-close Celery beat task runs every hour. It queries for `resolved` tickets older than 7 days and any active ticket with `updated_at` older than 30 days.
- Reference number generation uses a database sequence to ensure uniqueness across concurrent requests.
