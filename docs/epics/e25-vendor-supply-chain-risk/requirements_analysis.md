# Requirement Validation Report

**Document:** E25 — Vendor & Supply Chain Risk
**Date:** 2026-02-26
**Type:** Epic (FULL validation)
**Status:** Needs Revision (minor gaps)

## Summary

Strong epic with clear regulatory motivation (NIS2/DORA), well-defined entities, and good awareness of the existing foundation. The document correctly identifies that this extends `procurement_bc/vendor` rather than creating a new BC. Main gaps: missing VendorContract state machine transitions, missing inverse operations for some use cases, missing delete strategy per entity, and the "Supply Chain Security Scoring" (section 3) is described as a concept but has no corresponding entity, endpoint, or calculation specification. Overall, the epic is nearly ready for implementation with a few targeted additions.

## Business Alignment Assessment

**Primary Objective:** Compliance (NIS2/DORA regulatory requirement)
**Contribution:** Clear — directly mandated by NIS2 Art. 21(2)(d) and DORA Art. 28
**KPIs Defined:** Yes (5 measurable targets)
**Justification Type:** Objective with regulatory evidence

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Yes | 100% targets, 40% threshold, 60/30/7 day reminders |
| Evidence sources | Yes | NIS2 Article 21(2)(d), DORA Article 28 cited |
| Revenue impact | No | Regulatory compliance, not revenue-driven — acceptable |
| Customer names/tickets | N/A | Regulation-driven, not customer-driven |

### Experimentation Assessment

**Is this an experiment?** No — regulatory requirement.

**RED FLAGS:**
- [ ] Subjective justification detected — **No, regulatory basis is solid**
- [ ] Missing revenue/cost impact — **Acceptable: compliance-driven**
- [ ] No evidence provided — **No, NIS2/DORA articles cited**

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| VendorContract | C/R/U/D/L | Yes (draft, active, expired, terminated) | **MISSING** — Hard delete? Soft delete? Archive? |
| VendorRiskAssessment | C/R/L | Stateless (immutable snapshot) | **MISSING** — Can assessments be deleted? Probably shouldn't (audit trail) |
| VendorDependency | C/R/U/D/L | Stateless | **MISSING** — Hard delete assumed, confirm |
| Vendor (extended) | Existing | Existing (is_active) | Existing (deactivate) |

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Contract status transitions | States listed (draft/active/expired/terminated) but no transition rules or triggers defined | High | What are valid transitions? Can terminated → active? Does expired auto-trigger? |
| Contract document attachments | Section 1 mentions "attached documents" but no entity field or endpoint for file uploads | Medium | Are contract document uploads in scope for v1, or deferred? |
| Supply chain security scoring calculation | Section 3 describes a "composite score" but there's no entity, no endpoint, no algorithm defined | High | Is this just the cached `risk_level` from assessments, or a separate composite calculation? If composite, define the formula. |
| Vendor performance metrics — data source | US8 mentions "incident count, avg resolution time" but no endpoint or query is defined for this | Medium | Is this part of the risk-profile endpoint, or a separate query? How are vendor-linked incidents aggregated? |
| Bulk vendor assessment | No bulk operations for assessments across multiple vendors | Low | Is batch assessment needed, or one-by-one is sufficient? |
| Assessment reassessment trigger | KPI says "not older than review cadence" but no mechanism to enforce or alert on stale assessments | Medium | Should a Celery task check for vendors with expired assessments and alert? |

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| VendorContract | State machine transitions | What transitions are valid? draft→active, active→terminated, active→expired? Can any state go back to draft? |
| VendorContract | Expired auto-transition | Does the system automatically set `expired` when end_date passes? (Celery task needed?) |
| VendorContract | Terminated vs deleted | Is termination a soft-delete or a distinct business status? Can terminated contracts be reactivated? |
| VendorRiskAssessment | Immutability enforcement | Document says "immutable snapshot" — confirm no update/delete endpoints are intentional |
| Vendor.risk_level | Cache invalidation | When is the cached risk_level updated? Only on new assessment, or also if assessment is deleted? |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `app.py` | Router registration | New sub-routers for contracts, assessments, dependencies | Low risk — additive |
| `procurement_bc/vendor/domain/entities.py` | Entity extension | 4 new fields | Backward compatible (all nullable/optional) |
| `procurement_bc/vendor/infrastructure/models.py` | Model extension | 4 new columns | Migration needed — backward compatible |
| `alembic/versions/` | New migration | 3 new tables + vendor column additions | Standard migration |
| `core/celery.py` | Beat schedule | 2 new periodic tasks | Low risk — additive |
| `notification_bc/notification/domain/enums.py` | New event types | CONTRACT_RENEWAL_REMINDER, CONCENTRATION_RISK_ALERT | Low risk — enum extension |
| `web/app/src/router.tsx` | New route | /vendors/:id detail page | Low risk — additive |
| `web/app/src/pages/admin/VendorListPage.tsx` | UI enhancement | Risk level badges, link to detail | Medium risk — existing page modification |
| `web/app/src/locales/` | i18n | New keys for EN + ES | Low risk — additive |
| `web/app/src/types/index.ts` | TypeScript types | New interfaces | Low risk — additive |
| `risk_bc` (not listed!) | **Cross-BC interaction** | RiskLinkType.VENDOR already exists — risk register can link to vendors. Does E25 need to show linked risks on the vendor detail page? | **Clarify** — add to collateral impact if yes |
| `incident_bc` (partially listed) | **Cross-BC interaction** | VendorReader port exists. Vendor detail page incidents tab will need to query incidents by vendor. | **Clarify** — need a new query or port for "incidents by vendor_id"? |

