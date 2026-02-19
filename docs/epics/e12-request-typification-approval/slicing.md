# Slicing: E12 - Request Typification & Approval

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-18
**Total Features:** 5

## Slicing Rationale

E12 has a natural progression: categories/subtypes (F0) are a pure data expansion with no behavior change, priority scoring (F1) builds on category data plus a new department field, the approval workflow (F2) introduces a new status and gate logic, the auto-assignment timing fix (F3) adjusts E11's hook, and the frontend (F4) exposes everything. Each feature is independently deployable — F0 alone already improves classification, F1 alone already improves triage.

## Dependency Graph

```text
F0: Request Categories & Subtypes (domain + API + migration)
  ├── F1: Priority Scoring (service + department weight)
  │     └── F3: Auto-Assignment Timing Fix (adjust E11 hook)
  └── F2: Approval Workflow (status machine + events + notifications)
        └── F3: Auto-Assignment Timing Fix
              └── F4: Frontend UX (React pages + i18n)
```

## Features Summary

| # | Feature | Covers | Complexity | Depends | Status |
|---|---------|--------|------------|---------|--------|
| F0 | Request Categories & Subtypes | US-E12-001 | Medium | E3 | Done |
| F1 | Priority Scoring | US-E12-002, US-E12-003 | Medium | F0, E11 | Done |
| F2 | Approval Workflow | US-E12-004 | High | F0, E4, E11 | Done |
| F3 | Auto-Assignment Timing Fix | US-E12-004 (partial) | Low | F2, E11 | Done |
| F4 | Frontend UX | US-E12-001..US-E12-005 | High | F0, F1, F2, F3, E7, E9 | Done |

---

## F0: Request Categories & Subtypes

**Scope:** Extend `RequestType` enum with 3 new values. Add `RequestSubtype` enum and `subtype` field to `ServiceRequest`. Migration, API changes, backward-compatible.

### Domain Changes
- Add `REPAIR`, `CONFIGURATION`, `ACCESS_REQUEST` to `RequestType` enum
- Create `RequestSubtype` enum with all subtype values:
  - `HARDWARE`, `SOFTWARE`, `NETWORK`, `SECURITY`, `OTHER` (for incident/repair)
  - `COMPUTER`, `MOBILE`, `PERIPHERAL`, `MONITOR`, `SOFTWARE_LICENSE` (for new_equipment)
  - `SOFTWARE_INSTALL`, `ACCOUNT_SETUP`, `PERMISSIONS` (for configuration)
  - `SYSTEM_ACCESS`, `PHYSICAL_ACCESS`, `VPN` (for access_request)
- Add `VALID_SUBTYPES: dict[RequestType, list[RequestSubtype]]` mapping
- Add `subtype: Optional[RequestSubtype]` to `ServiceRequest` entity

### Migration
- `ALTER TABLE service_requests ADD COLUMN subtype VARCHAR(50) NULL`

### Command Changes
- `CreateRequestCommand`: Accept optional `subtype` field, validate against `VALID_SUBTYPES[type]`
- `ServiceRequest.create()`: Store subtype

### Query Changes
- `ListRequestsQuery`: Add `subtype` filter parameter
- `MyRequestsQuery`: Add `subtype` filter parameter

### API Changes
- `POST /api/v1/requests`: Accept `subtype` in request body (optional)
- `GET /api/v1/requests`: Accept `subtype` query parameter for filtering
- Response schemas: Include `subtype` field

### Tests
- Unit: subtype validation (valid, invalid, null), backward compatibility (request without subtype)
- Integration: create request with subtype, filter by subtype, old requests still work
- ~10 tests

### Files

