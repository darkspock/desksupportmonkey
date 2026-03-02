# Epic E53 — Request Conversation & Email Notifications

**Date:** 2026-03-02
**Priority:** High
**Status:** Pending
**Bounded Context:** `request_bc` (existing), `notification_bc` (existing)
**Dependencies:** E3 (Service Requests) — Done, E4 (Real-time & Notifications) — Done, E19 (SLA Management) — Done

---

## Business Alignment

### Objective

Transform request comments into a proper bidirectional conversation between technicians and employees, with email notifications and a "waiting for employee" status. Today, comments exist but there is no way to ask the employee a question and track that the ball is in their court — and the employee has no reason to check the app because there are no email notifications.

### KPI Targets

| KPI | Target |
|-----|--------|
| Employee response time | 50% of employee replies within 4 hours of technician message |
| Email open rate | 60%+ of message notification emails opened |
| Reduced back-and-forth | Technicians can set "waiting for employee" to clearly signal who needs to act |
| SLA fairness | Time spent in "waiting for employee" excluded from SLA resolution clock |

### Evidence

- Every major ITSM tool (ServiceNow, Freshdesk, Zendesk, Jira SM) has bidirectional messaging with email notifications
- Current system: technician adds a comment asking for info → employee has no idea unless they check the app → request sits idle → SLA breaches → technician gets blamed
- Email notification with a direct link is the industry standard for keeping non-technical employees engaged
- "Waiting for customer" is a standard ITIL status present in all mature service desk products

---

## Problem Statement

### Current Situation

1. **No email notifications on messages.** When a technician asks the employee a question via comment, the only notification is in-app (WebSocket + notification bell). If the employee doesn't have the app open, they never see it.

2. **No "waiting for employee" status.** The technician has no way to signal that they're blocked on the employee's response. The request stays in `in_progress` and the SLA clock keeps ticking — unfairly penalizing the technician.

3. **Comments are a flat list.** Comments work, but there is no visual distinction between "technician asking a question" and "employee providing info". The conversation is technically bidirectional but feels like a flat log, not a conversation.

4. **No email link to access the request.** Even if we sent emails, there's no mechanism to generate a secure, direct link that takes the employee straight to the request detail.

### Pain Points

| Problem | Impact |
|---------|--------|
| No email on comment | Employees miss technician questions — requests stall |
| No "waiting for employee" status | SLA unfairly counts time waiting for employee response |
| No direct link in email | Even with notifications, the employee has to navigate to find the request |
| No visual conversation flow | Hard to follow the back-and-forth in a flat comment list |

### Who Is Affected

- **Employees:** Don't know when a technician needs more info from them
- **Technicians:** Can't track which requests are blocked on employee response, SLA ticks unfairly
- **Admins:** SLA reports are skewed because "waiting for employee" time is counted as resolution time

---

## Proposed Solution

### Overview

Three changes that work together:

1. **New status: `waiting_for_employee`** — Technician can move a request from `in_progress` → `waiting_for_employee`. When the employee replies (adds a comment), the status auto-transitions back to `in_progress`. SLA clock pauses while in this status.

2. **Email notification on message** — When a comment is added to a request, the other party receives an email with the message content and a direct link to the request. Technician comments → employee gets email. Employee comments → technician gets email (if they have email notifications enabled).

3. **Conversation UX improvements** — Visual distinction between technician messages (left-aligned, brand color) and employee messages (right-aligned, neutral). Timestamp grouping. "Waiting for your reply" banner when status is `waiting_for_employee`.

---

## Feature: New Status — Waiting for Employee

### Status Transition Changes

Current transitions:
```
pending_approval  → submitted, rejected
submitted         → in_review
in_review         → in_progress, rejected
in_progress       → resolved, in_review, rejected
resolved          → in_progress
rejected          → submitted, in_review, in_progress
```

New transitions (additions marked with **→**):
```
pending_approval  → submitted, rejected
submitted         → in_review
in_review         → in_progress, rejected
in_progress       → resolved, in_review, rejected, **waiting_for_employee**
**waiting_for_employee → in_progress, resolved, rejected**
resolved          → in_progress
rejected          → submitted, in_review, in_progress
```

### Rules

