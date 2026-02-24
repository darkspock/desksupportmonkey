# Requirement Validation Report

**Document:** `docs/epics/e30-custom-fields/requirements.md`
**Date:** 2026-02-24
**Type:** Epic (Full Validation)
**Status:** Valid (all questions resolved, requirements updated)

---

## Summary

The E30 Custom Fields epic is a well-structured and thoroughly documented requirement. It covers the core EAV pattern, clear entity definitions, API design, frontend integration, and architecture decisions. The document demonstrates strong technical thinking and addresses most edge cases proactively. However, there are several gaps and risks identified across the 12-step validation that should be addressed before implementation begins. The most significant issues are: (1) missing orphan cleanup strategy when target entities are deleted, (2) no audit trail integration defined for custom field changes, (3) insufficient detail on search/filter implementation specifics, and (4) missing inverse operations and error recovery flows.

**Overall Quality: 7/10 -- Good foundation, but storage architecture must change (EAV rejected by stakeholder).**

---

## Step 1: Business Alignment Assessment

**Primary Objective:** Revenue / Churn (Enterprise feature differentiation)
**Contribution:** Clear -- enables Enterprise plan upsell and reduces churn from data-inflexible workflows
**KPIs Defined:** Partially
**Justification Type:** Objective with data (competitive and customer evidence)

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Partial | "Top-3 feature request" is vague -- how many prospects? No ticket count or revenue impact estimate |
| Evidence sources | Partial | Mentions "Enterprise prospects" but no customer names, ticket IDs, or CS data references |
| Revenue impact | No | No estimate of potential conversions or revenue from custom fields as Enterprise differentiator |
| Customer names/tickets | No | No specific customer names, deal IDs, or support ticket references |

### KPI Assessment

The KPIs defined are:
1. "30% higher asset data completeness" -- **Measurable but unmeasured baseline.** How is "data completeness" measured today? What fields count? This needs a baseline definition to be actionable.
2. "Zero code deployments required" -- **Valid operational metric**, easy to verify.
3. "Custom field values searchable and filterable" -- **Binary capability, not a KPI.** This is an acceptance criterion, not a measurable target.
4. "Custom fields appear in PDF/CSV exports" -- **Binary capability, not a KPI.** Same issue.

### Experimentation Assessment

**Is this an experiment?** No

### RED FLAGS

- [x] Missing revenue/cost impact (and not an experiment)
- [x] No evidence provided -- no customer names, ticket IDs, or deal pipeline references
- [ ] Subjective justification detected (and not an experiment) -- Evidence is reasonable but lacks specifics
- [ ] Experiment without success metrics
- [ ] Experiment without investment limit

**Recommendation:** Add at least 2-3 specific Enterprise prospect names/deals that cited custom fields as a blocker. Estimate potential revenue impact (e.g., "3 Enterprise prospects in pipeline worth $X/month cited custom fields as requirement"). Replace capability-based KPIs with measurable ones (e.g., "80% of Enterprise companies configure at least 1 custom field within 30 days").

---

## Step 2: Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| CustomFieldDefinition | Create, Read, Update, Delete, List, Reorder | Active / Inactive (via `is_active`) | Hard delete (US-004) + Soft deactivate (US-003) |
| CustomFieldValue | Create, Read, Update (upsert), Bulk upsert | N/A (stateless value) | Cascaded on definition delete; **orphan cleanup on entity delete undefined** |

### Entity Analysis

**CustomFieldDefinition:**
- Well-defined with all fields, types, indexes, and validation rules.
- Factory method pattern should be applied (per critical-rules.md).
- `field_key` auto-generation logic is documented but implementation specifics need care (slug collision on label change, unicode handling).

**CustomFieldValue:**
- Straightforward value storage.
- The unique constraint `(field_definition_id, entity_id)` correctly prevents duplicate entries.
- **GAP:** No explicit mention of what happens to CustomFieldValues when the target entity (asset, request, incident) is deleted. The requirements mention "No FK to target entities" and "Orphan cleanup handled by a periodic task or on entity deletion" in architecture decisions but this is not detailed as a use case or requirement.

---

