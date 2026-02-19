# Slicing: E15 - Appointment Scheduling

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 5

## Slicing Rationale

E15 introduces a new bounded context (`appointment_bc`) with 3 database tables, 17 API endpoints, 2 Celery Beat tasks, and a calendar frontend. The slicing follows the established bottom-up pattern: F0 builds all domain entities, enums, migrations, and repositories (no API). F1 delivers the core appointment lifecycle (CRUD + status transitions + notifications). F2 adds technician availability management (independent from appointment CRUD). F3 adds the Celery Beat tasks for reminders and no-show detection (depends on F1 for appointment data). F4 delivers all frontend pages (calendar, availability settings, request detail integration, dashboard).

This mirrors E14's pattern: F0 is domain+infrastructure foundation, F1-F2 are independent vertical backend slices, F3 adds async behavior, and F4 delivers the frontend.

## Dependency Graph

```text
F0: Appointment Domain & Infrastructure (entities, migrations, repos, availability service)
 ├── F1: Appointment CRUD & Notifications (create, confirm, cancel, complete, reschedule + events)
 │    └── F3: Celery Tasks — Reminders & No-Show (scheduled background tasks)
 ├── F2: Availability Management (recurring schedule, overrides, slot computation API)
 └── F4: Frontend — Calendar & UX (calendar page, availability settings, request detail, dashboard, i18n)
      └── depends on F1 + F2 + F3
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Appointment Domain & Infrastructure | Entities, enums, migrations, repos, domain service | Medium | None | Done |
| F1 | Appointment CRUD & Notifications | US-E15-001, US-E15-003, US-E15-006, US-E15-007 | High | F0 | Done |
| F2 | Availability Management | US-E15-002 | Medium | F0 | Done |
| F3 | Celery Tasks — Reminders & No-Show | US-E15-005, US-E15-007 (no-show) | Small | F1 | Done |
| F4 | Frontend — Calendar & UX | US-E15-004, dashboard, request detail, i18n | High | F1, F2, F3 | Done |

---

## F0: Appointment Domain & Infrastructure

**Scope:** Create the entire `appointment_bc` bounded context — domain entities, enums, repository interfaces, SQLAlchemy models, migrations, repository implementations, and the AvailabilityService domain service. Pure backend — no API endpoints, no frontend.

### Domain Layer
- `AppointmentStatus` enum with 5 values and `VALID_TRANSITIONS` dict
- `Appointment` entity with state machine methods (confirm, cancel, complete, mark_no_show)
- `TechnicianAvailability` entity (recurring weekly windows)
- `AvailabilityOverride` entity (date-specific blocks/extras)
- `AvailabilityService` domain service — computes available slots from recurring + overrides - existing appointments
- Repository interfaces for all 3 entities

### Infrastructure Layer
- 3 migrations: `appointments`, `technician_availabilities`, `availability_overrides`
- 3 SQLAlchemy models (all using `Mapped[type]` annotations)
- 3 repository implementations with tenant isolation (`company_id` scoping)

### Tests
- Unit: appointment state machine transitions (valid + invalid), entity creation, AvailabilityService slot computation
- ~15 tests

### Files

| File | Action |
|------|--------|
| `src/appointment_bc/appointment/domain/entities.py` | Create |
| `src/appointment_bc/appointment/domain/enums.py` | Create |
| `src/appointment_bc/appointment/domain/repository.py` | Create |
| `src/appointment_bc/appointment/domain/services.py` | Create — AvailabilityService |
| `src/appointment_bc/appointment/infrastructure/models.py` | Create |
| `src/appointment_bc/appointment/infrastructure/repository.py` | Create |
| `alembic/versions/` | Create — 3 migrations |
| `tests/unit/appointment_bc/appointment/domain/test_entities.py` | Create |
| `tests/unit/appointment_bc/appointment/domain/test_services.py` | Create |

---

## F1: Appointment CRUD & Notifications

**Scope:** Full appointment lifecycle — create (technician books directly, employee requests), confirm, cancel, complete, reschedule. List and get endpoints. Notification events for all transitions. Request status cascade (auto-cancel appointments when request is resolved/rejected).

### Application Layer
- `CreateAppointmentCommand` + handler (validates overlap for both technician and employee, checks request status/assignment, sets initial status based on creator role)
- `ConfirmAppointmentCommand` + handler (PENDING → CONFIRMED)
- `CancelAppointmentCommand` + handler (mandatory reason, notify other party)
- `CompleteAppointmentCommand` + handler (CONFIRMED → COMPLETED, records notes)
- `RescheduleAppointmentCommand` + handler (cancel old + create new PENDING with `rescheduled_from_id`)
- `ListAppointmentsQuery` + handler (with filters: status, date range, technician_id, request_id)
- `GetAppointmentQuery` + handler
- `MyAppointmentsQuery` + handler (employee's own appointments)

### HTTP Layer
- Router: 8 endpoints (`POST`, `GET` list, `GET` detail, `POST confirm`, `POST cancel`, `POST complete`, `POST reschedule`, `GET my`)
- Schemas: `AppointmentCreate`, `AppointmentResponse`, `CancelRequest`, `CompleteRequest`, `RescheduleRequest`
- Dependencies: `get_appointment_repo`

### Notifications
- Add 5 EventType values: `APPOINTMENT_CREATED`, `APPOINTMENT_CONFIRMED`, `APPOINTMENT_CANCELLED`, `APPOINTMENT_RESCHEDULED`, `APPOINTMENT_COMPLETED`
- Add resolver methods to TargetResolver (technician ↔ employee notification routing)
- No changes to NotificationSubscriber (already handles all events generically)

### Collateral Impact
- Edit `src/request_bc/request/application/commands/change_request_status.py` — auto-cancel linked appointments when request moves to RESOLVED or REJECTED (via event or direct call)

### Tests
- Unit: all command handlers, overlap detection, role-based initial status, request status cascade (~18 tests)
- Integration: all 8 endpoints, booking flow, cancel/reschedule (~12 tests)

### Files

| File | Action |
|------|--------|
| `src/appointment_bc/appointment/application/commands/create_appointment.py` | Create |
| `src/appointment_bc/appointment/application/commands/confirm_appointment.py` | Create |
| `src/appointment_bc/appointment/application/commands/cancel_appointment.py` | Create |
| `src/appointment_bc/appointment/application/commands/complete_appointment.py` | Create |
| `src/appointment_bc/appointment/application/commands/reschedule_appointment.py` | Create |
| `src/appointment_bc/appointment/application/queries/list_appointments.py` | Create |
| `src/appointment_bc/appointment/application/queries/get_appointment.py` | Create |
| `src/appointment_bc/appointment/application/queries/my_appointments.py` | Create |
| `adapters/http/api/appointments/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register appointment router |
| `src/notification_bc/notification/domain/enums.py` | Edit — add 5 appointment event types |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit — add appointment resolvers |
| `src/request_bc/request/application/commands/change_request_status.py` | Edit — auto-cancel linked appointments |
| `tests/unit/appointment_bc/appointment/application/commands/` | Create — command tests |
| `tests/unit/appointment_bc/appointment/application/queries/` | Create — query tests |
| `tests/integration/test_appointments_endpoints.py` | Create |

