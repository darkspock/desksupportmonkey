# Requirement Validation Report

**Document:** E16 - Shipping & Logistics
**Date:** 2026-02-18
**Status:** Valid (minor improvements recommended)

## Summary

E16 is a well-structured epic with comprehensive coverage. The state machine is clean, entities are clearly defined, use cases cover the main flows, and validation decisions close all ambiguous questions upfront. Three minor gaps identified: (1) missing `recipient_user_id` on Shipment for notification routing, (2) no explicit handling of "asset already in another active shipment" conflict, (3) missing cancellation event type. None are blockers.

## Business Alignment Assessment

**Primary Objective:** Operational efficiency / Asset traceability
**Contribution:** Clear — fills a real gap in asset movement tracking between existing asset states
**KPIs Defined:** Yes (4 targets)
**Justification Type:** Objective with data (references existing pain points in E3 repair workflows and E14 procurement)

### Justification Quality
| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | KPIs are qualitative ("100% traceability", "zero lost") — no baseline |
| Evidence sources | Partial | References existing system gaps, not customer requests/tickets |
| Revenue impact | No | Indirect — prevents financial loss from lost equipment |
| Customer names/tickets | No | Internal platform, not customer-facing |

**Note:** This is an internal operations tool. Customer-facing metrics don't apply. Evidence is based on system capability gaps, which is appropriate.

### Experimentation Assessment
**Is this an experiment?** No

**RED FLAGS:**
- [ ] ~~Subjective justification detected~~ — Justified by system gaps
- [ ] ~~Missing revenue/cost impact~~ — Justified by operational need + E22 dependency
- [ ] ~~No evidence provided~~ — Evidence based on existing system limitations
- [ ] ~~Experiment without success metrics~~ — N/A
- [ ] ~~Experiment without investment limit~~ — N/A

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| Shipment | Create, Read, Update (PATCH), List, Filter | 6 states, 10 transitions | Cancel (no delete) |
| ShipmentItem | Create (via Shipment), Read (via Shipment) | None (junction) | Implicit with shipment |
| ShippingAddress | Create, Read, Update, List, Filter | None | Soft-delete (is_active) |

## Missing Use Cases

| Use Case | Reason | Priority | Recommendation |
|----------|--------|----------|----------------|
| Duplicate asset in active shipment | Asset A is in DISPATCHED shipment S1. Technician tries to create new shipment with Asset A. What happens? | High | Add validation: asset cannot be in more than one active (DRAFT/DISPATCHED/IN_TRANSIT) shipment simultaneously. Add to Technical Constraints. |
| Bulk status update | Technician delivers 5 shipments from same carrier batch | Low | Not critical for MVP. Can be added later. |
| Shipment list for employee | Employee wants to see shipments sent to them (not just appointments) | Medium | Consider adding `GET /my/shipments` endpoint, similar to `GET /my/appointments`. Currently only notifications inform employees. |

## Missing State Information

| Entity | Missing Info | Recommendation |
|--------|--------------|----------------|
| Shipment | DISPATCHED → DISPATCHED (update tracking info) — is this a valid self-transition? | Clarify: PATCH endpoint handles tracking updates without state change. This is fine — not a transition, just a field update. No action needed. |
| Shipment | What happens to linked ShipmentItems when shipment is CANCELLED? | The items remain as historical records. Linked assets are not modified on cancellation. Document this explicitly. |
| ShipmentItem | Can items be added/removed after shipment creation? | Decided implicitly: items are set at creation (US-E16-001). For returns, items can differ from original (UC-003 alt flow 3a). Should clarify whether DRAFT shipments allow item modification via PATCH. |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Asset Detail (frontend) | UI Extension | Add "Shipment History" section | Edit AssetDetailPage.tsx |
| Request Detail (frontend) | UI Extension | Show linked shipments | Edit RequestDetailPage.tsx |
| Dashboard (frontend) | UI Extension | Add active shipments card | Edit DashboardPage.tsx |
| Notification EventTypes | Enum Extension | Add 4 event types | Edit enums.py |
| Notification TargetResolver | Logic Extension | Add shipment resolvers | Edit target_resolver.py |
| Sidebar | Nav Addition | Add "Shipments" + "Addresses" | Edit Sidebar.tsx |
| Router | Route Addition | Add ~5 routes | Edit router.tsx |
| i18n | Translation Keys | ~80 keys EN + ES | Edit en.ts, es.ts |
| app.py | Router Registration | 2 new routers | Edit app.py |
| **Asset entity** | **Cross-BC side effect** | **Delivery updates asset status (ASSIGNED, IN_STOCK)** | **This is the most architecturally sensitive impact. The shipping_bc must call asset_bc to update status. Use event-driven or direct repository call, consistent with E14's goods receipt pattern.** |

## Slicing Assessment

**Size:** Large (3 entities, 18 endpoints, state machine, frontend pages, notifications, dashboard)
**Slicing needed:** Yes
**Recommended slicing:**

