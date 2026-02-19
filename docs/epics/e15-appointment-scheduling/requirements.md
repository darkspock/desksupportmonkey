# Requirements: E15 - Appointment Scheduling

**Type:** Epic
**Status:** Validated
**Created:** 2026-02-18
**Author:** AI
**Priority:** Medium
**Depends on:** E0 (Foundation), E1 (Company Management), E3 (Service Requests), E4 (Real-time & Notifications), E7 (Frontend)

---

## Business Alignment

**Objective:** Operational efficiency and service quality
**KPI Targets:**
- Reduce average time-to-resolution for on-site support requests by enabling pre-scheduled appointments instead of ad-hoc walk-ups
- Decrease technician idle time between support sessions by providing calendar-based workload visibility (target: 90%+ slot utilization during work hours)
- Reduce missed or double-booked support interactions from 100% untracked to 0% with structured scheduling
- Improve employee satisfaction by giving employees predictable support time windows instead of open-ended "we'll get to it" responses

**Evidence:**
- Service requests (E3) track status but not *when* support will happen — there is no scheduled time commitment between technician and employee
- Technicians work from a queue with no time-based planning — employees have no visibility into when their request will be addressed
- On-site support (desk setup, equipment handoff, troubleshooting) requires physical presence but has no coordination mechanism
- Equipment handoff from procurement (E14) and onboarding requests (E3) would benefit from scheduled delivery/setup times

---

## Problem Statement

### Current Situation

After E3/E12, the request lifecycle assigns technicians to requests and tracks status transitions, but provides no mechanism for scheduling *when* the technician will actually meet with the employee. Technicians work from an unordered queue, and employees receive status updates ("in progress") without knowing when to expect the technician. For tasks requiring physical presence (desk setup, equipment handoff, troubleshooting), both parties resort to informal coordination via email or chat.

### Pain Points

1. **No time commitment** — When a request is assigned to a technician, the employee has no idea when the technician will address it. There is no way to schedule a specific date and time for the support interaction.
2. **No availability visibility** — Technicians have no way to publish their available time slots. There is no calendar view showing when technicians are free or busy.
3. **Double-booking and conflicts** — Without a booking system, technicians may promise overlapping times to different employees, or employees may not be at their desk when the technician arrives.
4. **No reminders** — There is no automated reminder mechanism for upcoming support sessions. Both parties rely on memory, leading to no-shows and wasted trips.
5. **No rescheduling flow** — When conflicts arise (employee out sick, technician delayed), there is no structured way to reschedule. The original time commitment is lost.

### Impact if Not Solved

- Support interactions remain uncoordinated — technicians waste time looking for employees and vice versa
- Employee satisfaction drops because support feels unpredictable
- On-site tasks (equipment delivery, desk setup) are delayed because neither party knows when to be present
- Management has no data on technician scheduling efficiency or support capacity planning

---

## Goals

1. **Appointment booking** — Allow technicians or employees to schedule support appointments linked to service requests, with a specific date, time, and duration.
2. **Technician availability** — Provide a mechanism for technicians to define their available time slots (recurring weekly schedules and one-off overrides) so employees and admins can book within available windows.
3. **Calendar view** — Provide a visual calendar for technicians showing their scheduled appointments, and a simpler view for employees showing their upcoming appointments.
4. **Reminders and notifications** — Send automated reminders before appointments and notify both parties of bookings, cancellations, and reschedules.
5. **Rescheduling and cancellation** — Allow either party to reschedule or cancel appointments with proper notifications and reason tracking.

---

## Validation Decisions (Closed)

