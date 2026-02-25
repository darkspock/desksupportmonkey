# Requirement Validation Report

**Document:** E31: Workflow Templates with Checklists
**Date:** 2026-02-25
**Status:** Valid (all questions resolved)

## Summary

The requirement is well-structured with clear domain model, database design, API endpoints, and implementation phases. The "keep it simple" philosophy is sound -- checklist items as booleans avoids complexity. There are a few gaps that should be addressed before implementation.

## Business Alignment Assessment

**Primary Objective:** Churn reduction / Operational efficiency
**Contribution:** Clear -- teams lack structured multi-step workflow tracking
**KPIs Defined:** Partially -- directional but not measurable
**Justification Type:** Objective (operational need)

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | No data on how many requests need checklists |
| Evidence sources | No | No ticket IDs or customer references |
| Revenue impact | No | No quantified churn/efficiency impact |
| Customer names/tickets | No | Anecdotal "offboarding example" only |

### Experimentation Assessment

**Is this an experiment?** Could be treated as one.

| Criteria | Defined | Details |
|----------|---------|---------|
| Hypothesis | Partially | Structured checklists will improve completion rates |
| Test method | No | Not defined |
| Success metrics | No | Not defined beyond "reduce missed steps" |
| Investment limit | No | No max effort defined |
| Decision criteria | No | Not defined |

