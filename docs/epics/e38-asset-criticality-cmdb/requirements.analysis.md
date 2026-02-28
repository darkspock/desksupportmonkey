# Requirement Validation Report

**Document:** E38 — Asset Criticality & CMDB
**Date:** 2026-02-26
**Type:** Epic (Full Validation)
**Status:** Valid — Minor gaps to address

## Summary

Excellent requirement document. The scope is well-defined, entities are clearly specified with fields and constraints, use cases cover the main flows with error scenarios, and the regulatory alignment (NIS2/DORA/ISO 27001) is strong. The existing codebase foundation is thoroughly documented. Two actionable gaps were identified: (1) the SLA escalation feature assumes requests are linked to assets, but the current `ServiceRequest` entity has no `asset_id` field — this cross-BC dependency needs clarification; (2) the CIRelationship entity is missing an explicit delete strategy and update use case.

## Business Alignment Assessment

**Primary Objective:** Compliance (NIS2/DORA regulatory requirements)
**Contribution:** Clear — directly satisfies NIS2 Art. 21(2)(i) and 21(2)(c)
**KPIs Defined:** Yes — 4 measurable targets
**Justification Type:** Objective with regulatory evidence

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Yes | 100%, 0 orphans, < 5 min |
| Evidence sources | Yes | NIS2 Art. 21, DORA Art. 5-6, ISO 27001 A.5.9 |
| Revenue impact | N/A | Compliance-driven, not revenue |
| Customer names/tickets | N/A | Regulatory mandate, not customer request |

**RED FLAGS:**
- None detected. Regulatory compliance is a valid objective that doesn't require traditional revenue/customer evidence.

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| Asset (extended) | C/R/U — existing. New: Set criticality, Update BIA | N/A (stateless fields, existing status machine unchanged) | N/A — existing soft-delete |
| CIRelationship | C/R/D — Create, List, Delete | Stateless (no lifecycle) | **Gap: not specified** (see below) |
| AssetEvent (extended) | C/R — existing, new event types | N/A — append-only | N/A — immutable |

### CIRelationship Delete Strategy

The requirement specifies "create, list, delete" for CIRelationship but does not clarify:
- **Hard or soft delete?** Recommend **hard delete** — relationships are structural metadata, not business records. Once removed, the relationship simply no longer exists. Event sourcing on the Asset captures the `ci_relationship_deleted` event for audit trail.
- **Cascade on asset decommission?** The doc says "existing relationships are preserved for history" when an asset is decommissioned. This is correct — decommissioned assets keep their relationships for historical reference but cannot be *new* targets.

**Recommendation:** Explicit hard delete for CIRelationship is fine. The audit trail lives in AssetEvent, not in the relationship record itself.

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| UC: Update CIRelationship description | Only create and delete covered — what if user wants to edit the description? | Low | Allow description edits or require delete + recreate? |
| UC: Bulk set criticality | Admin may want to classify multiple assets at once (e.g., "mark all servers as High") | Low | Defer to future? Current UI supports single-asset only |
| UC: BIA review reminder (Celery task) | Mentioned in Section 2 ("periodic review reminder") but no dedicated use case or task detail | Medium | Is a Celery periodic task needed for BIA review reminders, or is the CMDB dashboard "overdue reviews" table sufficient? |
| UC: Export CMDB data | Reporting pattern — no PDF/CSV export mentioned for CMDB dashboard | Low | Defer to future? Dashboard may be sufficient initially |

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| CIRelationship | Delete strategy (hard vs soft) | Recommend hard delete — audit trail in AssetEvent. Agree? |
| CIRelationship | Update operation | Description editable after creation? |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Asset entity/model | Extension | 7 new nullable columns | Migration with null defaults — backward compatible |
| Asset detail page | Extension | New criticality badge, BIA section, dependencies tab | Extend existing page |
| Asset list page | Extension | New criticality filter + column | Extend existing page |
| SLA query handler | **Cross-BC integration** | **Needs asset lookup from request** | **See critical note below** |
| Asset CSV import | Minor | Optionally accept criticality column | Low priority |
| MCP server asset tools | Minor | Expose criticality in responses | Update tool responses |
| Asset schemas/responses | Extension | New fields in API responses | Add to existing response schema |
| New: ci_relationships table | New table | FK to assets table | Migration with indexes |
| Request BC | **Potential gap** | No asset_id on ServiceRequest | See critical note |

### Critical Note: SLA Escalation — Cross-BC Asset Link

The requirement states: *"When a service request is linked to a critical asset, the SLA priority is escalated."*

However, **`ServiceRequest` has no `asset_id` or linked asset field**. The current entity has: `type`, `title`, `description`, `status`, `priority`, `assigned_to`, `subtype`, `data`, `custom_fields_data`, `workflow_template_id`.

**Options:**
1. **Add `asset_id` to ServiceRequest** — requires modifying request_bc entity, model, migration, schemas. Larger scope.
2. **Use the `data` JSON field** — requests already have a `data: dict` field. Asset references could be stored there (e.g., `data.asset_id`). Less formal but no migration needed.
3. **Defer SLA escalation** — implement criticality + CMDB now, add SLA escalation as a follow-up when request-asset linking is formalized.
4. **Query from incident side** — Security incidents (incident_bc) already link to affected assets. SLA escalation could apply only to incidents, not general requests.

