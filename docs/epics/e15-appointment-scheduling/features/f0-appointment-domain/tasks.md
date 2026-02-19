# Tasks: F0 — Appointment Domain & Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-18
**Total Tasks:** 14
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Package structure | 1 | S |
| Domain - Enums | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Service | 1 | M |
| Domain - Repository interfaces | 1 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Tests - Domain entities | 1 | M |
| Tests - Domain service | 1 | M |
| Verification | 1 | S |

---

## Phase 1: Package Structure

### 1. Create `appointment_bc` package tree
- [x] Create directory structure:
  ```
  src/appointment_bc/__init__.py
  src/appointment_bc/appointment/__init__.py
  src/appointment_bc/appointment/domain/__init__.py
  src/appointment_bc/appointment/application/__init__.py
  src/appointment_bc/appointment/application/commands/__init__.py
  src/appointment_bc/appointment/application/queries/__init__.py
  src/appointment_bc/appointment/infrastructure/__init__.py
  ```
- All `__init__.py` files are empty

---

## Phase 2: Domain Layer — Enums

### 2. Create `AppointmentStatus` enum
- [x] Create `src/appointment_bc/appointment/domain/enums.py`
  - `AppointmentStatus(str, Enum)` with values: `PENDING`, `CONFIRMED`, `COMPLETED`, `CANCELLED`, `NO_SHOW`
  - `is_terminal` property: `True` for COMPLETED, CANCELLED, NO_SHOW
  - `VALID_TRANSITIONS` dict:
    - PENDING → [CONFIRMED, CANCELLED]
    - CONFIRMED → [COMPLETED, CANCELLED, NO_SHOW]
    - COMPLETED → []
    - CANCELLED → []
    - NO_SHOW → []
  - `InvalidAppointmentStatusTransitionError` exception with `current` and `target` fields

---

## Phase 3: Domain Layer — Entities

### 3. Create domain entities
- [x] Create `src/appointment_bc/appointment/domain/entities.py`
  - **`Appointment`** dataclass:
    - Fields: `id`, `company_id`, `request_id`, `technician_id`, `employee_id`, `status` (AppointmentStatus), `scheduled_start` (datetime), `scheduled_end` (datetime), `duration_minutes` (int), `created_by` (str)
    - Optional fields: `location`, `notes`, `cancellation_reason`, `cancelled_by`, `rescheduled_from_id`, `completed_at`, `created_at`, `updated_at`
    - Boolean flags: `reminder_24h_sent` (default False), `reminder_1h_sent` (default False)
    - Factory `create(company_id, request_id, technician_id, employee_id, scheduled_start, duration_minutes, created_by, initial_status, location?, rescheduled_from_id?, id?)`:
      - Validates `duration_minutes` in {30, 60, 90}
      - Computes `scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)`
      - Sets `status` to `initial_status` parameter
    - `_transition(target)` — validates against `VALID_TRANSITIONS`, raises `InvalidAppointmentStatusTransitionError`
    - `confirm()` — PENDING → CONFIRMED
    - `cancel(reason, cancelled_by)` — → CANCELLED, sets `cancellation_reason` and `cancelled_by`
    - `complete(notes?)` — CONFIRMED → COMPLETED, sets `completed_at = datetime.now(UTC)` and optional `notes`
    - `mark_no_show()` — CONFIRMED → NO_SHOW
    - `mark_reminder_sent(reminder_type: str)` — sets `reminder_24h_sent=True` or `reminder_1h_sent=True`
  - **`TechnicianAvailability`** dataclass:
    - Fields: `id`, `company_id`, `technician_id`, `day_of_week` (int 0-6), `start_time` (time), `end_time` (time)
    - Factory `create(company_id, technician_id, day_of_week, start_time, end_time, id?)`:
      - Validates `day_of_week` in range(7)
      - Validates `start_time < end_time`
  - **`AvailabilityOverride`** dataclass:
    - Fields: `id`, `company_id`, `technician_id`, `date` (date), `is_available` (bool)
    - Optional fields: `start_time` (time), `end_time` (time), `reason` (str)
    - Factory `create(company_id, technician_id, date, is_available, start_time?, end_time?, reason?, id?)`:
      - If `is_available=True`, validates `start_time` and `end_time` are provided and `start_time < end_time`

---

## Phase 4: Domain Layer — Service