1. **Bounded context:** New `appointment_bc` with a single subdomain `appointment`. Appointments are a distinct scheduling concern — they reference requests and users but have their own lifecycle.
2. **Appointment scope:** One appointment links to one service request and involves one technician and one employee. Group appointments or multi-technician sessions are not in scope.
3. **Availability model:** Technicians define recurring weekly availability windows (e.g., "Monday 9:00-12:00, 14:00-17:00") plus one-off date overrides (blocked dates, extra availability). The system computes available slots from this data.
4. **Slot duration:** Appointments have a configurable duration (30, 60, or 90 minutes). Default is 60 minutes. The slot duration is set per appointment, not globally.
5. **Who can book:** Technicians can create appointments for any request assigned to them. Admins can create appointments for any request. Employees can request an appointment for their own open requests (creates a PENDING appointment that the assigned technician must confirm).
6. **Appointment status machine:** `PENDING → CONFIRMED → COMPLETED` with `CANCELLED` and `RESCHEDULED` as terminal/transition states. See status machine in Entities section.
7. **Timezone:** All times stored in UTC. Frontend converts to local timezone for display. Company-level timezone setting is not in scope for this epic (use browser timezone).
8. **Location:** Appointments have an optional `location` text field (e.g., "Building A, Floor 3, Desk 42" or "Remote - Teams link"). No structured location management.
9. **Reminders:** Automated reminders via the existing notification system at 24 hours and 1 hour before the appointment. Implemented as Celery Beat tasks.
10. **Calendar integration:** No external calendar sync (Google Calendar, Outlook) in this epic. Internal calendar view only. External sync is a future enhancement.
11. **Rescheduling:** Rescheduling creates a new appointment linked to the old one (preserving history) and cancels the old one. The new appointment must be confirmed by the other party.
12. **No-show tracking:** After appointment end time passes without being marked as completed, the system marks it as `NO_SHOW` via a Celery Beat task. This is informational — no automatic consequences.

---

## Non-Goals (This Epic)