## Step 3: CRUD Check

### CustomFieldDefinition

| Operation | Defined | Endpoint | Notes |
|-----------|---------|----------|-------|
| Create | Yes | POST `/definitions` | With validation (max 20, unique key) |
| Read | Yes | GET `/definitions` | Filter by entity_type |
| Update | Yes | PUT `/definitions/{id}` | Label, description, options, required |
| Delete | Yes | DELETE `/definitions/{id}` | Hard delete + cascades values |
| List | Yes | GET `/definitions` | Filter by entity_type |
| Reorder | Yes | PUT `/definitions/reorder` | Bulk sort_order update |
| Deactivate | Yes | POST `/definitions/{id}/deactivate` | Soft-delete |
| Activate | Yes | POST `/definitions/{id}/activate` | Restore |

**Missing operations:**
- **Get single definition by ID** -- No `GET /definitions/{id}` endpoint listed. Needed for the edit modal to load current state. The list endpoint returns all, but a single-resource GET is standard REST practice.
- **Bulk delete** -- Not needed for v1 (admin manages small numbers).
- **Export/Import field definitions** -- Not needed for v1.

### CustomFieldValue

| Operation | Defined | Endpoint | Notes |
|-----------|---------|----------|-------|
| Read | Yes | GET `/values/{entity_type}/{entity_id}` | Get values for an entity |
| Upsert | Yes | PUT `/values/{entity_type}/{entity_id}` | Bulk upsert |
| Delete individual | No | -- | Cannot clear a single custom field value |
| Delete by entity | No | -- | No explicit endpoint/behavior when target entity is deleted |

**Missing operations:**
- **Clear/delete individual value** -- What if a user wants to clear a non-required field back to empty? Is sending `null` or empty string in the upsert sufficient? This should be explicitly documented.
- **Orphan value cleanup** -- When an asset/request/incident is deleted, custom field values for that entity become orphans. The periodic task mentioned in architecture decisions is not specified as a requirement.

---

## Step 4: Status & State Analysis

### CustomFieldDefinition States

| State | Description |
|-------|-------------|
| `is_active = true` | Field visible on forms, validated, displayed on detail pages |
| `is_active = false` | Field hidden from forms, existing values preserved, shown grayed out on detail views |

**Transitions:**
| From | To | Trigger | Side Effects |
|------|-----|---------|-------------|
| Active | Inactive | Admin deactivates | Hidden from create/edit forms, excluded from required validation |
| Inactive | Active | Admin reactivates | Restored to forms |
| Any | Deleted | Admin hard-deletes | Definition + all values permanently removed |

**Missing state information:**
| Entity | Missing Info | Question |
|--------|--------------|----------|
| CustomFieldDefinition | No "draft" state | Should new fields take effect immediately or is a publish step needed? (Doc says immediate -- this is fine but should be confirmed) |
| CustomFieldDefinition | Deletion of definitions with values | US-004 mentions confirmation dialog but no "soft-delete before hard-delete" grace period. Is immediate permanent deletion acceptable? |
| CustomFieldValue | Null vs empty string | Is a null value different from an empty string? What is the initial state of a value for a new required field on existing entities? |

### Critical Gap: Required Fields on Existing Entities

**When an admin adds a new required custom field, what happens to existing entities that were created before the field existed?**

The requirement does not address this. Options:
1. Existing entities are non-compliant until edited (validation only on save)
2. Existing entities are exempt from the required constraint
3. Admin must backfill values before marking as required

This is a critical UX and data integrity question that must be resolved before implementation.

---

## Step 5: Use Case Pattern Detection

### CRUD Pattern
| Check | Status | Gap |
|-------|--------|-----|
| Create | Covered | -- |
| Read | Covered | Missing GET single definition endpoint |
| Update | Covered | -- |
| Delete | Covered | Orphan cleanup undefined |
| List | Covered | -- |
| Filter | Covered | Custom fields as filters |
| Search | Covered | Text/number searchable |
| Export | Mentioned | "Custom fields included in PDF/CSV reports" -- but no detail on implementation |
| Import | Not addressed | What about CSV import of assets with custom field values? E2 has CSV import. |

