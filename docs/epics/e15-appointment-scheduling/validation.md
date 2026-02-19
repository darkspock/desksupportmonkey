# Requirement Validation Report

**Document:** E15 - Appointment Scheduling
**Date:** 2026-02-18
**Status:** Valid

## Summary

The E15 requirements document is comprehensive and implementation-ready. It defines a well-scoped new bounded context (`appointment_bc`) with clear entity models, a complete state machine, 7 user stories with testable acceptance criteria, 6 use cases with main/alternative/error flows, and detailed technical constraints. The collateral impact on existing systems is minimal and well-documented. All open questions are resolved with clear rationale.

Two minor gaps identified (employee overlap detection, admin appointment management) — both are low-risk and can be addressed during implementation.

---

## Business Alignment Assessment

**Primary Objective:** Operational efficiency and service quality
**Contribution:** Clear — scheduling gap in the request lifecycle is well-documented
**KPIs Defined:** Yes (4 targets)
**Justification Type:** Objective with workflow gap analysis

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | "100% to 0%" is specific; "90%+ slot utilization" is specific; but no baseline metrics for time-to-resolution or satisfaction |
| Evidence sources | Yes | References E3, E12, E14 gap analysis — valid for internal tooling |
| Revenue impact | N/A | Internal operations tool — operational efficiency is the correct framing |
| Customer names/tickets | N/A | Internal tool — no external customer evidence needed |

**Note:** For an internal IT service desk tool, workflow gap analysis is appropriate evidence. External customer evidence is not applicable.

### Experimentation Assessment
**Is this an experiment?** No — this is a standard feature epic.

**RED FLAGS:**
- [ ] Subjective justification detected — **No.** Pain points are concrete workflow gaps.
- [ ] Missing revenue/cost impact — **N/A.** Internal tool, operational efficiency framing is correct.
- [ ] No evidence provided — **No.** Evidence references existing epics and their limitations.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| Appointment | Create, Read, List, Filter | PENDING, CONFIRMED, COMPLETED, CANCELLED, NO_SHOW | Soft (cancel) |
| TechnicianAvailability | Create (upsert), Read, Update (upsert), Delete (reset), List | N/A (config) | Hard delete (reset to defaults) |
| AvailabilityOverride | Create, Read, Update, Delete, List | N/A (config) | Hard delete |

**Assessment:** All 3 entities have complete CRUD coverage. Appointment uses soft cancel instead of delete, which is correct for audit trail. Availability entities support hard delete since they are configuration data.

---

## Missing Use Cases

| Use Case | Reason | Priority | Recommendation |
|----------|--------|----------|----------------|
| Admin creates appointment for any request | Validation decision #5 says admins can create for "any request" but no dedicated UC covers admin-specific flow | Low | Covered implicitly by UC-001 — technician flow works for admin via role hierarchy. Add a note in UC-001 alternative flows. |
| Bulk cancel appointments (technician sick) | If a technician calls in sick, multiple appointments may need cancelling | Low | Not needed for MVP. Can cancel individually. Add as future enhancement. |
| View appointment history for a technician | Admin may want to see past appointment statistics per technician | Low | Covered by list endpoint with filters. Dashboard stats cover aggregate. Sufficient for MVP. |

---

## Missing State Information

| Entity | Missing Info | Recommendation |
|--------|--------------|----------------|
| Appointment | `RESCHEDULED` mentioned in validation decision #6 as a "transition state" but not in the actual enum — the document clarifies rescheduling creates a new appointment and cancels the old one | No change needed — design is correct. Old appointment → CANCELLED (reason: "Rescheduled"), new appointment → PENDING. |
| Appointment | No explicit handling of what happens when the linked request is resolved/rejected while an appointment is pending/confirmed | Add to technical constraints: "When a request moves to RESOLVED or REJECTED, any PENDING or CONFIRMED appointments for that request should be auto-cancelled by the status change handler." |
| TechnicianAvailability | No validation for overlapping availability windows on the same day (e.g., two entries for Monday 9:00-12:00 and 10:00-14:00) | Add validation: availability windows for the same technician + day_of_week must not overlap. |

---

## Collateral Impact Assessment

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Request Detail Page (technician + employee) | Frontend | Add "Schedule/Request Appointment" button + appointment cards | Frontend edit — both `RequestDetailPage.tsx` and employee view |
| Dashboard Page | Frontend | Add appointment stats card | Frontend edit |
| Notification EventType enum | Domain | Add 7 new event types (appointment.*) | Enum extension |
| TargetResolver | Application | Add resolver methods for appointment events | ~7 new resolver methods |
| NotificationSubscriber | Application | No changes needed — already handles all events generically | None |
| Sidebar Navigation | Frontend | Add Calendar/Appointments nav item | Frontend edit |
| Router (frontend) | Frontend | Add calendar page route + availability settings route | Frontend edit |
| app.py | Backend | Register appointment + availability routers | Router registration |
| Celery Beat config | Backend | Add 2 scheduled tasks (reminders + no-show detection) | Celery config edit |
| i18n (EN + ES) | Frontend | ~60-80 new translation keys | Locale file edits |
| Request status change handler | Backend | Auto-cancel appointments when request is resolved/rejected | **NEW — not in original doc** |

**Assessment:** Collateral impact is well-identified. One gap found: request status changes should cascade to linked appointments.

---

## Slicing Assessment

**Size:** Large (3 entities, 3 migrations, 17 API endpoints, 7+ command/query handlers, calendar frontend, 2 Celery Beat tasks)
**Slicing needed:** Yes — recommend 4-5 features
**Suggested slicing:**

