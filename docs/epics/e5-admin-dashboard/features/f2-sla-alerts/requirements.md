# F2: SLA Breach Alerts

**Epic:** E5 - Admin Dashboard
**Feature:** F2
**Status:** Pending
**Depends on:** F0
**Date:** 2026-02-15

---

## User Stories

### US-E5-007: SLA Breach Alerts
**As an** admin, **I want** to see requests that have been open longer than SLA thresholds **so that** I can escalate overdue requests.

---

## Acceptance Criteria

### SLA Alerts (`GET /api/v1/dashboard/alerts/sla`)
- [ ] Returns open requests that exceed priority-based SLA thresholds
- [ ] Hardcoded SLA thresholds:
  - urgent: 4 hours
  - high: 24 hours (1 day)
  - medium: 72 hours (3 days)
  - low: 168 hours (7 days)
- [ ] Only open requests (submitted, in_review, in_progress)
- [ ] Response includes: id, title, type, priority, status, assigned_to, created_at, hours_open, sla_threshold_hours, breached (boolean)
- [ ] Sorted by hours_open desc (most overdue first)
- [ ] Admin+ role only
- [ ] Scoped by company_id

---

## Dependencies

- F0 must be complete (dashboard router exists)
- `ServiceRequestModel` exists with status, priority, created_at, assigned_to fields
- RequestStatus open values: submitted, in_review, in_progress
- RequestPriority values: low, medium, high, urgent
