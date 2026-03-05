# Requirement Validation Report

**Document:** E54 — Reseller Program
**Date:** 2026-03-02
**Status:** Needs Revision (minor)

## Summary

Strong epic with well-defined domain model, clear business rules, and good separation of concerns (dedicated `reseller_bc`). The document is implementation-ready for most features. A few gaps need attention: missing CRUD operations on some entities, one incorrect Stripe event name, missing state transitions for `ResellerCommission`, and some edge cases around demo account lifecycle and commission disputes. None are blockers — all are clarifications.

## Business Alignment Assessment

**Primary Objective:** Revenue (new acquisition channel)
**Contribution:** Clear — reseller channel reduces CAC and provides organic distribution
**KPIs Defined:** Yes
**Justification Type:** Objective with market evidence

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | Yes | 20 resellers / 30% of new accounts / 10% conversion |
| Evidence sources | Partial | Industry references (Freshworks, Zendesk) but no DSM-specific data (no pilot resellers, no letters of intent) |
| Revenue impact | Implicit | Commission is a cost, but CAC reduction not quantified |
| Customer names/tickets | No | No specific reseller candidates named |

**RED FLAGS:**
- [ ] Subjective justification detected
- [ ] Missing revenue/cost impact
- [x] No evidence provided — industry benchmarks are good but no DSM-specific pipeline (acceptable for a new channel with no prior data)
- [ ] Experiment without success metrics
- [ ] Experiment without investment limit

> **Assessment:** KPIs are reasonable for a new channel. The lack of DSM-specific evidence is expected — there are no resellers yet. Consider framing this as an **experiment** with a pilot group of 3-5 resellers and clear kill criteria.

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| `Reseller` | C ✅ R ✅ U ✅ D ⚠️ L ✅ | `active`, `suspended`, `deactivated` ✅ | Not specified |
| `ResellerClient` | C ✅ R ✅ U ❌ D ❌ L ✅ | No states (link entity) ✅ | Not specified |
| `ResellerCommission` | C ✅ R ✅ U ⚠️ D ❌ L ✅ | `pending`, `confirmed`, `paid` ✅ | Not specified |
| `ResellerPayout` | C ✅ R ✅ U ✅ D ❌ L ✅ | `requested`, `approved`, `paid`, `rejected` ✅ | Not specified |

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Delete/deactivate a reseller client link | What if a company switches away from a reseller? Client cancels? | Low | Can a reseller-client link be severed? Or is it permanent for historical tracking? |
| Reseller profile update | Reseller can't edit their own `company_name`, `tax_id` | Medium | Should resellers be able to edit their profile, or is it super_admin only? |
| Demo account cleanup/expiry | Demo accounts created by resellers sit on Free plan forever | Low | Should demo accounts auto-expire or have a TTL? Or are they just regular Free accounts? |
| Commission dispute | A reseller disagrees with a commission amount or status | Low | Is there a dispute flow, or do they just contact support? |
| Refund handling | Client gets a Stripe refund after commission was confirmed | High | Should confirmed commissions be clawed back on refund? Need to handle `charge.refunded` webhook |
| Reseller deletes own account | GDPR — reseller wants to be forgotten | Low | Data retention policy for resellers? |
| Bulk commission confirmation | 30-day window expires, pending → confirmed | Medium | Is this a cron job? Celery beat task? Triggered on read? |
| Stripe event mismatch | Epic says `invoice.paid` but codebase uses `invoice.payment_succeeded` | High | The Stripe webhook dispatcher at `stripe_webhook_dispatcher.py:108` handles `invoice.payment_succeeded`, NOT `invoice.paid`. The epic must match the actual event name. |

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| `Reseller` | Transition triggers and side effects | What triggers `active` → `suspended`? Manual super_admin action only? Or automatic on policy violation? |
| `Reseller` | Delete strategy | Soft delete (set `deactivated`) or hard delete? The doc says "deactivated = can't log in, clients remain linked" — this is effectively soft delete, but should be explicit. |
| `ResellerCommission` | `pending` → `confirmed` trigger | Document says "after 30 days" but doesn't specify the mechanism. Cron job? Lazy check on read? Celery beat task? |
| `ResellerCommission` | Missing `cancelled`/`clawed_back` status | What happens if the client gets a refund? Commission should be reverted. |
| `ResellerPayout` | `rejected` → next state? | Can a rejected payout be re-requested? Or does the reseller create a new payout request? |
| `ResellerPayout` | `approved` → `paid` timing | Is there a time limit? Can it stay in `approved` indefinitely? |
| `ResellerClient` | Immutability | Can source change? Can a `referral` client be re-attributed to `manual`? Document says "first attribution wins" which implies immutable, but should be explicit. |

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| Registration flow (`register_company`) | Integration | Add referral code check on registration | Modify `adapters/http/api/registration/routers.py` |
| Stripe webhook dispatcher | Integration | Add commission creation hook on `invoice.payment_succeeded` | Modify `stripe_webhook_dispatcher.py` — **Note: epic says `invoice.paid` but codebase uses `invoice.payment_succeeded`** |
| Stripe webhook dispatcher | Integration | Handle `charge.refunded` for commission clawback | New handler needed (currently not handled) |
| Super admin UI | New pages | Reseller management, payout approval | New React pages under `/admin/resellers/*` |
| Frontend router | New app section | Entire `/reseller/*` mini-app | Separate React app or same app with dual auth context |
| Database | New tables | 4 tables + migration | New alembic migration |
| Seed data (`make seed`) | Refactor | Must accept `company_id` parameter | Modify seed command to be reusable |
| Frontend auth context | Architecture | Reseller JWT vs User JWT | Need to decide: same React app with two auth providers, or separate build? |
| Google/Microsoft OAuth config | Config | Reseller OAuth uses same client IDs or different? | If same OAuth app, callback URLs must handle both user and reseller flows |
| Navigation / sidebar | UI | Super admin sidebar needs "Resellers" section | Add nav items + route guards |
| CORS / API routing | Infrastructure | `/reseller/*` endpoints need separate auth middleware | New FastAPI router with reseller dependency injection |