### 4. Create `AvailabilityService` domain service
- [x] Create `src/appointment_bc/appointment/domain/services.py`
  - **`TimeSlot`** frozen dataclass: `start: time`, `end: time`
  - **`AvailabilityService`** class with static method:
    - `compute_available_slots(target_date, duration_minutes, recurring_windows, overrides, existing_appointments) -> list[TimeSlot]`
    - Algorithm:
      1. Get recurring windows matching `target_date.weekday()` (Monday=0)
      2. If no recurring windows and target_date is weekday (Mon-Fri), use default: [(09:00, 12:00), (14:00, 17:00)]
      3. If no recurring windows and target_date is weekend, return []
      4. Apply overrides for the specific date:
         - `is_available=False` with no time range → clear all windows (entire day blocked)
         - `is_available=False` with time range → subtract that range from windows
         - `is_available=True` with time range → add that window
      5. Subtract existing CONFIRMED appointment time blocks
      6. Split remaining windows into bookable slots of `duration_minutes` length (aligned to slot boundaries)
      7. Return list of `TimeSlot`
    - Helper `_subtract_range(windows, block_start, block_end)` — removes a time range from a list of windows, splitting if necessary
    - Helper `_split_into_slots(windows, duration_minutes)` — divides windows into fixed-duration slots

---

## Phase 5: Domain Layer — Repository Interfaces

### 5. Create repository interfaces
- [x] Create `src/appointment_bc/appointment/domain/repository.py`
  - **`AppointmentRepositoryInterface(ABC)`**:
    - `save(appointment) -> Appointment`
    - `find_by_id(id, company_id) -> Optional[Appointment]`
    - `find_all(company_id, page, page_size, status?, technician_id?, employee_id?, request_id?, date_from?, date_to?) -> tuple[list[Appointment], int]`
    - `find_by_technician_date_range(technician_id, company_id, start, end) -> list[Appointment]`
    - `find_by_employee_date_range(employee_id, company_id, start, end) -> list[Appointment]`
    - `find_by_request_id(request_id, company_id) -> list[Appointment]`
    - `find_confirmed_before(before_datetime) -> list[Appointment]`
    - `find_needing_reminder(reminder_type, window_start, window_end) -> list[Appointment]`
    - `find_pending_or_confirmed_by_request(request_id) -> list[Appointment]`
  - **`TechnicianAvailabilityRepositoryInterface(ABC)`**:
    - `save_all(technician_id, company_id, windows) -> None`
    - `find_by_technician(technician_id, company_id) -> list[TechnicianAvailability]`
    - `find_by_technician_day(technician_id, company_id, day_of_week) -> list[TechnicianAvailability]`
  - **`AvailabilityOverrideRepositoryInterface(ABC)`**:
    - `save(override) -> AvailabilityOverride`
    - `find_by_id(id, company_id) -> Optional[AvailabilityOverride]`
    - `find_by_technician_date_range(technician_id, company_id, date_from, date_to) -> list[AvailabilityOverride]`
    - `find_by_technician_date(technician_id, company_id, date) -> list[AvailabilityOverride]`
    - `delete(id, company_id) -> bool`

---

## Phase 6: Infrastructure — Migrations

### 6. Create Alembic migrations
- [x] Create `alembic/versions/f1a2b3c4d5e6_create_appointments.py`
  - Table `appointments` with all fields from design
  - Indexes on: `company_id`, `technician_id`, `employee_id`, `request_id`, `status`, `scheduled_start`
  - FK to `companies(id)`, `service_requests(id)`, `users(id)` (x2), self-referential `appointments(id)`
- [x] Create `alembic/versions/f2b3c4d5e6f7_create_technician_availabilities.py`
  - Table `technician_availabilities` with all fields
  - UniqueConstraint on `(technician_id, day_of_week, start_time)`
  - Index on `technician_id`
- [x] Create `alembic/versions/f3c4d5e6f7a8_create_availability_overrides.py`
  - Table `availability_overrides` with all fields
  - UniqueConstraint on `(technician_id, date, start_time)`
  - Composite index on `(technician_id, date)`

---

## Phase 7: Infrastructure — Models