- Only a **technician or admin** can move a request to `waiting_for_employee` (not the employee)
- When **any comment is added** to a request in `waiting_for_employee` status, the status **auto-transitions** back to `in_progress` (regardless of who writes it — employee or technician)
- A technician can also manually move it back to `in_progress` without waiting for the employee
- The technician can resolve or reject directly from `waiting_for_employee` (skip back to `in_progress`)

### SLA Impact

- Time spent in `waiting_for_employee` is **excluded** from the SLA resolution time calculation
- The SLA clock **pauses** when entering `waiting_for_employee` and **resumes** when leaving
- This requires a change to the SLA calculation in `sla_bc` — the breach calculation must subtract `waiting_for_employee` duration

#### SLA Tracking Mechanism

Two new fields on the `ServiceRequest` entity:
- `sla_paused_at: Optional[datetime]` — Set to `now()` when status changes to `waiting_for_employee`. Cleared when leaving.
- `sla_paused_total_seconds: int` — Accumulates total paused time across multiple waiting cycles. When leaving `waiting_for_employee`, add `(now - sla_paused_at).total_seconds()` to this field and clear `sla_paused_at`.

The SLA query subtracts `sla_paused_total_seconds` from the elapsed resolution time:
```python
resolution_elapsed = (resolved_at_or_now - created_at).total_seconds() - request.sla_paused_total_seconds
```

This supports multiple `in_progress` → `waiting_for_employee` → `in_progress` cycles correctly.

### User Stories

**US-01:** As a technician, I can change a request status to "waiting for employee", so that the employee knows I need information from them and the SLA clock pauses.

Acceptance Criteria:
- [ ] New status value `waiting_for_employee` added to `RequestStatus` enum
- [ ] Valid transition: `in_progress` → `waiting_for_employee`
- [ ] Only technician/admin can set this status
- [ ] Status change fires `REQUEST_STATUS_CHANGED` event (existing)
- [ ] Status badge rendered in UI with distinct color (e.g., amber/warning)
- [ ] i18n labels: ES "Pendiente del empleado" / EN "Waiting for employee"

**US-02:** As an employee, when I reply to a request in "waiting for employee" status, the status automatically returns to "in progress".

Acceptance Criteria:
- [ ] `AddCommentHandler` checks if request is in `waiting_for_employee` status
- [ ] If yes, any new comment auto-triggers `ChangeRequestStatusCommand` → `in_progress` (regardless of author)
- [ ] Status change event fired for the auto-transition
- [ ] Notification sent to assigned technician: "Employee replied — request is back in progress"

**US-03:** As an admin, I can see SLA reports where "waiting for employee" time is excluded from resolution time.

Acceptance Criteria:
- [ ] SLA breach calculation subtracts total time in `waiting_for_employee` from elapsed resolution time
- [ ] SLA dashboard and per-request SLA status reflect the adjusted time
- [ ] Request event timeline shows clear "clock paused" / "clock resumed" markers

### Domain Changes

#### RequestStatus enum

Add to `src/request_bc/request/domain/enums.py`:
```python
WAITING_FOR_EMPLOYEE = "waiting_for_employee"
```

#### Transition map

Update `VALID_TRANSITIONS` in the ServiceRequest entity:
```python
RequestStatus.IN_PROGRESS: [
    RequestStatus.RESOLVED,
    RequestStatus.IN_REVIEW,
    RequestStatus.REJECTED,
    RequestStatus.WAITING_FOR_EMPLOYEE,  # NEW
],
RequestStatus.WAITING_FOR_EMPLOYEE: [    # NEW
    RequestStatus.IN_PROGRESS,
    RequestStatus.RESOLVED,
    RequestStatus.REJECTED,
],
```

#### Auto-transition on any comment

In the `AddCommentHandler.handle()` method, after saving the comment:
```python
if request.status == RequestStatus.WAITING_FOR_EMPLOYEE:
    request.change_status(RequestStatus.IN_PROGRESS)
    self.request_repo.save(request)
    # Fire status change event
```

Any comment (from any user) on a request in `waiting_for_employee` status triggers the auto-transition back to `in_progress`.

### Database Changes

- Add `waiting_for_employee` to the status check constraint on the `service_requests` table (Alembic migration)
- Add `sla_paused_at` (nullable datetime) and `sla_paused_total_seconds` (integer, default 0) columns to `service_requests`
- No new tables needed

