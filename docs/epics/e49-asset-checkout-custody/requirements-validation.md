# Requirement Validation Report

**Document:** E49 — Asset Checkout & Custody Management
**Date:** 2026-02-26
**Status:** Approved (all gaps resolved)

## Summary

Strong epic with clear problem statement, well-defined domain model, and solid feature slicing. The codebase is ready for this — maintenance BC, notification BC, and asset domain all support it. A few gaps need addressing before implementation.

## Business Alignment Assessment
**Primary Objective:** Churn / Compliance
**Contribution:** Clear — legal protection (custody proof), GDPR compliance, operational accuracy (location vs assignment)
**KPIs Defined:** No
**Justification Type:** Objective with real operational problems

### Justification Quality
| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | No data on how many "I never received it" disputes exist |
| Evidence sources | No | No customer tickets or incident references |
| Revenue impact | No | Should quantify GDPR non-compliance risk (fines) |
| Customer names/tickets | No | Not provided |

**RED FLAGS:**
- [x] Missing revenue/cost impact (GDPR fines could be quantified)
- [ ] Subjective justification detected — No, the problems are real and well-articulated

**Proceed anyway?** Yes — this is a compliance feature with obvious operational value. KPIs would be nice but aren't blocking.

## Entities Identified
| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| AssetCheckout | Create (checkout), Read (history/current), Update (accept/checkin) | Open → Accepted → Closed | Not defined ⚠️ |
| AssetCondition (enum) | N/A | NEW, GOOD, FAIR, DAMAGED, UNUSABLE | N/A |

## Missing Use Cases
| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Cancel checkout | Technician made a mistake, checked out to wrong person | HIGH | What happens? Delete record? Or mark as cancelled? |
| Edit checkout notes | Technician forgot to note accessories | MEDIUM | Allow editing notes_out after creation? |
| Bulk checkout | Onboarding: assign 3 devices to new employee | LOW | Phase 2? |
| Checkout without assignment | Loaner device, temporary use | MEDIUM | Must the asset be ASSIGNED first, or can checkout auto-assign? |
| Transfer checkout | Employee A gives device to Employee B directly | LOW | Require checkin + new checkout, or allow transfer? |
| Delete checkout record | Data correction | LOW | Should this be allowed? Audit implications. |
| List all open checkouts | Dashboard view: "who has what" company-wide | HIGH | Not in API endpoints — only per-asset. Need a global query. |

## Missing State Information
| Entity | Missing Info | Question |
|--------|--------------|----------|
| AssetCheckout | No explicit status field | Is status derived from null checks (accepted_at, checked_in_at)? This works but isn't explicit. |
| AssetCheckout | No cancellation flow | Can a checkout be cancelled? What status would that be? |
| AssetCheckout | Delete strategy not defined | Soft delete? Hard delete? Archive? |
| Asset | IN_REPAIR → IN_STOCK transition trigger | Who/what triggers this? Maintenance completion event? Is this already implemented? |

## Collateral Impact
| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| assign_asset.py | Breaking change | Remove auto-location move | Must update simultaneously with checkout feature |
| unassign_asset.py | Breaking change | Remove auto-location move + add guard | Must update simultaneously |
| SystemLocation.EMPLOYEE | Removal | Existing assets at "Empleado" location need migration | Migration must handle gracefully |
| create_company.py seeding | Extension | Add GDPR template, remove EMPLOYEE location from seeding | Update seeding logic |
| Asset detail frontend | UI change | Assignment no longer shows location change | Frontend must be updated |
| Asset list/filters | Potential impact | If users filter by "Empleado" location, those filters break | Check if location filters exist |
| Reports | Potential impact | Any report using "Empleado" location breaks | Check existing reports |
| Audit trail | Extension | New event types needed | Add to event types enum |
| My Equipment page | Extension | Add pending acceptance + confirm receipt | New frontend section |
| Maintenance BC | Integration | Auto-create on checkin | Need to verify maintenance creation can be triggered externally |
| Dashboard | Potential | May want "pending acceptances" widget | Not in scope but consider |

