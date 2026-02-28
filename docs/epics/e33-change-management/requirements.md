# E33 — Endpoint Change Management (Simplified)

**Type:** Epic
**Status:** Draft
**Created:** 2026-02-27
**Author:** AI
**Priority:** High (DORA)

## Business Alignment

**Objective:** DORA Compliance — Cap. II, Art. 9 (Change Management Procedures)
**KPI Target:** 100% of planned endpoint changes tracked with formal approval and rollback plan
**Evidence:** DORA Art. 9 requires "formal policies and procedures for ICT change management, including changes to software, hardware, firmware components, systems or security parameters" with "adequate safeguards against unauthorized changes" and "adequate procedures to ensure changes are tested, approved, implemented in a controlled manner"

## Problem Statement

### Current Situation

DSM tracks reactive work (service requests, incidents) and preventive work (maintenance). But there is no formal mechanism to track **planned changes** to endpoints — OS rollouts, software deployments, configuration changes, firmware updates.

Maintenance (E17) handles individual asset tasks (clean fan, replace battery). Service requests (E3) handle reactive problems (broken keyboard, access request). Neither captures the DORA-required lifecycle of a planned change: proposal, risk assessment, approval, scheduled implementation, rollback plan, and post-implementation review.

### Pain Points

- No formal approval workflow for endpoint changes (OS updates pushed without CAB review)
- No rollback plan documentation before implementing changes
- No traceability between a planned change and which assets were affected
- No post-implementation review to capture lessons learned
- Audit gap: DORA auditors cannot verify change management procedures exist

### Impact if Not Solved

- DORA non-compliance for ICT change management (Art. 9)
- No evidence trail for auditors
- Untracked changes can cause incidents without clear attribution

## Proposed Solution

A **lightweight change management** module as a new `change_bc` bounded context. Follows ITIL change management principles but scoped exclusively to endpoint/microinformatica changes.

**Design philosophy: minimal viable DORA compliance.** Reuse existing patterns from maintenance_bc, incident_bc, and request_bc. No over-engineering.

### What It Is

- A **Change Request** entity with a formal lifecycle (draft → approval → implementation → review → closed)
- Three change types: **Standard** (pre-approved, low risk), **Normal** (CAB approval required), **Emergency** (expedited, post-implementation review mandatory)
- Link affected assets to the change request
- Mandatory rollback plan field before approval
- Post-Implementation Review (PIR) as a simple sub-entity
- Change calendar view (list of scheduled/in-progress changes)
- Admin dashboard widget with change metrics

### What It Is NOT

- Not a full ITIL change management suite (no CAB board UI, no complex workflows)
- Not for server/network/infrastructure changes (separate application)
- No automated deployment or orchestration
- No integration with SCCM, Intune, or MDM tools (future scope)

### User Stories

#### US-001: Create a Change Request
**As an** admin or technician
**I want** to create a change request documenting a planned endpoint change
**So that** the change is formally tracked with risk assessment and rollback plan

**Acceptance Criteria:**
- [ ] Can create a change request with: title, description, change type (standard/normal/emergency), business justification, risk assessment (free text), rollback plan (free text), planned date, affected assets (optional at creation)
- [ ] Change type determines approval flow: standard → auto-approved (SCHEDULED), normal/emergency → PENDING_APPROVAL
- [ ] Change request is scoped to company (multi-tenant)
- [ ] Creator is recorded as `requested_by`

#### US-002: Approve or Reject a Change Request
**As an** admin
**I want** to approve or reject pending change requests
**So that** only reviewed changes proceed to implementation

**Acceptance Criteria:**
- [ ] Admin can approve a change in PENDING_APPROVAL status → transitions to SCHEDULED
- [ ] Admin can reject a change in PENDING_APPROVAL status → transitions to REJECTED (terminal)
- [ ] Rejection requires a reason (mandatory field)
- [ ] Approval can include optional notes
- [ ] Both actions record who approved/rejected and when

#### US-003: Implement a Change
**As a** technician or admin
**I want** to mark a change as in-progress and then as implemented
**So that** the implementation timeline is tracked

**Acceptance Criteria:**
- [ ] Can transition SCHEDULED → IN_PROGRESS (records `started_at`)
- [ ] Can transition IN_PROGRESS → IMPLEMENTED (records `implemented_at`)
- [ ] Can add implementation notes when marking as implemented
- [ ] Can assign a change to a specific technician (`assigned_to`)

#### US-004: Roll Back a Change
**As a** technician or admin
**I want** to mark a change as rolled back
**So that** failed implementations are tracked

**Acceptance Criteria:**
- [ ] Can transition IN_PROGRESS → ROLLED_BACK or IMPLEMENTED → ROLLED_BACK
- [ ] Rollback requires a reason (mandatory)
- [ ] ROLLED_BACK is a terminal state

#### US-005: Complete Post-Implementation Review
**As an** admin
**I want** to review a completed change and record the outcome
**So that** lessons learned are captured for DORA compliance

