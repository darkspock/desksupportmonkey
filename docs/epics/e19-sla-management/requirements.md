# E19: SLA Management — Requirements

**Date:** 2026-02-23
**Priority:** High
**Plan Gate:** Enterprise (`sla` feature key)

## Overview

Replace the hardcoded SLA thresholds (E5) with a configurable SLA policy system. Admins define response and resolution time targets per priority and optionally per request type/category. The system detects breaches in near-real-time, auto-escalates, notifies managers, and provides compliance reporting.

## Context

Currently, `SLA_THRESHOLDS_HOURS` in `src/request_bc/request/domain/constants.py` defines hardcoded resolution thresholds used only for dashboard alerts. E19 replaces this with:
- Admin-configurable SLA policies per priority (and optionally per request type)
- Separate response time and resolution time targets
- Automatic breach detection via Celery periodic task
- Escalation rules (auto-assign, auto-escalate priority, notify manager)
- SLA compliance reports and dashboard

## User Stories

### US1: Create SLA Policy
As an **admin**, I want to create SLA policies with response and resolution time targets per priority level, so that I can define service expectations for my organization.

**Acceptance Criteria:**
- Admin can create a named SLA policy (e.g., "Standard SLA", "VIP SLA")
- Each policy defines response_time_hours and resolution_time_hours per priority (urgent, high, medium, low)
- Optionally scope a policy to specific request types (incident, new_equipment, etc.)
- Only one active policy per priority+type combination (or a default if no type specified)
- Validation: response_time must be less than resolution_time

### US2: Edit/Delete SLA Policy
As an **admin**, I want to edit or delete SLA policies, so that I can adjust service targets as needed.

**Acceptance Criteria:**
- Admin can update policy name, targets, and type scope
- Admin can deactivate (soft-delete) a policy
- Cannot delete if policy has active breaches being tracked (warn)

### US3: SLA Breach Detection
As a **system**, I want to periodically check open requests against their applicable SLA policy, so that breaches are detected automatically.

**Acceptance Criteria:**
- Celery beat task runs every 5 minutes
- For each open request, find the matching SLA policy (by priority + type, fallback to priority-only default)
- Calculate response time: time from created_at to first status change beyond SUBMITTED (IN_REVIEW or later)
- Calculate resolution time: time from created_at to resolved_at (or current time if still open)
- If response_time exceeds policy.response_time_hours → mark response_breached
- If resolution_time exceeds policy.resolution_time_hours → mark resolution_breached
- Track breach timestamps on the request (first_response_at, response_breached_at, resolution_breached_at)

### US4: SLA Escalation Rules
As an **admin**, I want to define escalation actions when an SLA is about to breach or has breached, so that critical requests get attention.

**Acceptance Criteria:**
- Each SLA policy can have escalation rules:
  - **Warning** at X% of target time (e.g., 75%): notify assigned technician
  - **Breach**: notify admin/manager, optionally auto-escalate priority
- Escalation actions: notify_assignee, notify_admins, escalate_priority
- Each escalation fires only once per request per threshold

### US5: SLA Notifications
As a **manager/admin**, I want to be notified when SLA breaches occur, so that I can take corrective action.

**Acceptance Criteria:**
- New notification event types: SLA_WARNING, SLA_RESPONSE_BREACHED, SLA_RESOLUTION_BREACHED
- Notifications sent to: assigned technician (warning), admins (breach)
- Notification includes: request title, priority, time elapsed, SLA target

### US6: SLA Compliance Dashboard
As an **admin**, I want a dashboard showing SLA compliance metrics, so that I can monitor service quality.

**Acceptance Criteria:**
- Overall SLA compliance percentage (met vs breached in period)
- Compliance by priority level
- Compliance by request type
- Average response time vs target
- Average resolution time vs target
- Breach trend over time (weekly/monthly)

### US7: SLA Compliance Report
As an **admin**, I want to generate SLA compliance reports, so that I can share metrics with stakeholders.

**Acceptance Criteria:**
- New report type: sla_compliance
- Includes: period, total requests, met/breached counts, compliance %, avg times
- Uses existing Celery report generation pipeline (E6)

### US8: SLA Status on Request Detail
As a **technician**, I want to see the SLA status on each request, so that I know which requests need urgent attention.

**Acceptance Criteria:**
- Request detail shows: applicable SLA policy name, response target, resolution target
- Visual indicator: on-track (green), warning (yellow), breached (red)
- Time remaining or time exceeded

## Entities

### SlaPolicy
- `id`: ULID
- `company_id`: str
- `name`: str (e.g., "Standard SLA")
- `priority`: RequestPriority (urgent/high/medium/low)
- `request_type`: Optional[RequestType] (null = applies to all types for this priority)
- `response_time_hours`: float
- `resolution_time_hours`: float
- `warning_threshold_pct`: int (default 75 — trigger warning at 75% of target)
- `escalate_on_breach`: bool (default False)
- `is_active`: bool (default True)
- `created_at`: datetime
- `updated_at`: datetime

### SlaBreachRecord
- `id`: ULID
- `company_id`: str
- `request_id`: str
- `policy_id`: str
- `breach_type`: SlaBreachType (response_warning / response_breach / resolution_warning / resolution_breach)
- `target_hours`: float
- `actual_hours`: float
- `escalated`: bool
- `created_at`: datetime

## Enums

### SlaBreachType
- `response_warning`
- `response_breach`
- `resolution_warning`
- `resolution_breach`

## API Endpoints

### SLA Policies (admin only)
- `POST /api/v1/sla/policies` — Create policy
- `GET /api/v1/sla/policies` — List policies
- `GET /api/v1/sla/policies/{id}` — Get policy detail
- `PUT /api/v1/sla/policies/{id}` — Update policy
- `DELETE /api/v1/sla/policies/{id}` — Deactivate policy

### SLA Status (technician+)
- `GET /api/v1/sla/requests/{request_id}/status` — Get SLA status for a request

### SLA Dashboard (admin only)
- `GET /api/v1/sla/dashboard` — SLA compliance metrics

### SLA Report (admin only)
- Uses existing `POST /api/v1/reports` with type `sla_compliance`

## Integration Points

1. **Request BC**: Read request data (priority, type, status, created_at, resolved_at). Track first_response_at.
2. **Notification BC**: New event types for SLA warnings/breaches
3. **Report BC**: New report type for SLA compliance
4. **Dashboard**: Replace hardcoded SLA alerts with policy-based breach data
5. **Plan Gate**: Check `sla` feature availability before operations
6. **Celery Beat**: Periodic task for breach detection

## Definition of Done

- [ ] SLA policy CRUD with validation (response < resolution)
- [ ] Celery task detecting breaches every 5 minutes
- [ ] Breach records persisted with timestamps
- [ ] Notifications sent on warning/breach events
- [ ] SLA status visible on request detail (frontend)
- [ ] SLA compliance dashboard page
- [ ] SLA compliance report type
- [ ] Admin frontend: policy management page
- [ ] Plan gate enforced (Enterprise only)
- [ ] Unit tests for domain logic + command handlers
- [ ] Integration tests for endpoints
- [ ] i18n translations EN/ES
