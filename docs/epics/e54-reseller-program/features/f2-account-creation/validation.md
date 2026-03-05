# Feature Validation Report

**Document:** F2 — Account Creation
**Type:** Feature
**Parent Epic:** [E54 — Reseller Program](../../requirements.md)
**Date:** 2026-03-02
**Status:** Valid

---

## Epic Reference Check

- [x] Parent epic referenced (`../../requirements.md`)
- [x] Epic exists and is accessible
- [x] Feature scope aligns with epic slice (matches F2 in slicing.md)

---

## Summary

F2 is a well-defined feature with clear acceptance criteria, specific technical scope, and sensible boundaries. It introduces one new entity (`ResellerClient`), two account creation flows (demo and normal), a Celery beat task for demo expiry, and three frontend pages. The requirements correctly identify collateral impact (seed data refactor, cross-BC company creation). All key dependencies (F1, company creation service, Celery infrastructure, Free plan defaults) exist and are ready. Minor gaps noted below — none blocking.

---

## Feature-Specific Validation

### Entity: ResellerClient

| Operation | Defined | Notes |
|-----------|---------|-------|
| Create | Yes | Via demo/normal account creation commands |
| Read | Yes | Via client list query |
| Update | No | Not needed — immutable link entity |
| Delete | No | Not addressed (see gap below) |
| List | Yes | `GET /reseller/clients` and `GET /admin/resellers/:id/clients` |

**States:** No state machine — `ResellerClient` is a stateless link entity. Source enum (`manual`, `referral`) is set at creation and immutable. Appropriate.

**Delete Strategy:** Not specified. This is a minor gap:
- What happens to `ResellerClient` records when a demo account is purged after 44 days? Should the link record be deleted or retained for historical tracking?
- What happens if a company is deleted independently (e.g., by super admin)?

**Recommendation:** Retain `ResellerClient` records even after company purge (for historical client_count accuracy). The company_id becomes a dangling FK, but the record serves audit/history purposes. Alternatively, soft-delete. This should be clarified but is not blocking.

### Demo Account Flow

| Aspect | Defined | Notes |
|--------|---------|-------|
| Creation endpoint | Yes | `POST /reseller/clients/demo` |
| Seed data population | Yes | Reuses `make seed` logic |
| Free plan assignment | Yes | Company model defaults to "free" — works automatically |
| Admin credentials shown once | Yes | Acceptance criterion defined |
| Demo flag in client list | Yes | "Demo accounts are marked as demo in the client list" |
| Auto-expiry (14 days) | Yes | Celery beat task, daily check |
| Data retention (30 days) | Yes | Purge after 44 days (14 + 30) |
| Suspended reseller blocked | Yes | 403 for suspended resellers |

**Gaps:**
1. **Demo flag storage**: How is a company marked as "demo"? The `ResellerClient` doesn't have an `is_demo` field, and the `Company` entity doesn't have one either. The requirements say "clearly marked as demo" but don't specify the mechanism.
   - **Options:** (a) Add `is_demo: bool` to `ResellerClient`, (b) add `is_demo: bool` to Company, (c) infer from creation source + Free plan + age. Option (a) is simplest and keeps it in reseller_bc.
   - **Recommendation:** Add `is_demo: bool` field to `ResellerClient`. Design phase can decide.

2. **Admin credentials format**: "Admin credentials are shown to the reseller once at creation time" — what credentials exactly? If using the existing `CreateCompanyCommand` with an admin email, it sends a magic link. For demo accounts without an admin email, how does the reseller access the demo? Is a temporary password generated?
   - **Recommendation:** Clarify in design phase. Likely: generate a random password for the demo admin user, return it in the response body. The reseller shares it with the prospect.

3. **Demo account limit**: No limit on how many demo accounts a reseller can create. Is this intentional? Could be abused (spam demo creation consuming resources).
   - **Recommendation:** Consider a limit (e.g., max 5 active demos per reseller). Not blocking — can be added later.

### Normal Account Flow

| Aspect | Defined | Notes |
|--------|---------|-------|
| Creation endpoint | Yes | `POST /reseller/clients/account` |
| Parameters | Yes | Company name, admin email, plan |
| Admin onboarding | Yes | Standard magic link flow |
| Attribution | Yes | ResellerClient with source=manual |
| First-wins rule | Yes | "A company can only be linked to one reseller" |

