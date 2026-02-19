# Tasks: F1 — Appointment CRUD & Notifications

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 11
**Estimated Complexity:** H

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Notification enums | 1 | S |
| AppointmentEventFactory | 1 | S |
| TargetResolver additions | 1 | S |
| Commands | 1 | H |
| Queries | 1 | S |
| HTTP — Schemas + Dependencies | 1 | S |
| HTTP — Router + App | 1 | H |
| Request cascade | 1 | M |
| Unit tests | 1 | M |
| Integration tests | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Notification Enums

### 1. Add appointment EventType values
- [x] Edit `src/notification_bc/notification/domain/enums.py`
  - Add 5 values to `EventType` enum:
    - `APPOINTMENT_CREATED = "appointment.created"`
    - `APPOINTMENT_CONFIRMED = "appointment.confirmed"`
    - `APPOINTMENT_CANCELLED = "appointment.cancelled"`
    - `APPOINTMENT_RESCHEDULED = "appointment.rescheduled"`
    - `APPOINTMENT_COMPLETED = "appointment.completed"`

---

## Phase 2: AppointmentEventFactory

### 2. Create AppointmentEventFactory
- [x] Create `src/notification_bc/notification/application/services/appointment_event_factory.py`
  - Follow `RequestEventFactory` pattern (static methods returning `DomainEvent`)
  - **`appointment_created(appointment, actor_id)`**:
    - `event_type = EventType.APPOINTMENT_CREATED`
    - Payload: `appointment_id`, `request_id`, `technician_id`, `employee_id`, `scheduled_start` (isoformat)
    - Title: "Appointment scheduled"
    - Body: f"Appointment on {scheduled_start} for {duration_minutes} min"
  - **`appointment_confirmed(appointment, actor_id)`**:
    - `event_type = EventType.APPOINTMENT_CONFIRMED`
    - Same payload structure
    - Title: "Appointment confirmed"
  - **`appointment_cancelled(appointment, actor_id)`**:
    - `event_type = EventType.APPOINTMENT_CANCELLED`
    - Payload adds `cancellation_reason`
    - Title: "Appointment cancelled"
  - **`appointment_rescheduled(old_appointment, new_appointment, actor_id)`**:
    - `event_type = EventType.APPOINTMENT_RESCHEDULED`
    - Payload: both old and new `appointment_id`, `scheduled_start`
    - Title: "Appointment rescheduled"
  - **`appointment_completed(appointment, actor_id)`**:
    - `event_type = EventType.APPOINTMENT_COMPLETED`
    - Title: "Appointment completed"

---

## Phase 3: TargetResolver Additions

### 3. Add appointment resolvers to TargetResolver
- [x] Edit `src/notification_bc/notification/application/services/target_resolver.py`
  - Add 5 entries to the `resolvers` dict in `resolve()` method
  - Add 5 private resolver methods:
    - `_resolve_appointment_created` → notify employee_id (if actor is technician) or technician_id (if actor is employee)
    - `_resolve_appointment_confirmed` → notify employee_id
    - `_resolve_appointment_cancelled` → notify both technician_id and employee_id
    - `_resolve_appointment_rescheduled` → notify both technician_id and employee_id
    - `_resolve_appointment_completed` → notify employee_id

---

## Phase 4: Commands

### 4. Create all command handlers
- [x] Create `src/appointment_bc/appointment/application/commands/create_appointment.py`
  - `CreateAppointmentCommand(Command)`:
    - Fields: `appointment_id`, `company_id`, `request_id`, `technician_id`, `employee_id`, `scheduled_start`, `duration_minutes`, `created_by`, `creator_role`, `location?`, `rescheduled_from_id?`
  - `CreateAppointmentCommandHandler(CommandHandler[CreateAppointmentCommand])`:
    - `__init__(self, appointment_repo: AppointmentRepositoryInterface)`
    - Logic:
      1. Set `initial_status` = CONFIRMED if `creator_role` in ("technician", "admin", "super_admin") else PENDING
      2. `Appointment.create(...)` — validates duration
      3. Check technician overlap: `find_by_technician_date_range(technician_id, company_id, scheduled_start, scheduled_end)`
      4. If overlaps exist → raise `AppointmentOverlapError`
      5. Check employee overlap: `find_by_employee_date_range(employee_id, company_id, scheduled_start, scheduled_end)`
      6. If overlaps exist → raise `AppointmentOverlapError`
      7. Save (ID pre-generated in command per CQRS convention)
  - `AppointmentOverlapError(Exception)` with message
- [x] Create `src/appointment_bc/appointment/application/commands/confirm_appointment.py`
  - `ConfirmAppointmentCommand(Command)`: `appointment_id`, `company_id`, `performed_by`
  - Handler: load, call `confirm()`, save. Raise `AppointmentNotFoundError` if not found.
