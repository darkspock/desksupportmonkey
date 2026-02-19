# Solution Design: F0 — Appointment Domain & Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `appointment_bc`

## Summary

F0 creates the entire `appointment_bc` bounded context foundation: 3 domain entities (`Appointment`, `TechnicianAvailability`, `AvailabilityOverride`), 1 status enum with transitions, 1 domain service (`AvailabilityService`), 3 repository interfaces, 3 SQLAlchemy models, 3 Alembic migrations, and 3 repository implementations. No API endpoints or frontend — pure domain + infrastructure.

## Architecture Decision

New bounded context `appointment_bc` with a single subdomain `appointment`. Follows the same DDD structure as `procurement_bc` and `request_bc`.

### Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| ULIDMixin | `core/mixins.py` | Yes | None |
| TimestampMixin | `core/mixins.py` | Yes | None |
| Base (SQLAlchemy) | `core/base.py` | Yes | None |
| Command/CommandHandler | `src/framework/application/command_bus.py` | Yes (F1) | None |
| Query/QueryHandler | `src/framework/application/query_bus.py` | Yes (F1) | None |
| PO enum pattern | `src/procurement_bc/purchase_order/domain/enums.py` | Pattern reuse | Adapt for AppointmentStatus |
| PO entity pattern | `src/procurement_bc/purchase_order/domain/entities.py` | Pattern reuse | Adapt for Appointment |

## Implementation Plan

### 1. Domain Layer

#### 1.1 Enums

**File:** `src/appointment_bc/appointment/domain/enums.py`

**`AppointmentStatus`** — `str, Enum` with 5 values:

| Value | Description | Terminal |
|-------|-------------|----------|
| `PENDING` | Employee requested, awaiting technician confirmation | No |
| `CONFIRMED` | Scheduled and confirmed by both parties | No |
| `COMPLETED` | Technician marked as done after the appointment | Yes |
| `CANCELLED` | Cancelled by either party with reason | Yes |
| `NO_SHOW` | Auto-detected: not completed 2h after end time | Yes |

**`VALID_TRANSITIONS`** dict:

```python
VALID_TRANSITIONS = {
    PENDING: [CONFIRMED, CANCELLED],
    CONFIRMED: [COMPLETED, CANCELLED, NO_SHOW],
    COMPLETED: [],
    CANCELLED: [],
    NO_SHOW: [],
}
```

**`InvalidAppointmentStatusTransitionError`** — Exception with `current` and `target` status.

#### 1.2 Entities

**File:** `src/appointment_bc/appointment/domain/entities.py`

**`Appointment`** — Main entity with state machine:

```python
@dataclass
class Appointment:
    id: str
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    status: AppointmentStatus
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    created_by: str
    location: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    rescheduled_from_id: Optional[str] = None
    reminder_24h_sent: bool = False
    reminder_1h_sent: bool = False
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

Factory method `create()`:
- Generates ULID
- Computes `scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)`
- Sets initial status based on parameter (PENDING for employee, CONFIRMED for technician)
- Validates `duration_minutes` is in {30, 60, 90}

State machine methods:
- `confirm()` — PENDING → CONFIRMED
- `cancel(reason: str, cancelled_by: str)` — PENDING/CONFIRMED → CANCELLED
- `complete(notes: Optional[str])` — CONFIRMED → COMPLETED (sets `completed_at`)
- `mark_no_show()` — CONFIRMED → NO_SHOW
- `mark_reminder_sent(reminder_type: str)` — sets `reminder_24h_sent` or `reminder_1h_sent`

All use `_transition(target)` pattern from PO entity.

**`TechnicianAvailability`** — Configuration entity:

```python
@dataclass
class TechnicianAvailability:
    id: str
    company_id: str
    technician_id: str
    day_of_week: int          # 0=Monday, 6=Sunday
    start_time: time
    end_time: time
```

Factory method `create()`:
- Validates `day_of_week` in range 0-6
- Validates `start_time < end_time`

**`AvailabilityOverride`** — Date-specific override:

```python
@dataclass
class AvailabilityOverride:
    id: str
    company_id: str
    technician_id: str
    date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
```

Factory method `create()`:
- If `is_available=True`, requires `start_time` and `end_time` and validates `start_time < end_time`
- If `is_available=False`, `start_time` and `end_time` are optional (blocks entire day if omitted)

#### 1.3 Domain Service

**File:** `src/appointment_bc/appointment/domain/services.py`

**`AvailabilityService`** — Computes available time slots:

```python
class AvailabilityService:
    @staticmethod
    def compute_available_slots(
        date: date,
        duration_minutes: int,
        recurring_windows: list[TechnicianAvailability],
        overrides: list[AvailabilityOverride],
        existing_appointments: list[Appointment],
    ) -> list[TimeSlot]:
