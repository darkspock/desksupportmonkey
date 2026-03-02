# Requirement Validation Report

**Document:** E53 — Request Conversation & Email Notifications
**Date:** 2026-03-02
**Status:** Valid (all gaps resolved after stakeholder Q&A)

## Summary

Solid epic with clear business justification and well-defined technical scope. The 3-feature structure (status + email + UX) is coherent and the existing infrastructure (EventBus, EmailService, TargetResolver) supports implementation cleanly. However, there are several gaps that should be addressed before implementation: the SLA pause mechanism lacks a tracking strategy, email infrastructure references don't match the actual codebase (Brevo, not SMTP), comment edit/delete is unaddressed, and the auto-transition logic has edge cases. None are blockers — all are refinements.

---

## Business Alignment Assessment

**Primary Objective:** Churn (retain customers by matching industry-standard support features)
**Contribution:** Clear — without email notifications and conversation tracking, DSM Control is significantly behind competitors (ServiceNow, Freshdesk, Zendesk, Jira SM)
**KPIs Defined:** Yes (4 KPIs with measurable targets)
**Justification Type:** Objective with industry evidence

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | KPI targets are defined (50% reply in 4h, 60% open rate) but no customer-specific data |
| Evidence sources | Yes | Industry comparison with named competitors |
| Revenue impact | Indirect | Table-stakes feature — lack of it causes churn, not a direct revenue generator |
| Customer names/tickets | No | No specific customer complaints or ticket IDs cited |

### Experimentation Assessment
**Is this an experiment?** No — this is a table-stakes feature that every ITSM competitor already has.

**RED FLAGS:**
- [ ] Subjective justification detected — N/A, industry evidence is strong
- [ ] Missing revenue/cost impact — Acceptable: this is a churn-prevention / feature-parity feature
- [ ] No evidence provided — N/A, competitors listed
- [ ] Experiment without success metrics — N/A
- [ ] Experiment without investment limit — N/A

**Verdict:** Business alignment is sound. The justification is "competitor parity" which is valid for a product at this stage. No customer-specific data is a minor gap but doesn't weaken the case.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| RequestComment (existing) | Create ✓, Read ✓, List ✓, Update ✗, Delete ✗ | N/A (stateless) | Not addressed |
| RequestStatus.WAITING_FOR_EMPLOYEE (new value) | N/A (enum value) | Transitions fully defined | N/A |
| Email notification (transient) | Create (send) only | N/A (fire-and-forget) | N/A |

---

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Comment editing | Employee or technician types wrong info — no edit capability mentioned | Low | Should comments be editable? Or is immutability intentional for audit trail? |
| Comment deletion | Sensitive info posted by accident — no delete capability | Medium | Should comments be deletable? Soft-delete with admin-only permission? |
| Email delivery failure | What happens if Brevo returns an error? No retry logic mentioned | Medium | Should we retry failed emails? How many times? |
| Multiple employees on a request | Request created by manager on behalf of employee — who gets notified? | Medium | Does `created_by` always equal the employee who should receive emails? Or could the request be created on behalf of someone else? |
| Reassignment while waiting | Request is in `waiting_for_employee` and gets reassigned to a different technician | Low | Should the new technician be notified that the request is waiting for employee response? |
| Bulk status change | Admin changes multiple requests to waiting_for_employee at once | Low | Is bulk status change to `waiting_for_employee` needed? (Probably not initially) |
| Email preview before sending | Technician wants to see what the employee will receive | Low | Deferred — nice-to-have |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| SLA clock | **How to track waiting_for_employee duration** — the requirements say "subtract time" but don't specify the tracking mechanism. There are no dedicated `sla_pause_start` / `sla_pause_end` fields. RequestEvent log exists but wasn't designed for SLA calculation. | How will the SLA calculator determine total time spent in `waiting_for_employee`? Options: (A) Query status-change events from RequestEvent table, (B) Add dedicated `sla_paused_at` / `sla_paused_duration_seconds` fields to ServiceRequest, (C) Create a new `SlaClockEntry` table tracking clock pauses |
| ServiceRequest.resolved_at | Currently set when status changes to RESOLVED or REJECTED. If request goes `waiting_for_employee` → `resolved`, does `resolved_at` still get set correctly? | Verify the existing `change_status` logic handles this path |
| Email send log | No tracking of which emails were sent/failed/opened | Should we log email sends for debugging and KPI measurement (open rate)? Or rely on Brevo's dashboard? |

