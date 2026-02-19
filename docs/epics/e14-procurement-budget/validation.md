# Requirement Validation Report

**Document:** E14 - Procurement & Budget
**Date:** 2026-02-18
**Status:** Valid (all gaps resolved)

## Summary

The E14 requirements document is comprehensive and well-structured. It covers 5 entities, 21+ API endpoints, 6 user stories with testable acceptance criteria, 6 detailed use cases, and a complete PO state machine with transition table. The document follows the epic template closely and includes collateral impact analysis, technical constraints, and non-goals.

**Overall quality: Strong.** Three gaps need attention before slicing — one state machine gap (ORDERED → CANCELLED missing), one missing use case (PO PDF/print for vendors), and one cascade constraint gap (department deletion with POs). All are fixable without restructuring.

---

## Business Alignment Assessment

**Primary Objective:** Operational efficiency and cost control
**Contribution:** Clear — closes the procurement gap between E12 approval and E2 asset deployment
**KPIs Defined:** Yes — 4 measurable targets
**Justification Type:** Objective with structural evidence (gap in existing workflow)

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | "100% to 0%" is measurable but not based on real incident data |
| Evidence sources | Yes | References E12 gap, informal channels, missing cost data |
| Revenue impact | N/A | Internal tool — cost control, not revenue generation |
| Customer names/tickets | N/A | Internal platform feature, not customer-facing |

### RED FLAGS:
- [ ] ~~Subjective justification detected~~ — No, evidence is structural
- [ ] ~~Missing revenue/cost impact~~ — N/A for internal tool
- [ ] ~~No evidence provided~~ — Evidence is workflow gap from E12
- [ ] ~~Experiment without success metrics~~ — Not an experiment
- [ ] ~~Experiment without investment limit~~ — Not an experiment

**Assessment:** Acceptable. For an internal platform tool, structural evidence (identified workflow gap) is sufficient. Traditional SaaS KPIs (Revenue/Churn/Sales) don't apply directly.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| PurchaseOrder | C/R/U(draft)/L/Filter ✅ | 8 states, transition table ✅ | Cancel (soft) ✅ |
| PurchaseOrderItem | C/R/U(draft)/D(draft)/L ✅ | No status (qty tracking) ✅ | Delete from draft PO ✅ |
| PurchaseOrderRequest | Create implicit ✅ | N/A (join table) ✅ | Cascade with PO ✅ |
| Vendor | C/R/U/L/Search ✅ | active/inactive ✅ | Soft deactivate ✅ |
| DepartmentBudget | C(upsert)/R/U(upsert)/L ✅ | N/A (value entity) ✅ | Not defined (set to 0) ✅ |
| CompanyProcurementConfig | C(upsert)/R/U(upsert) ✅ | N/A (singleton) ✅ | Not needed ✅ |

**CRUD coverage: Complete.** All entities have appropriate operations defined.

---

## Missing Use Cases

| # | Use Case | Reason | Priority | Recommendation |
|---|----------|--------|----------|----------------|
| 1 | Cancel ORDERED PO (vendor cancels) | State machine doesn't allow ORDERED → CANCELLED | **High** | Add transition with conditions |
| 2 | PO PDF/print for vendor | Common procurement need — send PO to vendor | Medium | Add to scope or Non-Goals |
| 3 | Bulk budget allocation | Admin sets budgets for all departments at once | Low | Defer — single dept at a time is fine for MVP |
| 4 | PO export (CSV list) | Export PO list for finance/audit | Low | Defer — reports cover this partially |
| 5 | Department deleted with POs/budget | What happens to POs and budget when department is deactivated? | **High** | Define cascade/constraint behavior |
| 6 | PO item cancelled by vendor mid-receipt | One item of a multi-item PO won't be delivered | Medium | Define whether received_qty can stay < qty and PO can still close |

---

## Missing State Information

| Entity | Missing Info | Recommendation |
|--------|--------------|----------------|
| PurchaseOrder | ORDERED → CANCELLED transition not defined | Add: vendor cancels order, admin cancels after ordering. Conditions: admin role, mandatory reason. Side effect: notify creator. |
| PurchaseOrder | No restore from CANCELLED | Expected — cancellation is final. Document explicitly. |
| PurchaseOrder | PARTIALLY_RECEIVED → CLOSED (skip RECEIVED) | Should admin be able to close a partially received PO when remaining items are cancelled by vendor? Add this transition. |
| Vendor | No mention of what happens to POs when vendor is deactivated | Clarify: existing POs with deactivated vendor remain valid; vendor just not selectable for new POs. (Already implied but not explicit.) |

### Recommended State Machine Additions

```
ORDERED → CANCELLED         (admin cancels after ordering — vendor issue)
PARTIALLY_RECEIVED → CLOSED (admin closes with partial receipt — remaining items cancelled)
```