### Lifecycle Pattern
- Field definition lifecycle (create -> active -> deactivate -> reactivate -> delete) is well covered.
- **Missing:** Field definition versioning. If an admin changes options on a select field, historical values may become orphaned from the current option list. How are these displayed?

### State Machine Pattern
- Adequate for the simple active/inactive toggle.
- No complex multi-step transitions needed.

### Bulk Operations Pattern
- **Missing:** Bulk value editing. Can a technician apply the same custom field value to multiple assets at once? (e.g., set "Building" = "HQ" for 50 assets). Not required for v1 but worth noting as a future consideration.
- **Missing:** What happens during CSV import (E2)? Are custom fields included in CSV columns? If not, imported assets will lack custom field values.

### Reporting Pattern
- Mentioned but not detailed. "Custom fields included in PDF/CSV export reports" -- which report templates? The codebase has `asset_inventory.html`, `request_summary.html`, etc. Each would need modification.
- **Missing:** No specific report or dashboard for custom field usage analytics (e.g., how many fields configured, data completeness per field).

### Role-Based Access Pattern
- Well defined: Admin manages definitions, Technician+ fills values, Employee sees fields on request forms.
- **Missing:** The requirement explicitly defers role-based field visibility but does not clarify if employees can see ALL custom fields on requests or only fields the admin has marked for employee visibility. US-005 says "technician" but US-007 says "user viewing." What about the employee portal request creation flow?

### Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Get single definition by ID | Standard REST pattern, needed for edit modal | High | Confirm: should GET `/definitions/{id}` be added? |
| Clear/null a custom field value | User wants to remove a previously entered value | High | Is sending null/empty in upsert sufficient to clear a value? |
| Orphan value cleanup on entity deletion | Custom field values left behind when asset/request/incident deleted | Critical | Implement via (a) event-driven cleanup, (b) periodic task, or (c) on-read cleanup? |
| CSV import with custom fields | E2 asset CSV import needs to handle custom field columns | Medium | Should CSV import accept custom field columns? Or is that deferred? |
| Required field on existing entities | New required field added but existing entities have no value | Critical | Validation only on next save? Backfill required? Exempt existing? |
| Select option removal with existing values | Admin removes an option that has existing values | High | US-002 says "shows a warning" -- but does it block removal or allow it? What happens to existing values referencing the removed option? |
| Admin changes field label | Label changes but field_key stays the same | Low | Confirmed immutable field_key -- any API consumers relying on label need to know this |
| Concurrent field definition edits | Two admins editing the same field simultaneously | Low | Optimistic locking needed? Or last-write-wins? |

---

## Step 6: Inverse Operation Check

| Action | Inverse | Defined | Gap |
|--------|---------|---------|-----|
| Create definition | Delete definition | Yes | -- |
| Activate field | Deactivate field | Yes | -- |
| Set field value | Clear field value | Partial | No explicit "clear value" behavior documented |
| Add select option | Remove select option | Partial | Warning shown but outcome unclear -- does removal succeed? Are existing values preserved as-is? |
| Make field required | Make field optional | Yes | Via update |
| Reorder fields | Reorder fields (reverse) | Yes | Same mechanism |
| Hard delete definition | **Undelete** | **No** | No undo/recovery. Documented as "cannot be undone" which is acceptable but risky |
| Fill custom fields on entity create | Remove entity (cascade values?) | **No** | Orphan cleanup not specified |

### Missing Inverse Operations

1. **Undo hard delete** -- Intentionally omitted (acceptable), but the confirmation dialog described in US-004 must be very clear about permanence.
2. **Restore orphaned values after entity restore** -- If assets can be restored from decommissioned status, do custom field values survive? Yes, because values are not deleted on entity status change. But if the entity is truly hard-deleted from the database, values become orphans.

---

## Step 7: User Journey Check

### Admin: Create a Custom Field

