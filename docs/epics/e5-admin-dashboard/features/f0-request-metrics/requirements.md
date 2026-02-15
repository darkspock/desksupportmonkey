# F0: Request Metrics + Dashboard Router

**Epic:** E5 - Admin Dashboard
**Feature:** F0
**Status:** Pending
**Date:** 2026-02-15

---

## User Stories

### US-E5-001: Request Summary Metrics
**As an** admin, **I want** to see a summary of all requests by type, priority, and status **so that** I can understand the current workload.

### US-E5-002: Resolution Time Analytics
**As an** admin, **I want** to see average resolution time for requests **so that** I can measure team performance and identify bottlenecks.

### US-E5-004: Requests Over Time
**As an** admin, **I want** to see request volume trends over time **so that** I can identify patterns and plan staffing.

---

## Acceptance Criteria

### Request Summary (`GET /api/v1/dashboard/requests/summary`)
- [ ] Returns counts by status (submitted, in_review, in_progress, resolved, rejected)
- [ ] Returns counts by type (incident, new_equipment, onboarding)
- [ ] Returns counts by priority (low, medium, high, urgent)
- [ ] Returns total_open (submitted + in_review + in_progress)
- [ ] Returns total_resolved count
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Resolution Time (`GET /api/v1/dashboard/requests/resolution-time`)
- [ ] Returns average resolution time overall (in hours, float)
- [ ] Returns average resolution time per technician (assigned_to)
- [ ] Only considers requests with resolved_at (resolved/rejected)
- [ ] Resolution time = resolved_at - created_at (in hours)
- [ ] Optional from_date/to_date filters (on resolved_at)
- [ ] Admin+ role only
- [ ] Scoped by company_id

### Request Trend (`GET /api/v1/dashboard/requests/trend`)
- [ ] Returns time-series data bucketed by day (default), week, or month
- [ ] Query param `bucket` accepts: day, week, month
- [ ] Each bucket: period label, total count, breakdown by type
- [ ] Default last 30 days, configurable via from_date/to_date
- [ ] Admin+ role only
- [ ] Scoped by company_id

---

## Dependencies

- Dashboard router does not exist yet — F0 creates it
- `ServiceRequestModel` exists with all required fields
- `require_role(UserRole.ADMIN)` dependency exists
- `app.py` needs router registration