---

## F2: Availability Management

**Scope:** Technician availability CRUD — recurring weekly schedule (upsert), date-specific overrides (add, list, delete), and available slot computation endpoint. Independent from appointment CRUD (both depend on F0).

### Application Layer
- `SetAvailabilityCommand` + handler (upsert recurring weekly windows, validates no overlap on same day)
- `GetAvailabilityQuery` + handler (returns technician's recurring schedule)
- `AddOverrideCommand` + handler (add date-specific block or extra availability)
- `ListOverridesQuery` + handler (date range filter)
- `DeleteOverrideCommand` + handler
- `GetAvailableSlotsQuery` + handler (uses AvailabilityService to compute open slots for a technician + date range + duration)

### HTTP Layer
- Router: 6 endpoints on `/api/v1/availability/`
- Schemas: `AvailabilityWindow`, `AvailabilitySetRequest`, `OverrideCreate`, `AvailableSlot`, `AvailableSlotsResponse`
- Dependencies: `get_availability_repo`, `get_override_repo`, `get_appointment_repo`

### Tests
- Unit: availability upsert, override add/delete, overlap validation (~8 tests)
- Integration: all 6 availability endpoints (~8 tests)

### Files

| File | Action |
|------|--------|
| `src/appointment_bc/appointment/application/commands/set_availability.py` | Create |
| `src/appointment_bc/appointment/application/commands/add_override.py` | Create |
| `src/appointment_bc/appointment/application/commands/delete_override.py` | Create |
| `src/appointment_bc/appointment/application/queries/get_availability.py` | Create |
| `src/appointment_bc/appointment/application/queries/list_overrides.py` | Create |
| `src/appointment_bc/appointment/application/queries/get_available_slots.py` | Create |
| `adapters/http/api/availability/` | Create — routers, schemas, dependencies |
| `app.py` | Edit — register availability router |
| `tests/unit/appointment_bc/appointment/application/commands/test_availability.py` | Create |
| `tests/unit/appointment_bc/appointment/application/queries/test_slots.py` | Create |
| `tests/integration/test_availability_endpoints.py` | Create |

---

## F3: Celery Tasks — Reminders & No-Show

**Scope:** Two Celery Beat scheduled tasks: (1) appointment reminders at 24h and 1h before, (2) auto no-show detection 2h after appointment end. Both use existing notification infrastructure.

### Celery Tasks
- `send_appointment_reminders` — runs every 15 minutes via Celery Beat
  - Queries CONFIRMED appointments where start time is within 24-25h (24h reminder) or 60-75min (1h reminder)
  - Checks `reminder_24h_sent` / `reminder_1h_sent` flags for idempotency
  - Publishes `APPOINTMENT_REMINDER` event via notification system
  - Updates reminder flags on appointment entity
- `detect_no_shows` — runs every 30 minutes via Celery Beat
  - Queries CONFIRMED appointments where `scheduled_end + 2 hours < now`
  - Marks as NO_SHOW via `Appointment.mark_no_show()`
  - Publishes `APPOINTMENT_NO_SHOW` event

### Notifications
- Add 2 EventType values: `APPOINTMENT_REMINDER`, `APPOINTMENT_NO_SHOW`
- Add resolver methods to TargetResolver (both parties for both events)

### Tests
- Unit: reminder timing logic, idempotency (flag checks), no-show detection timing (~8 tests)
- Integration: not applicable (Celery tasks are tested via unit tests with mocked repos)

### Files

| File | Action |
|------|--------|
| `core/tasks/appointments.py` | Create — 2 Celery tasks |
| `core/celery.py` | Edit — add 2 Beat schedule entries |
| `src/notification_bc/notification/domain/enums.py` | Edit — add APPOINTMENT_REMINDER, APPOINTMENT_NO_SHOW |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit — add 2 resolver methods |
| `tests/unit/core/tasks/test_appointments.py` | Create |

---

## F4: Frontend — Calendar & UX

**Scope:** All frontend pages and components for appointment scheduling. Calendar week view for technicians, availability settings page, request detail appointment integration, employee "My Appointments" view, dashboard appointment stats card, routing, sidebar, i18n.

### Frontend Pages
- `CalendarPage.tsx` — Technician week view
  - Custom Tailwind grid: 7 columns (Mon-Sun) × time rows (8:00-18:00)
  - Appointment blocks with employee name, request title, time, location, status badge
  - Available/unavailable window highlighting
  - Click slot to create appointment (opens modal or inline form)
  - Click appointment to view detail / navigate to request
  - Week navigation (previous/next week)
  - Admin: dropdown to select technician
- `AvailabilitySettingsPage.tsx` — Technician availability config
  - Recurring weekly schedule form (day checkboxes + time ranges per day)
  - Override management: add blocked date, add extra availability, delete override
  - Simple form following existing settings page patterns
- `MyAppointmentsPage.tsx` — Employee list view
  - Upcoming appointments list with date, time, technician name, request title, status, location
  - Past appointments (collapsed/expandable)
  - Actions: cancel, request reschedule

### Request Detail Integration
- `RequestDetailPage.tsx` — Add appointment section
  - "Schedule Appointment" button (technician) or "Request Appointment" button (employee)
  - Booking modal: date picker showing available slots, duration selector, location input
  - Appointment history card: list of appointments for this request with status badges

### Dashboard Integration
- `DashboardPage.tsx` — Add appointment stats card
  - Technician dashboard: today's appointments count, next appointment time
  - Admin dashboard: this week's stats (scheduled, completed, no-shows, cancellations)

### Routing & Navigation
- Add 3 lazy imports and routes: CalendarPage, AvailabilitySettingsPage, MyAppointmentsPage
- Sidebar: add "Calendar" for technician+, "My Appointments" for employee

### i18n
- ~70 keys for both EN and ES covering:
  - `nav.calendar`, `nav.my_appointments`
  - `page.calendar.*` — week view, navigation, slot labels
  - `page.availability.*` — settings form labels
  - `page.appointments.*` — booking form, status labels, actions
  - `page.request_detail.appointment.*` — schedule button, history card
  - `page.dashboard.appointments.*` — stats card labels
  - `enum.appointment_status.*` — PENDING, CONFIRMED, etc.

### Tests
- Frontend build: `npm run build`
- TypeScript compilation: `npx tsc --noEmit`

### Files

| File | Action |
|------|--------|
| `web/app/src/pages/technician/CalendarPage.tsx` | Create |
| `web/app/src/pages/technician/AvailabilitySettingsPage.tsx` | Create |
| `web/app/src/pages/employee/MyAppointmentsPage.tsx` | Create |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — add appointment section |
| `web/app/src/pages/employee/RequestDetailPage.tsx` | Edit — add request appointment button |
| `web/app/src/pages/admin/DashboardPage.tsx` | Edit — add appointment stats card |
| `web/app/src/types/index.ts` | Edit — add Appointment, Availability, Override types |
| `web/app/src/router.tsx` | Edit — add 3 routes |
| `web/app/src/components/layout/Sidebar.tsx` | Edit — add 2 nav items |
| `web/app/src/locales/en.ts` | Edit — ~70 keys |
| `web/app/src/locales/es.ts` | Edit — ~70 keys |

---

## Recommended Implementation Order

1. **F0** — Appointment Domain & Infrastructure (~1 session): entities, enums, migrations, repos, AvailabilityService, domain tests
2. **F1** — Appointment CRUD & Notifications (~1-2 sessions): all command/query handlers, 8 endpoints, events, request cascade, tests
3. **F2** — Availability Management (~1 session): availability CRUD, slot computation, 6 endpoints, tests. Can parallelize with F1.
4. **F3** — Celery Tasks — Reminders & No-Show (~0.5 session): 2 Celery Beat tasks, reminder tests
5. **F4** — Frontend — Calendar & UX (~1-2 sessions): calendar page, availability settings, request detail integration, dashboard, i18n

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1/F2 → F3 → F4)
- [x] Each feature independently deployable (after dependencies)
- [x] Vertical slices — F1 delivers full appointment lifecycle, F2 delivers full availability management
- [x] Shared foundation identified (F0)
- [x] No overlapping scope — each feature owns its files
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (7 user stories, 6 use cases, 17 endpoints)

## Risk Notes

- **AvailabilityService complexity:** Slot computation must handle recurring windows, date overrides, existing appointment subtraction, and slot splitting. This is the most algorithmically complex piece — thorough unit tests are critical.
- **Overlap detection race conditions:** Two concurrent booking requests could both pass overlap validation. In production, use `SELECT ... FOR UPDATE` on the technician's appointments for the date range to prevent this. In MVP, the unique constraint + DB-level check is sufficient.
- **Calendar UI:** Custom Tailwind grid for week view is moderate frontend effort. Keep it simple — no drag-and-drop, no resize, just click-to-book.
- **Request cascade:** Auto-cancelling appointments when a request is resolved touches the request BC. Keep the coupling minimal — use an event subscriber pattern or a simple direct call in the status change handler.