---

## Feature: Email Notifications on Messages

### Overview

When a comment is added to a request, send an email to the other party with:
- Subject: `[DSM-{request_number}] New message on: {request_title}`
- Body: The comment text, who wrote it, and a link to the request
- CTA button: "View Request" → deep link to `https://app.dsmcontrol.com/requests/{request_id}`

### Rules

| Event | Email recipient | Condition |
|-------|----------------|-----------|
| Technician adds comment | Request creator (employee) | Always |
| Technician sets "waiting for employee" | Request creator (employee) | Always — includes the status change message |
| Employee adds comment | Assigned technician | If request has an assigned technician |
| Employee adds comment | Request creator | Never (they wrote it) |

### User Stories

**US-04:** As an employee, I receive an email when a technician adds a comment to my request, so that I know there is a message for me without checking the app.

Acceptance Criteria:
- [ ] Email sent to employee on `REQUEST_COMMENT_ADDED` event when actor is technician
- [ ] Email contains: comment body, technician name/email, request title, request number
- [ ] Email contains a "View Request" button linking to the request detail page
- [ ] Email uses the existing email template system (or a new template if needed)
- [ ] Employee can access the request via the link (authenticated via magic link or session)

**US-05:** As a technician, I receive an email when the employee replies to a request, so that I know the employee has responded.

Acceptance Criteria:
- [ ] Email sent to assigned technician on `REQUEST_COMMENT_ADDED` event when actor is employee
- [ ] Email contains: comment body, employee name/email, request title
- [ ] If no technician assigned, no email is sent (only in-app notification)

**US-06:** As an employee, when a technician sets my request to "waiting for employee", I receive an email telling me the technician needs my input.

Acceptance Criteria:
- [ ] Email sent on status change to `waiting_for_employee`
- [ ] Email subject clearly indicates action required: "Action required: {request_title}"
- [ ] Email body includes the latest technician comment (if one was added at the same time)
- [ ] Email contains "Reply in DSM" button linking to the request

### Technical Design

#### Email Subscriber

Add an `EmailSubscriber` to the event bus in `notification_bc` that listens for:
- `REQUEST_COMMENT_ADDED` — send email to the "other party"
- `REQUEST_STATUS_CHANGED` where new status is `waiting_for_employee` — send email to employee

#### Email Template

New HTML email template `request_message.html`:

```
Subject: [DSM-{number}] {subject_line}

Hi {recipient_name},

{author_name} wrote on request "{request_title}":

---
{comment_body}
---

[View Request]({request_url})

---
DSM Control — IT Service Desk
```

Variant for "waiting for employee":
```
Subject: [DSM-{number}] Action required: {request_title}

Hi {recipient_name},

{technician_name} needs more information on your request "{request_title}".

{comment_body_if_present}

Please reply as soon as possible.

[Reply in DSM]({request_url})

---
DSM Control — IT Service Desk
```

#### Request URL Generation

The email needs a deep link to the request. The URL format is:
```
{FRONTEND_URL}/requests/{request_id}
```

Where `FRONTEND_URL` is the configured frontend URL (e.g., `https://app.dsmcontrol.com`). The employee must be authenticated to view the request — if they're not logged in, the app redirects to login first, then back to the request.

#### Email Sending Infrastructure

The codebase already has email sending via Brevo HTTP API (used for magic link and admin promotion emails):
- Dev: `ConsoleEmailService` (logs to console, no actual email sent)
- Prod: `BrevoEmailService` (HTTP API, requires `BREVO_API_KEY`)

The email subscriber sends via a Celery task to avoid blocking the request handler. Celery task uses retry with exponential backoff (3 attempts: 30s, 2min, 10min). Failures are logged but never block the comment save.

### Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| `notification_bc` | New `EmailSubscriber` for comment/status events | Create subscriber + register in event bus |
| `notification_bc` | Email template for request messages | Create HTML template |
| `core/celery.py` | New Celery task for sending request message emails | Create task |
| `.env` | `FRONTEND_URL` already exists (used for magic links) | Verify it's available to the email template |

---

## Feature: Conversation UX Improvements

### Overview

Update the request detail page to make the comment thread feel like a conversation rather than a flat log.

