# Requirement Validation Report

**Document:** E50 - Onboarding Wizard
**Path:** `docs/epics/e50-onboarding-wizard/requirements.md`
**Type:** Epic (FULL validation)
**Date:** 2026-02-28
**Status:** Valid (minor gaps to address)

## Summary

Strong requirement document. The business case is clear, user stories are well-defined with testable acceptance criteria, and the solution smartly leverages existing infrastructure (nav visibility, compliance controls). Two gaps need attention before implementation: (1) the compliance controls API doesn't have a "enable framework" endpoint -- it works at individual control level, and (2) the module-to-nav mapping has orphaned items (SLA, Billing, Reports) not assigned to any module.

---

## Business Alignment Assessment

**Primary Objective:** Churn reduction / Activation rate
**Contribution:** Clear -- reduces cognitive overload on first login, increases module adoption
**KPIs Defined:** Yes
**Justification Type:** Objective with data (comparative -- estimated baselines)

### Justification Quality

| Criteria | Status | Notes |
|----------|--------|-------|
| Specific numbers | Yes | 30+ menu items, 9 modules, <5 min target, 40%->80% activation |
| Evidence sources | Partial | Competitor reference (InvGate). No specific customer complaints or churn data cited. |
| Revenue impact | Indirect | Churn reduction -> retention -> revenue. No dollar estimate. |
| Customer names/tickets | No | No specific customer feedback cited. |

### Experimentation Assessment
**Is this an experiment?** No

**RED FLAGS:**
- [ ] ~~Subjective justification detected~~ -- KPIs are defined
- [x] Missing specific customer evidence -- acceptable since this is a UX best-practice pattern; "estimated 40%" baseline is acknowledged as estimated, not measured
- [ ] ~~No evidence provided~~ -- competitor evidence provided

**Verdict:** Acceptable. The 40%->80% activation KPI is based on estimates, not measured data. Recommend adding analytics post-launch to validate the hypothesis. Not blocking.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| Company (modified) | Update only (add sector, onboarding flag) | N/A (existing entity) | N/A |
| OnboardingStatus (concept) | Not a separate entity -- flag on Company | pending -> completed | N/A |

**Assessment:** Correct decision to avoid creating a new entity. Two new fields on Company are sufficient. No CRUD gaps for the scope.

---

## Step 1: Business Alignment -- PASS

See assessment above. KPIs defined, objective clear, competitor evidence provided.

## Step 2: Entity Identification -- PASS

Minimal entity changes. Correctly reuses existing nav config and compliance control entities.

## Step 3: CRUD Check -- PASS

| Operation | Covered? | Notes |
|-----------|----------|-------|
| Create sector | Yes | Set during onboarding, US-002 |
| Read sector | Yes | Company Settings page, UC-004 |
| Update sector | Yes | Company Settings page, UC-004 |
| Delete sector | N/A | Nullable field, can be cleared |
| Create onboarding flag | Yes | Set on completion/skip |
| Read onboarding flag | Yes | Checked on every admin login |
| Update onboarding flag | N/A | One-way transition, write-once |

## Step 4: Status & State Analysis -- PASS

| Entity | States | Transitions | Side Effects |
|--------|--------|-------------|--------------|
| Onboarding flag | `null` (pending) -> timestamp (completed) | One-way on wizard completion or skip | None -- flag only |
| Sector field | `null` -> sector value | Set during onboarding or settings | Suggestion toast when changed later (UC-004) |

Simple state model. Appropriate for a configuration flag.

## Step 5: Use Case Pattern Detection -- PASS (minor gap)

| Pattern | Covered? | Notes |
|---------|----------|-------|
| CRUD | Yes | Sector CRUD covered |
| Lifecycle | Yes | Onboarding pending->completed |
| State Machine | Yes | Simple one-way transition |
| Bulk Operations | N/A | Not applicable |
| Reporting | No | No analytics on onboarding completion rates (explicitly excluded in scope) |

**Missing use case identified:**

| Use Case | Reason | Priority | Question |
|----------|--------|----------|----------|
| UC-006: Re-run onboarding | What if admin made wrong choices? Can they re-trigger the wizard, or must they go to individual settings? | Low | Is "Settings > Nav Visibility" sufficient, or should there be a "Re-run setup wizard" button? |
| UC-007: Company created by Super Admin with sector pre-set | Super Admin creates company and sets sector upfront. Does onboarding still trigger? | Low | Should the wizard skip Step 1 if sector is already set? |

