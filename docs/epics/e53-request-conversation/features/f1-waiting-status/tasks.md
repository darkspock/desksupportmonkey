# Implementation Tasks: F1 — Waiting Status

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-02
**Total Tasks:** 14
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Entities | 1 | M |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | S |
| Application - Commands | 1 | M |
| Application - Queries | 1 | M |
| HTTP - Routers | 1 | S |
| Frontend - Badge + i18n | 1 | S |
| Frontend - RequestDetailPage | 1 | M |
| Frontend - RequestQueuePage | 1 | S |
| Frontend - Dashboard verification | 1 | S |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |

---

## Phase 1: Domain Layer

### TASK-001: Add WAITING_FOR_EMPLOYEE to RequestStatus enum and transitions

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add the new enum value and update the transition map.

**File:** `src/request_bc/request/domain/enums.py`

**Implementation:**

1. Add to `RequestStatus`:
```python
WAITING_FOR_EMPLOYEE = "waiting_for_employee"
```

2. Update `VALID_STATUS_TRANSITIONS`:
```python
RequestStatus.IN_PROGRESS: [
    RequestStatus.RESOLVED,
    RequestStatus.IN_REVIEW,
    RequestStatus.REJECTED,
    RequestStatus.WAITING_FOR_EMPLOYEE,  # NEW
],
RequestStatus.WAITING_FOR_EMPLOYEE: [   # NEW
    RequestStatus.IN_PROGRESS,
    RequestStatus.RESOLVED,
    RequestStatus.REJECTED,
],
```

**Acceptance Criteria:**
- [ ] `WAITING_FOR_EMPLOYEE = "waiting_for_employee"` in `RequestStatus`
- [ ] `IN_PROGRESS` transitions include `WAITING_FOR_EMPLOYEE`
- [ ] `WAITING_FOR_EMPLOYEE` transitions to `IN_PROGRESS`, `RESOLVED`, `REJECTED`
- [ ] No other transitions changed

---

### TASK-002: Add SLA pause fields and update change_status() on ServiceRequest

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Add `sla_paused_at` and `sla_paused_total_seconds` fields to the `ServiceRequest` dataclass. Modify `change_status()` to handle SLA clock pause/resume atomically with the status change.

**File:** `src/request_bc/request/domain/entities.py`

**Implementation:**

1. Add fields to the `ServiceRequest` dataclass:
```python
sla_paused_at: Optional[datetime] = None
sla_paused_total_seconds: int = 0
```

2. Replace the `change_status()` method:
```python
def change_status(self, new_status: RequestStatus) -> None:
    allowed = VALID_STATUS_TRANSITIONS.get(self.status, [])
    if new_status not in allowed:
        raise InvalidStatusTransitionError(self.status, new_status)

    # SLA clock: accumulate paused time when LEAVING waiting_for_employee
    if self.status == RequestStatus.WAITING_FOR_EMPLOYEE and self.sla_paused_at:
        elapsed = (datetime.now(timezone.utc) - self.sla_paused_at).total_seconds()
        self.sla_paused_total_seconds = (self.sla_paused_total_seconds or 0) + int(elapsed)
        self.sla_paused_at = None

    self.status = new_status

    # SLA clock: start pausing when ENTERING waiting_for_employee
    if new_status == RequestStatus.WAITING_FOR_EMPLOYEE:
        self.sla_paused_at = datetime.now(timezone.utc)

    if new_status in (RequestStatus.RESOLVED, RequestStatus.REJECTED):
        self.resolved_at = datetime.now(timezone.utc)
```

**Acceptance Criteria:**
- [ ] `sla_paused_at: Optional[datetime] = None` field added
- [ ] `sla_paused_total_seconds: int = 0` field added
- [ ] Entering `WAITING_FOR_EMPLOYEE` sets `sla_paused_at = now()`
- [ ] Leaving `WAITING_FOR_EMPLOYEE` accumulates elapsed seconds into `sla_paused_total_seconds` and clears `sla_paused_at`
- [ ] `resolved_at` still set when transitioning to `RESOLVED` or `REJECTED`
- [ ] Transition from `WAITING_FOR_EMPLOYEE` → `RESOLVED` both accumulates pause AND sets `resolved_at`
- [ ] Import `timezone` from `datetime` if not already imported

---

