# Epic E3: Service Requests

**Type:** Epic
**Status:** Pending Validation
**Created:** 2026-02-15
**Priority:** High
**Depends on:** E1 (Company Management), E2 (Asset Inventory)

---

## Business Alignment

**Objective:** Enable employees to submit IT service requests (incidents, new equipment, onboarding) and technicians to manage a prioritized queue with full state machine lifecycle, comments, and internal notes.

This epic delivers the core business workflow of the platform. E0-E2 built the foundation (auth, companies, assets), but without service requests there is no actual IT helpdesk functionality. E3 is the primary interaction point between employees and IT staff. It is also a prerequisite for real-time notifications (E4), admin dashboard metrics (E5), and report generation (E6).

---

## Problem Statement

### Current Situation
E0-E2 delivered authentication, company/user management, and asset inventory. But:
- No way for employees to report issues or request equipment
- No workflow for IT technicians to receive and process work
- No request lifecycle tracking or state machine
- No communication channel between employees and technicians
- No prioritization or queue management

### What E3 Delivers
A complete service request system where:
- Employees create typed requests (incident, new equipment, onboarding)
- Requests follow a validated state machine: `submitted` → `in_review` → `in_progress` → `resolved`/`rejected`
- System assigns automatic priority based on request type
- Technicians claim requests from a prioritized queue
- Both parties communicate via comments; technicians can add private internal notes
- Employees track their requests in a "My Requests" view

---

## Proposed Solution

### US-E3-001: Create Service Request (Employee)
**As an** employee
**I want** to submit a service request to the IT department
**So that** I can report problems or request equipment

**Acceptance Criteria:**
- [ ] `POST /api/v1/requests` creates a new service request
- [ ] Request types: `incident`, `new_equipment`, `onboarding`
- [ ] Required fields: type, title, description
- [ ] Optional fields: asset_id (for incidents), equipment_type (for new_equipment), employee_name + start_date + department_id (for onboarding)
- [ ] Request is created in `submitted` status
- [ ] Priority is auto-assigned based on type: incident=high, onboarding=medium, new_equipment=low
- [ ] Any authenticated user (employee+) can create requests
- [ ] Requests are scoped by company_id (multi-tenancy)

### US-E3-002: Request State Machine
**As a** technician
**I want** requests to follow a defined lifecycle
**So that** I can track progress and ensure nothing falls through the cracks

**Acceptance Criteria:**
- [ ] Valid states: `submitted`, `in_review`, `in_progress`, `resolved`, `rejected`
- [ ] Valid transitions:
  - `submitted` → `in_review` (technician picks up)
  - `in_review` → `in_progress` (technician starts work)
  - `in_review` → `rejected` (technician rejects)
  - `in_progress` → `resolved` (technician completes)
  - `in_progress` → `in_review` (technician sends back for re-evaluation)
- [ ] Invalid transitions return 409 with clear error message
- [ ] `PATCH /api/v1/requests/{id}/status` changes request status
- [ ] Only technician+ role can change status
- [ ] Status change records who changed it and when

### US-E3-003: Request Priority
**As a** technician
**I want** requests to have priority levels
**So that** I can work on the most urgent issues first

**Acceptance Criteria:**
- [ ] Priority levels: `low`, `medium`, `high`, `urgent`
- [ ] Default priority by type: incident=high, onboarding=medium, new_equipment=low
- [ ] Technician can override priority via `PATCH /api/v1/requests/{id}/priority`
- [ ] Only technician+ role can change priority
- [ ] Priority change is recorded in request history

### US-E3-004: Technician Queue
**As a** technician
**I want** to see all open requests in a prioritized queue
**So that** I can pick up and process work efficiently

**Acceptance Criteria:**
- [ ] `GET /api/v1/requests` lists all requests for the company
- [ ] Default sort: priority desc, then created_at asc (urgent first, oldest first within same priority)
- [ ] Filter by: status, type, priority, assigned_to
- [ ] Filter `assigned_to=me` shows only requests assigned to current technician
- [ ] Filter `assigned_to=none` shows unassigned requests
- [ ] Search by title or description (partial match)
- [ ] Pagination with page and page_size
- [ ] Only technician+ role can see the full queue

### US-E3-005: Claim/Assign Request
**As a** technician
**I want** to claim a request from the queue
**So that** other technicians know I'm handling it

**Acceptance Criteria:**
- [ ] `PATCH /api/v1/requests/{id}/assign` assigns request to a technician
- [ ] Technician can self-assign (claim) by passing their own user_id
- [ ] Only technician+ can assign
- [ ] Assignment is recorded in request history
- [ ] Request must be in `submitted` or `in_review` status to be assigned
- [ ] A request can be reassigned to a different technician