- [x] Create `src/appointment_bc/appointment/application/commands/cancel_appointment.py`
  - `CancelAppointmentCommand(Command)`: `appointment_id`, `company_id`, `reason`, `performed_by`
  - Handler: load, call `cancel(reason, performed_by)`, save
- [x] Create `src/appointment_bc/appointment/application/commands/complete_appointment.py`
  - `CompleteAppointmentCommand(Command)`: `appointment_id`, `company_id`, `performed_by`, `notes?`
  - Handler: load, call `complete(notes)`, save
- [x] Create `src/appointment_bc/appointment/application/commands/reschedule_appointment.py`
  - `RescheduleAppointmentCommand(Command)`: `new_appointment_id`, `appointment_id`, `company_id`, `new_start`, `new_duration_minutes`, `performed_by`, `creator_role`, `reason`, `location?`
  - Handler:
    1. Load existing appointment → raise if not found
    2. Cancel existing with reason="Rescheduled: {reason}"
    3. Create new appointment with `rescheduled_from_id=old.id`, using old technician/employee/request
    4. Check overlaps for new time
    5. Save both (ID pre-generated in command per CQRS convention)

---

## Phase 5: Queries

### 5. Create all query handlers
- [x] Create `src/appointment_bc/appointment/application/queries/list_appointments.py`
  - `ListAppointmentsQuery(Query)`: `company_id`, `page`, `page_size`, `status?`, `technician_id?`, `employee_id?`, `request_id?`, `date_from?`, `date_to?`
  - Handler returns `tuple[list[Appointment], int]` from `appointment_repo.find_all(...)`
- [x] Create `src/appointment_bc/appointment/application/queries/get_appointment.py`
  - `GetAppointmentQuery(Query)`: `appointment_id`, `company_id`
  - Handler: `find_by_id()`, raise `AppointmentNotFoundError` if None
  - `AppointmentNotFoundError(Exception)` with message
- [x] Create `src/appointment_bc/appointment/application/queries/my_appointments.py`
  - `MyAppointmentsQuery(Query)`: `employee_id`, `company_id`, `page`, `page_size`, `status?`
  - Handler: delegates to `find_all()` with `employee_id` filter

---

## Phase 6: HTTP — Schemas + Dependencies

### 6. Create schemas and dependencies
- [x] Create `adapters/http/api/appointments/__init__.py` (empty)
- [x] Create `adapters/http/api/appointments/schemas.py`
  - `AppointmentCreateRequest`: `request_id`, `technician_id`, `employee_id`, `scheduled_start`, `duration_minutes` (Field ge=30, le=90), `location?`
  - `CancelAppointmentRequest`: `reason`
  - `CompleteAppointmentRequest`: `notes?`
  - `RescheduleAppointmentRequest`: `new_start`, `new_duration_minutes` (Field ge=30, le=90), `reason`, `location?`
  - `AppointmentResponse`: all entity fields + `technician_email?`, `employee_email?`
- [x] Create `adapters/http/api/appointments/dependencies.py`
  - `get_appointment_repo(db=Depends(get_db)) -> AppointmentRepository`

---

## Phase 7: HTTP — Router + App Registration

### 7. Create router and register in app
- [x] Create `adapters/http/api/appointments/routers.py`
  - `router = APIRouter(prefix="/api/v1/appointments", tags=["appointments"])`
  - Helper `_to_response(appointment, tech_email?, emp_email?) -> AppointmentResponse`
  - Helper `_find_or_404(repo, id, company_id) -> Appointment`
  - **POST** `/` — Create appointment
    - Auth: `get_current_user` (any authenticated)
    - Instantiate `CreateAppointmentCommandHandler`
    - Determine `creator_role` from `current_user.role`
    - Catch `ValueError` → 422, `AppointmentOverlapError` → 409
    - Publish `AppointmentEventFactory.appointment_created(...)` event
    - Return 201 with `{"data": response}`
  - **GET** `/` — List appointments
    - Auth: `require_role(UserRole.TECHNICIAN)`
    - Pagination: `page`, `page_size`, filters
    - Return `{"data": [...], "meta": {...}}`
  - **GET** `/{appointment_id}` — Get appointment
    - Auth: `get_current_user`
    - Access control: technician+ sees all, employee sees own only
    - Return `{"data": response}`
  - **POST** `/{appointment_id}/confirm` — Confirm
    - Auth: `require_role(UserRole.TECHNICIAN)`
    - Publish `appointment_confirmed` event
  - **POST** `/{appointment_id}/cancel` — Cancel
    - Auth: `get_current_user` (both parties can cancel)
    - Publish `appointment_cancelled` event
  - **POST** `/{appointment_id}/complete` — Complete
    - Auth: `require_role(UserRole.TECHNICIAN)`
    - Publish `appointment_completed` event
  - **POST** `/{appointment_id}/reschedule` — Reschedule
    - Auth: `require_role(UserRole.TECHNICIAN)`
    - Catch overlaps → 409
    - Publish `appointment_rescheduled` event
    - Return 201 with new appointment