### 7. Create SQLAlchemy models
- [x] Create `src/appointment_bc/appointment/infrastructure/models.py`
  - **`AppointmentModel(ULIDMixin, TimestampMixin, Base)`**:
    - `__tablename__ = "appointments"`
    - All fields with `Mapped[type]` annotations
    - `company_id`: `Mapped[str]` FK to `companies.id`, indexed
    - `request_id`: `Mapped[str]` FK to `service_requests.id`, indexed
    - `technician_id`: `Mapped[str]` FK to `users.id`, indexed
    - `employee_id`: `Mapped[str]` FK to `users.id`, indexed
    - `status`: `Mapped[str]` default `"PENDING"`
    - `scheduled_start`: `Mapped[datetime]` (DateTime column)
    - `scheduled_end`: `Mapped[datetime]` (DateTime column)
    - `duration_minutes`: `Mapped[int]` default 60
    - `location`: `Mapped[Optional[str]]` (Text, nullable)
    - `notes`: `Mapped[Optional[str]]` (Text, nullable)
    - `cancellation_reason`: `Mapped[Optional[str]]` (Text, nullable)
    - `cancelled_by`: `Mapped[Optional[str]]` (String(26), nullable)
    - `rescheduled_from_id`: `Mapped[Optional[str]]` FK to `appointments.id`, nullable
    - `reminder_24h_sent`: `Mapped[bool]` default False
    - `reminder_1h_sent`: `Mapped[bool]` default False
    - `completed_at`: `Mapped[Optional[datetime]]` (DateTime, nullable)
    - `created_by`: `Mapped[str]` (String(26))
  - **`TechnicianAvailabilityModel(ULIDMixin, TimestampMixin, Base)`**:
    - `__tablename__ = "technician_availabilities"`
    - `company_id`, `technician_id`: `Mapped[str]` FK indexed
    - `day_of_week`: `Mapped[int]` (Integer)
    - `start_time`: `Mapped[time]` (Time column)
    - `end_time`: `Mapped[time]` (Time column)
    - UniqueConstraint on `(technician_id, day_of_week, start_time)`
  - **`AvailabilityOverrideModel(ULIDMixin, TimestampMixin, Base)`**:
    - `__tablename__ = "availability_overrides"`
    - `company_id`, `technician_id`: `Mapped[str]` FK indexed
    - `date`: `Mapped[date]` (Date column)
    - `is_available`: `Mapped[bool]` default False
    - `start_time`: `Mapped[Optional[time]]` (Time, nullable)
    - `end_time`: `Mapped[Optional[time]]` (Time, nullable)
    - `reason`: `Mapped[Optional[str]]` (Text, nullable)
    - UniqueConstraint on `(technician_id, date, start_time)`

---

## Phase 8: Infrastructure — Repositories

### 8. Create repository implementations
- [x] Create `src/appointment_bc/appointment/infrastructure/repository.py`
  - **`AppointmentRepository(AppointmentRepositoryInterface)`**:
    - `__init__(self, session: Session)`
    - `save()`: upsert pattern — check existing by id, update fields or create new model
    - `find_by_id()`: query by id + company_id, map model → entity
    - `find_all()`: paginated query with optional filters (status, technician_id, employee_id, request_id, date_from, date_to)
    - `find_by_technician_date_range()`: overlap query — `WHERE technician_id = ? AND status = 'CONFIRMED' AND scheduled_start < end AND scheduled_end > start`
    - `find_by_employee_date_range()`: same pattern for employee
    - `find_by_request_id()`: filter by request_id + company_id
    - `find_confirmed_before()`: `WHERE status = 'CONFIRMED' AND scheduled_end < before_datetime`
    - `find_needing_reminder()`: `WHERE status = 'CONFIRMED' AND reminder_Xh_sent = FALSE AND scheduled_start BETWEEN window_start AND window_end`
    - `find_pending_or_confirmed_by_request()`: `WHERE request_id = ? AND status IN ('PENDING', 'CONFIRMED')`
    - Private `_to_entity(model)` mapper method
  - **`TechnicianAvailabilityRepository(TechnicianAvailabilityRepositoryInterface)`**:
    - `save_all()`: delete existing for technician + company, bulk insert new windows
    - `find_by_technician()`: filter by technician_id + company_id
    - `find_by_technician_day()`: add day_of_week filter
    - Private `_to_entity(model)` mapper
  - **`AvailabilityOverrideRepository(AvailabilityOverrideRepositoryInterface)`**:
    - `save()`: insert new model
    - `find_by_id()`: query by id + company_id
    - `find_by_technician_date_range()`: filter by technician + date range
    - `find_by_technician_date()`: filter by technician + specific date
    - `delete()`: delete by id + company_id, return bool
    - Private `_to_entity(model)` mapper

---

## Phase 9: Tests — Domain Entities