## Slicing Assessment

**Size:** Large (3 new entities + entity extension + Celery tasks + dashboard + export + full frontend)
**Slicing needed:** Yes — already sliced in companion `slicing.md`
**Slicing quality:** Good — 5 vertical features, unidirectional dependencies

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|----------------|-----|
| report_bc export infrastructure | Exists (confirmed in codebase) | F4 reuses WeasyPrint + MinIO |
| Incidents by vendor query | **Needs investigation** | Vendor detail page incidents tab needs to list incidents linked to a vendor. Does this query exist in incident_bc? |
| Risk links to vendors | Enum exists, implementation exists (E37) | Vendor detail page could show linked risks — not mentioned in E25 |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** NIS2/DORA compliance — regulatory deadline depends on company's compliance timeline
**Realistic:** Yes — scope is well-defined with clear slicing
**Calendar conflicts:** None identified
**Buffer included:** N/A

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| NIS2 compliance gap | Vendors managed in spreadsheets | F0+F1 deliver core compliance value early |
| Scope creep from "performance metrics" | Delays F4 | Performance metrics can be deferred — not strictly NIS2/DORA required |

## Testing Assessment

**Tests defined:** Partially (DoD mentions unit + integration tests)

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (DoD) | No specific scenarios listed |
| Integration | Yes | Yes (DoD) | No specific scenarios listed |
| E2E | No | No | N/A for backend-heavy epic |
| UAT | Recommended | No | Auditor walkthrough of compliance evidence would be valuable |