## Phase 2: Infrastructure Layer

### TASK-003: Create Alembic migration for SLA pause columns

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `sla_paused_at` and `sla_paused_total_seconds` columns to the `service_requests` table. No CHECK constraint change needed — the status column is `String(20)` validated in domain layer.

**File:** `alembic/versions/e53f1_add_waiting_for_employee_status.py`

**Implementation:**
```python
def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("sla_paused_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "service_requests",
        sa.Column("sla_paused_total_seconds", sa.Integer(), server_default="0", nullable=False),
    )

def downgrade() -> None:
    op.drop_column("service_requests", "sla_paused_total_seconds")
    op.drop_column("service_requests", "sla_paused_at")
```

**Acceptance Criteria:**
- [ ] Migration runs without errors (`make db-upgrade`)
- [ ] `sla_paused_at` column is DateTime, nullable
- [ ] `sla_paused_total_seconds` column is Integer, default 0, not nullable
- [ ] Downgrade drops both columns

---

### TASK-004: Add columns to ServiceRequestModel

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-003

**Description:**
Add the two new columns to the SQLAlchemy model.

**File:** `src/request_bc/request/infrastructure/models.py`

**Implementation:**
Add after `first_response_at`:
```python
sla_paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
sla_paused_total_seconds: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
```

**Acceptance Criteria:**
- [ ] Both columns defined with correct types
- [ ] `Integer` import added if not present
- [ ] Model matches migration schema

---

### TASK-005: Update RequestRepository for new fields

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-004

**Description:**
Update the repository's entity↔model mapping to include the new SLA pause fields.

**File:** `src/request_bc/request/infrastructure/repository.py`

**Implementation:**

1. In `_to_entity()` (model → entity), add:
```python
sla_paused_at=model.sla_paused_at,
sla_paused_total_seconds=model.sla_paused_total_seconds or 0,
```

2. In `save()` (entity → model), add:
```python
model.sla_paused_at = request.sla_paused_at
model.sla_paused_total_seconds = request.sla_paused_total_seconds
```

**Acceptance Criteria:**
- [ ] `_to_entity()` hydrates `sla_paused_at` and `sla_paused_total_seconds`
- [ ] `save()` persists both fields
- [ ] Default `0` used when `sla_paused_total_seconds` is None in DB

---

## Phase 3: Application Layer

### TASK-006: Add auto-transition logic to AddCommentCommandHandler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-002, TASK-005

**Description:**
After saving a comment, if the request is in `WAITING_FOR_EMPLOYEE` status, auto-transition to `IN_PROGRESS`. Save the request and create a `status_changed` audit event.

**File:** `src/request_bc/request/application/commands/add_comment.py`

**Implementation:**
Add after the existing `save_event()` call:
```python
# AUTO-TRANSITION: any comment on waiting_for_employee → in_progress
if request.status == RequestStatus.WAITING_FOR_EMPLOYEE:
    old_status = request.status.value
    request.change_status(RequestStatus.IN_PROGRESS)
    self.request_repo.save(request)
    auto_event = RequestEvent.create(
        request_id=command.request_id,
        event_type="status_changed",
        data={"old_status": old_status, "new_status": RequestStatus.IN_PROGRESS.value, "auto": True},
        performed_by=command.author_id,
    )
    self.request_repo.save_event(auto_event)
```

**Acceptance Criteria:**
- [ ] Import `RequestStatus` from domain enums
- [ ] Auto-transition only fires when status is `WAITING_FOR_EMPLOYEE`
- [ ] `change_status()` called (triggers SLA accumulation)
- [ ] Request saved after status change
- [ ] Audit event created with `"auto": True` in data
- [ ] No transition attempted if status is any other value

---

### TASK-007: Update SLA query to subtract paused time

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-005

**Description:**
Modify the resolution elapsed time calculation to subtract `sla_paused_total_seconds`. Also handle the case where the request is currently in `waiting_for_employee` (active pause — `sla_paused_at` is set but not yet accumulated).

**File:** `src/sla_bc/sla/application/queries/get_request_sla.py`