---

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `request_bc/domain/enums.py` | Domain | Add enum value | Modify — low risk |
| `request_bc/domain/entities.py` | Domain | Add transitions + resolved_at logic for new paths | Modify — verify `resolved_at` is set correctly from `waiting_for_employee` → `resolved` |
| `request_bc/application/commands/add_comment.py` | Application | Auto-transition logic | Modify — medium complexity (needs request repo access + status change event) |
| `notification_bc/services/` | Application | New EmailSubscriber | Create new file — follows existing NotificationSubscriber pattern |
| `notification_bc/services/target_resolver.py` | Application | May need email-specific resolution (different from in-app targets) | Verify — current logic already resolves to created_by + assigned_to |
| `sla_bc/queries/get_request_sla.py` | Query | Subtract waiting time from resolution elapsed | Modify — **significant change**, needs tracking mechanism decided first |
| `core/email.py` | Infrastructure | Add email template functions | Modify — follows existing pattern (magic link, admin promotion) |
| `core/tasks/` | Infrastructure | New Celery task for async email | Create new task — follows existing pattern |
| `adapters/http/api/dependencies.py` | DI | Register EmailSubscriber in EventBus | Modify — 3 lines |
| `alembic/versions/` | Database | New migration for status enum | Create migration — standard |
| Frontend: `RequestDetailPage.tsx` | UI | Major redesign of comment section | Modify — significant frontend change |
| Frontend: `locales/*.ts` | UI | New i18n keys | Modify — straightforward |
| `adapters/mcp/tools/requests.py` | Integration | Verify change_request_status supports new value | Verify only — should work if enum is updated |
| Dashboard / reporting queries | Reporting | Any query that filters/counts by status needs to handle new value | Verify — check for hardcoded status lists |

**Additional collateral not mentioned in requirements:**

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Request list filters (frontend) | UI | Status filter dropdown needs `waiting_for_employee` option | Modify |
| Request list API | API | Any `status` filter parameter needs to accept new value | Verify |
| Dashboard status breakdown | Reporting | Pie chart / status counts need new category | Verify — if dynamically generated, may auto-include |
| Export / CSV | Reporting | Status column must show new value | Verify |
| Webhook payloads | Integration | If webhooks exist for status changes, new value will flow through | Verify |

---

## Slicing Assessment

**Size:** Medium (3 features, ~15 files to create/modify)
**Slicing needed:** Already sliced into 3 features
**Natural implementation order:** F1 (Status) → F2 (Email) → F3 (UX)

**Slicing quality:**
- F1 (Status) is independently valuable — technicians get the waiting status even without email
- F2 (Email) depends on F1 — email on `waiting_for_employee` needs the status to exist
- F3 (UX) depends on F1 — conversation bubbles can be built independently but waiting banner needs F1

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|----------------|-----|
| E23 email intake (reply-by-email) | Reply-To header format | The requirement wisely defers this, but the email Reply-To should be structured for future intake |
| Email unsubscribe preferences | Decision on whether to add | Open question #2 — recommend deferring but noting in design |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** Yes — scope is well-bounded for a medium epic
**Calendar conflicts:** None identified
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline specified. Risk is low — this is a priority feature but not time-boxed.

---

## Testing Assessment

**Tests defined:** Partially
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Good coverage of transitions, auto-transition, email subscriber, SLA |
| Integration | Yes | Yes | E2E flows for comment + status change + email |
| E2E | Should have | No | No browser/Playwright tests mentioned for conversation UI |
| UAT | Recommended | No | No UAT process defined — who verifies the UX? |

**Critical scenarios identified:** Yes — the key flows are well-covered
**Test data requirements:** Not explicitly defined — needs:
- A request in `in_progress` status with assigned technician
- Employee and technician user accounts
- SLA policy attached to the request
- Multiple waiting cycles for SLA calculation tests

---

## Definition of Done Assessment

**DoD defined:** Yes (14 checkboxes)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes (9 user stories with AC) | Yes |
| Quality gates | Yes (`make test` + `make lint`) | Yes |
| Sign-off process | No | Who reviews and approves? |
| Training needs | No | Do technicians need guidance on the new workflow? |

---

## Red Flags

- [x] **SLA tracking mechanism undefined** — The requirement says "subtract waiting_for_employee time" but doesn't specify HOW to track when the clock paused and resumed. This is a critical implementation detail that affects the SLA feature's design.
- [x] **Email infrastructure mismatch** — Requirements mention "SMTP" and "Mailpit" for dev, but the actual codebase uses Brevo HTTP API for production and `ConsoleEmailService` for development. The requirement references `APP_URL` but the codebase uses `FRONTEND_URL`. These are naming discrepancies that should be corrected.
- [x] **Auto-transition edge case** — The requirement checks `command.author_id == request.created_by` to trigger auto-transition. But what if a request was created by a manager on behalf of an employee? The `created_by` may not be the "employee" in the conversation. Consider using a role-based check instead (is the commenter a non-technician?).
- [ ] Comment edit/delete not addressed — Acceptable if immutability is intentional for audit trail, but should be explicitly stated.

---

## Open Questions for Stakeholder