### User Stories

**US-07:** As a user viewing a request, I can see comments displayed as a conversation with clear visual distinction between technician and employee messages.

Acceptance Criteria:
- [ ] Employee messages aligned right with neutral background (similar to chat bubbles)
- [ ] Technician messages aligned left with brand-colored accent
- [ ] Each message shows author name, role badge (Employee / Technician), and relative timestamp
- [ ] Messages grouped by date (e.g., "Today", "Yesterday", "Feb 28")

**US-08:** As an employee viewing my request in "waiting for employee" status, I see a clear banner telling me the technician needs my response.

Acceptance Criteria:
- [ ] Amber/warning banner at the top of the comment section: "The technician is waiting for your reply"
- [ ] The comment input is visually emphasized (e.g., subtle pulse or highlight border)
- [ ] After the employee submits a reply, the banner disappears and status changes to in_progress

**US-09:** As a technician, when I change a request to "waiting for employee", I can optionally include a message explaining what I need.

Acceptance Criteria:
- [ ] Status change dialog for `waiting_for_employee` includes an optional text field: "What do you need from the employee?"
- [ ] If text is provided, it's saved as a comment before the status change
- [ ] Both the comment and status change are sent in the email notification

### Frontend Changes

| File | Change |
|------|--------|
| `RequestDetailPage.tsx` | Redesign comment section as conversation bubbles |
| `RequestDetailPage.tsx` | Add "waiting for employee" banner |
| `RequestDetailPage.tsx` | Status change dialog with optional message for `waiting_for_employee` |
| `locales/en.ts` + `es.ts` | Add i18n keys for new status, banner, and conversation UI |

---

## Database Migration

Single Alembic migration:

1. **Alter `service_requests.status`** — Add `waiting_for_employee` to the allowed values (update CHECK constraint or enum type)
2. **Add columns** — `sla_paused_at` (nullable datetime) and `sla_paused_total_seconds` (integer, default 0) to `service_requests`
3. No new tables required

---

## i18n Keys

### Spanish
```
request_status.waiting_for_employee: "Pendiente del empleado"
request_detail.waiting_banner: "El técnico está esperando tu respuesta"
request_detail.waiting_message_placeholder: "¿Qué necesitas del empleado?"
request_detail.status_change_waiting: "Marcar como pendiente del empleado"
email.request_message.subject: "[DSM-{number}] Nuevo mensaje en: {title}"
email.request_message.action_required: "[DSM-{number}] Se necesita tu respuesta: {title}"
email.request_message.view_request: "Ver petición"
email.request_message.reply_in_dsm: "Responder en DSM"
```

### English
```
request_status.waiting_for_employee: "Waiting for employee"
request_detail.waiting_banner: "The technician is waiting for your reply"
request_detail.waiting_message_placeholder: "What do you need from the employee?"
request_detail.status_change_waiting: "Mark as waiting for employee"
email.request_message.subject: "[DSM-{number}] New message on: {title}"
email.request_message.action_required: "[DSM-{number}] Your reply needed: {title}"
email.request_message.view_request: "View request"
email.request_message.reply_in_dsm: "Reply in DSM"
```

---

## Collateral Impact (Full)

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| `request_bc/domain/enums.py` | Add `WAITING_FOR_EMPLOYEE` to `RequestStatus` | Modify enum |
| `request_bc/domain/entities.py` | Add transition rules for new status | Update `VALID_TRANSITIONS` |
| `request_bc/application/commands/add_comment.py` | Auto-transition on employee reply | Modify handler |
| `notification_bc` | Email subscriber for comments + status changes | New subscriber |
| `notification_bc` | Email templates (2 variants) | New templates |
| `sla_bc` | Exclude `waiting_for_employee` time from SLA calculation | Modify breach calculation |
| `alembic/` | Migration to add status value | New migration |
| Frontend: `RequestDetailPage.tsx` | Conversation bubbles, waiting banner, status dialog | Modify page |
| Frontend: `locales/en.ts` + `es.ts` | New i18n keys | Add keys |
| `adapters/mcp/tools/requests.py` | `change_request_status` tool already supports any valid status — no change needed | Verify only |
| Frontend: request list filters | Status filter dropdown needs `waiting_for_employee` option | Add to status filter |
| Frontend: dashboard status breakdown | Status pie chart / counts need new category | Verify dynamic generation or add explicitly |
| Frontend: CSV/export | Status column must include new value | Verify |