Updated transition table rows to add:

| From | To | Trigger | Conditions | Side Effects |
|------|----|---------|------------|--------------|
| ORDERED | CANCELLED | cancel() | Admin role, mandatory reason | Notifies creator. Records cancellation reason |
| PARTIALLY_RECEIVED | CLOSED | close() | Technician+ role | Finalizes PO with partial receipt |

---

## Collateral Impact Assessment

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Asset Entity | Data | Add `purchase_cost_cents` field | Migration + entity + model edit. **Confirmed: field does not exist.** |
| Request Detail Page | UI | Show linked POs section | Frontend edit (new card component) |
| Dashboard Page | UI | 2 new cards (Budget Health, Recent POs) | Frontend edit |
| Report System | Domain | Add `DEPARTMENT_SPENDING` to ReportType enum | Enum + template + Celery task. **Current types: asset_inventory, request_summary, technician_performance.** |
| Departments Page | UI | Budget column (allocated/spent/remaining) | Frontend edit |
| Notification EventType | Domain | Add 5 new event types (po.submitted, po.approved, po.cancelled, po.received, budget.threshold_reached) | Enum + subscriber + resolver. **Current: 9 event types.** |
| Department Delete | Business rule | Prevent deactivation if department has non-closed POs | Add check to `DeleteDepartmentCommandHandler`. **Current pattern: blocks if users assigned.** |
| Sidebar Navigation | UI | Add PO and Vendor nav items | Sidebar.tsx edit |
| Router | UI | Add 5+ new routes (PO list, PO detail, PO form, vendor list, procurement settings) | router.tsx edit |
| i18n | UI | ~80-100 new keys (EN + ES) | Locale file edits |
| app.py | Infrastructure | Register new routers (purchase-orders, vendors, budgets, procurement-settings) | Router registration |

**Impact coverage in document: Good.** 9 of 11 impacts were identified. Missing: department deletion constraint and app.py router registration.

---

## Slicing Assessment

**Size:** LARGE — 6 entities, 6 user stories, 21+ endpoints, 5+ frontend pages, Celery task, notifications, migrations
**Slicing needed:** Yes — mandatory. Too large for a single implementation pass.
**Recommended slicing:** 6-8 features following bottom-up dependency order

**Suggested slice order:**
1. F0: Domain + Migrations (entities, enums, models, migrations for all 6 tables)
2. F1: Vendor CRUD (simplest entity, needed by PO)
3. F2: Procurement Config (company settings, needed by PO approval logic)
4. F3: PO Lifecycle (core — create, submit, approve, cancel, ordered)
5. F4: Budget Allocation (department budgets, spending computation)
6. F5: Budget Enforcement (warn/strict modes, auto-approval threshold)
7. F6: Goods Receipt (receive items, asset creation/linking)
8. F7: Frontend + Reports + Dashboard (all UI, spending report, dashboard cards)

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| E25 Vendor Management | No — minimal vendor entity is sufficient | E25 expands with contracts/SLAs later |
| E20 Asset Lifecycle | No — `purchase_cost_cents` is the only field needed | E20 adds depreciation/TCO later |
| E4 Notification infra | Already complete | Just need new event types |
| E6 Report infra | Already complete | Just need new report type |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** N/A
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline, no risk. Proceed at normal pace.

---

## Testing Assessment

**Tests defined:** Partially — mentioned in DoD but not detailed per use case

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (DoD) | Need specifics: PO state machine transitions, budget computation, enforcement modes, fiscal year calculation |
| Integration | Yes | Yes (DoD) | Need specifics: all 21+ endpoints, PO workflow end-to-end, budget enforcement, concurrent PO numbering |
| E2E | No | No | Not needed — integration tests cover HTTP stack |
| UAT | No | No | Internal tool — manual testing sufficient |

**Critical scenarios identified:** Yes — PO lifecycle, budget enforcement, goods receipt, auto-approval
**Test data requirements:** Not explicitly defined but existing test fixtures (conftest.py) provide company/department/user data. New fixtures needed: vendor, PO, budget.

**Missing critical test scenarios:**
1. Concurrent PO number generation (race condition)
2. Budget computation with POs across multiple statuses
3. Fiscal year boundary edge cases (start_month != January)
4. Partial receipt → full receipt → close sequence
5. PO with deactivated vendor
6. Department deletion blocked by active POs

---

## Definition of Done Assessment

**DoD defined:** Yes — 19 checkboxes
**Coverage:** Comprehensive

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes (per US) | Yes — testable |
| Quality gates | Partial | Missing: lint, type check, test coverage threshold |
| Sign-off process | No | Not defined — but project uses standard progress tracking (tasks.md → slicing.md → roadmap.md) |
| Training needs | N/A | Internal tool — no training needed |

