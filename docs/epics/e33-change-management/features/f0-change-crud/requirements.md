# Feature: Change Request CRUD + State Machine + List/Detail Pages

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** L

## Scope

### Included

- New bounded context `change_bc` with `change_request` subdomain
- ChangeRequest entity with all fields from the epic (title, description, change_type, status, business_justification, risk_assessment, rollback_plan, planned_date, requested_by, assigned_to, approved/rejected fields, timestamps, implementation_notes, rollback_reason)
- ChangeType enum: standard, normal, emergency
- ChangeStatus enum with 8 states: draft, pending_approval, scheduled, in_progress, implemented, closed, rejected, rolled_back
- Full state machine with VALID_TRANSITIONS dict and is_terminal property
- Auto-approve for standard type (DRAFT → SCHEDULED, skipping PENDING_APPROVAL)
- Rollback plan required for normal/emergency types at submit time
- ChangeEvent entity (append-only audit trail): created, submitted, approved, rejected, started, implemented, rolled_back, closed, updated, assigned
- ChangeEventType enum
- Commands: CreateChangeRequest, UpdateChangeRequest, SubmitChangeRequest, ApproveChangeRequest, RejectChangeRequest, StartChange, ImplementChange, RollbackChange, CloseChange, AssignChange
- Queries: ListChangeRequests (paginated, filtered), GetChangeRequestDetail (with timeline)
- Edit rules: fields editable in DRAFT and PENDING_APPROVAL only
- No hard delete (DORA audit compliance)
- SQLAlchemy models, repository, Alembic migration
- HTTP router with all endpoints
- Frontend: ChangeListPage (paginated table with filters), ChangeDetailPage (all fields, timeline, action buttons per status/role)
- Navigation: add "Changes" item in sidebar
- i18n keys for EN and ES

### Excluded (in other features)

- Asset linking (F1)
- Post-Implementation Review entity and PIR section on detail page (F2)
- PIR enforcement for emergency close (F2)
- Change dashboard (F3)
- Notifications (deferred)

## User Value

When this feature is complete, admins and technicians can:
- Create change requests for planned endpoint changes (OS rollout, software update, config change)
- Submit changes for approval (normal/emergency require CAB/admin approval; standard auto-approved)
- Approve or reject pending change requests (admin only)
- Track implementation: start → implement → close
- Roll back failed changes with mandatory reason
- View the full timeline of events for each change
- List and filter all change requests by status, type, date, assignee, and search text
- Assign a change to a specific technician for implementation

This alone provides DORA Art. 9 compliance: formal change tracking, approval, rollback plan, and audit trail.

## Acceptance Criteria

- [ ] Can create a change request with title, description, change_type, business_justification, risk_assessment, rollback_plan, planned_date
- [ ] Standard type auto-approves to SCHEDULED on submit
- [ ] Normal/emergency type goes to PENDING_APPROVAL on submit
- [ ] Rollback plan is mandatory for normal/emergency at submit time (422 if empty)
- [ ] Admin can approve PENDING_APPROVAL → SCHEDULED (optional notes, records approved_by/approved_at)
- [ ] Admin can reject PENDING_APPROVAL → REJECTED (reason mandatory, records rejected_by/rejected_at)
- [ ] Technician/admin can start SCHEDULED → IN_PROGRESS (records started_at)
- [ ] Technician/admin can implement IN_PROGRESS → IMPLEMENTED (records implemented_at, optional notes)
- [ ] Technician/admin can rollback IN_PROGRESS or IMPLEMENTED → ROLLED_BACK (reason mandatory)
- [ ] Admin can close IMPLEMENTED → CLOSED (records closed_at)
- [ ] Fields editable in DRAFT and PENDING_APPROVAL only (422 if editing in later states)
- [ ] Admin can assign change to a technician (records ASSIGNED event)
- [ ] ChangeEvent created for every state transition and edit
- [ ] List page with pagination, filter by status/type/date range/assigned_to, search by title
- [ ] Detail page shows all fields, event timeline, action buttons per current status and user role
- [ ] Sidebar navigation includes "Changes" item
- [ ] i18n keys for all labels and enums in EN and ES
- [ ] Invalid state transitions return 422
- [ ] Multi-tenant: all operations scoped to company_id
- [ ] Only admin can approve/reject; technician+ can create/start/implement/rollback
- [ ] No delete endpoint (audit trail permanence)

## Technical Scope

### Entities (owned by this feature)

- **ChangeRequest** — main aggregate root with all fields
- **ChangeEvent** — append-only audit trail

### Entities (used from dependencies)

- None (this is the foundation feature)

### Key Components

- `src/change_bc/change_request/domain/entities.py` — ChangeRequest, ChangeEvent
- `src/change_bc/change_request/domain/enums.py` — ChangeType, ChangeStatus, ChangeEventType, VALID_TRANSITIONS
- `src/change_bc/change_request/domain/repository.py` — ChangeRequestRepositoryInterface
- `src/change_bc/change_request/domain/exceptions.py` — domain errors
- `src/change_bc/change_request/application/commands/` — all commands
- `src/change_bc/change_request/application/queries/` — list + detail queries
- `src/change_bc/change_request/infrastructure/models.py` — SQLAlchemy models
- `src/change_bc/change_request/infrastructure/repository.py` — repository implementation
- `adapters/http/api/changes/` — router, schemas, dependencies
- `alembic/versions/e33a1_*.py` — migration
- `web/app/src/pages/admin/ChangeListPage.tsx`
- `web/app/src/pages/admin/ChangeDetailPage.tsx`

## Notes

- Follow maintenance_bc and incident_bc patterns for entity structure and state machine
- The approval workflow follows request_bc approve/reject pattern
- ChangeEvent follows the same pattern as VulnerabilityEvent, IncidentTimeline, RiskHistory
- The DRAFT state is the creation state; submit is a separate action that triggers approval routing
- For simplicity, create + submit can be a single API call (create already submitted) with a `submit` boolean flag, or two separate endpoints. Design phase decides.