## Step 6: Inverse Operation Check -- PASS

| Action | Inverse | Covered? |
|--------|---------|----------|
| Enable module | Disable module | Yes (toggle cards, Step 3) |
| Enable framework | Disable framework | Yes (uncheck in Step 2) |
| Set sector | Change sector | Yes (UC-004, Company Settings) |
| Complete onboarding | Re-trigger onboarding | Partially -- no explicit re-trigger, but individual settings accessible |
| Skip onboarding | Undo skip | Not covered -- but all settings remain accessible via individual pages |

## Step 7: User Journey Check -- PASS

| Aspect | Covered? | Notes |
|--------|----------|-------|
| Preconditions | Yes | First admin login, onboarding not completed |
| Postconditions | Yes | Sector set, frameworks enabled, modules configured |
| Error recovery | Yes | UC-005 covers API failure gracefully |
| Undo/cancel | Partial | Skip is covered; changing settings later is covered; no "undo entire onboarding" |
| Back navigation in wizard | Not specified | Can admin go back from Step 3 to Step 1? Assumed yes but not stated. |

## Step 8: Collateral Impact Analysis -- PASS (one gap found)

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Company entity | Schema | 2 new fields | Migration |
| Company Settings page | UI | New sector dropdown | Minor frontend change |
| Nav visibility API | Dependency | Called during onboarding | No changes |
| Compliance controls API | Dependency | Called during onboarding | **GAP: See below** |
| Login flow | Routing | Onboarding redirect | Frontend routing change |
| Sidebar | None | Already respects hidden_nav_items | No changes |
| User/auth context | Data | Needs `onboarding_completed_at` in user response | Backend: include in company data returned on login |

**CRITICAL GAP: Compliance Controls API**

The requirement states: "Selected frameworks are auto-enabled in the existing compliance controls system." However, code review reveals:

- There is NO `POST /api/v1/audit/frameworks/{name}/enable` endpoint
- Controls are created individually via `POST /api/v1/audit/controls`
- The frontend `ComplianceControlsPage.tsx` seeds predefined controls per framework when admin clicks "Activate" on a framework

**Options:**
1. The onboarding wizard frontend replicates the same seeding logic from `ComplianceControlsPage.tsx` (quick but duplicates logic)
2. Create a new backend endpoint `POST /api/v1/audit/frameworks/{name}/activate` that bulk-creates predefined controls (clean but new backend work)
3. Extract the seeding logic into a shared frontend util called by both pages (moderate)

**Recommendation:** Option 2 -- a backend command is cleaner and avoids frontend duplication. This is a small addition (one command, one endpoint).

## Step 9: Requirement Slicing Analysis -- PASS

**Size:** Medium
**Slicing needed:** Optional -- could be delivered as a single feature, but slicing into 2 features is viable:
- F1: Backend (migration + sector/onboarding fields + framework activation endpoint)
- F2: Frontend (wizard UI + routing)

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Analytics tracking | No | Explicitly excluded, can be added later |
| Guided tours | No | Separate epic |
| API endpoint protection | Clarify | Hiding nav != disabling endpoints. Is that acceptable? Stated as excluded but worth confirming. |

## Step 10: Time Constraints Assessment -- PASS

**Deadline:** None specified
**Type:** Soft priority
**Reason:** UX improvement, no external pressure
**Realistic:** Yes -- medium scope, leverages existing infrastructure
**Calendar conflicts:** None
**Buffer included:** N/A (no deadline)

No deadline risks.

## Step 11: Testing Assessment -- PASS

**Tests defined:** Yes (in Definition of Done)

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Sector save command, onboarding completion command |
| Integration | Yes | Yes | New/modified endpoints |
| Frontend | Yes | Partially | "Chrome, Firefox, Safari" mentioned but no specific test framework/approach |
| E2E | No | No | Not mentioned -- acceptable for wizard flow |
| UAT | No | No | Not mentioned |

**Critical scenarios identified:** Yes -- happy path, skip, second admin, sector change, API failure
**Test data requirements:** Not explicitly defined -- needs seed data with a company that hasn't onboarded