---

## Red Flags

- [x] **ORDERED → CANCELLED missing** — If a vendor cancels after order is placed, there's no way to cancel the PO. This is a real business scenario. **Must fix.**
- [x] **PARTIALLY_RECEIVED → CLOSED missing** — If some items are never going to arrive (vendor partial cancellation), the PO can never be closed. **Must fix.**
- [x] **Department deletion with POs** — No mention of what happens to POs and budgets when a department is deactivated. Needs constraint check (block deactivation if active POs exist) or cascade rule. **Must fix.**
- [ ] ~~No PO PDF/print~~ — Nice to have, not critical. Can be added in a later epic or as a follow-up. Flag for user decision.
- [ ] ~~No bulk operations~~ — Acceptable for MVP. Individual operations are sufficient.

---

## Open Questions for Stakeholder

1. **ORDERED → CANCELLED:** Should an admin be able to cancel a PO that has already been marked as ORDERED (e.g., vendor cancels the order)? Recommendation: Yes — add this transition.
2. **Partial close:** Should a PO be closeable from PARTIALLY_RECEIVED when remaining items will never arrive? Recommendation: Yes — add PARTIALLY_RECEIVED → CLOSED transition.
3. **PO PDF/print:** Should technicians be able to generate a printable PO document to send to vendors? This is common in procurement but adds scope. Include in E14 or defer?
4. **Department deactivation:** Should department deactivation be blocked if the department has open (non-closed/non-cancelled) POs? Recommendation: Yes — follow existing pattern from user check.

---

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective identified
- [x] Contribution clear
- [x] KPIs defined
- [ ] Evidence with specific data points (acceptable — internal tool)

### Content Completeness: 7/7 passed
- [x] Problem statement
- [x] Goals
- [x] Validation decisions
- [x] Non-goals
- [x] User stories with acceptance criteria
- [x] Domain model
- [x] Technical constraints

### Use Case Coverage: 4/6 passed
- [x] Happy paths defined (6 use cases)
- [x] Alternative flows defined
- [x] Error scenarios defined
- [x] Role-based access defined
- [ ] ORDERED cancellation scenario missing
- [ ] Partial close scenario missing

### Entity States: 5/7 passed
- [x] PurchaseOrder state machine with diagram
- [x] Transition table with triggers/conditions/side effects
- [x] Vendor activate/deactivate
- [x] Delete strategies defined
- [x] Inverse operations documented
- [ ] ORDERED → CANCELLED transition missing
- [ ] PARTIALLY_RECEIVED → CLOSED transition missing

### Collateral Impact: 9/11 passed
- [x] Asset entity
- [x] Request detail page
- [x] Dashboard
- [x] Report system
- [x] Departments page
- [x] Notifications
- [x] Sidebar/Router
- [x] i18n
- [x] Technical constraints
- [ ] Department deletion constraint not documented
- [ ] app.py router registration not mentioned

### Slicing: 2/2 passed
- [x] Size assessed as Large
- [x] Slicing needed (not yet done — expected, it's the next step)

### Time Constraints: 2/2 passed
- [x] No deadline — documented
- [x] No calendar conflicts — documented

### Testing: 2/3 passed
- [x] Unit and integration tests required
- [x] Critical scenarios identified
- [ ] Specific test scenarios not enumerated (acceptable — defined at tasks level)

### Definition of Done: 2/3 passed
- [x] 19 acceptance criteria defined
- [x] Testable and clear
- [ ] Quality gates not explicit (lint, type check)

---

## Recommendations

1. **[Must Fix] Add ORDERED → CANCELLED transition** to the PO state machine. Trigger: admin cancel. Conditions: admin role, mandatory cancellation reason. Side effects: notify creator. This covers the common case of a vendor cancelling a placed order.

2. **[Must Fix] Add PARTIALLY_RECEIVED → CLOSED transition** to the PO state machine. Trigger: admin/technician close. This covers the case where remaining items are permanently unavailable (vendor partial cancellation, discontinued product).

3. **[Must Fix] Add department deactivation constraint** to Collateral Impact. When a department is deactivated, block if the department has POs in non-terminal status (not CLOSED or CANCELLED). Follow existing pattern from `DeleteDepartmentCommandHandler` user count check.

4. **[Should Fix] Clarify vendor deactivation behavior** — explicitly state that existing POs with a deactivated vendor remain valid; the vendor is simply not selectable for new POs.

5. **[Nice to Have] PO PDF/print** — Defer to a follow-up or include as an optional F8. Common procurement need but not blocking for core functionality.

6. **[Nice to Have] Add quality gates to DoD** — "Lint passes (mypy + flake8)" and "TypeScript compiles (`tsc --noEmit`)" for completeness, following E12/E13 patterns.
