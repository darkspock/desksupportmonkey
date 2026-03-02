# Solution Design: F1 — Waiting Status

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Bounded Contexts:** `request_bc` (primary), `sla_bc` (SLA calculation), `notification_bc` (events)

## Summary

Add `WAITING_FOR_EMPLOYEE` to the `RequestStatus` enum with bidirectional transitions from `in_progress`. Extend the `ServiceRequest` entity with two new fields (`sla_paused_at`, `sla_paused_total_seconds`) for SLA clock pause tracking. Modify `AddCommentCommandHandler` to auto-transition requests out of `waiting_for_employee` when any comment is added. Update the SLA query to subtract paused time. Add the status to frontend badge colors, transition maps, and filter/kanban.

## Architecture Decision

**Approach:** Minimal domain extension — add enum value + transition rules + 2 new fields. No new entities, no new commands/queries, no new bounded contexts.

**Why:** The existing `change_status()` method on `ServiceRequest` already validates transitions via `VALID_STATUS_TRANSITIONS`. Adding a new status value is a natural extension. The SLA pause fields avoid the overhead of querying the event log for clock calculations.

**Alternatives considered:**
1. *New `SlaClockEntry` table* — Rejected: overkill for tracking pause/resume. The two-field approach handles multiple cycles correctly.
2. *Query `RequestEvent` log for SLA calculation* — Rejected: fragile, slower at query time, not designed for this purpose.
3. *New `ChangeStatusToWaitingCommand`* — Rejected: the existing `ChangeRequestStatusCommand` already handles all transitions generically. Adding special-case commands fragments the state machine.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `RequestStatus` enum | `src/request_bc/request/domain/enums.py` | Yes | Add `WAITING_FOR_EMPLOYEE` value |
| `VALID_STATUS_TRANSITIONS` dict | `src/request_bc/request/domain/enums.py` | Yes | Add transitions for `IN_PROGRESS` → `WAITING_FOR_EMPLOYEE` and `WAITING_FOR_EMPLOYEE` → `{IN_PROGRESS, RESOLVED, REJECTED}` |
| `ServiceRequest.change_status()` | `src/request_bc/request/domain/entities.py` | Yes | Add SLA pause/resume logic (set `sla_paused_at` on enter, accumulate on leave) |
| `ServiceRequest` dataclass | `src/request_bc/request/domain/entities.py` | Yes | Add `sla_paused_at` and `sla_paused_total_seconds` fields |
| `ChangeRequestStatusCommandHandler` | `src/request_bc/request/application/commands/change_request_status.py` | Yes | No changes — transition validation already delegates to `ServiceRequest.change_status()` |
| `AddCommentCommandHandler` | `src/request_bc/request/application/commands/add_comment.py` | Yes | Add auto-transition: if status is `WAITING_FOR_EMPLOYEE`, call `change_status(IN_PROGRESS)` and save |
| `ServiceRequestModel` | `src/request_bc/request/infrastructure/models.py` | Yes | Add `sla_paused_at` and `sla_paused_total_seconds` columns |
| `RequestRepository` | `src/request_bc/request/infrastructure/repository.py` | Yes | Update `_to_entity()` and `save()` for new fields |
| `GetRequestSlaStatusQueryHandler` | `src/sla_bc/sla/application/queries/get_request_sla.py` | Yes | Subtract `sla_paused_total_seconds` from resolution elapsed time |
| `RequestEventFactory.status_changed()` | `src/notification_bc/.../event_factory.py` | Yes | No changes — already includes `old_status` and `new_status` in payload |
| `TargetResolver._resolve_request_status_changed()` | `src/notification_bc/.../target_resolver.py` | Yes | No changes — already targets `created_by` + `assigned_to` |
| Status badge colors | `web/app/src/components/ui/Badge.tsx` | Yes | Add `waiting_for_employee: 'warning'` |
| Status transitions (frontend) | `web/app/src/pages/technician/RequestDetailPage.tsx` | Yes | Add transitions, status flow steps, UI button |
| Kanban columns | `web/app/src/pages/technician/RequestQueuePage.tsx` | Yes | Include `waiting_for_employee` in `in_progress` column |
| i18n | `web/app/src/locales/en.ts` + `es.ts` | Yes | Add status label |
| Status change endpoint | `adapters/http/api/requests/routers.py` | Yes | No changes — already accepts any `status` string and delegates to command handler |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| `ServiceRequest` | `src/request_bc/request/domain/entities.py` | Add `sla_paused_at: Optional[datetime]` and `sla_paused_total_seconds: int` fields. Modify `change_status()` to handle SLA pause/resume. |