```

Algorithm:
1. Get recurring windows for the given day_of_week
2. Apply overrides for the specific date:
   - If `is_available=False` and no time range → remove all windows (blocked day)
   - If `is_available=False` with time range → subtract that range from windows
   - If `is_available=True` → add the override window
3. Subtract existing CONFIRMED appointment blocks from remaining windows
4. Split remaining windows into bookable slots of `duration_minutes` length
5. Return list of `TimeSlot(start_time, end_time)` value objects

**Default availability:** If no recurring windows exist for a weekday (Mon-Fri), assume 09:00-12:00 and 14:00-17:00. Weekends default to no availability.

**`TimeSlot`** — Simple value object:

```python
@dataclass(frozen=True)
class TimeSlot:
    start: time
    end: time
```

#### 1.4 Repository Interfaces

**File:** `src/appointment_bc/appointment/domain/repository.py`

**`AppointmentRepositoryInterface`:**
- `save(appointment) -> Appointment`
- `find_by_id(id, company_id) -> Optional[Appointment]`
- `find_all(company_id, page, page_size, status?, technician_id?, employee_id?, request_id?, date_from?, date_to?) -> tuple[list[Appointment], int]`
- `find_by_technician_date_range(technician_id, company_id, start, end) -> list[Appointment]` — for overlap detection
- `find_by_employee_date_range(employee_id, company_id, start, end) -> list[Appointment]` — for employee overlap
- `find_by_request_id(request_id, company_id) -> list[Appointment]`
- `find_confirmed_before(before_datetime) -> list[Appointment]` — for no-show detection
- `find_needing_reminder(reminder_type, window_start, window_end) -> list[Appointment]` — for reminders
- `find_pending_or_confirmed_by_request(request_id) -> list[Appointment]` — for request cascade

**`TechnicianAvailabilityRepositoryInterface`:**
- `save_all(technician_id, company_id, windows: list[TechnicianAvailability]) -> None` — upsert (delete old, insert new)
- `find_by_technician(technician_id, company_id) -> list[TechnicianAvailability]`
- `find_by_technician_day(technician_id, company_id, day_of_week) -> list[TechnicianAvailability]`

**`AvailabilityOverrideRepositoryInterface`:**
- `save(override) -> AvailabilityOverride`
- `find_by_id(id, company_id) -> Optional[AvailabilityOverride]`
- `find_by_technician_date_range(technician_id, company_id, date_from, date_to) -> list[AvailabilityOverride]`
- `find_by_technician_date(technician_id, company_id, date) -> list[AvailabilityOverride]`
- `delete(id, company_id) -> bool`

### 2. Infrastructure Layer

#### 2.1 Migrations

**Migration 1: `create_appointments`**

```sql
CREATE TABLE appointments (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    request_id VARCHAR(26) NOT NULL REFERENCES service_requests(id),
    technician_id VARCHAR(26) NOT NULL REFERENCES users(id),
    employee_id VARCHAR(26) NOT NULL REFERENCES users(id),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 60,
    location TEXT,
    notes TEXT,
    cancellation_reason TEXT,
    cancelled_by VARCHAR(26),
    rescheduled_from_id VARCHAR(26) REFERENCES appointments(id),
    reminder_24h_sent BOOLEAN NOT NULL DEFAULT FALSE,
    reminder_1h_sent BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_by VARCHAR(26) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX ix_appointments_company_id ON appointments(company_id);
CREATE INDEX ix_appointments_technician_id ON appointments(technician_id);
CREATE INDEX ix_appointments_employee_id ON appointments(employee_id);
CREATE INDEX ix_appointments_request_id ON appointments(request_id);
CREATE INDEX ix_appointments_status ON appointments(status);
CREATE INDEX ix_appointments_scheduled_start ON appointments(scheduled_start);
```

**Migration 2: `create_technician_availabilities`**

```sql
CREATE TABLE technician_availabilities (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    technician_id VARCHAR(26) NOT NULL REFERENCES users(id),
    day_of_week INTEGER NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(technician_id, day_of_week, start_time)
);

CREATE INDEX ix_technician_availabilities_technician ON technician_availabilities(technician_id);
```

**Migration 3: `create_availability_overrides`**

```sql
CREATE TABLE availability_overrides (
    id VARCHAR(26) PRIMARY KEY,
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    technician_id VARCHAR(26) NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT FALSE,
    start_time TIME,
    end_time TIME,
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(technician_id, date, start_time)
);

CREATE INDEX ix_availability_overrides_technician_date ON availability_overrides(technician_id, date);
```

#### 2.2 SQLAlchemy Models

**File:** `src/appointment_bc/appointment/infrastructure/models.py`

3 models following `Mapped[type]` pattern:

- `AppointmentModel` — extends `ULIDMixin, TimestampMixin, Base`
  - All fields from entity mapped to columns
  - `__tablename__ = "appointments"`
  - ForeignKeys to `companies`, `service_requests`, `users` (technician + employee), self-referential (`rescheduled_from_id`)

- `TechnicianAvailabilityModel` — extends `ULIDMixin, TimestampMixin, Base`
  - `__tablename__ = "technician_availabilities"`
  - UniqueConstraint on `(technician_id, day_of_week, start_time)`
  - Uses `Time` column type for `start_time` / `end_time`

- `AvailabilityOverrideModel` — extends `ULIDMixin, TimestampMixin, Base`
  - `__tablename__ = "availability_overrides"`
  - UniqueConstraint on `(technician_id, date, start_time)`
  - Uses `Date` for `date`, `Time` for optional `start_time` / `end_time`

#### 2.3 Repository Implementations

**File:** `src/appointment_bc/appointment/infrastructure/repository.py`

3 repository classes, each takes `Session` in `__init__`:

- `AppointmentRepository(AppointmentRepositoryInterface)` — full CRUD with model↔entity mapping
  - `save()` follows upsert pattern from PO repo
  - `find_by_technician_date_range()` uses overlap query: `AND model.scheduled_start < end AND model.scheduled_end > start AND model.status == 'CONFIRMED'`
  - `find_confirmed_before()` uses: `WHERE status = 'CONFIRMED' AND scheduled_end < before_datetime`
  - `find_needing_reminder()` filters by reminder flag + time window

- `TechnicianAvailabilityRepository(TechnicianAvailabilityRepositoryInterface)` — simple CRUD
  - `save_all()` deletes existing for technician, inserts new batch

- `AvailabilityOverrideRepository(AvailabilityOverrideRepositoryInterface)` — simple CRUD

### 3. Package Structure

```
src/appointment_bc/
├── __init__.py
└── appointment/
    ├── __init__.py
    ├── application/
    │   ├── __init__.py
    │   ├── commands/
    │   │   └── __init__.py
    │   ├── queries/
    │   │   └── __init__.py
    │   └── ports.py              (optional, for dependency injection)
    ├── domain/
    │   ├── __init__.py
    │   ├── entities.py
    │   ├── enums.py
    │   ├── repository.py
    │   └── services.py
    └── infrastructure/
        ├── __init__.py
        ├── models.py
        └── repository.py
```

## Testing Strategy

### Unit Tests (~15 tests)

**`tests/unit/appointment_bc/appointment/domain/test_entities.py`:**
- Appointment.create() sets correct initial status (PENDING vs CONFIRMED)
- Appointment.create() validates duration (30/60/90 only)
- Appointment.create() computes scheduled_end correctly
- confirm() transitions PENDING → CONFIRMED
- confirm() from CONFIRMED raises InvalidAppointmentStatusTransitionError
- cancel() from PENDING → CANCELLED with reason
- cancel() from CONFIRMED → CANCELLED with reason
- cancel() from COMPLETED raises error
- complete() from CONFIRMED → COMPLETED sets completed_at
- complete() from PENDING raises error
- mark_no_show() from CONFIRMED → NO_SHOW
- TechnicianAvailability.create() validates day_of_week range
- TechnicianAvailability.create() validates start < end
- AvailabilityOverride.create() validates start < end when is_available=True

**`tests/unit/appointment_bc/appointment/domain/test_services.py`:**
- compute_available_slots() with simple recurring window returns correct slots
- compute_available_slots() with blocked override removes entire day
- compute_available_slots() with partial block removes time range
- compute_available_slots() subtracts existing appointments
- compute_available_slots() with extra override adds slots
- compute_available_slots() with no recurring windows returns default weekday hours
- compute_available_slots() on weekend with no windows returns empty
- compute_available_slots() splits windows into correct duration chunks

## Implementation Order

1. Package structure (`__init__.py` files)
2. Enums (`AppointmentStatus`, `VALID_TRANSITIONS`, error)
3. Entities (`Appointment`, `TechnicianAvailability`, `AvailabilityOverride`)
4. Domain service (`AvailabilityService`, `TimeSlot`)
5. Repository interfaces (3 ABC classes)
6. Migrations (3 Alembic migrations)
7. SQLAlchemy models (3 models)
8. Repository implementations (3 classes)
9. Unit tests (entities + service)
10. Verification (lint + tests)

## Risks

- **AvailabilityService algorithm complexity:** Time window arithmetic (subtract, split, merge) requires careful implementation. Extensive unit tests are critical.
- **Time vs DateTime:** Availability uses `time` (no date), appointments use `datetime` (with date). Conversion between them in the service needs care with timezone handling.
- **Self-referential FK:** `rescheduled_from_id` references `appointments(id)`. SQLAlchemy handles this with `ForeignKey("appointments.id")` — no issues expected.
