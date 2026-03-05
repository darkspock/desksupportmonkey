# Feature Validation Report

**Document:** F5 — Payout Requests
**Type:** Feature
**Parent Epic:** [../../requirements.md](../../requirements.md) (E54 — Reseller Program)
**Date:** 2026-03-03
**Status:** Valid

## Epic Reference Check

- [x] Parent epic referenced — `../../requirements.md`
- [x] Epic exists and is accessible
- [x] Feature scope aligns with epic slice — F5 maps directly to epic's "Payout Requests" feature and `ResellerPayout` entity

## Feature-Specific Validation

### Entity: ResellerPayout

| Operation | Defined | Notes |
|-----------|---------|-------|
| Create | Yes | `POST /reseller/payouts` — creates with `status = requested` |
| Read | Yes | `GET /reseller/payouts` (reseller), `GET /admin/payouts` (admin) |
| Update | Yes | `PATCH /admin/payouts/:id` — approve/reject/mark-paid |
| Delete | No | Not needed — payouts are never deleted (correct for financial records) |
| List | Yes | Both reseller and admin endpoints with pagination |

### State Machine: PayoutStatus

| From | To | Trigger | Side Effects |
|------|----|---------|--------------|
| *(new)* | `requested` | Reseller clicks "Request Payout" | Amount locked = available balance at time of request |
| `requested` | `approved` | Super admin approves | `processed_at` and `processed_by` set |
| `requested` | `rejected` | Super admin rejects | `notes` set; balance unlocked for next request |
| `approved` | `paid` | Super admin marks as paid | `payment_reference` set; associated confirmed commissions → `paid` |

**Assessment:** State machine is well-defined. All transitions are unidirectional with clear triggers and side effects.

**Note:** There's no `approved → rejected` transition defined — once approved, the only path is to `paid`. This seems intentional (approval is a commitment).

### Inverse Operations

| Action | Inverse | Covered |
|--------|---------|---------|
| Request payout | Cancel payout | **Not specified** — but acceptable since rejection serves this purpose |
| Approve payout | Reject already-approved | **Not specified** — see note above |
| Mark as paid | Reverse payment | **Not specified** — acceptable; actual money transfer is external |

### Acceptance Criteria Assessment

All 16 acceptance criteria are:
- [x] Testable — each maps to a specific API behavior or UI element
- [x] Unambiguous — clear status codes (400, 403) and status transitions specified
- [x] Complete — covers reseller flow, admin flow, edge cases (suspended, below threshold)

### Dependency Check

| Dependency | Status | Available |
|------------|--------|-----------|
| F4 Commission Tracking | Done | Yes — all required methods exist |
| `ResellerCommission` entity | Exists | Yes — but needs `mark_as_paid()` method (minor addition) |
| `GetAvailableBalanceQuery` | Exists | Yes — formula: `confirmed - paid + clawbacks` |
| `Reseller.min_payout_cents` | Exists | Yes — field with default 5000 |
| Commission repo `.sum_*` methods | Exist | Yes — all three SUM methods implemented |

### Codebase Readiness

| Component | Current State | Action for F5 |
|-----------|---------------|---------------|
| `src/reseller_bc/payout/` | Does not exist | Create entire payout subdomain |
| `ResellerCommission.mark_as_paid()` | Missing | Add domain method for `CONFIRMED → PAID` transition |
| Reseller routes | No payout endpoints | Add `GET/POST /reseller/payouts` |
| Admin routes | No payout endpoints | Add `GET /admin/payouts`, `PATCH /admin/payouts/:id` |
| Frontend | No payout pages | Create `PayoutsPage.tsx` and `PayoutManagementPage.tsx` |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `ResellerCommission` entity | Modification | Add `mark_as_paid()` method | Backward-compatible addition |
| Commission repository | Read | F5 uses existing SUM queries | No changes needed |
| Available balance query | Read | F5 uses it to calculate payout amount | No changes needed |
| Reseller dashboard | Update | Show pending payout status | Minor update to dashboard query |
| Admin reseller routes | Extension | New payout management endpoints | Add to existing router |
| Reseller routes | Extension | New payout endpoints | Add to existing router |
| Frontend nav | Extension | Add "Payouts" nav item to sidebar | Minor update to ResellerLayout |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Realistic:** Yes — Complexity rated S (Small), all dependencies in place

## Testing Assessment

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (in epic) | Feature-level test scenarios not detailed, but straightforward from AC |
| Integration | Yes | Yes (in epic) | Payout request → approve → mark paid flow explicitly listed |
| E2E | No | No | Not needed for S-complexity feature |
| UAT | No | No | Manual verification sufficient |

**Critical scenarios identified:** Yes
- Request payout with insufficient balance (400)
- Suspended reseller cannot request (403)
- Approve → mark as paid marks commissions as paid
- Reject → immediate re-request
- Balance locking (concurrent payout prevention)

## Red Flags

None identified.

## Open Questions for Stakeholder

1. **Concurrent payout requests:** Should the system prevent a reseller from having multiple `requested` or `approved` payouts simultaneously? The requirement says "locks the current balance" but doesn't explicitly say "one active payout at a time." **Recommendation:** Prevent creating a new payout while one is `requested` or `approved` — simplifies balance calculation and prevents confusion.

2. **Admin payout listing scope:** The requirement defines `GET /admin/payouts` as a flat list of all payouts. Should there also be filtering by reseller, or is the existing `GET /admin/resellers/:id/commissions` pattern (per-reseller) sufficient? **Recommendation:** Support both — flat admin list with optional `?reseller_id=` filter, plus per-reseller view.

## Checklist Summary

### Epic Reference: 3/3 passed
### Content Completeness: 5/5 passed
### Entity States: 4/4 passed
### Collateral Impact: 7/7 identified
### Testing: 4/4 scenarios covered

## Recommendations

1. **Add a "one active payout" guard** — prevent creating a new payout request while one is in `requested` or `approved` status. This is implied by the "locks the current balance" requirement but should be explicit in the design.
2. **Add `mark_as_paid()` to `ResellerCommission` entity** — this is a small backward-compatible addition needed during F5 implementation.
3. **Proceed to design phase** — the requirement is complete and ready for `/requirement-design`.
