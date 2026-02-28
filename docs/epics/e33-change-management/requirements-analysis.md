# Requirement Validation Report

**Document:** E33 — Endpoint Change Management (Simplified)
**Type:** Epic
**Date:** 2026-02-27
**Status:** Valid

## Summary

Well-structured, lightweight epic with clear DORA compliance motivation. The requirement covers all essential areas: entities with detailed fields, a complete state machine with transitions, 9 user stories with acceptance criteria, use cases, collateral impact, and scope exclusions. The "minimal viable DORA compliance" approach is sound — reuses proven patterns from existing BCs while creating a clean new bounded context.

A few minor gaps identified below — none are blockers.

## Business Alignment Assessment

**Primary Objective:** Regulatory Compliance (DORA Cap. II, Art. 9)
**Contribution:** Clear — fills the last DORA-urgent gap for microinformatica scope
**KPIs Defined:** Yes — "100% of planned endpoint changes tracked with formal approval and rollback plan"
**Justification Type:** Objective with regulatory reference

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | N/A | Regulatory compliance — not revenue-driven |
| Evidence sources | Yes | DORA Art. 9 direct quote |
| Revenue impact | N/A | Compliance-driven, not revenue |
| Customer names/tickets | N/A | Regulatory requirement |

**RED FLAGS:**
- None. Regulatory compliance justification is valid without revenue metrics.

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| ChangeRequest | Create, Read, Update, List (Delete not addressed) | 8 states, full transitions | **Not specified** |
| ChangeEvent | Create, Read (append-only) | N/A | N/A (immutable) |
| PostImplementationReview | Create, Read | N/A | **Not specified** |
| ChangeAsset | Create (link), Delete (unlink), Read | N/A | Implicit (unlink = delete row) |

### Gap: Delete Strategy for ChangeRequest

The requirement does not specify whether change requests can be deleted. Given DORA audit requirements, hard delete should be prohibited. Soft delete or archive-only is the appropriate strategy. **Recommendation:** Add "ChangeRequests cannot be deleted — soft delete or simply rely on terminal states (CLOSED, REJECTED, ROLLED_BACK) to archive."

This is a minor gap — the design phase will default to "no delete" following the incident_bc pattern.

### Gap: Update Scope for ChangeRequest

US-001 covers creation, but there is no explicit user story for updating a change request (editing title, description, risk assessment, etc.). The state machine implies DRAFT is editable, and the ChangeEvent enum includes "updated" — but no acceptance criteria define what can be edited and in which states.

**Recommendation:** Clarify: "ChangeRequest fields (title, description, justification, risk assessment, rollback plan, planned date) can be edited while in DRAFT or PENDING_APPROVAL. No edits allowed after SCHEDULED." This follows the incident_bc pattern where fields are locked after confirmation.

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Edit a change request | No user story for updating fields pre-approval | Medium | What fields are editable, and until which state? |
| Cancel a draft change | No way to abandon a change in DRAFT status | Low | Can DRAFT → CANCELLED? Or just leave it in DRAFT forever? |
| Reassign a change | US-003 mentions assigned_to but no dedicated assignment flow | Low | Is assignment part of creation, or a separate action? |

### Assessment

- **Edit** is implicitly needed but not critical to define now — design will handle it.
- **Cancel draft** is a nice-to-have. DRAFT changes can simply remain unused. Not a blocker.
- **Reassign** is covered by US-003 ("Can assign a change to a specific technician") — good enough.

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| ChangeRequest | Delete/archive strategy | Recommend: no delete (audit compliance) |
| ChangeRequest | Editable fields per state | Recommend: editable in DRAFT + PENDING_APPROVAL only |
| ChangeRequest | DRAFT → DRAFT (update without submit) | Implied but not explicit in transitions table |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Sidebar / navSections.ts | UI | New nav item | Identified in requirement |
| router.tsx | UI | New routes | Identified in requirement |
| locales (en.ts, es.ts) | UI | New i18n keys | Identified in requirement |
| app.py | Backend | Register router | Identified in requirement |
| Alembic | DB | New migration | Identified in requirement |
| Notification enums | Backend | New event types | Identified as optional/deferred |
| Compliance Dashboard (E39) | Future | Evidence linking | Identified as future scope |
| Asset detail page | UI | **Not mentioned** — should asset detail show linked changes? | Low priority, can defer |

### Assessment

Collateral impact is well-documented. The only unmentioned item is whether asset detail pages should show linked changes (reverse lookup). This is a nice-to-have and can be deferred.

## Slicing Assessment