**ServiceRequest.change_status() — updated logic:**

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

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| `RequestStatus` | `src/request_bc/request/domain/enums.py` | Add `WAITING_FOR_EMPLOYEE = "waiting_for_employee"` |

**VALID_STATUS_TRANSITIONS — additions:**

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

#### Domain Events

No new domain events. The existing `REQUEST_STATUS_CHANGED` event already carries `old_status` and `new_status` in its payload, which is sufficient.

### 2. Application Layer

#### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| `AddCommentCommand` | `AddCommentCommandHandler` | **Modify**: After saving the comment, check if request is in `WAITING_FOR_EMPLOYEE`. If yes, auto-transition to `IN_PROGRESS`, save request, and create a status_changed event. |

**AddCommentCommandHandler.handle() — auto-transition addition:**

```python
def handle(self, command: AddCommentCommand) -> None:
    request = self.request_repo.find_by_id(command.request_id, command.company_id)
    if not request:
        raise RequestNotFoundException(command.request_id)

    comment = RequestComment.create(
        request_id=command.request_id,
        author_id=command.author_id,
        body=command.body,
        id=command.id,
    )
    self.request_repo.save_comment(comment)

    event = RequestEvent.create(
        request_id=command.request_id,
        event_type="comment_added",
        data={"comment_id": comment.id, "author_id": command.author_id},
        performed_by=command.author_id,
    )
    self.request_repo.save_event(event)

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

**Note:** The router (not the handler) publishes domain events to the EventBus for notification subscribers. The auto-transition status change also needs an EventBus event. Two options:

- **Option A:** Pass `event_bus` into the handler — breaks current pattern (handlers don't have EventBus)
- **Option B (recommended):** Return a flag from the handler indicating auto-transition occurred, and let the router publish the event

Since commands return None, Option B requires the router to re-check the request status after the command. The router already loads the request — it can compare old vs new status.

**Router-level approach:**

```python
# In the add_comment endpoint (routers.py)
old_status = sr.status.value  # capture before command

handler.handle(AddCommentCommand(...))

# Refresh request to check for auto-transition
sr_after = request_repo.find_by_id(request_id, current_user.company_id)
if sr_after and sr_after.status.value != old_status:
    # Auto-transition happened — publish status change event
    event = RequestEventFactory.status_changed(
        sr_after, old_status=old_status, new_status=sr_after.status.value,
        actor_id=current_user.id,
    )
    event_bus.publish(event, db)
```

#### Queries

| Query | Handler | Description |
|-------|---------|-------------|
| `GetRequestSlaStatusQuery` | `GetRequestSlaStatusQueryHandler` | **Modify**: Subtract `sla_paused_total_seconds` from resolution elapsed time. Handle active pause (status is currently `waiting_for_employee`). |

**SLA calculation change:**

```python
# Current:
resolution_elapsed = (resolved_at_or_now - created_at).total_seconds() / 3600

# New:
paused_seconds = request.sla_paused_total_seconds or 0
# If currently paused (still in waiting_for_employee), add ongoing pause time
if request.sla_paused_at:
    paused_seconds += (now - request.sla_paused_at).total_seconds()