**Implementation:**
Replace the resolution elapsed calculation with:
```python
# Calculate total paused time (finalized + active)
paused_seconds = request.sla_paused_total_seconds or 0
if request.sla_paused_at:
    paused_seconds += (now - request.sla_paused_at).total_seconds()

# Subtract paused time from resolution elapsed
if request.resolved_at:
    resolution_elapsed = ((request.resolved_at - created).total_seconds() - paused_seconds) / 3600
else:
    resolution_elapsed = ((now - created).total_seconds() - paused_seconds) / 3600
resolution_elapsed = max(0, round(resolution_elapsed, 2))
```

**Acceptance Criteria:**
- [ ] Finalized paused time (`sla_paused_total_seconds`) subtracted from resolution elapsed
- [ ] Active pause time (`now - sla_paused_at`) included when request is currently in `waiting_for_employee`
- [ ] `resolution_elapsed` never goes negative (`max(0, ...)`)
- [ ] Rounding preserved (2 decimal places)
- [ ] No change to response elapsed time (SLA response time is unaffected)

---

## Phase 4: HTTP Layer

### TASK-008: Publish auto-transition event from comment endpoint

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-006

**Description:**
After executing `AddCommentCommand`, detect if an auto-transition occurred (status changed from `waiting_for_employee` to `in_progress`) and publish a `REQUEST_STATUS_CHANGED` domain event so notification subscribers are triggered.

**File:** `adapters/http/api/requests/routers.py`

**Implementation:**
In the `add_comment` endpoint, before calling the handler:
```python
old_status = sr.status.value  # capture before command
```

After the handler call and before the return:
```python
# Check for auto-transition and publish event
sr_after = request_repo.find_by_id(request_id, current_user.company_id)
if sr_after and sr_after.status.value != old_status:
    auto_event = RequestEventFactory.status_changed(
        sr_after, old_status=old_status, new_status=sr_after.status.value,
        actor_id=current_user.id,
    )
    event_bus.publish(auto_event, db)
```

**Acceptance Criteria:**
- [ ] `old_status` captured before handler execution
- [ ] Request reloaded after handler to detect status change
- [ ] `REQUEST_STATUS_CHANGED` event published only when auto-transition occurred
- [ ] Event includes correct `old_status` and `new_status`
- [ ] No event published when status didn't change (normal comment on non-waiting request)

---

## Phase 5: Frontend

### TASK-009: Add badge color and i18n keys for waiting_for_employee

**Phase:** Frontend
**Complexity:** S
**Dependencies:** None (can start in parallel with backend)

**Description:**
Add the status badge color mapping and i18n labels for the new status.

**Files:**
- `web/app/src/components/ui/Badge.tsx`
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Implementation:**

1. **Badge.tsx** (line 22) — add to status color map:
```typescript
waiting_for_employee: 'warning',
```

2. **en.ts** — add to enum translations:
```typescript
waiting_for_employee: 'Waiting for employee',
```

3. **es.ts** — add to enum translations:
```typescript
waiting_for_employee: 'Pendiente del empleado',
```

**Acceptance Criteria:**
- [ ] Badge renders amber/warning color for `waiting_for_employee`
- [ ] English label: "Waiting for employee"
- [ ] Spanish label: "Pendiente del empleado"

---

### TASK-010: Update RequestDetailPage status transitions

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-009