| Step | Precondition | Postcondition | Error Recovery | Status |
|------|-------------|---------------|----------------|--------|
| Navigate to Settings > Custom Fields | Admin role, Enterprise plan | Settings page loads | 402 if not Enterprise | Defined |
| Select entity type tab | -- | Tab content loads | -- | Defined |
| Click "Add Field" | < 20 fields for this type | Modal opens | Show "limit reached" if >= 20 | Defined |
| Fill label, type, options | -- | Form validates | Inline validation errors | Partially defined |
| Save | Label generates unique field_key | Field created, appears on forms | **field_key collision handling?** | Gap |
| **Gap:** What happens if two fields with similar labels generate the same slug? | -- | -- | -- | **Not defined** |

### Technician: Fill Custom Fields on Asset Create

| Step | Precondition | Postcondition | Error Recovery | Status |
|------|-------------|---------------|----------------|--------|
| Open create asset form | Custom fields defined | Form renders standard + custom fields | If no fields defined, no custom section | Defined |
| Fill custom fields | Required fields filled, valid types | Values validated client-side | Validation errors shown | Defined |
| Submit form | All validation passes | Asset created + values saved | **Partial save?** If asset creates OK but values fail, what happens? | **Gap** |

### Critical Gap: Atomicity of Entity + Custom Fields Save

**When creating/editing an asset with custom fields, is the save atomic?**

The architecture says "values are stored in a separate table" and "Integration via query-time enrichment." This implies:
1. Asset is saved via asset_bc
2. Custom field values are saved via custom_field_bc

**If the custom field value save fails after the asset is successfully created, we have an inconsistent state.** The requirement must specify whether:
- (a) Both saves happen in the same DB transaction
- (b) Custom field save is a separate operation with retry/compensation
- (c) The frontend makes two separate API calls (create asset, then upsert values)

Based on the API design (separate endpoints for entity CRUD vs custom field values), option (c) seems implied. But this means a user could create an asset and have the custom field save fail, leaving required custom fields empty. This needs explicit documentation and error handling strategy.

---

## Step 8: Collateral Impact Analysis

### Verified Impacts (from requirements document)

| Component | Type | Impact | Action Required | Validated Against Codebase |
|-----------|------|--------|-----------------|---------------------------|
| `app.py` | Router registration | Register `custom_fields` router | Add `include_router` | Yes -- follows existing pattern |
| `adapters/http/api/assets/routers.py` | Response enrichment | Asset responses include `custom_fields` | Inject service, modify `_to_response()` | Yes -- current `_to_response()` does not include custom_fields |
| `adapters/http/api/assets/schemas.py` | Schema update | Add `custom_fields` to `AssetResponse` | Optional list field | Yes -- validated schema exists |
| Request routers | Response enrichment | Request responses include `custom_fields` | Inject service | Yes -- `adapters/http/api/requests/routers.py` exists |
| Incident routers | Response enrichment | Incident responses include `custom_fields` | Inject service | Yes -- `adapters/http/api/incidents/routers.py` exists |
| Frontend pages | UI changes | Multiple pages need custom field rendering | Dynamic field component | Confirmed pages exist |
| `web/app/src/locales/` | i18n | ~30 new translation keys | EN + ES files | Confirmed locale files exist |
| `tests/conftest.py` | Test setup | Register custom field models | Import models | Confirmed conftest exists |
| Report templates | PDF/CSV | Include custom fields in reports | Template modification | Confirmed: `asset_inventory.html`, `request_summary.html`, `incident_report.html` |