resolution_elapsed = ((resolved_at_or_now - created_at).total_seconds() - paused_seconds) / 3600
resolution_elapsed = max(0, round(resolution_elapsed, 2))
```

### 3. Infrastructure Layer

#### Models

| Model | File Path | Changes |
|-------|-----------|---------|
| `ServiceRequestModel` | `src/request_bc/request/infrastructure/models.py` | Add `sla_paused_at: Mapped[Optional[datetime]]` and `sla_paused_total_seconds: Mapped[int]` columns |

```python
# New columns on ServiceRequestModel:
sla_paused_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
sla_paused_total_seconds: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
```

#### Repository

| Interface | Implementation | Changes |
|-----------|----------------|---------|
| `RequestRepositoryInterface` | `RequestRepository` | Update `save()` to persist new fields. Update `_to_entity()` to hydrate new fields. |

**_to_entity() addition:**

```python
sla_paused_at=model.sla_paused_at,
sla_paused_total_seconds=model.sla_paused_total_seconds or 0,
```

**save() addition:**

```python
model.sla_paused_at = request.sla_paused_at
model.sla_paused_total_seconds = request.sla_paused_total_seconds
```

#### Migrations

| Migration | Description |
|-----------|-------------|
| `e53f1_add_waiting_for_employee_status` | Add `sla_paused_at` (DateTime, nullable) and `sla_paused_total_seconds` (Integer, default 0) columns to `service_requests`. No CHECK constraint change needed — the status column is `String(20)` without a CHECK constraint (validated in domain layer). |

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

### 4. HTTP Layer

#### Endpoints

No new endpoints. The existing PATCH `/api/v1/requests/{request_id}/status` already accepts any status string and delegates validation to the command handler / entity.

**Modification to add_comment endpoint** (`POST /api/v1/requests/{request_id}/comments`):

After executing `AddCommentCommand`, check if auto-transition occurred and publish `REQUEST_STATUS_CHANGED` event if so.

#### Router changes

| File | Change |
|------|--------|
| `adapters/http/api/requests/routers.py` | Modify `add_comment` endpoint to detect and publish auto-transition event |

### 5. Frontend Changes

#### Badge color

| File | Change |
|------|--------|
| `web/app/src/components/ui/Badge.tsx` | Add `waiting_for_employee: 'warning'` to status color map (line 22) |

#### Status transitions (RequestDetailPage.tsx)

```typescript
// Line ~729 - Add to nextStatuses:
in_progress: ['resolved', 'rejected', 'waiting_for_employee'],
waiting_for_employee: ['in_progress', 'resolved', 'rejected'],

// Line ~250 - STATUS_FLOW: Add waiting_for_employee between in_progress and resolved
// (or handle separately since it's a side-branch, not a linear step)