**RED FLAGS:**
- [x] Missing specific numbers (how many requests would use checklists?)
- [x] No measurable KPIs (what's the target reduction in missed steps?)
- [ ] ~~Subjective justification~~ (operational need is clear)
- [ ] ~~Experiment without investment limit~~ (not formally an experiment)

**Recommendation:** This is a standard operational improvement. The need is clear even without hard numbers. Proceed, but define success criteria post-launch (e.g., "X% of onboarding requests use checklists within 30 days").

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| WorkflowTemplate | C, R, U, D, L | is_active (bool) | Hard delete |
| ChecklistItemDefinition | Managed inline with template | N/A (embedded) | CASCADE with template |
| RequestChecklistItem | C (generate + ad-hoc), R, U (toggle/assign), D (ad-hoc) | is_completed (bool) | Hard delete (ad-hoc only) |

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Duplicate template | Admin wants to copy an existing template as starting point | Low | Needed for Phase 1? |
| Activate/Deactivate template | Document says `is_active` exists but no explicit toggle endpoint | Medium | Add PATCH toggle endpoint? |
| Bulk toggle checklist items | Technician wants to check all items at once | Low | Phase 2? |
| Checklist item edit | Technician wants to edit title/description of an ad-hoc item | Low | Currently only add/remove, no edit |
| Template used count | Admin wants to see how many requests use a template | Low | Useful for admin UI |
| What happens to existing checklists when template is updated? | Template update should NOT affect already-stamped checklists | High | Confirm: stamped items are independent copies? |
| What happens to checklist when request is deleted? | Cascade delete? | Medium | Confirm cascade behavior |

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| WorkflowTemplate | No activate/deactivate endpoint | Should there be a PATCH endpoint to toggle `is_active`? |
| RequestChecklistItem | No uncomplete validation | Can a completed item be un-toggled? Any restrictions? |
| WorkflowTemplate | Unique constraint handling | What happens if admin tries to create a second template for same type+subtype? Error message? |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `requests/routers.py` | Modification | Add checklist generation after create, resolution guard before status change | Yes - modify create_request and change_request_status |
| `requests/schemas.py` | Modification | Add checklist + checklist_progress to RequestResponse | Yes - add new fields |
| `RequestDetailPage.tsx` | Modification | Add checklist card | Yes |
| `NewRequestPage.tsx` | None | No changes needed (checklist is auto-generated) | No |
| `app.py` | Modification | Register new routers | Yes |
| Request list/search | None | Checklist doesn't affect list queries | No |
| Reports | None | No report changes in Phase 1 | No |
| Notifications | None | Phase 3 (out of scope) | No |
| SLA | Potential | Should checklist completion affect SLA timers? | Confirm: No SLA impact in Phase 1 |
| Audit trail | Potential | Should checklist toggles be audited? | Confirm: No audit in Phase 1 |

## Slicing Assessment

**Size:** Medium
**Slicing needed:** Already sliced into 3 phases
**Phase independence:** Good -- Phase 1 backend, Phase 2 frontend, Phase 3 polish

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Icon library | Yes | Need to decide before frontend implementation (lucide-react recommended) |
| Template description + icon fields | Yes | Added to domain model to support the UI shown in screenshot |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** Yes -- scope is well-defined
**Calendar conflicts:** None identified
**Buffer included:** Phase 3 is optional, provides natural buffer

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| No deadline specified | No risk | Ship when ready |

## Testing Assessment

**Tests defined:** Partially
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | "Unit tests + integration tests" mentioned |
| Integration | Yes | Yes | Endpoints listed |
| E2E | No | No | Manual verification defined |
| UAT | No | No | Not defined |

**Critical scenarios identified:** Partially
- Happy path: template create -> request create -> checklist appears -> toggle -> resolve
- Resolution guard: try to resolve with incomplete required items
- Missing: error scenarios, edge cases

**Test data requirements:** Seed data with example templates mentioned

## Definition of Done Assessment

**DoD defined:** Partially

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Partially | Verification section covers basics |
| Quality gates | Yes | make test, make test-integration, tsc --noEmit |
| Sign-off process | No | Not defined |
| Training needs | No | Not defined |

## Red Flags

- [x] **Resolution guard needs the `require_all_complete` flag from the template, but at runtime checklist items don't store which template they came from.** Need to store `template_id` on `request_checklist_items` OR check the template at resolution time via request_type+company_id lookup.
- [ ] No explicit handling of "what if template is deleted but requests still have checklists from it" -- should be fine since items are copies, but worth confirming.
- [x] **Unique constraint on `(company_id, request_type, request_subtype)` means NULL subtype needs special handling** -- PostgreSQL treats NULL != NULL in unique constraints. Need `COALESCE` or a partial index.

## Resolved Questions (Stakeholder Decisions 2026-02-25)

| # | Question | Decision |
|---|----------|----------|
| 1 | Resolution guard: how to know `require_all_complete` at runtime? | **Store `require_all_complete` flag on `request_checklist_items`** at generation time. Self-contained, independent of template changes. |
| 2 | NULL subtype unique constraint? | **Application-level check** in the command handler before saving. No special DB constraint. |
| 3 | Can completed items be un-toggled? | **Yes, freely.** Any technician+ can check/uncheck any item. GitHub checkbox metaphor. |
| 4 | Should checklist actions be audited? | **Yes, in Phase 1.** Record toggle, assign, add, remove actions. |
| 5 | Icon library? | **lucide-react.** Install as dependency. Store icon name as string on template. |
| 6 | Activate/deactivate template? | Handle via update endpoint (set `is_active` field). No separate toggle endpoint needed. |

## Checklist Summary

### Business Alignment: 2/4 passed
- [x] Objective identified
- [x] Contribution clear
- [ ] KPIs measurable
- [ ] Evidence provided

### Content Completeness: 7/8 passed
- [x] Domain model defined
- [x] Database schema defined
- [x] API endpoints defined
- [x] Frontend described
- [x] Integration points documented
- [x] Phases defined
- [x] Out of scope defined
- [ ] Error scenarios incomplete

### Use Case Coverage: 5/7 passed
- [x] CRUD for templates
- [x] Checklist generation
- [x] Toggle/assign items
- [x] Ad-hoc items
- [x] Resolution guard
- [ ] Activate/deactivate template
- [ ] Template duplication

### Entity States: 2/3 passed
- [x] WorkflowTemplate states (is_active)
- [x] RequestChecklistItem states (is_completed)
- [ ] State transition rules incomplete (un-toggle?)

### Collateral Impact: 3/3 passed
- [x] Request router modifications identified
- [x] Request schema modifications identified
- [x] Frontend modifications identified

### Slicing: 3/3 passed
- [x] Phases clearly defined
- [x] Phase independence maintained
- [x] Out of scope listed

### Time Constraints: 1/1 passed
- [x] No deadline pressure

### Testing: 2/3 passed
- [x] Test types identified
- [x] Verification criteria defined
- [ ] Edge case scenarios missing

### Definition of Done: 2/4 passed
- [x] Quality gates defined
- [x] Basic acceptance criteria
- [ ] Sign-off process
- [ ] Training needs

## Recommendations

1. **CRITICAL: Add `template_id` and `require_all_complete` to `request_checklist_items` table** -- needed for the resolution guard to know whether to enforce completion. Store it at generation time so it's independent of template changes.
2. **CRITICAL: Handle NULL subtype in unique constraint** -- use `COALESCE(request_subtype, '')` in the unique index or a partial unique index.
3. **Add activate/deactivate endpoint** for templates (or handle via update).
4. **Allow un-toggle** (check/uncheck) with no restrictions -- keep it simple, matching the GitHub checkbox metaphor.
5. **Confirm icon library** -- `lucide-react` recommended, no icon library currently in project.
6. **Add `description` and `icon` fields** to WorkflowTemplate entity (already added in the saved requirement based on the UI screenshot).