### Missing Collateral Impacts (Not Listed in Requirements)

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| **Audit middleware** (`adapters/http/middleware/audit.py`) | Audit trail | Custom field CRUD should be audited | Audit middleware auto-captures write operations on `/api/v1/` paths -- should work automatically, but verify the `custom-fields` resource name is parsed correctly |
| **MCP Server** (`adapters/mcp/server.py`) | Tool integration | E35 MCP server exposes asset/request tools. Should custom field values be included in MCP responses? Should there be MCP tools for custom field management? | **Not addressed.** MCP asset/request tools should return custom fields in responses. Consider adding custom field definition management tools for AI assistants. |
| **E2 CSV Import** (`ImportAssetsService`) | Import flow | CSV import currently has fixed columns. Custom field columns would need to be recognized and stored. | Not addressed in requirements. At minimum, document as out-of-scope for v1 and ensure import doesn't break. |
| **My Equipment view** (employee portal) | Employee portal | `adapters/http/api/my/routers.py` returns assets for the employee. Should these include custom fields? | Not mentioned explicitly. If "all entity responses include custom_fields," this should include my-equipment. |
| **Plan gate enforcement** | Billing | `custom_fields` key is already in `_ENTERPRISE_FEATURES`. But plan gating needs to be applied on definition endpoints. What about value read endpoints? | Requirement says "Definition management requires Enterprise. Reading custom field values on entities is available to all plans." -- Needs integration with existing `require_plan()` dependency pattern. |
| **Notification system** | Events | Should changes to custom field definitions trigger notifications? (e.g., "Admin added new required field to assets") | Not addressed. Low priority but worth noting. |
| **Search functionality** | Cross-entity search | "Text/number custom fields searchable via the main search input" -- this requires JOIN queries against `custom_field_values` table during list operations. **Performance concern** for large datasets. | Needs indexing strategy and potentially a search-optimized query approach. |
| **SLA system** (E19) | SLA evaluation | Could custom fields affect SLA policies? (e.g., SLA based on a custom "urgency reason" field) | Out of scope per non-goals (E31 territory), but confirm no interaction needed. |
| **Seed data** (`scripts/seed_demo_data.py`) | Demo data | Should demo data include example custom field definitions and values? | Important for sales demos and testing. Not mentioned. |

---

## Step 9: Slicing Assessment

**Size:** Large
**Estimated effort:** 3-5 developer-weeks
**Slicing needed:** Yes

### Recommended Feature Slicing

| Feature | Scope | Priority | Dependencies |
|---------|-------|----------|--------------|
| F0: CustomFieldDefinition CRUD | Domain entities, repository, endpoints for definition management, plan gating | P0 | None |
| F1: CustomFieldValue Storage | Value entity, upsert endpoint, get values endpoint, type validation/coercion | P0 | F0 |
| F2: Entity Response Enrichment | Asset/request/incident responses include custom_fields, batch loading | P0 | F1 |
| F3: Admin UI | Settings > Custom Fields page, tabs, create/edit/delete modals, reorder | P0 | F0 |
| F4: Frontend Dynamic Rendering | Custom field components in create/edit forms and detail pages | P0 | F1, F2, F3 |
| F5: Search & Filter | Custom field values searchable and filterable in list views | P1 | F2 |
| F6: Export Integration | Custom fields in PDF/CSV report templates | P1 | F2 |
| F7: Orphan Cleanup | Periodic task or event-driven cleanup for orphaned values | P2 | F1 |

### Out of Scope Dependencies

| Item | Info Needed Now | Why |
|------|----------------|-----|
| E31 Workflow Automations | No | Explicitly deferred; no info needed |
| CSV Import (E2) | Decision needed | Should CSV import include custom fields? Affects API design if yes |
| MCP Server (E35) | Decision needed | Should MCP tools return/manage custom fields? Affects response schemas |
| Seed data | Low | Nice to have for demos but not blocking |

### Red Flags

- [ ] **No slicing document exists yet.** The requirements document combines everything into one epic without feature decomposition. A `slicing.md` should be created before implementation.
- [ ] **Search/filter feature (F5) has performance implications** that need investigation before committing to the approach.

---

## Step 10: Time Constraints Assessment

**Deadline:** None
**Type:** Soft (no hard deadline)
**Reason:** Feature enhancement for Enterprise plan differentiation
**Realistic:** Yes -- scope is well-defined, no external dependencies blocking
**Calendar conflicts:** None identified
**Buffer included:** N/A (no deadline)

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| No deadline set | No immediate business impact | However, E30 is in Phase 9 of the roadmap. Other Phase 9 epics (E22 Onboarding, E31 Automations) may depend on E30 for custom fields on their entities |
| Search/filter complexity | Could increase scope significantly | Implement basic search first (exact match on select/boolean), defer full-text search to v1.1 |
| Cross-BC integration complexity | Integration with 3 target BCs (asset, request, incident) multiplies testing effort | Implement for assets first, then extend to requests and incidents |

