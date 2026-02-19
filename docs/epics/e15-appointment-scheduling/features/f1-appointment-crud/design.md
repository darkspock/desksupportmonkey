# Solution Design: F1 — Appointment CRUD & Notifications

**Requirement:** [../../requirements.md](../../requirements.md)
**Date:** 2026-02-18
**Bounded Context:** `appointment_bc`
**Depends on:** F0 (complete)

## Summary

F1 delivers the full appointment lifecycle: create, confirm, cancel, complete, reschedule, list, get, and "my appointments". It adds 8 API endpoints, 5 notification event types, an `AppointmentEventFactory`, and auto-cancel cascade when a linked request is resolved/rejected.

## Architecture Decision

All commands and queries follow the existing CQRS pattern: `Command`/`CommandHandler` and `Query`/`QueryHandler` from `src.framework.application.command_bus` and `query_bus`. Events use the existing `EventBus` + `DomainEvent` pattern with a new `AppointmentEventFactory`.

### Existing Code Reuse

| Component | Location | Reuse |
|-----------|----------|-------|
| Command/CommandHandler | `src/framework/application/command_bus.py` | Inherit |
| Query/QueryHandler | `src/framework/application/query_bus.py` | Inherit |
| EventBus | `src/notification_bc/notification/application/services/event_bus.py` | Use as-is |
| DomainEvent | `src/notification_bc/notification/domain/events.py` | Use as-is |
| RequestEventFactory | `src/notification_bc/notification/application/services/event_factory.py` | Pattern reuse |
| EventType | `src/notification_bc/notification/domain/enums.py` | Add 5 values |
| TargetResolver | `src/notification_bc/notification/application/services/target_resolver.py` | Add 5 resolvers |
| get_event_bus | `adapters/http/api/dependencies.py` | Use as-is |

## Implementation Plan

### 1. Application Layer — Commands

#### 1.1 CreateAppointmentCommand

**File:** `src/appointment_bc/appointment/application/commands/create_appointment.py`

```python
@dataclass
class CreateAppointmentCommand(Command):
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    scheduled_start: datetime
    duration_minutes: int
    created_by: str
    creator_role: str  # "technician" or "employee"
    location: Optional[str] = None
    rescheduled_from_id: Optional[str] = None
```

Handler logic:
1. Set `initial_status` = CONFIRMED if `creator_role` in ("technician", "admin"), else PENDING
2. Call `Appointment.create(...)` — validates duration
3. Check technician overlap via `appointment_repo.find_by_technician_date_range()`
4. Check employee overlap via `appointment_repo.find_by_employee_date_range()`
5. Save and return appointment ID

#### 1.2 ConfirmAppointmentCommand

**File:** `src/appointment_bc/appointment/application/commands/confirm_appointment.py`

```python
@dataclass
class ConfirmAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    performed_by: str
```

Handler: load appointment, call `confirm()`, save.

#### 1.3 CancelAppointmentCommand

**File:** `src/appointment_bc/appointment/application/commands/cancel_appointment.py`

```python
@dataclass
class CancelAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    reason: str
    performed_by: str
```

Handler: load appointment, call `cancel(reason, performed_by)`, save.

#### 1.4 CompleteAppointmentCommand

**File:** `src/appointment_bc/appointment/application/commands/complete_appointment.py`

```python
@dataclass
class CompleteAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    performed_by: str
    notes: Optional[str] = None
```

Handler: load appointment, call `complete(notes)`, save.

#### 1.5 RescheduleAppointmentCommand

**File:** `src/appointment_bc/appointment/application/commands/reschedule_appointment.py`

```python
@dataclass
class RescheduleAppointmentCommand(Command):
    appointment_id: str
    company_id: str
    new_start: datetime
    new_duration_minutes: int
    performed_by: str
    creator_role: str
    reason: str
    location: Optional[str] = None
```

Handler:
1. Load existing appointment
2. Cancel it with reason "Rescheduled"
3. Create new appointment with `rescheduled_from_id = old.id`
4. Check overlaps for new time
5. Save both, return new appointment ID

### 2. Application Layer — Queries

#### 2.1 ListAppointmentsQuery

**File:** `src/appointment_bc/appointment/application/queries/list_appointments.py`

```python
@dataclass
class ListAppointmentsQuery(Query):
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
    technician_id: Optional[str] = None
    employee_id: Optional[str] = None
    request_id: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
```

Handler: delegates to `appointment_repo.find_all(...)`.

#### 2.2 GetAppointmentQuery

**File:** `src/appointment_bc/appointment/application/queries/get_appointment.py`

```python
@dataclass
class GetAppointmentQuery(Query):
    appointment_id: str
    company_id: str
```

Handler: `find_by_id()`, raise `AppointmentNotFoundError` if None.

#### 2.3 MyAppointmentsQuery

**File:** `src/appointment_bc/appointment/application/queries/my_appointments.py`

```python
@dataclass
class MyAppointmentsQuery(Query):
    employee_id: str
    company_id: str
    page: int = 1
    page_size: int = 20
    status: Optional[str] = None
```

Handler: delegates to `appointment_repo.find_all()` with `employee_id` filter.

### 3. HTTP Layer

#### 3.1 Router

**File:** `adapters/http/api/appointments/routers.py`