## Slicing Assessment

**Size:** Large (new bounded context, new auth system, new frontend app, webhook integration)
**Slicing needed:** Yes — recommend 5 features as already defined
**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| White-label | No | Explicitly deferred |
| Stripe Connect | No | Manual payouts for now |
| Self-registration | No | Manual onboarding first |
| Refund handling | Yes | Refunds can happen from day 1 — need at least a basic strategy |

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** N/A — no deadline set
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| N/A | No deadline defined | Consider setting a soft target for MVP (F1+F2+F3) vs full (F4+F5) |

## Testing Assessment

**Tests defined:** Partially
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | Commission rounding, balance calc, referral code, status transitions, JWT |
| Integration | Yes | Yes | OAuth login, account creation, webhook → commission, payout flow, referral |
| E2E | Yes | No | Full reseller journey: login → create client → client pays → commission appears → request payout |
| UAT | Yes | No | No UAT process defined — who tests the reseller portal? |

**Critical scenarios identified:** Mostly — missing refund and concurrent payout scenarios
**Test data requirements:** Not defined — need mock Stripe events, mock OAuth tokens

## Definition of Done Assessment

**DoD defined:** Yes
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | 13 checkboxes, clear and testable |
| Quality gates | Partial | Tests mentioned, but no performance/security gates |
| Sign-off process | No | Who approves the reseller portal? Super admin? Product? |
| Training needs | No | Will resellers need documentation? Onboarding guide? |

## Red Flags

- [x] **Stripe event name mismatch** — Epic says `invoice.paid` but the codebase handles `invoice.payment_succeeded`. Must align before implementation.
- [x] **No refund handling** — If a client gets a refund after commission was confirmed, the reseller keeps the commission. This is a financial risk.
- [x] **Commission confirmation mechanism undefined** — "After 30 days" but no trigger mechanism specified (cron? lazy?). This is critical for the commission lifecycle.
- [ ] Frontend architecture unclear — same React app or separate build for reseller portal?
- [ ] OAuth callback routing — same OAuth app credentials for both users and resellers, or separate?

## Open Questions for Stakeholder