### 9. Unit tests for entities and enums
- [x] Create `tests/unit/appointment_bc/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/domain/__init__.py`
- [x] Create `tests/unit/appointment_bc/appointment/domain/test_entities.py`
  - `test_create_appointment_pending` — employee creates, status = PENDING
  - `test_create_appointment_confirmed` — technician creates, status = CONFIRMED
  - `test_create_validates_duration` — invalid duration (e.g., 45) raises ValueError
  - `test_create_computes_scheduled_end` — start + 60 min = end
  - `test_confirm_from_pending` — PENDING → CONFIRMED
  - `test_confirm_from_confirmed_raises` — already CONFIRMED → error
  - `test_cancel_from_pending` — PENDING → CANCELLED with reason
  - `test_cancel_from_confirmed` — CONFIRMED → CANCELLED with reason
  - `test_cancel_from_completed_raises` — COMPLETED → error
  - `test_complete_from_confirmed` — CONFIRMED → COMPLETED, sets completed_at
  - `test_complete_from_pending_raises` — PENDING → error
  - `test_mark_no_show` — CONFIRMED → NO_SHOW
  - `test_mark_no_show_from_cancelled_raises` — CANCELLED → error
  - `test_availability_validates_day_of_week` — day_of_week=7 raises ValueError
  - `test_availability_validates_times` — start >= end raises ValueError
  - `test_override_available_requires_times` — is_available=True without times raises ValueError
  - `test_appointment_status_is_terminal` — COMPLETED, CANCELLED, NO_SHOW are terminal
  - `test_appointment_status_not_terminal` — PENDING, CONFIRMED are not terminal

---

## Phase 10: Tests — Domain Service

### 10. Unit tests for AvailabilityService
- [x] Create `tests/unit/appointment_bc/appointment/domain/test_services.py`
  - `test_simple_recurring_window` — one window 09:00-12:00, duration 60 → 3 slots
  - `test_multiple_windows` — two windows (09:00-12:00, 14:00-17:00), duration 60 → 6 slots
  - `test_30_min_slots` — window 09:00-12:00, duration 30 → 6 slots
  - `test_90_min_slots` — window 09:00-12:00, duration 90 → 2 slots
  - `test_blocked_override_removes_entire_day` — is_available=False, no times → empty
  - `test_blocked_override_with_range` — blocks 10:00-11:00 from 09:00-12:00 → slots before and after
  - `test_extra_override_adds_window` — adds Saturday 10:00-14:00 → 4 slots (60min)
  - `test_subtract_existing_appointment` — appointment 10:00-11:00 removes that slot
  - `test_default_weekday_availability` — no recurring windows on Monday → defaults 09:00-12:00+14:00-17:00
  - `test_default_weekend_no_availability` — no recurring + no overrides on Saturday → empty
  - `test_no_slots_when_fully_blocked` — all windows consumed by appointments → empty
  - `test_partial_window_after_subtraction` — appointment partially overlaps window → remaining slots

---

## Phase 11: Verification

### 11. Verify
- [x] Lint passes: `make lint` (no new errors in appointment_bc)
- [x] Unit tests pass: `make test`
- [x] Migrations apply cleanly: `make db-upgrade` (requires Docker)
- [x] All `__init__.py` files present

---

## Dependency Graph

```
Package structure (1)
  └── Enums (2)
        └── Entities (3)
              ├── Domain Service (4) — uses entities
              └── Repository Interfaces (5) — uses entities
                    ├── Migrations (6) — independent of code
                    ├── Models (7) — mirrors entities
                    └── Repositories (8) — implements interfaces + uses models
                          ├── Entity Tests (9) — after entities
                          ├── Service Tests (10) — after service
                          └── Verification (11) — after all

```

## Execution Order

**Batch 1:** Task 1 (package structure)
**Batch 2 (Parallel):** Tasks 2 + 6 (enums + migrations — independent)
**Batch 3:** Task 3 (entities — depends on enums)
**Batch 4 (Parallel):** Tasks 4 + 5 + 7 (domain service + interfaces + models)
**Batch 5:** Task 8 (repositories — depends on interfaces + models)
**Batch 6 (Parallel):** Tasks 9 + 10 (tests — after all domain code)
**Batch 7:** Task 11 (verification)

## Final Checklist

- [x] All tasks completed
- [x] All `__init__.py` files created
- [x] All tests passing (unit)
- [x] mypy passes on new code
- [x] 3 entities with factory methods
- [x] 1 status enum with valid transitions
- [x] 1 domain service with slot computation
- [x] 3 repository interfaces
- [x] 3 SQLAlchemy models (Mapped[type])
- [x] 3 Alembic migrations
- [x] 3 repository implementations
- [x] ~30 unit tests covering entities + service