**Critical scenarios identified:** No — would benefit from listing:
- Contract with expired end_date → auto-expiry behavior
- Assessment scoring edge cases (all 1s, all 5s, mixed)
- Concentration risk at exactly 40% boundary
- Renewal reminder idempotency (don't send duplicate reminders)

**Test data requirements:** Not defined — seed data for demo vendors with contracts/assessments would be useful.

## Definition of Done Assessment

**DoD defined:** Yes (19 items)

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Mostly clear, some gaps noted below |
| Quality gates | Yes | Unit + integration tests passing |
| Sign-off process | No | Who validates NIS2/DORA compliance? |
| Training needs | No | Admin training on risk assessment questionnaire? |

## Red Flags

- [x] **Supply Chain Security Scoring undefined** — Section 3 describes a "composite vendor risk level" but no entity, endpoint, or algorithm is specified. Is this just the `risk_level` cached from the latest assessment? If it's truly composite (assessment + contracts + incidents + dependencies), the calculation needs to be defined.
- [x] **VendorContract state machine missing** — States listed but no transitions, triggers, or side effects defined. For an entity with 4 states, this is a significant gap.
- [x] **Contract document attachments mentioned but not modeled** — "attached documents" in section 1 has no entity field, storage, or endpoint.
- [ ] **Performance metrics vague** — US8 and section 6 describe "vendor SLA metrics: response time, resolution time, uptime" but no data source, calculation, or endpoint is specified beyond "derived from linked incidents."
- [ ] **Missing incidents-by-vendor query** — Vendor detail page's Incidents tab needs to fetch incidents linked to a specific vendor. No query or endpoint defined for this.

## Open Questions for Stakeholder

1. **Supply Chain Security Scoring:** Is the "composite score" (section 3) just the cached `risk_level` from the latest assessment, or a separate calculation combining multiple inputs? If composite, define the formula.
2. **Contract state transitions:** What are the valid transitions between draft/active/expired/terminated? Does expired trigger automatically via Celery when `end_date` passes?
3. **Contract document uploads:** Are file attachments in scope for v1? If yes, which storage (MinIO like reports)?
4. **Stale assessment alerts:** Should the system alert when a vendor's assessment is older than the company's review cadence? (Related to KPI "100% of vendors have current assessment")
5. **Vendor detail — linked risks:** Should the vendor detail page show risks linked to this vendor (from risk_bc's RiskLink)? The enum already exists.
6. **Incidents by vendor:** Does incident_bc have a query to list incidents linked to a specific vendor? If not, this needs to be added for the Incidents tab on the vendor detail page.

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective identified (regulatory compliance)
- [x] Contribution explained
- [x] KPIs with measurable targets
- [ ] Revenue/cost impact (N/A for compliance)

### Content Completeness: 8/11 passed
- [x] Problem statement
- [x] Who is affected
- [x] Proposed solution
- [x] User stories (11)
- [x] Entity definitions (3 new + 1 extension)
- [x] API endpoints (17 endpoints)
- [ ] Supply chain scoring algorithm undefined
- [ ] Contract document attachments unmodeled
- [x] Existing foundation documented
- [x] Resolved decisions (7)
- [ ] Performance metrics data source undefined

### Use Case Coverage: 8/12 passed
- [x] Contract CRUD
- [x] Assessment create/list
- [x] Dependency CRUD
- [x] Risk profile aggregation
- [x] Dashboard
- [x] Export
- [x] Renewal reminders
- [x] Concentration risk detection
- [ ] Contract state transitions
- [ ] Contract auto-expiry
- [ ] Stale assessment detection
- [ ] Bulk assessment

### Entity States: 2/4 passed
- [x] VendorContract states listed
- [ ] VendorContract transitions undefined
- [x] VendorRiskAssessment immutable (stateless by design)
- [ ] Delete strategy per entity undefined

### Collateral Impact: 8/10 passed
- [x] app.py
- [x] Entity/model extension
- [x] Migration
- [x] Celery tasks
- [x] Notification events
- [x] Frontend routes
- [x] i18n
- [x] TypeScript types
- [ ] risk_bc cross-BC interaction not listed
- [ ] incident_bc incidents-by-vendor query not addressed

### Slicing: 5/5 passed
- [x] Size assessed
- [x] Slicing done (5 features)
- [x] Dependencies clear
- [x] Vertical slices
- [x] Each feature delivers value

### Time Constraints: N/A
- No deadline specified

### Testing: 1/4 passed
- [x] Test types mentioned in DoD
- [ ] Critical scenarios not listed
- [ ] Test data requirements not defined
- [ ] UAT process not defined

### Definition of Done: 2/4 passed
- [x] Acceptance criteria listed (19 items)
- [x] Quality gates (tests passing)
- [ ] Sign-off process not defined
- [ ] Training needs not identified

## Recommendations

1. **Define VendorContract state machine** — Add valid transitions, triggers (manual vs automatic), and side effects. Specifically: does `expired` auto-trigger via Celery when `end_date < today`? This is critical for F0 implementation.

2. **Clarify "Supply Chain Security Scoring"** — Either: (a) confirm it's just the cached `risk_level` from the latest assessment and remove the separate section, or (b) define the composite formula. Current ambiguity will cause design confusion.

3. **Remove or defer "contract document attachments"** — Mentioned in section 1 but unmodeled. Either add a `VendorContractDocument` entity or explicitly state "document uploads deferred to future version."

4. **Add delete strategy per entity** — VendorContract: soft delete or hard? VendorRiskAssessment: immutable, no delete (confirm). VendorDependency: hard delete (confirm).

5. **Add stale assessment Celery task** — To support the KPI "100% of vendors have current assessment," add a periodic check that alerts when a vendor's latest assessment is older than the configured review cadence.

6. **Address cross-BC queries** — Vendor detail page needs: (a) incidents linked to vendor (from incident_bc), (b) optionally risks linked to vendor (from risk_bc). Define how these are fetched (ports? direct queries? API calls?).