### Dependencies Validation

- **E43 (Billing):** `custom_fields` feature key already exists in `plan_gate.py` at line 14. **Confirmed: dependency satisfied.**
- **E29 (Audit Trail):** Audit middleware at `adapters/http/middleware/audit.py` auto-captures write operations on `/api/v1/` paths. Custom field endpoints should be automatically audited. **Confirmed: should work without changes.**

---

## Step 11: Testing Assessment

**Tests defined:** Partially
**Critical scenarios identified:** Partially

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit: Entity validation | Yes | Yes | "Slug generation, max fields, type constraints" listed |
| Unit: Value coercion | Yes | Yes | "Type coercion and validation" listed |
| Unit: Command/Query handlers | Yes | Yes | "All command/query handlers" listed |
| Integration: Definition CRUD | Yes | Yes | Endpoint tests listed |
| Integration: Value upsert | Yes | Yes | Listed |
| Integration: Plan gating | Yes | Yes | "402 for non-Enterprise" listed |
| Integration: Response enrichment | Yes | Yes | "Asset/request enrichment" listed |
| Integration: Incident enrichment | Yes | **No** | Only asset/request enrichment mentioned, not incident |
| E2E: Admin creates field, tech fills value | Yes | **No** | No end-to-end user journey tests defined |
| Performance: List with custom field JOIN | Yes | **No** | No performance testing for search/filter with JOINs |
| Regression: Existing asset/request endpoints | Yes | **No** | Must verify that existing endpoints still work correctly with the new enrichment |
| Edge case: Max 20 fields limit | Yes | **No** | Need to test boundary: 19 fields OK, 20 OK, 21 fails |
| Edge case: Unicode field labels | Yes | **No** | Slug generation from unicode labels |
| Edge case: Concurrent definition edits | No | **No** | Low priority |

### Critical Test Scenarios NOT Identified

1. **Create asset with required custom field empty** -- Should return 422
2. **Edit asset, change custom field from valid to invalid value** -- Type mismatch
3. **Deactivate a required field, then create entity** -- Should not require the inactive field
4. **Delete field definition, verify cascaded value deletion**
5. **Admin on Free plan attempts to create field definition** -- Should return 402
6. **Search assets by custom field value** -- Verify JOIN performance with 10K+ assets
7. **Multi-select value with removed option** -- Display behavior for orphaned options
8. **Concurrent value upsert for the same entity** -- Race condition handling

### Test Data Requirements

- **Defined:** Not explicitly, but inferrable from the entity definitions.
- **Needed:** Test fixtures for:
  - Company with Enterprise plan (for plan gating tests)
  - Custom field definitions of each type (text, number, date, select, multi_select, boolean)
  - Assets/requests/incidents with custom field values
  - Company at the 20-field limit

---

## Step 12: Definition of Done Assessment

**DoD defined:** Yes
**DoD quality:** Good -- comprehensive checklist covering functional, frontend, testing, and infrastructure.

| Criteria | Defined | Clear | Issues |
|----------|---------|-------|--------|
| Acceptance criteria | Yes | Yes | 8 user stories with checkboxes |
| Quality gates | Partial | -- | No mention of mypy/flake8/lint passing, code review required, or performance benchmarks |
| Sign-off process | No | -- | Who approves the feature as done? Admin UAT? Product owner? |
| Training needs | No | -- | Admin documentation for "How to use custom fields" |
| Rollback plan | No | -- | If deployment fails, how to roll back migrations safely |
| Performance criteria | No | -- | No SLA for response time degradation from custom field JOINs |

### DoD Gaps

1. **No performance acceptance criteria.** Adding JOINs to every asset/request list query could degrade performance. Define acceptable latency (e.g., "asset list with custom fields < 200ms for 1000 assets with 20 custom fields each").
2. **No code quality gates.** Should specify `make lint` and `make test` pass.
3. **No migration rollback plan.** Adding two new tables is straightforward to roll back, but should be documented.
4. **No documentation/help content.** Enterprise admins need guidance on custom fields setup.

---

## Red Flags