- External calendar integration (Google Calendar, Outlook, iCal export).
- Recurring appointments (e.g., weekly maintenance check-ins).
- Multi-technician or group appointments.
- Room or resource booking (conference rooms, lab benches).
- Company-level timezone configuration (browser timezone is used).
- Drag-and-drop calendar UI (basic calendar grid with click-to-book is sufficient).
- Appointment templates or pre-filled appointment types.
- SLA integration (appointment scheduling does not affect SLA timers — that's E19).
- Automated technician assignment based on availability (technician must be pre-assigned to the request).

---

## User Stories

### US-E15-001: Book a support appointment
**As a** technician,
**I want to** schedule an appointment with an employee for a service request,
**So that** both parties know exactly when and where the support will happen.

**Acceptance Criteria:**
- [ ] Technician can create an appointment from the request detail page for any request assigned to them.
- [ ] Appointment requires: date, start time, duration (30/60/90 min), and optional location.
- [ ] System validates that the selected time slot does not overlap with the technician's existing appointments.
- [ ] System validates that the selected time does not overlap with the employee's existing appointments.
- [ ] System validates that the selected time falls within the technician's defined availability windows (if availability is set).
- [ ] Appointment is created in `CONFIRMED` status when created by a technician.
- [ ] Employee receives a notification about the scheduled appointment.
- [ ] Appointment appears on both the technician's and employee's calendar views.

### US-E15-002: Define technician availability
**As a** technician,
**I want to** set my available work hours,
**So that** appointments can only be booked during times I'm available.

**Acceptance Criteria:**
- [ ] Technician can define recurring weekly availability (e.g., Mon-Fri 9:00-12:00, 14:00-17:00).
- [ ] Availability windows on the same day must not overlap (system validates and rejects overlapping entries).
- [ ] Technician can add date-specific overrides: blocked dates (vacation, sick day) and extra availability (weekend on-call).
- [ ] Availability is displayed on the technician's calendar view.
- [ ] When booking an appointment, only available slots are shown as selectable.
- [ ] If no availability is configured, all work hours (Mon-Fri 9:00-17:00) are assumed available by default.
- [ ] Admin can view any technician's availability.

### US-E15-003: Employee requests an appointment
**As an** employee,
**I want to** request a support appointment for my open service request,
**So that** I can schedule a convenient time for the technician to help me.

**Acceptance Criteria:**
- [ ] Employee can request an appointment from their request detail page (only for requests in `IN_REVIEW` or `IN_PROGRESS` status with an assigned technician).
- [ ] Employee sees the assigned technician's available time slots.
- [ ] Employee selects a date, time, and optional preferred location.
- [ ] System validates that the selected time does not overlap with the employee's existing appointments.
- [ ] Appointment is created in `PENDING` status and the assigned technician is notified.
- [ ] Technician can confirm (→ `CONFIRMED`) or decline (→ `CANCELLED`) the appointment request.
- [ ] Employee receives notification of confirmation or decline.

### US-E15-004: Calendar view
**As a** technician,
**I want to** see a calendar of my scheduled appointments,
**So that** I can plan my day and avoid conflicts.

**Acceptance Criteria:**
- [ ] Technician calendar shows a week view with appointments displayed as time blocks.
- [ ] Each appointment block shows: employee name, request title (truncated), time, location, and status badge.
- [ ] Calendar highlights available and unavailable time windows.
- [ ] Clicking an appointment navigates to the appointment detail (or expands an inline view).
- [ ] Admin can view any technician's calendar.
- [ ] Employee has a simpler "My Appointments" list view showing upcoming appointments.

### US-E15-005: Appointment reminders
**As a** technician or employee,
**I want to** receive reminders before my appointment,
**So that** I don't forget and can prepare.

**Acceptance Criteria:**
- [ ] Both technician and employee receive a notification 24 hours before the appointment (if appointment is more than 24h away when confirmed).
- [ ] Both parties receive a notification 1 hour before the appointment.
- [ ] Reminders include: appointment time, location, request title, and the other party's name.
- [ ] Reminders are delivered through the existing in-app notification system (and WebSocket push).
- [ ] Cancelled appointments do not trigger reminders.

### US-E15-006: Reschedule and cancel appointments
**As a** technician or employee,
**I want to** reschedule or cancel an appointment,
**So that** I can adjust when conflicts arise.

**Acceptance Criteria:**
- [ ] Technician can cancel a confirmed appointment with a mandatory reason.
- [ ] Employee can cancel a confirmed appointment with a mandatory reason.
- [ ] Cancellation notifies the other party with the reason.
- [ ] Technician can reschedule: system cancels the old appointment and creates a new one in `PENDING` status for the employee to confirm.
- [ ] Employee can request a reschedule: system cancels the old appointment and creates a new one in `PENDING` status for the technician to confirm.
- [ ] Rescheduled appointment references the original appointment ID for history tracking.
- [ ] Appointments in the past cannot be cancelled or rescheduled (only marked as completed or no-show).

### US-E15-007: Complete and track appointments
**As a** technician,
**I want to** mark appointments as completed,
**So that** there is a record of support interactions.

**Acceptance Criteria:**
- [ ] Technician can mark a confirmed appointment as `COMPLETED` after the scheduled time.
- [ ] Completing an appointment records a completion timestamp and optional notes.
- [ ] Appointments not marked as completed within 2 hours after the scheduled end time are auto-marked as `NO_SHOW` by a background task.
- [ ] Appointment history is visible on the request detail page.
- [ ] Dashboard shows appointment statistics: total scheduled, completed, no-shows, cancellations.

---

## Entities

| Entity | Description | States |
|--------|-------------|--------|
| Appointment | Scheduled support session between technician and employee | PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW |
| TechnicianAvailability | Recurring weekly schedule for a technician | (no status — configuration entity) |
| AvailabilityOverride | Date-specific availability changes (blocks or extras) | (no status — configuration entity) |

### State Machine: Appointment

```
Employee requests
      │
      ▼
 ┌─────────┐  confirm   ┌───────────┐  complete  ┌───────────┐
 │ PENDING  │ ─────────> │ CONFIRMED │ ─────────> │ COMPLETED │
 └─────────┘            └───────────┘            └───────────┘
      │                      │
  decline/cancel         cancel│
      │                      │
      ▼                      ▼
 ┌───────────┐          ┌───────────┐
 │ CANCELLED │          │ CANCELLED │
 └───────────┘          └───────────┘

Technician creates directly:
 ┌───────────┐  complete  ┌───────────┐
 │ CONFIRMED │ ─────────> │ COMPLETED │
 └───────────┘            └───────────┘
      │                        ▲
  cancel│                  auto (2h)
      │                        │
      ▼                   ┌──────────┐
 ┌───────────┐            │ NO_SHOW  │
 │ CANCELLED │            └──────────┘
 └───────────┘
```

### State Transitions

| From | To | Trigger | Conditions | Side Effects |
|------|----|---------|------------|--------------|
| PENDING | CONFIRMED | confirm() | Technician confirms employee request | Notifies employee |
| PENDING | CANCELLED | decline() / cancel() | Either party cancels | Mandatory reason. Notifies other party |
| CONFIRMED | COMPLETED | complete() | Technician marks done. Current time >= scheduled start | Records completion timestamp + optional notes |
| CONFIRMED | CANCELLED | cancel() | Either party cancels | Mandatory reason. Notifies other party |
| CONFIRMED | NO_SHOW | auto_no_show() | Celery Beat: 2 hours after end time, still CONFIRMED | Informational. Notifies both parties |

### CRUD Operations

| Entity | Create | Read | Update | Delete | List | Filter | Search |
|--------|--------|------|--------|--------|------|--------|--------|
| Appointment | Yes | Yes | Yes (reschedule = cancel + new) | No (cancel instead) | Yes | status, date range, technician, request | — |
| TechnicianAvailability | Yes (upsert) | Yes | Yes (upsert) | Yes (reset to defaults) | Yes (per technician) | — | — |
| AvailabilityOverride | Yes | Yes | Yes | Yes | Yes (per technician, date range) | — | — |

### Inverse Operations

| Action | Inverse | Notes |
|--------|---------|-------|
| Create appointment | Cancel appointment | Mandatory reason |
| Confirm appointment | Cancel appointment | Before scheduled time |
| Complete appointment | — | Irreversible |
| Block date (override) | Delete override | Restores default availability |

---

## Use Cases

### UC-001: Technician books an appointment

**Actor:** Technician
**Preconditions:** Request is assigned to the technician. Request is in `IN_REVIEW` or `IN_PROGRESS` status.
**Postconditions:** Appointment is created in CONFIRMED status. Employee is notified.

**Main Flow:**
1. Technician opens the request detail page.
2. Clicks "Schedule Appointment".
3. Calendar picker shows technician's available slots for the next 2 weeks.
4. Technician selects a date and time slot.
5. Selects duration (30/60/90 min, default 60).
6. Optionally enters location.
7. Confirms booking.
8. System validates no overlap with existing appointments.
9. Appointment is created as CONFIRMED. Employee receives notification.

**Alternative Flows:**
- A1: Selected time overlaps with existing appointment → validation error, select another time.
- A2: Technician has no availability configured → all Mon-Fri 9:00-17:00 slots are shown.

**Error Scenarios:**
- E1: Request has no assigned technician → booking not available.
- E2: Request is in RESOLVED or REJECTED status → booking not available.

### UC-002: Employee requests an appointment

**Actor:** Employee
**Preconditions:** Request is assigned to a technician. Request is in `IN_REVIEW` or `IN_PROGRESS`.
**Postconditions:** Appointment is created in PENDING status. Technician is notified.

**Main Flow:**
1. Employee opens their request detail page.
2. Clicks "Request Appointment".
3. Sees the assigned technician's available time slots.
4. Selects a preferred date, time, and duration.
5. Optionally enters preferred location.
6. Submits the request.
7. Appointment is created as PENDING. Technician receives notification.
8. Technician confirms or declines.

**Alternative Flows:**
- A1: Technician confirms → appointment moves to CONFIRMED, employee is notified.
- A2: Technician declines → appointment moves to CANCELLED, employee is notified with reason.

**Error Scenarios:**
- E1: No assigned technician → appointment request not available.
- E2: Employee selects a slot that was just taken → validation error, refresh available slots.

### UC-003: Reschedule an appointment

**Actor:** Technician or Employee
**Preconditions:** Appointment is in CONFIRMED status. Appointment is in the future.
**Postconditions:** Old appointment is CANCELLED, new appointment is PENDING.

**Main Flow:**
1. User opens the appointment (from calendar or request detail).
2. Clicks "Reschedule".
3. Selects a new date and time from available slots.
4. Enters a reason for rescheduling.
5. System cancels the old appointment (reason: "Rescheduled") and creates a new PENDING appointment.
6. The other party receives a notification and must confirm the new time.

**Alternative Flows:**
- A1: Other party confirms → new appointment moves to CONFIRMED.
- A2: Other party declines → new appointment is CANCELLED. Both parties are back to no appointment.

### UC-004: Cancel an appointment

**Actor:** Technician or Employee
**Preconditions:** Appointment is in CONFIRMED or PENDING status.
**Postconditions:** Appointment is CANCELLED. Other party is notified.

**Main Flow:**
1. User opens the appointment.
2. Clicks "Cancel Appointment".
3. Enters mandatory cancellation reason.
4. Appointment moves to CANCELLED. Other party receives notification with reason.

**Error Scenarios:**
- E1: Appointment is in the past → cannot cancel (only mark as completed or let auto-no-show handle it).

### UC-005: Automated reminders

**Actor:** System (Celery Beat)
**Preconditions:** Appointment is in CONFIRMED status. Scheduled time is in the future.
**Postconditions:** Both parties receive reminder notifications.

**Main Flow:**
1. Celery Beat runs reminder check task every 15 minutes.
2. For each CONFIRMED appointment:
   - If start time is within 24-25 hours and 24h reminder not yet sent → send 24h reminder to both parties.
   - If start time is within 60-75 minutes and 1h reminder not yet sent → send 1h reminder to both parties.
3. Reminders are delivered via the notification system (in-app + WebSocket push).

**Alternative Flows:**
- A1: Appointment is cancelled before reminder time → no reminder sent.

### UC-006: Auto no-show detection

**Actor:** System (Celery Beat)
**Preconditions:** Appointment is in CONFIRMED status. End time was more than 2 hours ago.
**Postconditions:** Appointment moves to NO_SHOW. Both parties are notified.

**Main Flow:**
1. Celery Beat runs no-show check task every 30 minutes.
2. For each CONFIRMED appointment where `scheduled_end < now - 2 hours`:
   - Mark as NO_SHOW.
   - Notify both parties.

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Request Detail Page | Add "Schedule Appointment" button and appointment list/card | Frontend edit |
| Dashboard Page | Add appointment statistics (optional card) | Frontend edit |
| Notification System (`notification_bc`) | Handle new event types: `appointment.*` | Enum + subscriber + resolver updates |
| Sidebar Navigation | Add "Calendar" or "Appointments" nav item | Frontend edit |
| Router | Add routes for calendar page and appointment views | Frontend edit |
| app.py | Register new appointment router | Router registration |
| Celery Beat | Add reminder and no-show detection tasks to schedule | Celery config edit |
| Request Status Change (`request_bc`) | Auto-cancel linked appointments when request is resolved/rejected | Event subscriber or command handler edit |
| i18n (EN + ES) | ~60-80 new translation keys | Locale file edits |

---

## Domain & Data (High-Level)

### New Bounded Context: `appointment_bc`

#### Subdomain: `appointment`

**Entity: `Appointment`**
- `id` (ULID), `company_id`
- `request_id` (FK to service request)
- `technician_id` (FK to user — the assigned technician)
- `employee_id` (FK to user — the requesting employee)
- `status` (AppointmentStatus enum)
- `scheduled_start` (datetime, UTC)
- `scheduled_end` (datetime, UTC, computed from start + duration)
- `duration_minutes` (integer: 30, 60, or 90)
- `location` (nullable text)
- `notes` (nullable text — set on completion)
- `cancellation_reason` (nullable text)
- `cancelled_by` (nullable user ID)
- `rescheduled_from_id` (nullable FK to Appointment — links to original if rescheduled)
- `reminder_24h_sent` (bool, default false)
- `reminder_1h_sent` (bool, default false)
- `completed_at` (nullable datetime)
- `created_by` (user ID — who initiated the booking)
- `created_at`, `updated_at`

**Entity: `TechnicianAvailability`**
- `id` (ULID), `company_id`, `technician_id` (FK to user)
- `day_of_week` (integer 0-6, Monday=0)
- `start_time` (time, e.g., 09:00)
- `end_time` (time, e.g., 12:00)
- Unique constraint: `(technician_id, day_of_week, start_time)`

**Entity: `AvailabilityOverride`**
- `id` (ULID), `company_id`, `technician_id` (FK to user)
- `date` (date — specific day)
- `is_available` (bool — true = extra availability, false = blocked)
- `start_time` (nullable time — if available, specific window)
- `end_time` (nullable time — if available, specific window)
- `reason` (nullable text — e.g., "Vacation", "On-call")
- Unique constraint: `(technician_id, date, start_time)`

**Enum: `AppointmentStatus`**
```
PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW
```

### Computed Values (Not Stored)

- **Available slots:** Computed from `TechnicianAvailability` (recurring) + `AvailabilityOverride` (date-specific) - existing `Appointment` blocks for the requested date range.
- **Appointment duration:** `scheduled_end = scheduled_start + duration_minutes`.

### New Tables

| Table | Description |
|-------|-------------|
| `appointments` | Appointment records |
| `technician_availabilities` | Recurring weekly time windows |
| `availability_overrides` | Date-specific blocks/extras |

### Events

- `appointment.created` — New appointment booked or requested. Notifies the other party.
- `appointment.confirmed` — Technician confirms a pending appointment. Notifies employee.
- `appointment.cancelled` — Appointment cancelled. Notifies the other party with reason.
- `appointment.rescheduled` — Appointment rescheduled. Notifies the other party.
- `appointment.reminder` — Automated reminder (24h or 1h before). Notifies both parties.
- `appointment.completed` — Technician marks appointment as done.
- `appointment.no_show` — Auto-detected no-show. Notifies both parties.

### Dashboard Extensions

- **Appointments Today card** (technician dashboard): count of today's appointments, next appointment time.
- **Appointment Stats card** (admin dashboard): total scheduled this week, completed, no-shows, cancellations.

---

## API Endpoints (High-Level)

### Appointments
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/appointments` | employee+ | Create appointment (PENDING if employee, CONFIRMED if technician) |
| `GET` | `/api/v1/appointments` | technician+ | List appointments (paginated, filterable) |
| `GET` | `/api/v1/appointments/{id}` | employee+ | Get appointment detail |
| `POST` | `/api/v1/appointments/{id}/confirm` | technician+ | Confirm pending appointment |
| `POST` | `/api/v1/appointments/{id}/cancel` | employee+ | Cancel appointment with reason |
| `POST` | `/api/v1/appointments/{id}/complete` | technician+ | Mark appointment as completed |
| `POST` | `/api/v1/appointments/{id}/reschedule` | employee+ | Reschedule (cancel old + create new PENDING) |
| `GET` | `/api/v1/appointments/my` | employee | Employee's own appointments |

### Availability
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/availability/{technician_id}` | employee+ | Get technician's available slots for date range |
| `PUT` | `/api/v1/availability/me` | technician | Set/update own recurring weekly availability |
| `GET` | `/api/v1/availability/me` | technician | Get own availability settings |
| `POST` | `/api/v1/availability/me/overrides` | technician | Add date-specific override (block or extra) |
| `GET` | `/api/v1/availability/me/overrides` | technician | List own overrides |
| `DELETE` | `/api/v1/availability/me/overrides/{id}` | technician | Remove override |

### Dashboard
| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/dashboard/appointment-stats` | admin | Appointment statistics for dashboard card |

---

## Technical Constraints

- **UTC storage:** All datetime values stored in UTC. Frontend converts to browser local timezone for display.
- **Multi-tenant isolation:** All queries scoped by `company_id`. Appointments, availability, and overrides are company-scoped.
- **Overlap detection:** When creating or confirming an appointment, the system must verify no time overlap with the technician's AND the employee's existing CONFIRMED appointments for that date. Use a query with range overlap check: `existing.start < new.end AND existing.end > new.start`.
- **Request status cascade:** When a service request moves to `RESOLVED` or `REJECTED`, any PENDING or CONFIRMED appointments linked to that request must be auto-cancelled (reason: "Request closed"). This should be handled by the request status change command handler or via an event subscriber.
- **Availability computation:** Available slots are computed at query time by: (1) getting recurring windows for the requested day of week, (2) applying overrides for the specific date, (3) subtracting existing CONFIRMED appointment blocks, (4) splitting remaining windows into bookable slots of the requested duration.
- **Reminder idempotency:** Reminder flags (`reminder_24h_sent`, `reminder_1h_sent`) on the appointment entity prevent duplicate notifications if the Celery task runs multiple times.
- **No-show detection:** Celery Beat task runs every 30 minutes. Marks CONFIRMED appointments as NO_SHOW if `scheduled_end + 2 hours < now`.
- **Backward compatibility:** Existing requests, users, and notifications are unaffected. Appointment fields are additive.
- **E3 integration:** Appointments reference `request_id`. Only requests with an assigned technician in `IN_REVIEW` or `IN_PROGRESS` status can have appointments.
- **E4 integration:** Appointment events use existing notification pub/sub infrastructure.
- **SQLAlchemy 2.0:** All models use `Mapped[type]` annotations.
- **Framework base classes:** All commands/queries inherit from `Command`/`Query` and `CommandHandler`/`QueryHandler`.

---

## Definition of Done

- [ ] Appointment CRUD with full lifecycle (pending → confirmed → completed / cancelled / no-show).
- [ ] Technician can book appointments directly (CONFIRMED) from request detail.
- [ ] Employee can request appointments (PENDING → technician confirms/declines).
- [ ] Technician availability: recurring weekly schedule with day/time windows.
- [ ] Availability overrides: date-specific blocks and extra availability.
- [ ] Available slot computation: considers availability + overrides - existing appointments.
- [ ] Overlap detection prevents double-booking technicians.
- [ ] Rescheduling: cancel old + create new PENDING with history link.
- [ ] Cancellation with mandatory reason and notification to other party.
- [ ] Automated reminders at 24h and 1h before appointment (Celery Beat).
- [ ] Auto no-show detection 2h after appointment end (Celery Beat).
- [ ] Calendar view for technicians (week view with appointment blocks).
- [ ] "My Appointments" list view for employees.
- [ ] Appointment card on request detail page showing appointment history.
- [ ] Dashboard appointment statistics card.
- [ ] Appointment events and notifications (created, confirmed, cancelled, rescheduled, reminder, completed, no-show).
- [ ] Unit tests: appointment lifecycle, availability computation, overlap detection, reminder logic.
- [ ] Integration tests: all API endpoints, availability, booking flow.
- [ ] Frontend: calendar page, availability settings, appointment booking flow, request detail integration.
- [ ] i18n keys for all new UI text (English + Spanish).

---

## Time Constraints

**Deadline:** None
**Type:** None
**Dependencies:** E3 must be complete (it is). E4 must be complete (it is).
**Calendar Conflicts:** None identified.

---

## Open Questions

1. ~~Should employees be able to book appointments directly or only request them?~~ → Decided: Employees *request* appointments (PENDING), technicians *book* them (CONFIRMED). This prevents employees from blocking technician time without consent.
2. ~~Should appointment duration be fixed or variable?~~ → Decided: Variable per appointment (30/60/90 min). No global setting needed.
3. ~~Should rescheduling preserve the appointment or create a new one?~~ → Decided: Create a new appointment linked to the old one. Preserves history and requires re-confirmation.
4. ~~Should no-show have consequences (e.g., auto-close request)?~~ → Decided: No automatic consequences. NO_SHOW is informational for now. Consequences can be added in a future enhancement.
5. ~~Should there be a maximum number of appointments per request?~~ → Decided: No limit. A request can have multiple appointments (e.g., initial diagnosis + follow-up fix).
6. ~~Should external calendar sync be included?~~ → Decided: No. Internal calendar only. External sync (iCal, Google, Outlook) is a future enhancement.