## Slicing Assessment
**Size:** Large (7 features)
**Slicing needed:** Yes (already sliced)
**Slicing quality:** Good — logical progression from domain to application to HTTP to frontend

**Out of scope dependencies:**
| Item | Info Needed Now | Why |
|------|----------------|-----|
| Maintenance completion → IN_STOCK transition | Is this already implemented? | F1 depends on this: checkin creates maintenance, but who moves asset to IN_STOCK when maintenance completes? |
| Email templates | Does Brevo support dynamic templates? | F4 needs checkout confirmation email |
| Employee portal routing | Does /my/equipment already exist? | F6 depends on this |

## Time Constraints Assessment
**Deadline:** Not specified
**Type:** None
**Realistic:** Yes — scope is well-defined
**Calendar conflicts:** None identified
**Buffer included:** N/A

## Testing Assessment
**Tests defined:** Yes
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Missing: cancel checkout, edit notes, transfer |
| Integration | Yes | Yes | Good coverage of full lifecycle |
| E2E | No | No | Not needed for MVP |
| UAT | No | No | Should be defined for employee acceptance flow |

**Critical scenarios identified:** Yes — checkout, checkin, accept, unassign guard, GDPR auto-maintenance
**Test data requirements:** Not defined — need seed data for integration tests

## Definition of Done Assessment
**DoD defined:** Partially
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Partially (invariants defined, but no explicit AC list) | Yes |
| Quality gates | No | Missing |
| Sign-off process | No | Missing |
| Training needs | No | Employee acceptance requires user communication |

## Red Flags
- [x] No cancellation flow for checkouts (what if technician makes a mistake?)
- [x] No global "open checkouts" query endpoint (only per-asset)
- [x] Maintenance completion → IN_STOCK transition not verified as existing
- [x] No explicit acceptance criteria list (invariants are close but not formal)
- [ ] GDPR template hardcoded vs configurable — already addressed (configurable per company)

## Open Questions — RESOLVED

1. **Cancel checkout** — **RESOLVED:** Yes, allow cancel with `CANCELLED` status. Record preserved for audit trail with `cancelled_at`, `cancelled_by`, `cancel_reason`. Asset restored to pre-checkout state.
2. **Global checkouts view** — **RESOLVED:** Yes, `GET /checkouts` endpoint + dashboard widget for pending acceptances / open checkouts.
3. **Maintenance → IN_STOCK** — **RESOLVED:** Automatic transition. `MaintenanceCompleted` event triggers asset → `IN_STOCK`. New event handler to be implemented.
4. **Checkout without prior assignment** — **RESOLVED:** Allow direct checkout from `IN_STOCK`. System auto-assigns to target employee then creates checkout.
5. **Acceptance timeout** — **RESOLVED:** Configurable at company settings level (`checkout_acceptance_reminder_days`, default 3). Celery periodic task sends reminders.
6. **Condition tracking** — **RESOLVED:** 5-level enum + **optional** free-text description field (`condition_out_notes`, `condition_in_notes`).

## Checklist Summary
### Business Alignment: 2/4 passed
### Content Completeness: 7/9 passed
### Use Case Coverage: 5/12 passed (7 missing use cases identified)
### Entity States: 3/5 passed
### Collateral Impact: 8/11 identified
### Slicing: 4/4 passed
### Time Constraints: N/A (no deadline)
### Testing: 3/4 passed
### Definition of Done: 1/4 passed

## Recommendations — ALL INCORPORATED

All 6 recommendations have been incorporated into the updated requirements document:
1. Cancellation flow added (CANCELLED status, audit trail, cancel_reason)
2. Global checkouts endpoint added (`GET /checkouts`)
3. Maintenance → IN_STOCK automation added as new feature F3
4. Acceptance criteria covered by updated invariants and test cases
5. Direct checkout from IN_STOCK (auto-assign) added
6. Acceptance timeout config in company settings added