| File | Action |
|------|--------|
| `src/request_bc/request/domain/enums.py` | Edit — add 3 types, create RequestSubtype, add VALID_SUBTYPES |
| `src/request_bc/request/domain/entities.py` | Edit — add subtype field |
| `src/request_bc/request/infrastructure/models.py` | Edit — add subtype column |
| `src/request_bc/request/infrastructure/repository.py` | Edit — add subtype filter |
| `src/request_bc/request/application/commands/create_request.py` | Edit — accept and validate subtype |
| `src/request_bc/request/application/queries/list_requests.py` | Edit — add subtype filter |
| `src/request_bc/request/application/queries/my_requests.py` | Edit — add subtype filter |
| `adapters/http/api/requests/routers.py` | Edit — accept subtype in create, add filter param |
| `adapters/http/api/requests/schemas.py` | Edit — add subtype to request/response schemas |
| `alembic/versions/xxx_add_request_subtype.py` | Create — migration |
| `tests/unit/request_bc/request/application/commands/test_commands.py` | Edit — add subtype tests |
| `tests/integration/test_requests_endpoints.py` | Edit — add subtype tests |

---

## F1: Priority Scoring

**Scope:** Replace static `DEFAULT_PRIORITY` with a `PriorityScorer` service. Add `priority_weight` field to `Department`. Score considers type, subtype, department, and requester role.

### Domain Changes
- Add `priority_weight: int` to `Department` entity (default 0, range -1 to +2)
- Add `priority_weight` column to `DepartmentModel`

### Migration
- `ALTER TABLE departments ADD COLUMN priority_weight INTEGER NOT NULL DEFAULT 0`

### New Service
- `PriorityScorer` in `src/request_bc/request/application/services/priority_scorer.py`
- Input: type, subtype, department_id, user_role
- Output: priority + scoring breakdown dict
- Weight tables:
  - Type: incident→+2, repair→+1, onboarding→+1, new_equipment→0, configuration→0, access_request→0
  - Subtype: security→+1, hardware→+1, others→0
  - Department: `department.priority_weight` (fetched from DB)
  - Role: admin→+1, others→0
- Score→priority mapping: >=4→urgent, >=3→high, >=2→medium, <=1→low

### Command Changes
- `CreateRequestCommand`: Call `PriorityScorer` instead of `DEFAULT_PRIORITY[type]`
- Store scoring breakdown in `request.data.priority_scoring`

### Department Changes
- `UpdateDepartmentCommand`: Accept optional `priority_weight`
- API: Add `priority_weight` to department update body and response

### Tests
- Unit: scoring logic (all weight combinations), edge cases (no department, no subtype)
- Unit: department priority weight validation (range check)
- Integration: create request → verify computed priority, update department weight → verify effect
- ~12 tests

### Files

| File | Action |
|------|--------|
| `src/request_bc/request/application/services/priority_scorer.py` | Create |
| `src/request_bc/request/application/commands/create_request.py` | Edit — use PriorityScorer |
| `src/request_bc/request/application/ports.py` | Edit — add department repo port if needed |
| `src/company_bc/department/domain/entities.py` | Edit — add priority_weight |
| `src/company_bc/department/infrastructure/models.py` | Edit — add priority_weight column |
| `src/company_bc/department/infrastructure/repository.py` | Edit — update mapping |
| `src/company_bc/department/application/commands/update_department.py` | Edit — accept priority_weight |
| `adapters/http/api/departments/routers.py` | Edit — expose priority_weight |
| `adapters/http/api/departments/schemas.py` | Edit — add priority_weight to schemas |
| `alembic/versions/xxx_add_department_priority_weight.py` | Create — migration |
| `tests/unit/request_bc/request/application/services/test_priority_scorer.py` | Create |
| `tests/unit/request_bc/request/application/commands/test_commands.py` | Edit — scoring tests |
| `tests/integration/test_departments_endpoints.py` | Edit — priority_weight tests |

---

## F2: Approval Workflow

**Scope:** Add `pending_approval` status. Gate `new_equipment` requests through manager approval. New approve/reject commands. Notification integration.

### Domain Changes
- Add `PENDING_APPROVAL` to `RequestStatus` enum
- Update `VALID_STATUS_TRANSITIONS`:
  - Add `PENDING_APPROVAL → SUBMITTED` (approve)
  - Add `PENDING_APPROVAL → REJECTED` (reject)