**Acceptance Criteria:**
- [ ] Can add a PIR to an IMPLEMENTED change: outcome (successful/partial/failed), issues found, lessons learned, follow-up actions
- [ ] PIR is mandatory for emergency changes before closing
- [ ] Can transition IMPLEMENTED → CLOSED (with or without PIR for standard/normal; PIR required for emergency)
- [ ] CLOSED is a terminal state

#### US-006: Link Assets to a Change
**As an** admin or technician
**I want** to associate affected assets with a change request
**So that** I know which equipment is impacted

**Acceptance Criteria:**
- [ ] Can link one or more assets to a change request (M2M)
- [ ] Can unlink an asset from a change request
- [ ] Asset linking uses cross-BC reference pattern (string ID, no FK)
- [ ] Affected assets displayed on change detail page

#### US-007: List and Filter Changes
**As an** admin or technician
**I want** to view all change requests with filters
**So that** I can track upcoming and past changes

**Acceptance Criteria:**
- [ ] List page with pagination
- [ ] Filter by: status, change type, date range, assigned_to
- [ ] Search by title
- [ ] Sorted by planned_date (upcoming first for active, most recent first for closed)

#### US-008: Change Detail Page
**As an** admin or technician
**I want** to see full details of a change request including timeline
**So that** I can understand the change history

**Acceptance Criteria:**
- [ ] Detail page shows all change fields, affected assets, PIR (if exists), and event timeline
- [ ] Timeline shows all status transitions with actor and timestamp
- [ ] Action buttons based on current status and user role

#### US-009: Change Calendar / Dashboard Widget
**As an** admin
**I want** a summary of scheduled and in-progress changes
**So that** I can see what's happening and what's coming

**Acceptance Criteria:**
- [ ] Dashboard-style view showing: total open changes, changes by status, upcoming changes (next 30 days), recently implemented changes
- [ ] Link from each item to the change detail page

## Entities

| Entity | Description | States |
|--------|-------------|--------|
| ChangeRequest | A planned change to one or more endpoints | draft, pending_approval, scheduled, in_progress, implemented, closed, rejected, rolled_back |
| ChangeEvent | Audit trail entry for a change request | N/A (append-only) |
| PostImplementationReview | PIR record linked to a change | N/A (single record per change) |

### State Machine: ChangeRequest

```
                                    ┌──────────────┐
                                    │   REJECTED   │ (terminal)
                                    └──────┬───────┘
                                           │ reject
                                           │
DRAFT ──create──► PENDING_APPROVAL ──approve──► SCHEDULED ──start──► IN_PROGRESS ──implement──► IMPLEMENTED ──close──► CLOSED (terminal)
  │                                                                      │                          │
  │ (standard type: auto-approve)                                        │                          │
  └─────────────────────────────────────────► SCHEDULED                  │ rollback                  │ rollback
                                                                         │                          │
                                                                         ▼                          ▼
                                                                    ROLLED_BACK (terminal)    ROLLED_BACK (terminal)
```

### State Transitions

| From | To | Trigger | Conditions |
|------|----|---------|------------|
| (new) | DRAFT | create() | — |
| DRAFT | PENDING_APPROVAL | submit() | normal/emergency type |
| DRAFT | SCHEDULED | submit() | standard type (auto-approved) |
| PENDING_APPROVAL | SCHEDULED | approve() | admin role, optional notes |
| PENDING_APPROVAL | REJECTED | reject() | admin role, reason mandatory |
| SCHEDULED | IN_PROGRESS | start() | records started_at |
| IN_PROGRESS | IMPLEMENTED | implement() | records implemented_at, optional notes |
| IN_PROGRESS | ROLLED_BACK | rollback() | reason mandatory |
| IMPLEMENTED | CLOSED | close() | PIR required for emergency type |
| IMPLEMENTED | ROLLED_BACK | rollback() | reason mandatory |

### Entity: ChangeRequest — Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | ULID | auto | PK |
| company_id | str | yes | multi-tenant scope |
| title | str(200) | yes | |
| description | text | no | |
| change_type | enum | yes | standard / normal / emergency |
| status | enum | yes | see state machine |
| business_justification | text | no | why this change is needed |
| risk_assessment | text | no | free-text risk description |
| rollback_plan | text | no | mandatory before approval (enforced at submit) |
| planned_date | date | no | when the change is scheduled |
| requested_by | str | yes | user who created the change |
| assigned_to | str | no | technician implementing |
| approved_by | str | no | admin who approved |
| approved_at | datetime | no | |
| rejected_by | str | no | |
| rejected_at | datetime | no | |
| rejection_reason | text | no | mandatory on rejection |
| started_at | datetime | no | |
| implemented_at | datetime | no | |
| implementation_notes | text | no | |
| rollback_reason | text | no | mandatory on rollback |
| closed_at | datetime | no | |
| created_at | datetime | auto | |
| updated_at | datetime | auto | |