**Description:**
Add `waiting_for_employee` to the status transition map, the status flow stepper logic, and the action dropdown. Do NOT add it to the linear STATUS_FLOW stepper (it's a side-branch).

**File:** `web/app/src/pages/technician/RequestDetailPage.tsx`

**Implementation:**

1. **nextStatuses map** (~line 729) — add transitions:
```typescript
in_progress: ['resolved', 'rejected', 'waiting_for_employee'],
waiting_for_employee: ['in_progress', 'resolved', 'rejected'],
```

2. **nextStep map** (~line 747) — add:
```typescript
waiting_for_employee: 'in_progress',
```

3. **STATUS_FLOW / STATUS_FLOW_WITH_APPROVAL** (~line 250-251) — do NOT add `waiting_for_employee` (it's a side-branch, not a linear step). The stepper should show the current status correctly even when it's `waiting_for_employee` by treating it as a variant of `in_progress`.

4. **isRejected-style guards** — add check for `waiting_for_employee` where terminal/closed status checks exist (e.g., line 584 for appointments).

5. **canAssign check** — include `waiting_for_employee` in the list of statuses where assignment is possible if needed.

**Acceptance Criteria:**
- [ ] Technician can select "Waiting for employee" from action dropdown when status is `in_progress`
- [ ] From `waiting_for_employee`, can transition to `in_progress`, `resolved`, `rejected`
- [ ] Status flow stepper does NOT show `waiting_for_employee` as a step
- [ ] Status badge shows amber/warning in detail page header
- [ ] No broken UI when request is in `waiting_for_employee`

---

### TASK-011: Update RequestQueuePage kanban and stats

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Include `waiting_for_employee` requests in the `in_progress` kanban column and stats count.

**File:** `web/app/src/pages/technician/RequestQueuePage.tsx`

**Implementation:**

1. **Kanban in_progress column filter** (~line 338):
```typescript
items: kanbanRequests.filter((r) => r.status === 'in_progress' || r.status === 'waiting_for_employee'),
```

2. **Stats in_progress count** (~line 219):
```typescript
in_progress: all.filter(r => r.status === 'in_progress' || r.status === 'waiting_for_employee').length,
```

3. **canAssign check** (~line 275) — add `waiting_for_employee` if technician should be able to assign/reassign:
```typescript
const canAssign = ['submitted', 'in_review', 'in_progress', 'waiting_for_employee'].includes(r.status);
```

4. **Quick actions** — add "Mark in progress" action for `waiting_for_employee` requests:
```typescript
if (r.status === 'waiting_for_employee') {
    actions.push({
        label: t('enum.in_progress'),
        onClick: () => statusMut.mutate({ id: r.id, newStatus: 'in_progress' }),
    });
}
```

**Acceptance Criteria:**
- [ ] `waiting_for_employee` requests visible in the `in_progress` kanban column
- [ ] Stats count includes `waiting_for_employee` in `in_progress` total
- [ ] Quick action to return to `in_progress` available on kanban cards
- [ ] Kanban drag should not break for `waiting_for_employee` cards

---

### TASK-012: Verify dashboard and SLA dashboard handle new status

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Check `DashboardPage.tsx` and `SlaDashboardPage.tsx` to verify they handle the new status dynamically. If status breakdown is hardcoded, add `waiting_for_employee`.

**Files:**
- `web/app/src/pages/admin/DashboardPage.tsx`
- `web/app/src/pages/admin/SlaDashboardPage.tsx`
- `web/app/src/pages/technician/MyAssignedRequestsPage.tsx`

**Implementation:**
Read each file and verify:
1. Status breakdown charts — are they generated from API data (dynamic) or hardcoded?
2. Status filters — do they accept arbitrary values or have a fixed list?
3. If hardcoded, add `waiting_for_employee` to the relevant lists.

**Acceptance Criteria:**
- [ ] Dashboard status pie chart / counts include `waiting_for_employee`
- [ ] SLA dashboard correctly reflects paused time
- [ ] MyAssignedRequestsPage shows `waiting_for_employee` requests
- [ ] No broken UI on any admin/technician dashboard

---

## Phase 6: Tests

### TASK-013: Unit tests for status transitions, auto-transition, and SLA pause

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-002, TASK-006, TASK-007

**Description:**
Create unit tests covering all the domain and application layer changes.

**Files:**
- `tests/unit/request/test_request_status.py` (new or extend)
- `tests/unit/request/test_service_request.py` (new or extend)
- `tests/unit/request/test_add_comment.py` (new or extend)
- `tests/unit/sla/test_get_request_sla.py` (new or extend)

**Test scenarios:**

**Status transitions:**
- [ ] `in_progress` → `waiting_for_employee` ✓ (valid)
- [ ] `waiting_for_employee` → `in_progress` ✓ (valid)
- [ ] `waiting_for_employee` → `resolved` ✓ (valid)
- [ ] `waiting_for_employee` → `rejected` ✓ (valid)
- [ ] `submitted` → `waiting_for_employee` ✗ (raises `InvalidStatusTransitionError`)
- [ ] `in_review` → `waiting_for_employee` ✗ (raises `InvalidStatusTransitionError`)
- [ ] `resolved` → `waiting_for_employee` ✗ (raises `InvalidStatusTransitionError`)

**SLA pause/resume fields:**
- [ ] Entering `waiting_for_employee` sets `sla_paused_at` to current time
- [ ] Leaving `waiting_for_employee` accumulates elapsed seconds and clears `sla_paused_at`
- [ ] Multiple cycles: 2 × 1h = 2h accumulated in `sla_paused_total_seconds`
- [ ] `waiting_for_employee` → `resolved`: both accumulates pause AND sets `resolved_at`

**Auto-transition (AddCommentHandler):**
- [ ] Comment on `waiting_for_employee` request → status becomes `in_progress`
- [ ] Comment on `in_progress` request → no status change
- [ ] Comment on `submitted` request → no status change
- [ ] Auto-transition creates `status_changed` event with `"auto": True`

**SLA query:**
- [ ] Request with 4h total, 1h paused → resolution elapsed = 3h
- [ ] Request with 4h total, 0h paused → resolution elapsed = 4h (unchanged)
- [ ] Request currently in `waiting_for_employee` for 2h → active pause included in deduction
- [ ] Multiple cycles: 2h finalized + 1h active = 3h deducted
- [ ] Resolution elapsed never goes negative

---

### TASK-014: Integration tests for status change and comment auto-transition endpoints

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-008, TASK-005

**Description:**
Create integration tests for the HTTP endpoints.

**File:** `tests/integration/test_request_endpoints.py` (extend existing)

**Test scenarios:**

- [ ] `PATCH /requests/{id}/status` with `waiting_for_employee` → 200, status updated
- [ ] `PATCH /requests/{id}/status` with `waiting_for_employee` from `submitted` → 409 (invalid transition)
- [ ] `POST /requests/{id}/comments` on `waiting_for_employee` request → 200, comment saved AND status auto-transitions to `in_progress`
- [ ] `POST /requests/{id}/comments` on `waiting_for_employee` → `REQUEST_STATUS_CHANGED` event published
- [ ] `GET /requests/?status=waiting_for_employee` → returns matching requests
- [ ] Status filter API accepts `waiting_for_employee` as valid value

---

## Dependency Graph

```
TASK-001 (Enum)
    │
    └── TASK-002 (Entity + change_status)
            │
            ├── TASK-003 (Migration)
            │       │
            │       └── TASK-004 (Model)
            │               │
            │               └── TASK-005 (Repository)
            │                       │
            │                       ├── TASK-006 (AddComment auto-transition)
            │                       │       │
            │                       │       └── TASK-008 (Router event publish)
            │                       │
            │                       ├── TASK-007 (SLA query)
            │                       │
            │                       └── TASK-014 (Integration tests)
            │
            ├── TASK-006 ──► TASK-013 (Unit tests)
            └── TASK-007 ──► TASK-013

TASK-009 (Badge + i18n) ── no backend deps, can start immediately
    │
    ├── TASK-010 (RequestDetailPage)
    ├── TASK-011 (RequestQueuePage)
    └── TASK-012 (Dashboard verification)
```

## Execution Order

**Batch 1 (Parallel — backend + frontend start together):**
- TASK-001: Enum + transitions
- TASK-009: Badge color + i18n keys

**Batch 2 (After Batch 1):**
- TASK-002: Entity fields + change_status logic

**Batch 3 (After TASK-002, parallel):**
- TASK-003: Alembic migration
- TASK-010: RequestDetailPage transitions
- TASK-011: RequestQueuePage kanban + stats
- TASK-012: Dashboard verification

**Batch 4 (After TASK-003):**
- TASK-004: ServiceRequestModel columns

**Batch 5 (After TASK-004):**
- TASK-005: Repository mapping

**Batch 6 (After TASK-005, parallel):**
- TASK-006: AddCommentHandler auto-transition
- TASK-007: SLA query update

**Batch 7 (After TASK-006):**
- TASK-008: Router event publish

**Batch 8 (After all implementation, parallel):**
- TASK-013: Unit tests
- TASK-014: Integration tests

## Final Checklist

- [x] All 14 tasks completed
- [x] `make db-upgrade` — migration applies cleanly
- [x] `make test` — no new failures (12 pre-existing failures in vulnerability_bc, enums, location — unrelated)
- [x] `make lint` — no new errors (5 pre-existing mypy errors in vulnerability_bc — unrelated)
- [ ] Manual verification: set request to `waiting_for_employee`, add comment, confirm auto-transition
- [ ] Manual verification: SLA dashboard shows correct adjusted times