## Step 12: Definition of Done Assessment -- PASS

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | 12 testable criteria |
| Quality gates | Yes | make test + make test-integration |
| Sign-off process | No | Not specified (acceptable -- no formal UAT defined for DSM) |
| Training needs | No | N/A -- self-explanatory wizard |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| Company.sector | What happens if company is suspended/deactivated with sector set? | Probably nothing -- sector is informational. Confirm. |

---

## Red Flags

- [x] **Compliance API gap** -- No framework-level activation endpoint exists. Wizard can't "enable DORA" in one call. Needs new backend work or frontend workaround. **Impact: Medium. Must be resolved in design phase.**
- [x] **Orphaned nav items** -- SLA (`/sla/policies`, `/sla/dashboard`), Billing (`/billing`), Reports (`/reports`), and report-incident form are not assigned to any of the 9 modules. If all optional modules are disabled, these items still appear. **Impact: Low. Should be clarified before implementation.**
- [ ] ~~Missing back-navigation in wizard~~ -- Minor UX detail, can be resolved in design
- [ ] ~~No re-trigger mechanism~~ -- Low priority, individual settings pages are sufficient

---

## Open Questions for Stakeholder

1. **Compliance activation**: Should we create a new backend endpoint to activate all controls for a framework at once, or should the wizard frontend replicate the seeding logic from `ComplianceControlsPage.tsx`? (Recommend: new endpoint)
2. **Orphaned nav items**: Which module should SLA belong to? (Recommend: Service Desk). Which module should Billing belong to? (Recommend: always visible for admin, not tied to any module). Which module should Reports belong to? (Recommend: always visible for admin).
3. **Re-run wizard**: Should there be a "Re-run setup wizard" button in Company Settings, or is navigating to individual settings pages sufficient?
4. **Super Admin pre-setting sector**: If a Super Admin sets the sector when creating a company, should the wizard skip Step 1?

---

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective identified (Churn/Activation)
- [x] KPIs defined with measurable targets
- [x] Contribution clearly explained
- [ ] Specific customer evidence (estimated baselines, no real data -- acceptable)

### Content Completeness: 8/8 passed
- [x] Problem statement
- [x] Proposed solution
- [x] User stories with acceptance criteria
- [x] Scope (included/excluded)
- [x] Business rules
- [x] User impact per role
- [x] Dependencies identified
- [x] Notes for Planner

### Use Case Coverage: 5/6 passed
- [x] Happy path (UC-001)
- [x] Skip flow (UC-002)
- [x] Multi-admin scenario (UC-003)
- [x] Post-onboarding changes (UC-004)
- [x] Error handling (UC-005)
- [ ] Re-trigger wizard (not covered -- low priority)

### Entity States: 2/2 passed
- [x] Onboarding flag states defined
- [x] Sector field lifecycle defined

### Collateral Impact: 5/6 passed
- [x] Company entity changes
- [x] Company Settings page
- [x] Nav visibility API (no changes needed)
- [ ] Compliance controls API (**gap: no framework-level activation endpoint**)
- [x] Login flow routing
- [x] Sidebar (no changes needed)

### Slicing: 2/2 passed
- [x] Size assessed (Medium)
- [x] Slicing optional but viable

### Time Constraints: 3/3 passed
- [x] Deadline type identified (Soft)
- [x] No calendar conflicts
- [x] Scope realistic

### Testing: 3/4 passed
- [x] Test types identified
- [x] Critical scenarios covered
- [ ] Test data requirements not explicit
- [x] Quality gates defined (make test)

### Definition of Done: 3/3 passed
- [x] Acceptance criteria testable
- [x] Quality gates defined
- [x] DoD checklist present

---

## Recommendations

1. **Resolve compliance API gap** -- Add a backend command + endpoint to activate all predefined controls for a framework. Small scope (~1 new command + 1 endpoint). This is a blocker for design phase.
2. **Clarify orphaned nav items** -- Assign SLA to Service Desk module, Billing to "always visible" for admin, Reports to "always visible". Update the module-to-nav mapping table.
3. **Add back-navigation** -- Specify that the wizard supports going back to previous steps (assumed but not stated).
4. **Consider "re-run wizard" button** -- Low priority. A link in Company Settings > "Re-run onboarding wizard" would be nice-to-have but not blocking.
5. **Post-launch**: Add analytics to validate the 40%->80% activation KPI hypothesis.

**Overall verdict: Valid. Ready for design phase after resolving questions 1-2 above. Questions 3-4 can be resolved during design.**
