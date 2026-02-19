# Requirements: E12 - Request Typification & Approval

**Epic:** E12
**Date:** 2026-02-18
**Priority:** High
**Status:** Pending
**Depends on:** E0 (Foundation), E1 (Company Management), E3 (Service Requests), E4 (Notifications), E7 (Frontend), E9 (UX), E11 (Department Equipment Profiles)

---

## Problem Statement

Today, every request uses one of three coarse types (`incident`, `new_equipment`, `onboarding`) with a fixed default priority per type. There is no way to classify requests more granularly, no priority scoring based on the requester's context, and no approval gate for costly equipment requests. This causes:

1. **Flat classification** — technicians manually triage all requests because the system provides no subcategory signal. A broken keyboard and a server outage both arrive as "incident."
2. **Static priority** — a laptop request from a new VP and one from an intern both get `low` priority. Department criticality and role seniority are ignored.
3. **No spending control** — any employee can submit a `new_equipment` request that goes directly to the technician queue without management oversight or cost-awareness.

---

## Goals

1. **Extend request types** with new categories (`repair`, `configuration`, `access_request`) and add subcategories within each type for granular classification.
2. **Implement priority scoring** that considers request type, subcategory, requester department, and requester role to compute a smarter default priority.
3. **Add an approval workflow** for `new_equipment` requests so department managers can approve or reject before technicians begin work.
4. **Keep backward compatibility** — existing requests remain valid; new fields are optional for types that don't need them.
5. **Expose everything in the frontend** — updated request creation form, approval queue for managers, and category/subcategory filters throughout.

---

## Validation Decisions (Closed)

1. **Category model:** Extend the `RequestType` enum with new values (`repair`, `configuration`, `access_request`). Add a new `subtype` field (nullable string enum) as a second-level classifier.
2. **Subtype scope:** Subtypes are defined per type — e.g., `new_equipment` has subtypes `computer`, `mobile`, `peripheral`, `monitor`, `software`. Subtypes are system-defined enums, not user-configurable (for now).
3. **Priority scoring:** A `PriorityScorer` service computes priority at request creation time. Scoring rules are system-defined (not configurable per company in this epic). The computed priority replaces the simple `DEFAULT_PRIORITY` map.
4. **Approval trigger:** All `new_equipment` requests enter `pending_approval` status. Department manager approves or rejects. If no manager is assigned (E11), request skips approval and enters `submitted` directly.
5. **Approval actors:** Department manager of the requester's department, OR any admin. Approvals are logged as request events.
6. **Status machine extension:** Add `pending_approval` between creation and `submitted`. New transitions: `pending_approval → submitted` (approve) and `pending_approval → rejected` (reject).
7. **Notification integration:** Approval requests notify the department manager. Approval/rejection decisions notify the requester.

---

## Non-Goals (This Epic)

- Configurable scoring rules per company (future — weight tables, custom formulas).
- Budget thresholds for approval routing (E14 — Procurement & Budget).
- AI-powered classification (E13 — separate epic).
- Multi-level approval chains (single manager approval is sufficient for now).
- Custom request types defined by admins (E30 — Custom Fields).

---

## User Stories

### US-E12-001: Request categories and subtypes
**As an** employee,
**I want to** choose a specific category and subcategory when submitting a request,
**So that** technicians can prioritize and route my request faster.

**Acceptance Criteria:**
- [ ] Request types expand to: `incident`, `new_equipment`, `onboarding`, `repair`, `configuration`, `access_request`.
- [ ] Each type has optional subtypes:
  - `incident`: `hardware`, `software`, `network`, `security`, `other`
  - `new_equipment`: `computer`, `mobile`, `peripheral`, `monitor`, `software`
  - `repair`: `hardware`, `software`, `network`, `other`
  - `configuration`: `software_install`, `account_setup`, `permissions`, `other`
  - `access_request`: `system_access`, `physical_access`, `vpn`, `other`
  - `onboarding`: (no subtypes — full onboarding pack from E11)
- [ ] Subtype is nullable (backward compatible — old requests have no subtype).
- [ ] Frontend form shows subtype options dynamically when a type with subtypes is selected.
- [ ] Subtype is stored on the request entity and visible in list/detail views.
- [ ] API accepts `subtype` in create request payload (optional string field).

### US-E12-002: Smart priority scoring
**As a** technician,
**I want** request priority to reflect the requester's context,
**So that** high-impact requests surface first without manual triage.

**Acceptance Criteria:**
- [ ] Priority is auto-computed at creation time by a `PriorityScorer` service.
- [ ] Scoring considers four dimensions:
  - **Type weight**: incident/security → +2, repair → +1, new_equipment → 0, configuration → 0, access_request → 0, onboarding → +1
  - **Subtype weight**: security/hardware subtypes → +1, other subtypes → 0
  - **Department weight**: configurable per department (default 0, range -1 to +2)
  - **Role weight**: admin → +1, technician → 0, employee → 0