1. **Stripe event name:** The codebase uses `invoice.payment_succeeded`, not `invoice.paid`. Should we update the epic, or add a new handler for `invoice.paid`?
2. **Refund clawback:** If a client gets refunded, should the commission be reversed? If yes, need a `clawed_back` status and `charge.refunded` webhook handler.
3. **Commission confirmation mechanism:** Cron job (Celery beat) that runs daily and confirms commissions older than 30 days? Or lazy check on dashboard read?
4. **Reseller profile editing:** Can resellers edit their own `company_name` and `tax_id`, or is it super_admin only?
5. **Frontend architecture:** Should the reseller portal be part of the existing React app (with a separate auth context) or a standalone build?
6. **OAuth credentials:** Do resellers use the same Google/Microsoft OAuth app as regular users, or separate credentials?
7. **Demo account lifecycle:** Do demo accounts have an expiry, or do they live as Free accounts indefinitely?
8. **Payout rejection:** After a payout is rejected, can the reseller request again immediately with the same balance, or is there a cooldown?

## Checklist Summary

### Business Alignment: 3/4 passed
- [x] Objective aligned with company goals
- [x] KPIs defined with targets
- [x] Evidence provided (industry benchmarks)
- [ ] DSM-specific evidence (no pilot data — acceptable for new channel)

### Content Completeness: 7/8 passed
- [x] Problem statement clear
- [x] Solution overview defined
- [x] Domain model with entities and fields
- [x] User stories per feature
- [x] API endpoints defined
- [x] Business rules documented (13 rules)
- [x] Scope clearly defined (in/out)
- [ ] Missing mechanism for commission confirmation (cron vs lazy)

### Use Case Coverage: 5/8 passed
- [x] Account creation (demo + normal)
- [x] Referral attribution
- [x] Commission tracking
- [x] Payout lifecycle
- [x] Super admin management
- [ ] Refund / commission clawback
- [ ] Commission confirmation trigger
- [ ] Reseller profile self-edit

### Entity States: 3/4 passed
- [x] Reseller statuses defined
- [x] Payout statuses defined
- [x] Commission statuses defined
- [ ] Missing transition triggers and side effects documentation

### Collateral Impact: 4/6 passed
- [x] Registration flow impact identified
- [x] Stripe webhook impact identified
- [x] Super admin UI impact identified
- [x] Database impact identified
- [ ] Stripe event name mismatch not caught
- [ ] Refund webhook not considered

### Slicing: 3/3 passed
- [x] Size assessed as large
- [x] Already sliced into 5 features
- [x] Out of scope clearly defined

### Time Constraints: 1/1 passed
- [x] No deadline — acceptable for a new channel (recommend setting soft target)

### Testing: 2/4 passed
- [x] Unit test scenarios identified
- [x] Integration test scenarios identified
- [ ] E2E scenarios not defined
- [ ] UAT process not defined

### Definition of Done: 2/4 passed
- [x] Acceptance criteria testable
- [x] Core quality gates (tests pass, security isolation)
- [ ] Sign-off process not defined
- [ ] Training/documentation needs not addressed

## Recommendations

1. **Fix Stripe event name** — Change `invoice.paid` to `invoice.payment_succeeded` throughout the epic to match the existing codebase. This is a factual error.
2. **Add refund handling strategy** — Even if minimal: "On `charge.refunded`, mark the corresponding commission as `clawed_back` and deduct from available balance. If already paid out, create a negative commission record." This is a financial risk that should be addressed.
3. **Define commission confirmation mechanism** — Recommend: Celery beat task running daily that queries `ResellerCommission` where `status = pending` and `created_at < now - 30 days`, then updates to `confirmed`. Simple, reliable, auditable.
4. **Clarify frontend architecture** — Recommend: same React app, separate route tree under `/reseller/*`, with a `ResellerAuthProvider` context that checks for `type: reseller` JWT. Avoids a separate build/deploy pipeline.
5. **Consider experiment framing** — Since there are no existing resellers, frame this as an MVP experiment: build F1+F2+F3 first (portal + account creation + referral), then F4+F5 (commissions + payouts) once you have 3+ active resellers. This reduces initial scope.
