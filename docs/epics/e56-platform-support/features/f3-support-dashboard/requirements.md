# Feature: Support Dashboard

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 3
**Dependencies:** F2
**Complexity:** M

## Scope

### Included

- Support team dashboard page at `/support/tickets` (not `/super-admin/` — the support team has its own section)
- Support team login: support team members use existing SUPER_ADMIN accounts to authenticate; the UI labels this section as "Support" not "Super Admin"
- Table listing all tickets across all companies with: reference, company name, creator email, subject, category, status, priority, created date, last update
- Filters: status, priority, category, company
- Search: by subject or reference number
- Sorting: by any column
- Pagination: 20 per page
- Summary cards at top: open count, in_progress count, resolved count
- Ticket detail view for support team: read ticket + conversation, add response, change status (resolve, close, set waiting_on_customer), change priority
- Priority change: low, medium, high, urgent (internal action — creator not notified)
- Status changes: support team can resolve (from open/in_progress/waiting_on_customer), close (force-close from any active status), set waiting_on_customer
- Dashboard summary stats endpoint: `GET /api/v1/support-tickets/stats`
- "Support Tickets" link in the support team navigation
- i18n: all dashboard text in English and Spanish
- Multiple support team members can log in and manage tickets (not limited to a single person)

### Excluded (in other features)

- Ticket entity and endpoints (F2 — already created)
- Satisfaction rating display on dashboard (F4 — extends this view)
- AI assistant (F1 — independent)
- Ticket assignment to specific support team members (future iteration)
- SLA metrics or response time tracking (future iteration)

## User Value

When this feature is complete, the support team can view, filter, prioritize, and respond to support tickets from all companies in a single dashboard. They can change ticket status, adjust priority, and have conversations with customers — replacing the untracked email inbox with a structured workflow.

## Acceptance Criteria

- [ ] Dashboard page accessible at `/support/tickets` for support team (SUPER_ADMIN role)
- [ ] Support team can log in using existing auth flows (the UI calls this section "Support", not "Super Admin")
- [ ] Multiple support team members can access the dashboard simultaneously
- [ ] Table shows all tickets across all companies with required columns
- [ ] Filters work: status, priority, category, company
- [ ] Search works: by subject text or reference number
- [ ] Columns are sortable
- [ ] Pagination at 20 per page
- [ ] Summary cards show counts: open, in_progress, resolved
- [ ] Clicking a ticket opens the detail view with full conversation
- [ ] Support team can add responses (messages marked as `is_from_platform = true`)
- [ ] Support team can change status to `in_progress`, `waiting_on_customer`, `resolved`, `closed`
- [ ] Resolution requires a message
- [ ] Support team can change priority (low/medium/high/urgent)
- [ ] Priority change is silent — no notification to creator
- [ ] Status changes trigger appropriate email notifications to the creator
- [ ] "Support Tickets" link appears in support team navigation
- [ ] All dashboard text available in English and Spanish

## Technical Scope

### Entities (owned by this feature)

- None — F3 owns no entities. All entities are from F2.

### Entities (used from dependencies)

- `SupportTicket` (from F2)
- `TicketMessage` (from F2)

### Key Components

**Backend:**
- Support team endpoints (already defined in F2's backend, consumed by F3's frontend):
  - `GET /api/v1/support-tickets` — list all tickets (paginated, filterable)
  - `GET /api/v1/support-tickets/{id}` — ticket detail with messages
  - `POST /api/v1/support-tickets/{id}/messages` — add support team response
  - `PATCH /api/v1/support-tickets/{id}/status` — change status
  - `PATCH /api/v1/support-tickets/{id}/priority` — change priority
  - `GET /api/v1/support-tickets/stats` — dashboard summary stats

**Frontend:**
- `web/app/src/pages/support/SupportDashboardPage.tsx` — main dashboard with table, filters, search, summary cards
- `web/app/src/pages/support/SupportTicketDetailPage.tsx` — support team's ticket detail view (respond, change status/priority)
- Modify support team navigation — add "Support Tickets" link
- Shared components from F2 reused where possible (TicketStatusBadge, message display)

## Notes

- The support team uses existing SUPER_ADMIN role for auth. The naming distinction ("Support" vs "Super Admin") is UI-only — no new role is created.
- The support team endpoints are defined in F2's codebase (shared entity access), but the frontend that consumes them is built in F3. This avoids file overlap between features.
- The dashboard stats endpoint returns counts by status and other aggregate data for the summary cards.
- Future iterations may add: ticket assignment to specific team members, SLA metrics, response time tracking, and average satisfaction score (when F4 ships, the rating data becomes available).