| Feature | Scope | Complexity |
|---------|-------|------------|
| F0: Domain & Infrastructure | Entities, enums, migrations, repos, availability service | High |
| F1: Appointment CRUD | Create, confirm, cancel, complete, list, get + notifications | High |
| F2: Availability Management | Recurring schedule CRUD, overrides CRUD, slot computation endpoint | Medium |
| F3: Reminders & No-Show | Celery Beat tasks for reminders and auto no-show detection | Small |
| F4: Frontend — Calendar & UX | Calendar page, availability settings, request detail integration, dashboard card, i18n | High |

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| None | — | All dependencies (E3, E4) are complete |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** N/A
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis
No deadline — no risk.

---

## Testing Assessment

**Tests defined:** Yes (in Definition of Done)

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Overlap detection, availability computation, reminder logic — all mentioned |
| Integration | Yes | Yes | All API endpoints, availability, booking flow — mentioned |
| E2E | No | No | Not required for this project (no E2E framework) |
| UAT | No | No | Not required (internal tool, demo-verified) |

**Critical scenarios identified:** Yes
- Overlap detection (double-booking prevention)
- Availability computation (recurring + overrides - existing appointments)
- Reminder idempotency (no duplicate notifications)
- No-show auto-detection timing
- Rescheduling chain (cancel old → create new PENDING)
- Employee vs technician booking flow (PENDING vs CONFIRMED initial status)

**Test data requirements:** Defined implicitly (technician with availability, employee with request, various appointment states).

---

## Definition of Done Assessment

**DoD defined:** Yes (20 checkboxes)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — 7 stories with specific, testable criteria |
| Quality gates | Yes | Unit tests + integration tests + lint + frontend build |
| Sign-off process | Implicit | Follows project convention (make test, make lint, npm build) |
| Training needs | N/A | Internal tool — self-explanatory UI |

---

## Red Flags

- [ ] **None critical.** All red flags below are minor and non-blocking.

**Minor observations:**
1. Employee overlap detection not mentioned — should the system also check if the employee has a conflicting appointment? Currently only technician overlap is validated. **Recommendation:** Add employee overlap check as well — an employee shouldn't have two appointments at the same time.
2. No explicit mention of what `GET /api/v1/appointments/my` returns for technicians vs employees — endpoint exists for employees but technicians use the general list endpoint. This is fine but could be clearer.
3. The availability endpoint `GET /api/v1/availability/{technician_id}` is accessible by `employee+`, which means any employee can see any technician's schedule. This is intentional (needed for booking) but worth noting for privacy awareness.

---

## Open Questions for Stakeholder

All questions pre-resolved in the document. No new blocking questions identified.

**Suggestions for discussion (non-blocking):**
1. Should employee appointments also be overlap-checked? (Recommended: yes)
2. Should appointments auto-cancel when the linked request is resolved/rejected? (Recommended: yes — add to requirements)
3. Should availability window overlap validation be enforced? (Recommended: yes — prevent overlapping windows on same day)

---

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective identified (operational efficiency)
- [x] KPIs defined (4 targets)
- [ ] Baseline metrics for time-to-resolution (minor — hard to measure pre-implementation)
- [x] Evidence provided (workflow gap analysis)

### Content Completeness: 7/7 passed
- [x] Problem statement with pain points
- [x] Goals clearly defined (5 goals)
- [x] User stories with acceptance criteria (7 stories)
- [x] Entities with field definitions (3 entities)
- [x] State machine with transitions
- [x] API endpoints defined (17 endpoints)
- [x] Non-goals explicitly stated (9 items)

### Use Case Coverage: 5/6 passed
- [x] CRUD pattern covered
- [x] Lifecycle pattern covered (state machine)
- [x] State machine pattern covered (5 states, 5 transitions)
- [x] System-initiated patterns (reminders, no-show)
- [x] Inverse operations documented
- [ ] Admin-specific booking flow (minor — covered via role hierarchy)

### Entity States: 3/3 passed
- [x] Appointment: all states defined with transitions, triggers, conditions, side effects
- [x] TechnicianAvailability: stateless config entity — correct
- [x] AvailabilityOverride: stateless config entity — correct

### Collateral Impact: 8/9 passed
- [x] Affected existing entities identified
- [x] Notification system extension documented
- [x] Frontend impact documented
- [x] Celery Beat extension documented
- [x] Router registration identified
- [x] i18n impact quantified
- [x] No breaking changes
- [x] Backward compatibility confirmed
- [ ] Request status cascade to appointments (gap — add to requirements)

### Slicing: 3/3 passed
- [x] Size assessed (Large)
- [x] Slicing recommended (4-5 features)
- [x] No out-of-scope dependencies

### Time Constraints: 3/3 passed
- [x] No deadline (confirmed)
- [x] Dependencies satisfied
- [x] No calendar conflicts

### Testing: 4/4 passed
- [x] Unit tests defined
- [x] Integration tests defined
- [x] Critical scenarios identified
- [x] Test data requirements implied

### Definition of Done: 4/4 passed
- [x] Acceptance criteria testable
- [x] Quality gates defined
- [x] 20 specific checkboxes
- [x] Covers frontend + backend + tests + i18n

---

## Recommendations

1. **Add employee overlap validation** — When booking an appointment, also verify the employee doesn't have a conflicting appointment at the same time. Add to US-E15-001 and US-E15-003 acceptance criteria.

2. **Add request status cascade** — When a request moves to RESOLVED or REJECTED, auto-cancel any PENDING or CONFIRMED appointments linked to that request. Add as a new technical constraint and mention in collateral impact.

3. **Add availability window overlap validation** — Prevent technicians from creating overlapping availability windows on the same day (e.g., Monday 9:00-12:00 and 10:00-14:00). Add to US-E15-002 acceptance criteria.

4. **Update status to Validated** — After incorporating the 3 recommendations above, change document status from "Draft" to "Validated".
