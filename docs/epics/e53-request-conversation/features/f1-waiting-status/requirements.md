# Feature: Waiting Status

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F1
**Dependencies:** None
**Complexity:** M

## Scope

### Included
- `WAITING_FOR_EMPLOYEE` enum value added to `RequestStatus`
- `VALID_TRANSITIONS` updated: `in_progress` → `waiting_for_employee`, `waiting_for_employee` → `in_progress` / `resolved` / `rejected`
- Only technician/admin can set `waiting_for_employee`
- Auto-transition: any comment on a request in `waiting_for_employee` → status becomes `in_progress`
- SLA tracking fields: `sla_paused_at` (datetime) + `sla_paused_total_seconds` (int) on ServiceRequest
- SLA clock pause/resume logic in `change_status` (set `sla_paused_at` on enter, accumulate on leave)
- SLA query updated to subtract `sla_paused_total_seconds` from elapsed resolution time
- Alembic migration: new status value + new columns
- Frontend: status badge with amber/warning color for `waiting_for_employee`
- Frontend: status filter dropdown includes `waiting_for_employee`
- Frontend: dashboard status counts include `waiting_for_employee`
- i18n keys for the new status label (EN + ES)
- Unit tests: transition validation, auto-transition, SLA pause/resume
- Integration tests: status change endpoint, comment auto-transition

### Excluded (in other features)
- Email notifications on comment or status change → F2
- Conversation bubble UI → F3
- "Waiting for your reply" banner → F3
- Status change dialog with optional message → F3

## User Value

Technicians can set a request to "waiting for employee" to clearly signal that the ball is in the employee's court. The SLA clock pauses fairly. When any comment is added, the status automatically returns to `in_progress`. Admins see accurate SLA reports that exclude waiting time.

## Acceptance Criteria

- [ ] `WAITING_FOR_EMPLOYEE` added to `RequestStatus` enum
- [ ] `in_progress` → `waiting_for_employee` transition works; invalid transitions (e.g., `submitted` → `waiting_for_employee`) are rejected
- [ ] Only technician/admin can set this status (employee cannot)
- [ ] Any comment on a `waiting_for_employee` request auto-transitions to `in_progress`
- [ ] Status change fires `REQUEST_STATUS_CHANGED` event
- [ ] `sla_paused_at` set on entering `waiting_for_employee`, cleared + accumulated into `sla_paused_total_seconds` on leaving
- [ ] SLA query subtracts `sla_paused_total_seconds` from resolution elapsed time
- [ ] Multiple waiting cycles accumulate correctly (2 cycles of 1h each = 2h subtracted)
- [ ] Alembic migration applies cleanly
- [ ] Status badge shows amber/warning color in UI
- [ ] Status filter, dashboard counts, and CSV export include `waiting_for_employee`
- [ ] i18n: ES "Pendiente del empleado" / EN "Waiting for employee"
- [ ] Unit tests pass for transitions, auto-transition, SLA fields
- [ ] Integration tests pass for end-to-end flows
- [ ] `make test` and `make lint` pass

## Technical Scope

### Entities (owned by this feature)
- `RequestStatus.WAITING_FOR_EMPLOYEE` (new enum value)
- `ServiceRequest.sla_paused_at` (new field)
- `ServiceRequest.sla_paused_total_seconds` (new field)

### Entities (used from dependencies)
- `ServiceRequest` (existing — extends with new fields and transitions)
- `RequestComment` (existing — triggers auto-transition)

### Key Components
- `src/request_bc/request/domain/enums.py` — Add enum value
- `src/request_bc/request/domain/entities.py` — Update `VALID_TRANSITIONS`, add SLA pause logic in `change_status`
- `src/request_bc/request/application/commands/add_comment.py` — Auto-transition logic after saving comment
- `src/sla_bc/sla/application/queries/get_request_sla.py` — Subtract `sla_paused_total_seconds`
- `alembic/versions/` — Migration for status constraint + new columns
- `web/app/src/pages/technician/RequestDetailPage.tsx` — Status badge color
- `web/app/src/locales/en.ts` + `es.ts` — Status label

## Notes

- The `change_status` method on `ServiceRequest` must handle `sla_paused_at` / `sla_paused_total_seconds` atomically with the status change. When entering `waiting_for_employee`, set `sla_paused_at = now()`. When leaving (to any status), add `(now - sla_paused_at).total_seconds()` to `sla_paused_total_seconds` and clear `sla_paused_at`.
- The auto-transition in `AddCommentHandler` needs access to the request object to check status and trigger `change_status`. The handler already loads the request via `request_repo` — extend the existing flow.
- The existing `RequestEventFactory.status_changed` already includes `old_status` and `new_status` in the payload — no changes needed for event emission.