**Size:** Medium-Large (new BC, 4 entities, 9 user stories, full frontend)
**Slicing needed:** Yes — should be sliced into 3-5 features
**Recommended slicing:**
1. F0: ChangeRequest CRUD + state machine + list/detail pages (foundation)
2. F1: Approval/rejection workflow
3. F2: Asset linking
4. F3: Post-Implementation Review + close flow
5. F4: Dashboard view

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| None | — | Self-contained new BC |

## Time Constraints Assessment

**Deadline:** ASAP (soft)
**Type:** Soft
**Reason:** DORA compliance gap — last urgent item for micro scope
**Realistic:** Yes — scope is intentionally minimal, patterns are well-established
**Calendar conflicts:** None identified
**Buffer included:** No — but soft deadline allows flexibility

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| DORA audit before completion | Can demonstrate "in progress" with design docs and partial implementation | Prioritize F0 (CRUD + state machine) — delivers audit trail even without full frontend |

## Testing Assessment

**Tests defined:** Yes (at DoD level)
**Critical scenarios identified:** Implicitly via acceptance criteria

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (DoD) | None |
| Integration | Yes | Yes (DoD) | None |
| E2E | No | No | Not needed for MVP |
| UAT | No | No | Not needed for MVP |

**Critical scenarios identified:** Yes — state transitions, rollback plan validation, PIR enforcement for emergency type
**Test data requirements:** Not explicitly defined, but straightforward (create changes in various states)

## Definition of Done Assessment

**DoD defined:** Yes
**Quality:** Good — covers all layers (domain, application, infrastructure, HTTP, frontend, tests, migration)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — per user story |
| Quality gates | Yes | Unit + integration tests |
| Sign-off process | No | Not needed for this project |
| Training needs | No | Not applicable |

## Red Flags

None.

## Open Questions for Stakeholder

1. **Delete strategy:** Can change requests be deleted, or are they permanent (audit trail)? **Recommendation:** No delete — rely on terminal states.
2. **Edit scope:** Which fields can be edited, and until which state? **Recommendation:** All fields editable in DRAFT and PENDING_APPROVAL; locked after SCHEDULED.
3. **Cancel draft:** Should there be a way to explicitly cancel a DRAFT change, or is it fine to leave drafts abandoned? **Recommendation:** Not needed for MVP — drafts can sit unused.

None of these are blockers — all have clear recommended defaults that the design phase can adopt.

## Checklist Summary

### Business Alignment: 4/4 passed
- [x] Objective identified (DORA compliance)
- [x] KPI defined (100% tracking)
- [x] Evidence provided (Art. 9 quote)
- [x] Contribution clear (fills last DORA gap)

### Content Completeness: 8/9 passed
- [x] Problem statement clear
- [x] Solution described
- [x] User stories with acceptance criteria
- [x] Entity fields detailed
- [x] State machine defined
- [x] Use cases documented
- [x] Scope exclusions listed
- [ ] Edit/update flow not explicitly covered (minor)
- [x] "What It Is NOT" clearly defined

### Use Case Coverage: 4/5 passed
- [x] Create flow
- [x] Approval/rejection flow
- [x] Implementation + rollback flow
- [x] List/filter/detail
- [ ] Edit flow not explicitly documented (minor)

### Entity States: 5/5 passed
- [x] All states listed
- [x] All transitions documented
- [x] Triggers defined
- [x] Conditions specified
- [x] Terminal states identified

### Collateral Impact: 7/7 passed
- [x] UI components identified
- [x] Backend registration identified
- [x] Database migration identified
- [x] Notification impact identified
- [x] Compliance Dashboard impact identified
- [x] No breaking changes
- [x] No shared data dependencies

### Slicing: 2/2 passed
- [x] Size assessed (medium-large)
- [x] Scope exclusions well-defined

### Time Constraints: 3/3 passed
- [x] Deadline type identified (soft)
- [x] Reason documented (DORA)
- [x] Realistic assessment (yes, minimal scope)

### Testing: 2/2 passed
- [x] Test types identified
- [x] Critical scenarios implied by acceptance criteria

### Definition of Done: 2/2 passed
- [x] Acceptance criteria testable
- [x] Quality gates defined

**Overall: 37/39 checks passed (95%)**

## Recommendations

1. **Adopt defaults for minor gaps:** No delete (audit trail), editable in DRAFT/PENDING_APPROVAL only, no cancel-draft flow. These are straightforward and the design phase can handle them.
2. **Proceed to slicing.** The requirement is solid and complete enough for implementation. The two minor gaps (edit scope, delete strategy) have clear recommended solutions and don't require stakeholder input.