- Update `ServiceRequest.create()`:
  - For `new_equipment` type: check if requester's department has a manager
  - If manager exists: set initial status to `PENDING_APPROVAL`
  - If no manager: set initial status to `SUBMITTED` (skip approval)
- Add `approval_reason` tracking in request events

### New Commands
- `ApproveRequestCommand(request_id, company_id, performed_by)`
  - Validates: request is in `pending_approval` status
  - Validates: actor is department manager of requester's department, OR admin
  - Moves status to `submitted`
  - Creates event: `request.approved`
- `RejectRequestCommand(request_id, company_id, performed_by, reason: str)`
  - Same validations
  - Moves status to `rejected`, sets `resolved_at`
  - Creates event: `request.rejected` with reason

### Notification Changes
- New event type: `REQUEST_APPROVAL_NEEDED` — notify department manager
- New event type: `REQUEST_APPROVED` — notify requester
- Extend `REQUEST_REJECTED` handling to include approval context
- Update `TargetResolver` for new event types:
  - `REQUEST_APPROVAL_NEEDED` → department manager
  - `REQUEST_APPROVED` → requester
- Update `RequestEventFactory` with new event builders

### API Changes
- `POST /api/v1/requests/{id}/approve` — approve a pending request
- `POST /api/v1/requests/{id}/reject` — reject with body: `{ reason: str }`
- Update list requests to support `status=pending_approval` filter
- Create request response now includes `pending_approval` status when applicable

### Tests
- Unit: approval command validations (wrong status, wrong actor, cross-company)
- Unit: request creation routing (with manager → pending_approval, without → submitted)
- Unit: notification targeting for approval events
- Integration: full approval flow (create → approve → in_review → resolved)
- Integration: full rejection flow (create → reject)
- Integration: skip approval flow (no manager → submitted directly)
- ~15 tests

### Files

| File | Action |
|------|--------|
| `src/request_bc/request/domain/enums.py` | Edit — add PENDING_APPROVAL status, update transitions |
| `src/request_bc/request/domain/entities.py` | Edit — approval logic in create() |
| `src/request_bc/request/application/commands/approve_request.py` | Create |
| `src/request_bc/request/application/commands/reject_request.py` | Create |
| `src/request_bc/request/application/commands/create_request.py` | Edit — route to pending_approval |
| `src/notification_bc/notification/application/services/event_factory.py` | Edit — add approval events |
| `src/notification_bc/notification/application/services/target_resolver.py` | Edit — add approval routing |
| `src/notification_bc/notification/application/services/notification_subscriber.py` | Edit — handle new events |
| `adapters/http/api/requests/routers.py` | Edit — add approve/reject endpoints |
| `adapters/http/api/requests/schemas.py` | Edit — add reject reason schema |
| `tests/unit/request_bc/request/application/commands/test_approval.py` | Create |
| `tests/unit/request_bc/request/application/commands/test_commands.py` | Edit — pending_approval routing |
| `tests/unit/notification_bc/.../test_notification_subscriber.py` | Edit — approval events |
| `tests/integration/test_requests_endpoints.py` | Edit — approval flow tests |

---

## F3: Auto-Assignment Timing Fix

**Scope:** Move E11 auto-assignment trigger for `new_equipment` from request creation to after approval. `onboarding` requests still auto-assign at creation.

### Changes
- In request creation router: only trigger auto-assignment for `onboarding` (not `new_equipment`)
- Add auto-assignment trigger to `ApproveRequestCommand` handler: when a `new_equipment` request is approved, attempt auto-assignment
- Store auto-assignment metadata as before in `request.data.auto_assignment`

### Tests
- Unit: verify auto-assignment NOT called on new_equipment creation
- Unit: verify auto-assignment IS called on approval of new_equipment
- Unit: verify auto-assignment IS called on onboarding creation (unchanged)
- Integration: full flow — create new_equipment → approve → auto-assignment runs
- ~5 tests