**Gaps:**
1. **Plan selection**: The reseller "specifies plan (defaults to Free)". But plan selection implies billing. Does creating a normal account with a paid plan trigger Stripe subscription creation? The existing `CreateCompanyCommand` creates a Stripe customer. This needs clarification.
   - **Recommendation:** For this feature, default to Free plan only. Plan upgrades happen through the normal billing flow. Simplifies F2 significantly.

2. **Email domain validation**: The existing `CreateCompanyCommand` validates email domains. When a reseller creates an account with `admin_email`, what email domain is set for the company? Is it derived from the admin email?
   - **Recommendation:** Design phase should clarify — likely auto-derive domain from admin email.

### Celery Beat Tasks

| Task | Defined | Schedule | Notes |
|------|---------|----------|-------|
| Demo suspension | Yes | Daily | Suspend companies where demo created_at > 14 days |
| Demo data purge | Yes | Daily | Purge company data where demo created_at > 44 days |

**Gaps:**
1. **Purge scope**: "Purges data after 44 days" — what exactly is purged? The entire Company record? All associated data (users, assets, requests)? Or just the company status change?
   - The epic says "company is suspended, data retained for 30 more days, then purged"
   - **Recommendation:** Clarify in design: likely cascade delete the company and all associated data. This has significant collateral impact across multiple BCs.

2. **Notification**: Should the reseller be notified before demo expiry? (e.g., 3-day warning email)
   - **Recommendation:** Not in scope for F2 (nice-to-have for future).

### Collateral Impact

| Component | Impact | Verified in Codebase |
|-----------|--------|---------------------|
| Seed data script (`scripts/seed_demo_data.py`) | Refactor to accept `company_id` | Yes — currently hardcoded for 3 companies, no parameter support |
| Company creation service (`CreateCompanyCommand`) | Reuse via port from reseller_bc | Yes — exists, accepts name, email_domains, admin_email, id |
| Celery beat schedule (`core/celery.py`) | Add 2 new periodic tasks | Yes — 14 tasks exist, extensible pattern |
| Free plan default | Used for demo accounts | Yes — Company model defaults to "free" |
| Dashboard `client_count` | Return real data instead of placeholder | Yes — F1 dashboard query exists, currently returns 0 |

### Frontend Scope

| Page | Defined | Notes |
|------|---------|-------|
| Client list (`ClientsPage.tsx`) | Yes | Table with demo/normal distinction |
| Demo creation form (`CreateDemoPage.tsx`) | Yes | Form to trigger demo account creation |
| Normal account form (`CreateAccountPage.tsx`) | Yes | Form with company name, admin email, plan |

**Gaps:**
1. **Navigation update**: The `ResellerLayout.tsx` sidebar needs to add "Clients" and creation links. Not mentioned explicitly but implied.
2. **Credentials display**: After demo creation, how are admin credentials displayed? Modal? One-time toast? Dedicated success page? Not specified.
   - **Recommendation:** Design phase decides — likely a success modal with copy-to-clipboard.

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Realistic:** Yes — F2 is the natural next step after F1

---

## Red Flags

- [ ] No critical red flags identified

---

## Open Questions for Stakeholder

1. **Demo flag storage**: Where should the "is_demo" flag live — on `ResellerClient` or on `Company`? (Recommended: `ResellerClient`)
2. **Demo admin credentials**: Should demo accounts have a generated password, or use a different access mechanism?
3. **Demo account limit**: Should there be a max number of active demos per reseller?
4. **Normal account plan**: Can resellers create accounts on paid plans, or should F2 default to Free only (with upgrade via normal billing flow)?
5. **Demo purge scope**: Does "purge" mean cascade delete the entire company and all data across all BCs?
6. **ResellerClient on purge**: Should the `ResellerClient` record be deleted or retained when a demo company is purged?

---

## Checklist Summary

### Epic Reference: 3/3 passed
### Entity Coverage: 4/5 passed (delete strategy undefined)
### Acceptance Criteria: 17/18 passed (demo flag mechanism unclear)
### Collateral Impact: 5/5 identified
### Frontend Scope: 3/3 defined
### Time Constraints: N/A (no deadline)

---

## Recommendations

1. **Proceed to design** — the requirements are solid and all gaps are implementation-level decisions that the design phase can resolve.
2. **Add `is_demo` field** to `ResellerClient` entity during design.
3. **Clarify demo credential mechanism** in design (generated password shown once vs. magic link).
4. **Define purge behavior** precisely in design — cascade scope, FK handling, notification.
5. **Consider Free-only for F2** normal accounts — plan selection adds billing complexity better deferred.
6. **Add demo limit** as an optional enhancement (not blocking).
