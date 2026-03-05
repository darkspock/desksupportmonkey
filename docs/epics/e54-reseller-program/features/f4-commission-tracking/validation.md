# Feature Validation Report

**Document:** F4 — Commission Tracking
**Type:** Feature
**Parent Epic:** [../../requirements.md](../../requirements.md) (E54 — Reseller Program)
**Date:** 2026-03-03
**Status:** Valid

## Epic Reference Check
- [x] Parent epic referenced (`../../requirements.md`)
- [x] Epic exists and is accessible
- [x] Feature scope aligns with epic slice (F4 in slicing.md — "Commission Tracking", Complexity M)

## Feature-Specific Validation

### Entities

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| ResellerCommission | Create (webhook), Read (list/detail), Update (status transitions) | pending → confirmed → paid; clawed_back | Not specified (soft delete implied — `clawed_back` status) |

**State machine is well-defined:**
- `pending` → `confirmed` (Celery beat, after 30 days)
- `confirmed` → `paid` (F5 — payout)
- Any status → `clawed_back` (refund webhook)
- If already `paid` → `clawed_back` + negative record

### Technical Claims Verification

| Claim | Status | Notes |
|-------|--------|-------|
| `StripeWebhookDispatcher` exists (E43) | **Verified** | `src/company_bc/company/application/services/stripe_webhook_dispatcher.py` — extensible via if/elif in `_route()` |
| `invoice.payment_succeeded` handler exists | **Verified** | Currently dispatches `RestoreBillingCommand` (line 108-111) |
| `charge.refunded` handler exists | **Not found** | Needs implementation from scratch — new elif block in dispatcher |
| `Reseller.commission_pct` field | **Verified** | `src/reseller_bc/reseller/domain/entities.py` — int, default 20, validated 0-100 |
| `ResellerClient.reseller_id` + `company_id` | **Verified** | `src/reseller_bc/client/domain/entities.py` — both present with FK constraints |
| Celery beat configuration | **Verified** | `core/celery.py` — 14+ tasks using `@celery_app.task` pattern |
| Commission subdomain | **Not found** | Needs creation as `src/reseller_bc/commission/` |

### Acceptance Criteria Review

All 14 acceptance criteria are:
- [x] Testable (each has a clear pass/fail condition)
- [x] Unambiguous (specific calculations, statuses, endpoints defined)
- [x] Non-overlapping with other features (F5 boundary is clear)

### Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `StripeWebhookDispatcher._route()` | Integration | Add `charge.refunded` handler + extend `invoice.payment_succeeded` | Add elif blocks — backward compatible |
| `core/celery.py` | Configuration | Add `confirm-commissions` beat schedule | Append to `beat_schedule` dict |
| `core/tasks/` | New file | Create `commission.py` task module | New file, no conflicts |
| Reseller dashboard query | Query change | Return real commission totals | Modify `get_reseller_dashboard.py` |
| Alembic | Migration | New `reseller_commissions` table | New migration file |

### Scope Gaps Identified

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| No mention of duplicate webhook protection | Low | `StripeWebhookDispatcher` already has idempotency check via `is_stripe_event_processed()` — commissions should also key on `stripe_invoice_id` uniqueness |
| Demo account payment exclusion | Info | Requirement correctly specifies "Demo account payments (Free plan) do not generate commissions" — design must check `ResellerClient.is_demo` or plan type |
| No mention of bulk delete for commissions | Info | Appropriate — commissions are financial records and should never be deleted |
| No archive/purge strategy | Low | Acceptable for now — financial records should be retained indefinitely |

### Time Constraints

**Deadline:** Not specified (follows epic sequencing)
**Type:** None
**Calendar conflicts:** None

## Recommendations

1. **Ensure `stripe_invoice_id` is unique** on the commissions table to prevent duplicate commission creation if webhook is replayed (belt-and-suspenders alongside dispatcher idempotency).
2. **Verify Stripe event payload structure** for `charge.refunded` — specifically how to extract the original invoice ID for matching to the commission record.
3. **Design must address the `invoice.payment_succeeded` integration carefully** — the dispatcher already handles this event for `RestoreBillingCommand`. The commission hook must coexist (not replace) the existing billing handler.

## Checklist Summary
- **Epic Reference:** 3/3 passed
- **Entity Coverage:** 1/1 complete
- **State Machine:** Fully defined (4 states, all transitions specified)
- **Technical Claims:** 5/7 verified (2 expected gaps — `charge.refunded` handler and commission subdomain need creation)
- **Collateral Impact:** Identified and manageable
- **Acceptance Criteria:** 14/14 testable

**Verdict: Valid** — Feature is well-defined and ready for design phase. All external dependencies (Stripe dispatcher, Celery, Reseller/Client entities) are verified and available.