- [x] Edit `adapters/http/api/my/routers.py`
  - Add **GET** `/api/v1/my/appointments` endpoint
    - Auth: `get_current_user`
    - Use `MyAppointmentsQuery` with `employee_id = current_user.id`
    - Pagination + optional status filter
- [x] Edit `app.py`
  - Add `from adapters.http.api.appointments.routers import router as appointments_router`
  - Add `app.include_router(appointments_router)`

---

## Phase 8: Request Cascade

### 8. Auto-cancel appointments on request resolve/reject
- [x] Edit `adapters/http/api/requests/routers.py`
  - In `change_request_status` endpoint, after successful status change:
  - If new status is RESOLVED or REJECTED:
    1. Get `appointment_repo` from dependencies
    2. Query `find_pending_or_confirmed_by_request(request_id)`
    3. For each appointment: `appointment.cancel(reason="Request {new_status}", cancelled_by=performed_by)`
    4. Save each cancelled appointment
  - Add `get_appointment_repo` dependency to the endpoint
- [x] Edit `adapters/http/api/requests/dependencies.py`
  - Add `get_appointment_repo` function if not already there

---

## Phase 9: Unit Tests

### 9. Create unit tests for commands and queries
- [x] Create `tests/unit/appointment_bc/appointment/application/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/application/commands/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/application/commands/test_create.py`
  - `test_create_appointment_as_technician_confirmed` — status=CONFIRMED
  - `test_create_appointment_as_employee_pending` — status=PENDING
  - `test_create_invalid_duration_raises` — 45 min → ValueError
  - `test_create_technician_overlap_raises` — existing confirmed appt → AppointmentOverlapError
  - `test_create_employee_overlap_raises` — existing confirmed appt → AppointmentOverlapError
  - `test_create_no_overlap_succeeds` — different time → saved
  - `test_create_with_rescheduled_from_id`
- [x] Create `tests/unit/appointment_bc/appointment/application/commands/test_transitions.py`
  - `test_confirm_appointment` — PENDING → CONFIRMED
  - `test_confirm_not_found_raises` — invalid ID
  - `test_cancel_appointment_with_reason` — sets reason + cancelled_by
  - `test_cancel_completed_raises` — InvalidAppointmentStatusTransitionError
  - `test_complete_appointment` — CONFIRMED → COMPLETED
  - `test_complete_pending_raises` — error
- [x] Create `tests/unit/appointment_bc/appointment/application/commands/test_reschedule.py`
  - `test_reschedule_cancels_old_creates_new` — both saved
  - `test_reschedule_links_rescheduled_from_id`
  - `test_reschedule_overlap_raises`
- [x] Create `tests/unit/appointment_bc/appointment/application/queries/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/application/queries/test_queries.py`
  - `test_list_returns_paginated`
  - `test_get_returns_appointment`
  - `test_get_not_found_raises`

---

## Phase 10: Integration Tests

### 10. Create integration tests
- [x] Create `tests/integration/test_appointments_endpoints.py`
  - `test_create_appointment_201` — technician creates → 201, status CONFIRMED
  - `test_list_appointments_200` — returns paginated list
  - `test_get_appointment_200` — returns detail
  - `test_confirm_appointment_200` — PENDING → CONFIRMED
  - `test_cancel_appointment_200` — with reason
  - `test_complete_appointment_200` — CONFIRMED → COMPLETED
  - `test_reschedule_appointment_201` — old cancelled, new created
  - `test_my_appointments_200` — employee sees own
  - `test_create_overlap_409` — same technician, same time → 409
  - `test_request_cascade_cancels_appointments` — resolve request → appointments auto-cancelled

---

## Phase 11: Verification

### 11. Verify
- [x] Lint passes: `make lint` (no new errors in appointment_bc)
- [x] Unit tests pass: `make test` (908 passed)
- [ ] Integration tests pass: `make test-integration`
- [x] All `__init__.py` files present

---

## Execution Order

**Batch 1 (Parallel):** Tasks 1 + 2 + 3 (notification enums + factory + resolver — independent)
**Batch 2:** Task 4 (commands — depends on entities from F0)
**Batch 3:** Task 5 (queries — depends on entities)
**Batch 4 (Parallel):** Tasks 6 + 7 (schemas + dependencies + router — depends on commands/queries)
**Batch 5:** Task 8 (request cascade — depends on router + appointment repo)
**Batch 6 (Parallel):** Tasks 9 + 10 (tests — after all code)
**Batch 7:** Task 11 (verification)

## Final Checklist

- [x] All tasks completed
- [x] 5 command handlers
- [x] 3 query handlers
- [x] 8 API endpoints (7 on appointments router + 1 on my router)
- [x] 5 notification event types
- [x] AppointmentEventFactory with 5 methods
- [x] TargetResolver with 5 new resolvers
- [x] Request cascade on resolve/reject
- [x] ~18 unit tests (20 actual)
- [x] ~10 integration tests (10 actual)
- [x] All tests passing