**Recommendation:** Option 3 (defer SLA escalation to a follow-up) keeps this epic focused. SLA escalation requires cross-BC changes (request_bc + sla_bc) that may warrant their own feature slice. Alternatively, Option 2 is low-friction if the `data` field convention is acceptable.

## Slicing Assessment

**Size:** Large — 6 capability areas (criticality, BIA, CI relationships, impact propagation, SLA escalation, dashboard)
**Slicing needed:** Yes — will need feature-level slicing
**Suggested slices:**
1. **F0: Criticality + BIA fields** — extend Asset entity, migration, commands, detail page updates, list page filter
2. **F1: CI Relationships** — new entity, CRUD endpoints, dependencies tab on asset detail
3. **F2: Impact Propagation + CMDB Dashboard** — graph queries, dashboard page, sidebar entry
4. **F3: SLA Escalation** — cross-BC integration (depends on request-asset linking decision)

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| Request-asset linking | Decision on approach (field vs data JSON vs defer) | SLA escalation depends on it |
| BIA review Celery task | Include in scope or defer? | Mentioned but not detailed as a use case |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** N/A
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline — no risk.

## Testing Assessment

**Tests defined:** Yes — at high level in Definition of Done
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Adequately scoped |
| Integration | Yes | Yes | Adequately scoped |
| E2E | No | No | Not required for backend/API changes |
| UAT | No | No | Not formally required |

**Critical scenarios identified:** Yes — constraint validation (self-reference, duplicates, cross-company), decommissioned asset handling, recursive depth limiting
**Test data requirements:** Not explicitly defined — but standard mock patterns apply

## Definition of Done Assessment

**DoD defined:** Yes — 18 concrete checklist items
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | 18 testable items |
| Quality gates | Implicit | Tests + TypeScript check |
| Sign-off process | No | Not defined (standard for this project) |
| Training needs | No | Not required |

## Red Flags

- [ ] **SLA escalation assumes request-asset link that doesn't exist** — ServiceRequest has no `asset_id` field. Must decide approach before implementing that slice.
- [ ] **BIA review reminder task mentioned but not fully specified** — Is this a Celery task or just a dashboard indicator? Needs clarification.

## Open Questions for Stakeholder

1. **SLA escalation: How are requests linked to assets?** The current ServiceRequest entity has no asset reference. Options: add `asset_id` field, use `data` JSON, or defer SLA escalation to a future epic.
2. **CIRelationship updates:** Should description be editable after creation, or is delete + recreate sufficient?
3. **BIA review reminders:** Should this be a Celery periodic task sending notifications, or is the "overdue reviews" table on the CMDB dashboard sufficient?

## Checklist Summary

### Business Alignment: 4/4 passed
- [x] Objective identified (Compliance/NIS2)
- [x] Contribution clearly explained
- [x] KPIs defined with measurable targets
- [x] Evidence provided (regulatory articles)

### Content Completeness: 7/8 passed
- [x] Problem statement clear
- [x] Solution described
- [x] User stories defined (8 stories)
- [x] Entities with fields documented
- [x] Enums defined
- [x] Constraints specified
- [x] Event types listed
- [ ] BIA review reminder task detail incomplete

### Use Case Coverage: 5/6 passed
- [x] Set criticality (UC-001)
- [x] Record BIA (UC-002)
- [x] Create CI relationship (UC-003)
- [x] View dependency graph (UC-004)
- [x] View CMDB dashboard (UC-005)
- [ ] SLA escalation (UC-006) — depends on unresolved cross-BC linking

### Entity States: 3/3 passed
- [x] Asset states unchanged (existing machine)
- [x] CIRelationship is stateless (appropriate)
- [x] AssetEvent is append-only (appropriate)

### Collateral Impact: 7/9 passed
- [x] Asset entity extension documented
- [x] Frontend pages impact documented
- [x] Migration approach (nullable columns)
- [x] Risk BC — no impact
- [x] Incident BC — no impact
- [x] MCP server — documented
- [x] CSV import — documented
- [ ] SLA BC cross-BC integration not fully resolved
- [ ] Request BC — asset linking not addressed

### Slicing: 1/1 passed
- [x] Size acknowledged as Large, slicing will be needed

### Time Constraints: 1/1 passed
- [x] No deadline — no risk

### Testing: 2/2 passed
- [x] Unit tests required
- [x] Integration tests required

### Definition of Done: 1/1 passed
- [x] 18 testable acceptance criteria defined

## Recommendations

1. **Decide on request-asset linking approach** before slicing. This affects whether SLA escalation is included in E38 or deferred. Recommendation: defer SLA escalation (UC-006) to keep the epic focused, and add request-asset linking as a prerequisite in a future slice.
2. **Specify CIRelationship delete as hard delete.** The audit trail lives in AssetEvent — no need to soft-delete relationships.
3. **Clarify BIA review reminders.** Either: (a) add a Celery task similar to E25's stale assessment check, or (b) rely on the CMDB dashboard's "overdue reviews" table as a passive indicator. Option (b) is simpler and avoids notification fatigue.
4. **Allow CIRelationship description updates.** Simple PATCH endpoint, low effort, avoids awkward delete+recreate workflow.