- [ ] Raw score (sum of weights) maps to priority:
  - score >= 4 → `urgent`
  - score >= 3 → `high`
  - score >= 2 → `medium`
  - score <= 1 → `low`
- [ ] Default priority from `DEFAULT_PRIORITY` map is replaced by the scorer.
- [ ] Technicians can still manually change priority after creation.
- [ ] The computed score and breakdown are stored in `request.data.priority_scoring` for auditability.

### US-E12-003: Department priority weight
**As an** admin,
**I want to** set a priority weight per department,
**So that** critical departments (e.g., Engineering, Executive) get higher default priority.

**Acceptance Criteria:**
- [ ] `Department` entity gains a `priority_weight` field (integer, default 0, range -1 to +2).
- [ ] Admin can edit department priority weight from the Departments page.
- [ ] Priority weight is used by the `PriorityScorer` at request creation time.
- [ ] Migration adds the column with default value 0 (no behavior change for existing departments).

### US-E12-004: Approval workflow for new equipment requests
**As a** department manager,
**I want to** approve or reject new equipment requests from my team,
**So that** spending is controlled before technicians start working.

**Acceptance Criteria:**
- [ ] `new_equipment` requests are created with status `pending_approval` instead of `submitted`.
- [ ] If the requester's department has no manager assigned, request skips approval and enters `submitted` directly.
- [ ] Department manager and admins see a pending approvals queue (filtered request list).
- [ ] Manager can **approve** → request moves to `submitted` and enters the normal flow.
- [ ] Manager can **reject** → request moves to `rejected` with a mandatory reason.
- [ ] Approval/rejection creates a request event with the decision, actor, and reason.
- [ ] Requester is notified when their request is approved or rejected.
- [ ] Department manager is notified when a new equipment request from their team needs approval.

### US-E12-005: Category filters and visibility
**As a** technician,
**I want to** filter the request queue by type and subtype,
**So that** I can work on requests matching my expertise.

**Acceptance Criteria:**
- [ ] Request queue page includes subtype filter (populated dynamically based on selected type).
- [ ] Request list items show subtype badge when present.
- [ ] Request detail page displays type and subtype.
- [ ] "My Requests" page shows subtype for the employee's own requests.
- [ ] Dashboard request summary includes breakdown by subtype (new chart section or extended existing).
- [ ] Report generation includes subtype dimension.

---

## Domain & Data (High-Level)

### Extended Enums
- `RequestType`: Add `REPAIR`, `CONFIGURATION`, `ACCESS_REQUEST` to existing enum.
- `RequestSubtype`: New enum with values per parent type (flat enum, type→subtype mapping validated at application layer).
- `RequestStatus`: Add `PENDING_APPROVAL` to existing enum.

### Entity Changes
- `ServiceRequest`: Add `subtype: Optional[RequestSubtype]`.
- `Department`: Add `priority_weight: int` (default 0).

### Status Machine Extension
```
                  ┌─────────────────┐
                  │ pending_approval │ (new — new_equipment only)
                  └──────┬──────────┘
                   approve│    │reject
                         v    v
SUBMITTED ──> IN_REVIEW ──> IN_PROGRESS ──> RESOLVED
                  │                              │
                  └──> REJECTED <────────────────┘
```

### New Events
- `request.approval_requested` — when new_equipment request enters pending_approval
- `request.approved` — when manager approves
- `request.rejected` (existing) — extended with approval rejection reason

### Priority Scoring Metadata
Stored in `request.data.priority_scoring`:
```json
{
  "type_weight": 2,
  "subtype_weight": 1,
  "department_weight": 1,
  "role_weight": 0,
  "raw_score": 4,
  "computed_priority": "urgent"
}
```

---

## Technical Constraints

- Backward compatible: existing requests without subtype continue working.
- `pending_approval` status is only entered for `new_equipment` type — all other types go to `submitted` as before.
- Priority scoring runs synchronously during request creation (no async task needed — it's a simple calculation).
- E11 auto-assignment still triggers for `new_equipment` and `onboarding`, but for `new_equipment` it runs **after approval** (when moving from `pending_approval` to `submitted`), not at creation time.
- Multi-tenant isolation on all new fields and queries.
- Department `priority_weight` must be validated (range -1 to +2) at the domain layer.

---

## Definition of Done

- [ ] Request types extended with 3 new values and subtypes defined per type.
- [ ] Priority scoring replaces static defaults, with score breakdown stored on request.
- [ ] Department priority weight is admin-editable and feeds into scoring.
- [ ] Approval workflow gates `new_equipment` requests through manager approval.
- [ ] Auto-assignment (E11) triggers after approval, not at creation, for `new_equipment`.
- [ ] Frontend: updated request form, subtype filters, approval queue, department weight editor.
- [ ] Notifications: manager gets approval request, requester gets decision notification.
- [ ] Unit + integration tests cover scoring, approval flow, and backward compatibility.
- [ ] i18n keys for all new UI text (English + Spanish).