// Line ~747 - nextStep map: Add waiting_for_employee → in_progress
```

#### Kanban columns (RequestQueuePage.tsx)

`waiting_for_employee` requests should appear in the `in_progress` kanban column (they're still active, just paused). Add to the filter on line 338:

```typescript
items: kanbanRequests.filter((r) => r.status === 'in_progress' || r.status === 'waiting_for_employee'),
```

#### Status filter (RequestQueuePage.tsx)

Add `waiting_for_employee` to the status filter dropdown if one exists, or ensure the existing filter passes the value through.

#### Stats counts (RequestQueuePage.tsx)

Include `waiting_for_employee` in the `in_progress` count or add a separate stat:

```typescript
in_progress: all.filter(r => r.status === 'in_progress' || r.status === 'waiting_for_employee').length,
```

#### i18n

| File | Keys |
|------|------|
| `web/app/src/locales/en.ts` | `enum.waiting_for_employee: "Waiting for employee"` |
| `web/app/src/locales/es.ts` | `enum.waiting_for_employee: "Pendiente del empleado"` |

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/request_bc/request/domain/enums.py` | Modify | Add enum value + transitions |
| `src/request_bc/request/domain/entities.py` | Modify | Add fields + SLA pause logic in `change_status()` |
| `src/request_bc/request/application/commands/add_comment.py` | Modify | Auto-transition logic |
| `src/request_bc/request/infrastructure/models.py` | Modify | Add 2 columns |
| `src/request_bc/request/infrastructure/repository.py` | Modify | Map new fields in `_to_entity()` and `save()` |
| `src/sla_bc/sla/application/queries/get_request_sla.py` | Modify | Subtract paused time from resolution elapsed |
| `adapters/http/api/requests/routers.py` | Modify | Publish auto-transition event from comment endpoint |
| `alembic/versions/` | Create | New migration for columns |
| `web/app/src/components/ui/Badge.tsx` | Modify | Add badge color |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Modify | Add transitions + status flow |
| `web/app/src/pages/technician/RequestQueuePage.tsx` | Modify | Include in kanban column + stats |
| `web/app/src/locales/en.ts` | Modify | Add status label |
| `web/app/src/locales/es.ts` | Modify | Add status label |
| `web/app/src/pages/admin/DashboardPage.tsx` | Verify | Check if status breakdown is dynamic or hardcoded |
| `web/app/src/pages/admin/SlaDashboardPage.tsx` | Verify | Check if SLA dashboard handles new status |

#### Breaking Changes

None. The new status value is additive — existing transitions are unchanged. The two new database columns have defaults (nullable + server_default=0), so no backfill is needed.

## State Machine