- [x] **CRITICAL: EAV pattern rejected by stakeholder** -- The requirements document specifies Entity-Attribute-Value pattern with a separate `custom_field_values` table. The stakeholder has explicitly rejected this approach. Must use JSON storage instead: either a `custom_fields_data: JSON` column on each target entity table, or a single shared table with a JSON blob per entity. This affects the entire storage architecture, entity definitions, API design, and query approach. **The requirements.md must be rewritten before implementation.**
- [x] **Required fields on existing entities** -- Adding a new required field to assets that already exist creates a data integrity dilemma. Not addressed.
- [x] **Atomicity of entity + custom fields save** -- With JSON-on-entity approach, this becomes a non-issue (values saved with the entity in the same row). With shared table approach, same concern as before.
- [x] **No GET single definition endpoint** -- Standard REST pattern missing from API design.
- [x] **Select option removal behavior unclear** -- US-002 says "shows a warning" but doesn't specify if removal is blocked, what happens to existing values, or how orphaned option values are displayed.
- [ ] **No MCP server integration considered** -- E35 is already shipped. Custom fields should be included in MCP tool responses.
- [ ] **No seed data** -- Demo companies won't showcase custom fields unless seed data is created.
- [ ] **KPIs are weak** -- Two of four KPIs are binary capabilities, not measurable business metrics.

### Architecture Decision: JSON Storage (Stakeholder Directive)

The stakeholder has mandated: **no EAV**. Two options:

**Option A: JSON column on each entity (Recommended)**
- Add `custom_fields_data: JSONB` column to `assets`, `requests`, `incidents` tables
- Store as `{"field_key": value, ...}`
- Pros: No extra table, no JOINs, atomic saves, fast reads, PostgreSQL JSONB operators for filtering
- Cons: Alembic migration on 3 existing tables, duplicate storage schema across entities
- Orphan cleanup: automatic (data lives with the entity)
- Atomicity: solved (same row, same transaction)
- Search/filter: PostgreSQL `->>'key'` or `@>` operators, GIN index if needed

**Option B: Single shared table with JSON blob**
- One `custom_field_entity_values` table: `(entity_type, entity_id, data JSONB)` — one row per entity
- Pros: No changes to existing entity tables, centralized
- Cons: Extra JOIN on reads, separate transaction concern remains
- Orphan cleanup: still needed (event or periodic task)

**Recommendation: Option A** — eliminates orphan cleanup, atomicity, and JOIN performance concerns in one stroke.

---

## Open Questions — ALL RESOLVED

All questions have been answered by the stakeholder:

1. **Required field on existing entities:** Validate on next save only. Existing entities are not retroactively validated. Detail views show "Missing" indicator.
2. **Select option removal:** Allow removal. Existing values preserved as-is. Removed option can't be selected again.
3. **Entity deletion orphan cleanup:** N/A — JSONB column approach means data is deleted with the entity automatically.
4. **Atomicity:** N/A — JSONB column approach means values are saved atomically with the entity.
5. **CSV import:** Include in E30. CSV import recognizes custom field columns by `field_key`.
6. **MCP integration:** Include `custom_fields` in MCP asset/request responses. No new management tools.
7. **Employee visibility:** Per-field `visible_to_employees` flag (default: true). Admin chooses which fields employees see.
8. **field_key collision handling:** Return validation error: "A field with a similar name already exists." No auto-suffix.
9. **Search performance:** PostgreSQL JSONB operators (`->>'key'`). GIN index on `custom_fields_data` if needed. No JOINs required (data is on the same row).
10. **Audit trail:** Yes — custom field value changes captured in audit log with old/new values.

---

## Checklist Summary

### Business Alignment: 2/4 passed
- [x] Primary objective identified (Revenue/Churn)
- [x] Competitive analysis provided
- [ ] Specific customer evidence (names, tickets, revenue)
- [ ] Measurable KPIs with baselines

### Content Completeness: 7/9 passed
- [x] Problem statement clear
- [x] Entities well-defined
- [x] API endpoints documented
- [x] Response schemas documented
- [x] Architecture decisions documented
- [x] Non-goals explicitly stated
- [x] User stories with acceptance criteria
- [ ] Error handling flows
- [ ] Performance requirements