**Endpoints:**

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/appointments` | technician+ | Create appointment |
| GET | `/api/v1/appointments` | technician+ | List appointments |
| GET | `/api/v1/appointments/{id}` | any authenticated | Get appointment detail |
| POST | `/api/v1/appointments/{id}/confirm` | technician+ | Confirm pending appointment |
| POST | `/api/v1/appointments/{id}/cancel` | any authenticated | Cancel appointment |
| POST | `/api/v1/appointments/{id}/complete` | technician+ | Mark as completed |
| POST | `/api/v1/appointments/{id}/reschedule` | technician+ | Reschedule (cancel + create new) |
| GET | `/api/v1/my/appointments` | any authenticated | Employee's own appointments |

Note: "My appointments" goes on the existing `/api/v1/my/` router.

#### 3.2 Schemas

**File:** `adapters/http/api/appointments/schemas.py`

```python
class AppointmentCreateRequest(BaseModel):
    request_id: str
    technician_id: str
    employee_id: str
    scheduled_start: datetime
    duration_minutes: int = Field(ge=30, le=90)
    location: Optional[str] = None

class CancelAppointmentRequest(BaseModel):
    reason: str

class CompleteAppointmentRequest(BaseModel):
    notes: Optional[str] = None

class RescheduleAppointmentRequest(BaseModel):
    new_start: datetime
    new_duration_minutes: int = Field(ge=30, le=90)
    reason: str
    location: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: str
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    location: Optional[str]
    notes: Optional[str]
    cancellation_reason: Optional[str]
    cancelled_by: Optional[str]
    rescheduled_from_id: Optional[str]
    completed_at: Optional[datetime]
    created_by: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    # Enriched fields
    technician_email: Optional[str] = None
    employee_email: Optional[str] = None
```

#### 3.3 Dependencies

**File:** `adapters/http/api/appointments/dependencies.py`

```python
def get_appointment_repo(db = Depends(get_db)):
    return AppointmentRepository(db)
```

### 4. Notification Integration

#### 4.1 EventType additions

**File:** `src/notification_bc/notification/domain/enums.py` — Add:

```python
APPOINTMENT_CREATED = "appointment.created"
APPOINTMENT_CONFIRMED = "appointment.confirmed"
APPOINTMENT_CANCELLED = "appointment.cancelled"
APPOINTMENT_RESCHEDULED = "appointment.rescheduled"
APPOINTMENT_COMPLETED = "appointment.completed"
```

#### 4.2 AppointmentEventFactory

**File:** `src/notification_bc/notification/application/services/appointment_event_factory.py`

Static methods creating `DomainEvent` for each appointment event type. Payload always includes: `appointment_id`, `request_id`, `technician_id`, `employee_id`.

#### 4.3 TargetResolver additions

Add 5 resolver methods to existing `TargetResolver`. Each appointment event notifies the other party (technician ↔ employee):
- `CREATED` → notify employee (if technician created) or technician (if employee created)
- `CONFIRMED` → notify employee
- `CANCELLED` → notify both parties
- `RESCHEDULED` → notify both parties
- `COMPLETED` → notify employee

### 5. Collateral Impact — Request Status Cascade

**File:** `adapters/http/api/requests/routers.py` (or a subscriber)

When a request status changes to RESOLVED or REJECTED, auto-cancel all PENDING/CONFIRMED appointments linked to that request:
- Query `appointment_repo.find_pending_or_confirmed_by_request(request_id)`
- For each: call `appointment.cancel(reason="Request resolved", cancelled_by=performed_by)` and save

This is done in the request router's `change_request_status` endpoint, after the status change succeeds, using the appointment repo from dependencies.

### 6. App Registration

**File:** `app.py` — Add:
```python
from adapters.http.api.appointments.routers import router as appointments_router
app.include_router(appointments_router)
```

## Testing Strategy

### Unit Tests (~18 tests)

**`tests/unit/appointment_bc/appointment/application/commands/test_create.py`:**
- Create with valid data returns ID
- Create with invalid duration raises ValueError
- Create sets CONFIRMED status when creator is technician
- Create sets PENDING status when creator is employee
- Create detects technician overlap raises ValueError
- Create detects employee overlap raises ValueError
- Create with rescheduled_from_id links correctly

**`tests/unit/appointment_bc/appointment/application/commands/test_transitions.py`:**
- Confirm from PENDING succeeds
- Confirm from CONFIRMED raises error
- Cancel from PENDING sets reason and cancelled_by
- Cancel from COMPLETED raises error
- Complete from CONFIRMED sets completed_at
- Complete from PENDING raises error

**`tests/unit/appointment_bc/appointment/application/commands/test_reschedule.py`:**
- Reschedule cancels old and creates new
- Reschedule links via rescheduled_from_id
- Reschedule detects overlap on new time

**`tests/unit/appointment_bc/appointment/application/queries/test_queries.py`:**
- List returns paginated results
- Get returns appointment or raises not found

### Integration Tests (~10 tests)

**`tests/integration/test_appointments_endpoints.py`:**
- POST create → 201
- GET list → 200 with pagination
- GET detail → 200
- POST confirm → 200
- POST cancel → 200
- POST complete → 200
- POST reschedule → 201
- GET my appointments → 200
- Create with overlap → 409
- Status cascade on request resolve

## Implementation Order

1. Notification enums (add 5 EventType values)
2. AppointmentEventFactory
3. TargetResolver additions (5 methods)
4. Commands (create, confirm, cancel, complete, reschedule)
5. Queries (list, get, my)
6. Schemas + Dependencies
7. Router + App registration
8. Request cascade (collateral)
9. Unit tests
10. Integration tests
11. Verification