### Entity: ChangeEvent — Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | ULID | auto | PK |
| change_request_id | str | yes | FK |
| event_type | enum | yes | created, submitted, approved, rejected, started, implemented, rolled_back, closed, asset_linked, asset_unlinked, pir_added, updated, assigned |
| performed_by | str | yes | actor |
| data | JSON | no | extra context |
| created_at | datetime | auto | |

### Entity: PostImplementationReview — Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | ULID | auto | PK |
| change_request_id | str | yes | FK, unique (one PIR per change) |
| outcome | enum | yes | successful / partial / failed |
| issues_found | text | no | |
| lessons_learned | text | no | |
| follow_up_actions | text | no | |
| created_by | str | yes | |
| created_at | datetime | auto | |

### Cross-BC Link: ChangeAsset (join table)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| id | ULID | auto | PK |
| change_request_id | str | yes | FK to change_requests |
| asset_id | str | yes | cross-BC ref (no FK) |
| UniqueConstraint | | | (change_request_id, asset_id) |

## Use Cases

### UC-001: Create and Submit a Normal Change Request

**Actor:** Admin
**Preconditions:** Authenticated, admin role
**Postconditions:** Change request created in PENDING_APPROVAL status

**Main Flow:**
1. Admin fills in title, description, change type = "normal", business justification, risk assessment, rollback plan, planned date
2. Admin optionally links affected assets
3. System validates rollback plan is not empty (required for normal/emergency)
4. System creates change in PENDING_APPROVAL status
5. System records CREATED + SUBMITTED events
6. Change appears in the pending approval list

**Alternative Flows:**
- Standard type: skips approval, goes directly to SCHEDULED
- Emergency type: same as normal but flagged for expedited review

**Error Scenarios:**
- Missing rollback plan for normal/emergency type → 422
- Invalid change type → 422

### UC-002: Approve a Change

**Actor:** Admin
**Preconditions:** Change in PENDING_APPROVAL status
**Postconditions:** Change in SCHEDULED status

**Main Flow:**
1. Admin reviews change details, risk assessment, rollback plan
2. Admin clicks Approve (optional notes)
3. System transitions to SCHEDULED, records approved_by and approved_at
4. System records APPROVED event

### UC-003: Implement and Close with PIR

**Actor:** Technician/Admin
**Preconditions:** Change in SCHEDULED status
**Postconditions:** Change in CLOSED status with PIR

**Main Flow:**
1. Technician starts implementation → SCHEDULED → IN_PROGRESS
2. Technician completes implementation → IN_PROGRESS → IMPLEMENTED
3. Admin adds PIR (outcome, issues, lessons)
4. Admin closes change → IMPLEMENTED → CLOSED

### UC-004: Rollback a Failed Change

**Actor:** Technician/Admin
**Preconditions:** Change in IN_PROGRESS or IMPLEMENTED status
**Postconditions:** Change in ROLLED_BACK status

**Main Flow:**
1. During or after implementation, issues discovered
2. Technician/admin initiates rollback with mandatory reason
3. System transitions to ROLLED_BACK (terminal)
4. System records ROLLED_BACK event with reason

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| Sidebar / navSections.ts | Add "Changes" nav item in Operations section | Add nav entry |
| router.tsx | Add routes for list, detail, dashboard pages | Add lazy routes |
| locales (en.ts, es.ts) | Add i18n keys for changes module | Add translation keys |
| app.py | Register changes router | Add router include |
| Alembic | New migration for change_requests, change_events, post_implementation_reviews, change_assets tables | New migration file |
| Notification enums | Add CHANGE_APPROVED, CHANGE_REJECTED event types (optional, can defer) | Add enum values |
| Compliance Dashboard (E39) | Changes provide evidence for DORA Art. 9 controls | Future: link changes as compliance evidence |

## Definition of Done

- [ ] ChangeRequest CRUD with full state machine
- [ ] Approval/rejection workflow (admin only)
- [ ] Asset linking (M2M, cross-BC)
- [ ] Post-Implementation Review sub-entity
- [ ] Event timeline (ChangeEvent)
- [ ] List page with filters (status, type, date, assigned_to, search)
- [ ] Detail page with timeline, assets, PIR, action buttons
- [ ] Dashboard/calendar view (summary cards + upcoming changes)
- [ ] Unit tests for all commands and queries
- [ ] Integration tests for all endpoints
- [ ] i18n (EN + ES)
- [ ] Alembic migration

## Time Constraints

**Deadline:** ASAP — DORA compliance gap
**Type:** Soft
**Reason:** DORA Art. 9 requires formal change management procedures. E40 (vulnerability management) is now complete; E33 is the last DORA-urgent gap for micro scope.

## Scope Exclusions

- No change calendar with drag-and-drop scheduling
- No CAB board member management UI (admin = CAB for now)
- No automated conflict detection between overlapping changes
- No integration with MDM/SCCM/Intune
- No change templates or recurring changes
- No email notifications (in-app only, defer to future)
- No change-to-vulnerability linking (future scope)
- No SLA enforcement on change approval times

## Open Questions

None — scope is intentionally minimal for DORA compliance.