### Use Case Coverage: 5/8 passed
- [x] CRUD operations
- [x] State transitions (active/inactive)
- [x] Admin management journey
- [x] Technician usage journey
- [x] Integration (response enrichment)
- [ ] Orphan cleanup
- [ ] Existing entity backfill for required fields
- [ ] CSV import integration

### Entity States: 3/4 passed
- [x] States defined (active/inactive)
- [x] Transitions documented
- [x] Delete strategy clear
- [ ] Required field on existing entities behavior

### Collateral Impact: 6/9 passed
- [x] Target entity routers identified
- [x] Frontend pages identified
- [x] i18n identified
- [x] Test config identified
- [x] Report templates mentioned
- [x] Plan gating verified (key exists in plan_gate.py)
- [ ] MCP server integration
- [ ] Audit trail interaction
- [ ] Seed data

### Slicing: 1/3 passed
- [x] Size estimated (Large)
- [ ] Feature decomposition (no slicing.md)
- [ ] Out-of-scope dependencies resolved (CSV import, MCP)

### Time Constraints: 3/3 passed
- [x] No hard deadline (acceptable)
- [x] Dependencies verified (E43 billing key exists)
- [x] No blocking dependencies

### Testing: 4/7 passed
- [x] Unit tests identified
- [x] Integration tests identified
- [x] Plan gating test identified
- [x] Response enrichment test identified
- [ ] Performance tests
- [ ] E2E journey tests
- [ ] Edge case tests (max fields, unicode, concurrent edits)

### Definition of Done: 3/6 passed
- [x] Acceptance criteria defined and testable
- [x] Functional checklist comprehensive
- [x] Frontend checklist comprehensive
- [ ] Performance criteria
- [ ] Code quality gates
- [ ] Sign-off process / rollback plan

---

## Recommendations

### Critical (Must address before implementation)

1. **REWRITE STORAGE ARCHITECTURE: Replace EAV with JSON.** The entire requirements.md must be updated. Replace CustomFieldValue entity with a `custom_fields_data: JSONB` column on each target entity. Update architecture decisions, entity definitions, API endpoints (remove separate value endpoints), and resolved decisions. This is the single most important change.

2. **Define required-field-on-existing-entities behavior.** Recommended approach: validate required fields only on create/edit, not retroactively. Existing entities without values for new required fields should display a "Missing" indicator in detail views but not block anything until the entity is next edited.

3. **Add GET single definition endpoint.** Add `GET /api/v1/custom-fields/definitions/{id}` for the edit modal use case.

4. **Clarify select option removal behavior.** Recommended: allow removal, preserve existing values as-is (display as the literal string even if no longer in the options list), and show the removed option grayed out in the detail view. Do not block removal.

### High (Should address before implementation)

5. **Create a `slicing.md` feature decomposition.** The epic is too large for a single implementation pass. Recommend the 7-feature split identified in Step 9.

7. **Add performance acceptance criteria.** Define: "List endpoints with custom field enrichment must respond in < 300ms for 1000 entities with 20 custom fields each, measured on standard test infrastructure."

8. **Add field_key collision handling.** Either auto-append a numeric suffix or return a clear error message explaining the conflict.

### Medium (Address during implementation)

9. **Add MCP server integration plan.** At minimum, existing MCP asset/request tools should return `custom_fields` in responses.

10. **Add seed data for demo companies.** Create 3-5 example custom fields per entity type with sample values.

11. **Document audit trail behavior.** Confirm that custom field CRUD is captured by the audit middleware (it should be automatic based on the middleware pattern) and that value changes are captured.

12. **Add edge case test scenarios.** Unicode slug generation, max 20 field boundary, concurrent edits, multi-select with 50+ options.

### Low (Can be deferred to v1.1)

13. **CSV import with custom fields.** Defer to a follow-up enhancement. Document as out-of-scope.

14. **Custom field usage analytics.** Dashboard showing how many companies use custom fields, most popular field types, data completeness.

15. **Admin documentation/help content.** In-app tooltips or a knowledge base article explaining custom fields setup.