---

## Testing Requirements

### Unit Tests
- `RequestStatus` transition validation: `in_progress` → `waiting_for_employee` ✓, `submitted` → `waiting_for_employee` ✗
- Auto-transition: any comment on `waiting_for_employee` request → status becomes `in_progress`
- SLA paused fields: entering `waiting_for_employee` sets `sla_paused_at`, leaving accumulates into `sla_paused_total_seconds`
- Email subscriber: comment by technician → email to employee, comment by employee → email to technician
- SLA calculation: request with 2h in `waiting_for_employee` and 4h total → SLA counts 2h

### Integration Tests
- End-to-end: POST comment on request in `waiting_for_employee` by employee → verify status changed + email sent
- End-to-end: PATCH request status to `waiting_for_employee` → verify email sent to employee
- Verify `waiting_for_employee` appears in status badge, request list filters, and dashboard counts

---

## Definition of Done

- [ ] `waiting_for_employee` status added to enum with valid transitions
- [ ] Alembic migration applied
- [ ] Auto-transition on employee reply (comment triggers status change)
- [ ] Email notification on comment (technician → employee, employee → technician)
- [ ] Email notification on status change to `waiting_for_employee`
- [ ] Email template with "View Request" deep link
- [ ] SLA clock pauses during `waiting_for_employee`
- [ ] Conversation UI: chat bubbles with visual distinction
- [ ] "Waiting for your reply" banner in request detail
- [ ] Status change dialog with optional message
- [ ] i18n keys (EN + ES)
- [ ] Unit tests for status transitions, auto-transition, email sending
- [ ] Integration tests for end-to-end flows
- [ ] `waiting_for_employee` appears in request list status filters, dashboard counts, and CSV export
- [ ] `make test` and `make lint` pass

---

## Resolved Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Status name | `waiting_for_employee` | Matches ITIL "waiting for customer" pattern. Clear and unambiguous |
| Auto-transition trigger | Any comment (employee or technician) | Any new message means the conversation is active — status returns to in_progress |
| SLA behavior | Pause clock (exclude time) | Industry standard — unfair to count time when the technician is blocked |
| Email on every comment | Yes, always | Employees rarely check the app proactively. Email is the most reliable channel |
| Email reply-to-ticket | Deferred (future E23 integration) | Replying to the email to add a comment requires email intake (E23). For now, the email links to the app |
| Separate "conversation" entity | No — reuse existing comments | Comments already work. The change is UX + email + status, not data model |
| Comment vs message naming | Keep "comment" in backend, show as "message" in UI | Less migration risk. Frontend labels can say "Message" while the API stays "comment" |
| Comment immutability | Comments are immutable (no edit, no delete) | Intentional for audit trail — every message is permanent |
| SLA tracking mechanism | Fields on ServiceRequest (`sla_paused_at` + `sla_paused_total_seconds`) | Simple, performant, supports multiple waiting cycles |
| Email delivery failures | Celery retry with exponential backoff (3 attempts) | Log failures, never block comment save |
| Email infrastructure | Brevo HTTP API (prod) + ConsoleEmailService (dev) | Existing pattern, uses `FRONTEND_URL` for deep links |

---

## Open Questions

1. **Email frequency throttling:** If there are 5 comments in rapid succession, should we send 5 emails or batch them? Suggest: send each individually for now, add batching later if noise becomes a problem
2. **Email unsubscribe:** Should employees be able to opt out of comment emails? Suggest: not initially — these are critical operational messages, not marketing
3. **Reply by email:** Should employees be able to reply to the notification email and have it added as a comment? This is E23 (multi-channel intake) scope — deferred, but the email should use a Reply-To that's ready for future intake
4. **Multiple "waiting" cycles:** A request can go `in_progress` → `waiting_for_employee` → `in_progress` → `waiting_for_employee` multiple times. SLA must correctly subtract ALL waiting periods. Verify with tests
5. **Waiting timeout:** Should there be an auto-resolve or auto-close if the employee doesn't reply within X days? Suggest: deferred — admin can manually resolve/close