1. **SLA tracking mechanism:** How should we track time spent in `waiting_for_employee`? Three options:
   - (A) **Query RequestEvent table** — Look at status_changed events to reconstruct clock pauses. Cheapest but fragile.
   - (B) **Add fields to ServiceRequest** — `sla_paused_at: Optional[datetime]` + `sla_paused_total_seconds: int`. Simple but doesn't track individual cycles.
   - (C) **New SlaClockEntry table** — Tracks every pause/resume with timestamps. Most robust but more complex.
   - **Recommendation:** Option B for simplicity, with option C as a future upgrade if needed.

2. **Auto-transition trigger:** Should the auto-transition from `waiting_for_employee` → `in_progress` be triggered by:
   - (A) Only the request creator (`created_by`) — current requirement
   - (B) Any user with `employee` role — handles "created on behalf of" scenarios
   - (C) Any non-technician user — broadest
   - **Recommendation:** Option A for now, with a TODO for B if "on behalf of" requests become common.

3. **Email infrastructure naming:** The requirements reference `APP_URL` and "SMTP" but the codebase uses `FRONTEND_URL` and Brevo HTTP API. Should the requirement be updated, or should we add an `APP_URL` alias?
   - **Recommendation:** Use the existing `FRONTEND_URL` setting. Update the requirement to match the codebase.

4. **Comment immutability:** Are comments intentionally immutable (no edit, no delete) for audit trail purposes? If so, this should be explicitly stated. If not, edit/delete should be added to scope or deferred.
   - **Recommendation:** Explicitly state immutability is intentional. Add soft-delete as a future enhancement.

5. **Email delivery failure handling:** What happens if Brevo returns an error when sending a comment notification email?
   - **Recommendation:** Celery task with automatic retry (3 attempts, exponential backoff). Log failures. Don't block the comment save.

---

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective clearly defined
- [x] KPIs measurable
- [x] Evidence provided (industry comparison)
- [ ] Customer-specific data missing (acceptable for table-stakes feature)

### Content Completeness: 7/9 passed
- [x] Problem statement clear
- [x] Solution overview defined
- [x] User stories with acceptance criteria
- [x] Domain changes specified
- [x] Database migration defined
- [x] i18n keys defined
- [x] Resolved decisions documented
- [ ] SLA tracking mechanism not specified (implementation detail)
- [ ] Infrastructure references don't match codebase (naming)

### Use Case Coverage: 4/7 passed
- [x] Happy path well covered
- [x] Auto-transition logic defined
- [x] Status transitions complete
- [x] Email notification rules defined
- [ ] Comment edit/delete not addressed
- [ ] Email delivery failure not addressed
- [ ] Multi-employee / "on behalf of" scenario not addressed

### Entity States: 4/5 passed
- [x] New status value defined
- [x] Transition map complete
- [x] SLA impact described
- [x] Auto-transition trigger defined
- [ ] SLA clock pause/resume tracking mechanism missing

### Collateral Impact: 5/6 passed
- [x] Affected bounded contexts identified
- [x] Frontend changes listed
- [x] Database migration identified
- [x] MCP tool impact noted
- [x] Event bus integration described
- [ ] Dashboard/filter/export impact not mentioned (request list filters, status breakdown, CSV export)

### Slicing: 3/3 passed
- [x] Natural 3-feature split
- [x] Dependencies between features noted
- [x] Implementation order implied (F1 → F2 → F3)

### Time Constraints: 1/1 passed
- [x] No deadline — no risk

### Testing: 2/4 passed
- [x] Unit test scenarios defined
- [x] Integration test scenarios defined
- [ ] E2E / browser tests not mentioned
- [ ] Test data requirements not explicit

### Definition of Done: 3/4 passed
- [x] Acceptance criteria testable
- [x] Quality gates defined (make test + make lint)
- [ ] Sign-off process not defined
- [x] DoD checklist complete (14 items)

---

## Recommendations

1. **Define SLA tracking mechanism** before implementation. Recommend adding `sla_paused_at` and `sla_paused_total_seconds` fields to ServiceRequest for simplicity. This affects the database migration and SLA query logic — deciding later will cause rework.

2. **Fix infrastructure references** in the requirement. Replace "SMTP" with "Brevo HTTP API", "Mailpit" with "ConsoleEmailService", and `APP_URL` with `FRONTEND_URL`. Minor but prevents confusion during implementation.

3. **Explicitly state comment immutability** or add edit/delete to scope. The current silence on this topic will generate questions during implementation.

4. **Add Celery retry strategy** for email sending. Specify: 3 retries, exponential backoff, log failures, never block comment save. This is a 2-line addition to the requirement but saves implementation ambiguity.

5. **Add request list filter impact** to collateral. The status filter dropdown, dashboard status breakdown, and any CSV/export functionality need to handle the new status value.

6. **Consider the auto-transition edge case** where `created_by` doesn't match the actual employee. If "on behalf of" requests are planned, define the logic now. If not, document that `created_by` is always the employee.

**Overall assessment:** The epic is well-structured and close to implementation-ready. The SLA tracking mechanism is the only gap that should be resolved before starting — everything else can be clarified during implementation without rework risk.