### US-E3-006: Comments
**As an** employee or technician
**I want** to add comments to a request
**So that** we can communicate about the issue

**Acceptance Criteria:**
- [ ] `POST /api/v1/requests/{id}/comments` adds a comment
- [ ] Comment fields: body (required)
- [ ] `GET /api/v1/requests/{id}/comments` lists all comments for a request
- [ ] Comments are ordered by created_at ascending
- [ ] Any authenticated user can comment on requests in their company
- [ ] Employee can only see and comment on their own requests
- [ ] Comment records author (user_id) and timestamp

### US-E3-007: Internal Notes (Technician Only)
**As a** technician
**I want** to add internal notes that only technicians can see
**So that** I can record technical details without confusing the employee

**Acceptance Criteria:**
- [ ] `POST /api/v1/requests/{id}/notes` adds an internal note
- [ ] Note fields: body (required)
- [ ] `GET /api/v1/requests/{id}/notes` lists all internal notes
- [ ] Only technician+ role can create and view internal notes
- [ ] Notes are NOT visible to employees
- [ ] Notes are ordered by created_at ascending

### US-E3-008: My Requests (Employee)
**As an** employee
**I want** to see all my submitted requests and their current status
**So that** I can track the progress of my issues

**Acceptance Criteria:**
- [ ] `GET /api/v1/my/requests` lists all requests created by the current user
- [ ] Any authenticated user can access (employee+)
- [ ] Response includes: id, type, title, status, priority, assigned_to, created_at, updated_at
- [ ] Pagination with page and page_size
- [ ] Filter by status
- [ ] Default sort: created_at desc (newest first)

### US-E3-009: Request Detail
**As a** user
**I want** to see the full details of a request
**So that** I can understand its current state and history

**Acceptance Criteria:**
- [ ] `GET /api/v1/requests/{id}` returns full request detail
- [ ] Employees can only view their own requests
- [ ] Technicians can view any request in their company
- [ ] Response includes all request fields + assigned technician info
- [ ] Response includes comment count

---

## Entities

| Entity | Description | New in E3? |
|---|---|---|
| `ServiceRequest` | IT service request with type, status, priority | New |
| `RequestComment` | Public comment on a request | New |
| `RequestNote` | Internal note visible only to technicians | New |
| `RequestEvent` | Append-only event for request audit trail | New |

### ServiceRequest Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `company_id` | ULID | FK to Company, NOT NULL, indexed |
| `created_by` | ULID | FK to User, NOT NULL, indexed |
| `assigned_to` | ULID | FK to User, nullable, indexed |
| `type` | enum | incident, new_equipment, onboarding |
| `title` | string(255) | NOT NULL |
| `description` | text | NOT NULL |
| `status` | enum | submitted, in_review, in_progress, resolved, rejected |
| `priority` | enum | low, medium, high, urgent |
| `data` | JSON | Type-specific payload (asset_id, equipment_type, employee_name, start_date, etc.) |
| `resolved_at` | datetime | nullable, set when resolved/rejected |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

**Indexes:** `(company_id, status)`, `(company_id, created_by)`, `(company_id, assigned_to)`

### RequestComment Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `request_id` | ULID | FK to ServiceRequest, NOT NULL, indexed |
| `author_id` | ULID | FK to User, NOT NULL |
| `body` | text | NOT NULL |
| `created_at` | datetime | Auto, NOT NULL |

### RequestNote Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `request_id` | ULID | FK to ServiceRequest, NOT NULL, indexed |
| `author_id` | ULID | FK to User, NOT NULL |
| `body` | text | NOT NULL |
| `created_at` | datetime | Auto, NOT NULL |

### RequestEvent Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | PK |
| `request_id` | ULID | FK to ServiceRequest, NOT NULL, indexed |
| `event_type` | string(50) | created, status_changed, assigned, priority_changed, comment_added, note_added |
| `data` | JSON | Event-specific payload |
| `performed_by` | ULID | FK to User, NOT NULL |
| `created_at` | datetime | Auto, NOT NULL |

**No updated_at** — events are immutable (same pattern as AssetEvent).

---

## Use Cases

### UC-E3-001: Submit Request
**Actor:** Employee
**Preconditions:** Authenticated in an active company

**Main Flow:**
1. Employee provides type, title, description, and type-specific data
2. System validates required fields and type-specific data
3. System assigns priority based on type
4. System creates ServiceRequest (status=submitted)
5. System creates RequestEvent (type=created)
6. Returns created request