| Feature | Scope | Complexity |
|---------|-------|------------|
| F0 | Domain entities, enums, migrations, repositories | Medium |
| F1 | Shipment CRUD + state machine + notifications | High |
| F2 | Address management (CRUD, 7 endpoints) | Medium |
| F3 | Asset delivery side effects + shipment history | Small |
| F4 | Frontend (shipment pages, address pages, collateral edits, i18n) | High |

**Out of scope dependencies:**
| Item | Info Needed Now | Why |
|------|-----------------|-----|
| E22 (Onboarding) | Address reuse pattern | E22 will consume ShippingAddress — design the entity with E22 in mind (done: user_id FK on ShippingAddress) |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** Medium priority, no external pressure
**Realistic:** Yes — no deadline constraint
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis
| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| N/A — no deadline | N/A | N/A |

## Testing Assessment

**Tests defined:** Yes (in DoD)
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (~25 tests) | None |
| Integration | Yes | Yes (~20 tests) | None |
| E2E | No | No | Not needed (frontend build verification suffices) |
| UAT | No | No | Not needed (internal tool) |

**Critical scenarios identified:** Partially
- State machine transitions: Yes (covered by state table)
- Asset ownership validation: Yes (technical constraints)
- **Missing critical scenario:** Concurrent shipment creation for same asset (race condition). Recommend: add unique constraint or check in command handler.

**Test data requirements:** Not explicitly defined but follows existing patterns from conftest.py

## Definition of Done Assessment

**DoD defined:** Yes (19 checkboxes)
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Clear — testable checkboxes on each US |
| Quality gates | Yes | TypeScript compiles, build succeeds, all tests pass |
| Sign-off process | No | Not needed (internal development) |
| Training needs | No | Not needed (follows existing UI patterns) |

## Red Flags

- [ ] ~~No red flags detected~~

All items are well-addressed. The epic is clean and implementable.

## Open Questions for Stakeholder

All 5 open questions are already resolved (closed with strikethrough + "Decided:"). No remaining open questions.

**Suggested additions (optional, not blocking):**

1. Should DRAFT shipments allow adding/removing items via PATCH? (Recommendation: Yes, only while in DRAFT status)
2. Should there be a `GET /my/shipments` endpoint for employees to see their shipments? (Recommendation: Yes, low effort, high value — mirrors `/my/appointments` pattern)
3. Should a `shipment.cancelled` event be added alongside the existing 4 events? (Recommendation: Yes — cancellation is a notable event worth notifying about)

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective defined
- [x] KPIs defined
- [x] Evidence provided
- [ ] Quantitative baseline (not critical for internal tool)

### Content Completeness: 7/7 passed
- [x] Problem statement
- [x] Goals
- [x] User stories with acceptance criteria
- [x] Validation decisions (all closed)
- [x] Non-goals defined
- [x] Entities with fields
- [x] API endpoints listed

### Use Case Coverage: 5/6 passed
- [x] Create + Dispatch (UC-001)
- [x] Delivery (UC-002)
- [x] Returns (UC-003)
- [x] Address management (UC-004)
- [x] Asset history (UC-005)
- [ ] Missing: Employee view of own shipments (minor)

### Entity States: 3/3 passed
- [x] Shipment state machine (6 states, 10 transitions)
- [x] State diagram (ASCII art)
- [x] Side effects documented per transition

### Collateral Impact: 9/9 identified
- [x] All affected components listed
- [x] Action required specified for each
- [x] Cross-BC impact (asset status) identified

### Slicing: Ready
- [x] Size assessed (Large)
- [x] Slicing needed (Yes)
- [x] Recommended feature split provided

### Time Constraints: 1/1 passed
- [x] No deadline (explicitly stated)

### Testing: 2/2 passed
- [x] Unit tests scoped (~25)
- [x] Integration tests scoped (~20)

### Definition of Done: 1/1 passed
- [x] Comprehensive DoD with 19 checkboxes

## Recommendations

1. **Add asset-in-active-shipment validation** — Prevent the same asset from being in two active shipments simultaneously. Add to Technical Constraints section.
2. **Add `shipment.cancelled` event** — Currently only 4 events defined. Cancellation should also trigger a notification (especially if recipient was already notified of dispatch).
3. **Add `recipient_user_id` field to Shipment** — Currently `recipient_name` is a text field. For employee_home shipments, storing the `user_id` of the recipient enables notification routing and `/my/shipments` queries without relying solely on address.user_id.
4. **Consider `GET /my/shipments` endpoint** — Follows the `/my/appointments`, `/my/requests`, `/my/equipment` pattern. Low effort to add, gives employees visibility into their shipments beyond notifications.
5. **Clarify DRAFT item modification** — Allow adding/removing ShipmentItems while in DRAFT status via PATCH. Lock items after DISPATCHED.

**Overall verdict:** The epic is **valid and ready for slicing**. The 5 recommendations above are improvements, not blockers.