### Files

| File | Action |
|------|--------|
| `adapters/http/api/requests/routers.py` | Edit — change auto-assign trigger |
| `src/request_bc/request/application/commands/approve_request.py` | Edit — add auto-assign call |
| `tests/unit/request_bc/request/application/commands/test_approval.py` | Edit — auto-assign tests |
| `tests/integration/test_auto_assignment.py` | Edit — timing tests |

---

## F4: Frontend UX

**Scope:** Update request form with type/subtype selection. Add approval queue. Add subtype filters. Add department priority weight editor. i18n.

### Pages/Components

1. **NewRequestPage** — Edit: add subtype dropdown (dynamic based on type)
2. **RequestQueuePage** — Edit: add subtype filter, show subtype badge
3. **RequestDetailPage** — Edit: show subtype, show scoring breakdown, show approval actions for managers
4. **MyRequestsPage** — Edit: show subtype and approval status
5. **DepartmentsPage** — Edit: add priority weight editor per department row
6. **DashboardPage** — Edit: add subtype breakdown in request summary (optional, if time permits)

### Routing
- No new routes needed (approval actions are inline on RequestDetailPage)

### Sidebar
- No new nav items needed

### i18n
- EN + ES keys for:
  - New type labels: `enum.repair`, `enum.configuration`, `enum.access_request`
  - All subtype labels (~20 subtypes)
  - Approval UI: approve/reject buttons, rejection reason, pending_approval status
  - Priority scoring: breakdown labels, department weight labels
  - Filter labels for subtype
- ~50 keys per language

### Tests
- TypeScript compiles (`tsc --noEmit`)
- Build succeeds (`npm run build`)

### Files

| File | Action |
|------|--------|
| `web/app/src/types/index.ts` | Edit — add RequestSubtype, update RequestType/RequestStatus |
| `web/app/src/pages/employee/NewRequestPage.tsx` | Edit — add subtype selector |
| `web/app/src/pages/employee/MyRequestsPage.tsx` | Edit — show subtype, approval status |
| `web/app/src/pages/technician/RequestQueuePage.tsx` | Edit — add subtype filter |
| `web/app/src/pages/technician/RequestDetailPage.tsx` | Edit — show subtype, scoring, approval actions |
| `web/app/src/pages/admin/DepartmentsPage.tsx` | Edit — add priority weight editor |
| `web/app/src/locales/en.ts` | Edit — add ~50 keys |
| `web/app/src/locales/es.ts` | Edit — add ~50 keys |

---

## Recommended Implementation Order

1. **F0** — Foundation: new types, subtypes, migration, API, tests (~1 session)
2. **F1** — Scoring: PriorityScorer, department weight, tests (~1 session)
3. **F2** — Approval: new status, commands, notifications, tests (~1-2 sessions)
4. **F3** — Timing fix: move auto-assign trigger, tests (~0.5 session)
5. **F4** — Frontend: updated forms, filters, approval UI, i18n (~1-2 sessions)

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow (F0 → F1/F2 → F3 → F4)
- [x] Each feature independently deployable
- [x] Vertical slices — each feature delivers complete functionality
- [x] Backward compatible — existing requests work without subtype
- [x] No overlapping scope between features
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered (types + scoring + approval + frontend)

## Risk Notes

- **Enum migration:** Adding enum values to PostgreSQL requires `ALTER TYPE ... ADD VALUE`. Alembic handles this but values cannot be removed once added.
- **Approval skip logic:** When no manager is assigned, requests skip approval silently. Consider logging this decision for auditability.
- **Auto-assignment timing:** Moving the trigger for `new_equipment` to after approval means there's a delay. Technicians should understand that auto-assignment happens post-approval, not at creation.
- **Subtype proliferation:** Starting with system-defined subtypes. If users request custom subtypes, that's E30 (Custom Fields).