**Alternative Flows:**
- A1: Invalid request type → 422 "Invalid request type"
- A2: Missing required fields → 422 with field-level errors
- A3: asset_id provided for incident but asset not found → 422 "Asset not found"

### UC-E3-002: Claim and Process Request
**Actor:** Technician
**Preconditions:** Request exists in `submitted` status

**Main Flow:**
1. Technician views queue, finds unassigned request
2. Technician claims request (assigns to self)
3. System records assignment event, transitions to `in_review`
4. Technician investigates, adds internal notes
5. Technician transitions to `in_progress`
6. Technician resolves request, transitions to `resolved`
7. System records status change events at each step

**Alternative Flows:**
- A1: Request already assigned → can still reassign
- A2: Invalid status transition → 409 "Cannot transition from X to Y"
- A3: Technician rejects request → transitions to `rejected`

### UC-E3-003: Employee Tracks Request
**Actor:** Employee
**Preconditions:** Employee has submitted a request

**Main Flow:**
1. Employee views "My Requests" list
2. Employee selects a specific request
3. Employee sees full details, comments, and current status
4. Employee adds a comment to provide more information
5. Technician responds via comment

**Alternative Flows:**
- A1: Employee tries to view someone else's request → 404 (not found)

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `models_registry.py` | Add ServiceRequestModel, RequestCommentModel, RequestNoteModel, RequestEventModel | Update imports |
| `app.py` | Register request router, extend my router | Update router includes |
| Alembic | New migration for 4 tables | Generate migration |
| `adapters/http/api/my/routers.py` | Add "My Requests" endpoint | Modify existing file |

---

## Bounded Context

```
src/request_bc/
├── request/
│   ├── domain/
│   │   ├── entities.py         # ServiceRequest, RequestComment, RequestNote, RequestEvent
│   │   ├── enums.py            # RequestType, RequestStatus, RequestPriority + transitions
│   │   └── repository.py       # RequestRepositoryInterface
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_request.py
│   │   │   ├── change_request_status.py
│   │   │   ├── change_request_priority.py
│   │   │   ├── assign_request.py
│   │   │   ├── add_comment.py
│   │   │   └── add_note.py
│   │   └── queries/
│   │       ├── list_requests.py
│   │       ├── get_request.py
│   │       ├── list_comments.py
│   │       ├── list_notes.py
│   │       └── my_requests.py
│   └── infrastructure/
│       ├── models.py           # ServiceRequestModel, RequestCommentModel, RequestNoteModel, RequestEventModel
│       └── repository.py       # RequestRepository

adapters/http/api/
├── requests/
│   ├── routers.py              # Request CRUD + status + assign + comments + notes (technician)
│   └── schemas.py
├── my/
│   ├── routers.py              # Add "My Requests" (employee) alongside "My Equipment"
│   └── schemas.py
```

---

## Definition of Done

- [ ] Employee can create service requests (incident, new_equipment, onboarding)
- [ ] Request state machine enforces valid transitions
- [ ] Priority auto-assigned based on type, overridable by technician
- [ ] Technician can list, filter, and sort the request queue
- [ ] Technician can claim/assign requests
- [ ] Public comments work for both employees and technicians
- [ ] Internal notes are only visible to technicians
- [ ] Employees can view and filter their own requests
- [ ] Every request mutation creates an append-only event
- [ ] All endpoints respect RBAC
- [ ] All queries scoped by company_id
- [ ] Alembic migration creates tables and indexes
- [ ] Unit tests for domain entities, state machine, and business rules
- [ ] API tests for all endpoints

---

## Open Questions

1. **Request-asset linking:** For incidents, should `asset_id` be a foreign key or just stored in the JSON `data` field? **Recommend:** Store in `data` JSON — keeps the request entity generic and avoids coupling to asset_bc. The asset reference is informational, not a hard dependency.
2. **Resolved vs Closed:** Should there be a separate `closed` state after `resolved`? **Recommend:** No. Keep it simple with `resolved` as terminal. If needed later, add `closed` as a post-resolution state.
3. **Comment edit/delete:** Should users be able to edit or delete comments? **Recommend:** No for v1. Comments are append-only like events. Keeps the audit trail clean.
4. **Request reopening:** Should resolved requests be reopenable? **Recommend:** Not in v1. Employee can create a new request referencing the old one.
5. **Auto-assignment on status change:** When a technician moves a request to `in_review`, should they be auto-assigned? **Recommend:** Yes — transitioning to `in_review` without being assigned should auto-assign the acting technician.