```
                                    ┌─────────────────────┐
                                    │   pending_approval   │
                                    └──────┬──────┬───────┘
                                           │      │
                                    submitted  rejected
                                           │      │
                                    ┌──────▼──────▼───────┐
                                    │      submitted       │
                                    └──────────┬──────────┘
                                               │
                                          in_review
                                               │
                                    ┌──────────▼──────────┐
                                    │      in_review       │◄────────────┐
                                    └──────┬──────┬───────┘             │
                                           │      │                     │
                                    in_progress  rejected               │
                                           │                            │
                                    ┌──────▼──────────────┐             │
                              ┌────►│     in_progress      │─────►in_review
                              │     └──┬──────┬──────┬────┘
                              │        │      │      │
                              │   resolved rejected  waiting_for_employee
                              │                      │
                              │     ┌────────────────▼────────────────┐
                              │     │     waiting_for_employee        │
                              │     │  (SLA clock PAUSED)             │
                              └─────┤                                 │
                    (any comment)   │     → in_progress               │
                                    │     → resolved                  │
                                    │     → rejected                  │
                                    └─────────────────────────────────┘
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `request_bc` | Primary BC | Owns the status enum, entity, transitions |
| `sla_bc` | Cross-BC query | Reads `sla_paused_total_seconds` from ServiceRequest to adjust SLA calculation |
| `notification_bc` | Cross-BC event | Receives `REQUEST_STATUS_CHANGED` events — no changes needed (already handles all statuses generically) |

## Testing Strategy

| Test Type | Scope | Priority | File |
|-----------|-------|----------|------|
| Unit | `RequestStatus` enum — valid/invalid transitions | High | `tests/unit/request/test_request_status.py` |
| Unit | `ServiceRequest.change_status()` — SLA pause/resume fields | High | `tests/unit/request/test_service_request.py` |
| Unit | `AddCommentCommandHandler` — auto-transition on `waiting_for_employee` | High | `tests/unit/request/test_add_comment.py` |
| Unit | SLA query — subtraction of paused time | High | `tests/unit/sla/test_get_request_sla.py` |
| Unit | SLA query — active pause (currently in `waiting_for_employee`) | High | `tests/unit/sla/test_get_request_sla.py` |
| Unit | SLA query — multiple pause/resume cycles | High | `tests/unit/sla/test_get_request_sla.py` |
| Integration | PATCH status to `waiting_for_employee` — verify event published | Medium | `tests/integration/test_request_endpoints.py` |
| Integration | POST comment on `waiting_for_employee` request — verify auto-transition + event | Medium | `tests/integration/test_request_endpoints.py` |
| Integration | Status filter includes `waiting_for_employee` results | Low | `tests/integration/test_request_endpoints.py` |

### Critical Test Scenarios

1. **Happy path:** `in_progress` → `waiting_for_employee` → employee comments → auto-transition to `in_progress`
2. **SLA single cycle:** 4h total, 1h paused → SLA counts 3h
3. **SLA multiple cycles:** `in_progress` → `waiting` (1h) → `in_progress` → `waiting` (2h) → `in_progress` → SLA subtracts 3h total
4. **SLA active pause:** request currently in `waiting_for_employee` for 2h → SLA reflects 2h deduction even without finalized accumulation
5. **Invalid transition:** `submitted` → `waiting_for_employee` → raises `InvalidStatusTransitionError`
6. **Technician comment on waiting:** technician comments → also triggers auto-transition (per decision: any comment triggers it)
7. **Direct resolve from waiting:** `waiting_for_employee` → `resolved` → SLA finalizes paused time before resolving

## Implementation Order

1. [ ] Domain: Add `WAITING_FOR_EMPLOYEE` to `RequestStatus` enum + `VALID_STATUS_TRANSITIONS`
2. [ ] Domain: Add `sla_paused_at` and `sla_paused_total_seconds` fields to `ServiceRequest` entity
3. [ ] Domain: Modify `ServiceRequest.change_status()` for SLA pause/resume logic
4. [ ] Infrastructure: Add columns to `ServiceRequestModel`
5. [ ] Infrastructure: Create Alembic migration
6. [ ] Infrastructure: Update `RequestRepository._to_entity()` and `save()` for new fields
7. [ ] Application: Modify `AddCommentCommandHandler` for auto-transition
8. [ ] Application: Modify `GetRequestSlaStatusQueryHandler` to subtract paused time
9. [ ] HTTP: Modify `add_comment` router endpoint to publish auto-transition event
10. [ ] Frontend: Add badge color for `waiting_for_employee`
11. [ ] Frontend: Update status transitions in `RequestDetailPage.tsx`
12. [ ] Frontend: Include in kanban column + stats in `RequestQueuePage.tsx`
13. [ ] Frontend: Add i18n keys (EN + ES)
14. [ ] Frontend: Verify dashboard + SLA dashboard handle new status
15. [ ] Tests: Unit tests for transitions, auto-transition, SLA calculation
16. [ ] Tests: Integration tests for endpoints
17. [ ] Run `make test` and `make lint`

## Open Technical Questions

1. **STATUS_FLOW visualization on RequestDetailPage:** The status flow stepper (lines 250-251) is linear (`submitted → in_review → in_progress → resolved`). `waiting_for_employee` is a side-branch, not a linear step. Should it appear in the stepper? **Recommendation:** No — show it only as a status badge and in the action dropdown, not in the linear progress bar.

2. **Kanban column placement:** Should `waiting_for_employee` get its own kanban column or be included in the `in_progress` column? **Recommendation:** Include in `in_progress` column with a visual indicator (amber badge) to differentiate. Adding a 5th column fragments the view.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| SLA calculation precision | Low | Medium | Use `int` for `sla_paused_total_seconds` (rounding to nearest second). Test with multiple cycles. |
| Race condition: two comments posted simultaneously on `waiting_for_employee` | Very Low | Low | The second `change_status()` call will be a no-op (status already `in_progress`). The transition `in_progress → in_progress` is invalid, so it would raise an error. Add a guard: only auto-transition if status is still `WAITING_FOR_EMPLOYEE`. |
| Frontend hardcoded status lists | Medium | Low | Multiple files have hardcoded status values. A search-and-update pass is needed. Verified files: Badge.tsx, RequestDetailPage.tsx, RequestQueuePage.tsx, DashboardPage.tsx. |
