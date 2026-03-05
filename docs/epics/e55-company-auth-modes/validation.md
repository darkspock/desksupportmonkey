# Requirement Validation Report

**Document:** E55 — Company Login Slug, Multi-Company & Auth Mode (v2 — Identity/Membership Split)
**Date:** 2026-03-02
**Status:** Needs Revision (minor)

## Summary

Significantly improved architecture over v1. The identity/membership split (`users` for identity, `company_users` for per-company membership) is the correct normalization — it eliminates the password/OAuth duplication problem and removes the need for a separate allowlist table. The `membership_only` auth mode elegantly reuses the existing `company_users` table as the access control list.

The document is comprehensive with 31 business rules, 40-entry collateral impact table, a phased migration strategy, and thorough testing scenarios. The main gaps are: (1) business evidence still lacks specific customer data, (2) the collateral impact table doesn't explicitly note that 80+ router files are transitively affected (though most need no code changes), and (3) a few edge cases around the `is_platform_admin` transition need clarification.

**Overall: ready for slicing with minor clarifications.**

---

## Business Alignment Assessment

**Primary Objective:** Churn Reduction / Revenue Enablement
**Contribution:** Clear — unlocks contractor onboarding and multi-company use cases
**KPIs Defined:** Yes — 4 measurable targets
**Justification Type:** Subjective (industry patterns, no customer-specific data)

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | No customer count, ticket volume, or churn data |
| Evidence sources | No | No customer names, support ticket IDs, or survey data |
| Revenue impact | No | No estimate of revenue at risk or revenue unlocked |
| Customer names/tickets | No | Anecdotal references only |

### Experimentation Assessment

**Is this an experiment?** No

**RED FLAGS:**
- [x] Subjective justification detected (and not an experiment)
- [x] Missing revenue/cost impact (and not an experiment)
- [x] No evidence provided (and not an experiment)
- [ ] Experiment without success metrics
- [ ] Experiment without investment limit

> **Note:** KPIs are well-defined and measurable. The gap is in the *evidence* backing the initiative. Adding 2-3 customer-specific data points would strengthen prioritization. This is flagged but does NOT block development if the product owner confirms priority.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| `Company` (modified: +slug, +auth_mode) | C: slug auto-generated, R: by-slug endpoint, U: PATCH slug + PATCH auth_mode, D: N/A (existing lifecycle) | auth_mode: `domain` ↔ `membership_only` — bidirectional with defined side effects | Existing company lifecycle (ACTIVE → SUSPENDED → DEACTIVATED) unchanged |
| `User` (restructured: identity only) | No new CRUD — field redistribution. C/R/U/D unchanged. | Added `is_platform_admin` flag. Removed role/company_id (moved to CompanyUser). `is_anonymized` remains. | Existing GDPR anonymization scoped per company. Identity anonymized only when zero memberships remain. |
| `CompanyUser` (new: membership) | C: auto on domain login + explicit on invite/import, R: via user queries + company switcher, U: role change + dept assignment + activate/deactivate, D: **Not defined** | `is_active`: true ↔ false (bidirectional). Lockout prevention on last admin. | **Not explicitly defined** — is membership removal (hard delete) ever needed, or only deactivation? |
| `MagicLink` (modified: +company_id) | No CRUD changes | Existing lifecycle (created → used/expired) unchanged | Existing TTL expiry |

---

## Missing Use Cases

| # | Use Case | Reason | Priority | Question for Stakeholder |
|---|----------|--------|----------|--------------------------|
| 1 | **CompanyUser hard delete** | Document defines deactivation (is_active=false) but not removal. Can a membership be permanently deleted? E.g., "Remove this contractor entirely" vs. "Deactivate them." | Medium | Should membership removal (hard delete) be supported, or is deactivation sufficient? |
| 2 | **Platform admin creation/management** | `is_platform_admin` replaces SUPER_ADMIN but the document doesn't describe how platform admins are created post-migration. Currently `app.py` line 217 creates super_admin on startup. | Medium | How are new platform admins created? Startup script only, or admin endpoint? |
| 3 | **Platform admin company switcher** | A platform admin may have memberships in companies AND platform access. What does the company switcher show? "Platform view" + company A + company B? | Medium | Should the company switcher include a "Platform" option for platform admins? |
| 4 | **`UserRole.has_access()` with platform admin** | Today `SUPER_ADMIN.has_access(ADMIN)` returns true (level 5 > 4). With `is_platform_admin`, a platform admin inside a company has `company_users.role = admin`. The `has_access` method still works, but platform-level checks need a different mechanism. | Low | Verified: `require_role(UserRole.ADMIN)` + membership role will work. `is_platform_admin` needs a separate `require_platform_admin()` dependency. |
| 5 | **Existing `set-password` endpoint scoping** | `POST /api/v1/auth/set-password` uses `get_current_user()` which returns the user. In the new model, role check must come from membership. Not explicitly mentioned in F2. | Low | This endpoint already works with the composite object since it only needs user identity + role check. Confirm: no slug scoping needed (already authenticated). |
| 6 | **MCP tools tenant context** | 12+ MCP tool files in `adapters/mcp/tools/` use tenant context (`company_id`, `role`). Not listed in collateral impact. | Low | MCP tools likely need no code changes (tenant context populated by `get_current_user`), but should be listed for completeness. |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| `CompanyUser` | Delete strategy not defined | Hard delete (remove membership) or soft delete only (is_active=false)? |
| `CompanyUser` | No "pending" or "invited" state | When admin invites someone, the membership is created immediately as is_active=true. Should there be a "pending_acceptance" state? Or is immediate activation correct? |
| `User.is_platform_admin` | No state transitions defined | Can `is_platform_admin` be revoked? By whom? What happens to their memberships? |
| `Company.slug` | Login behavior when company is deactivated | `/login/{slug}` for a deactivated company — show "Company unavailable" or 404? |

---

## Collateral Impact

### Documented Impact (40 entries) — Codebase Verification

All 40 entries in the collateral impact table were **verified against the codebase**:

- **User entity fields** (company_id, role, department_id, employee_role_id, is_active): confirmed present at lines 14-19
- **UserRole.SUPER_ADMIN**: confirmed present in enum at line 10
- **All command handlers** (change_role, deactivate, activate, assign_department): confirmed they modify user-level fields
- **All query handlers** (get_current_user, list_users, get_user_detail): confirmed they return user with role/company
- **JWT create_token**: confirmed signature `(user_id, company_id, role)` at core/jwt.py line 31
- **Tenant context**: confirmed `set_tenant(company_id, user_id, role)` at core/tenant.py line 19
- **Auth dependencies**: confirmed `get_current_user()` reads user.company_id and user.role

### Transitive Impact Not Individually Listed

The 40-entry table is **accurate but incomplete in enumeration**. The identity/membership split transitively affects **80+ files** because `current_user.company_id` and `current_user.role` are used across all domain routers.

**However:** Most of these 80+ files **need no code changes** if `get_current_user()` returns a composite object that preserves the `.company_id` and `.role` interface. The change is concentrated in:

| Layer | Files Changed | Files Transitively Affected (no code change) |
|-------|---------------|----------------------------------------------|
| Core auth (`dependencies.py`, `tenant.py`) | 2 | 0 |
| Auth commands/queries/services | 12 | 0 |
| Company BC commands/ports | 3 | 0 |
| Audit BC (GDPR) | 2 | 0 |
| Auth routers/schemas | 3 | 0 |
| User routers | 1 | 0 |
| **All other domain routers** | **0** | **65+** (use `current_user.company_id`/`.role` unchanged) |
| MCP tools | 0 | 12+ (use tenant context unchanged) |
| Frontend | 6 | 0 |
| Database migration | 1 | 0 |

**Recommendation:** Add a note to the collateral impact section: "65+ domain routers and 12+ MCP tools transitively depend on `current_user.company_id` and `current_user.role`. These require NO code changes because the composite `get_current_user()` return value preserves these fields."

### SUPER_ADMIN → is_platform_admin Migration (20 files)

Files referencing `UserRole.SUPER_ADMIN` that need updating:

| File | Usage | Action |
|------|-------|--------|
| `src/auth_bc/user/domain/enums.py` | Enum definition | Remove SUPER_ADMIN value |
| `app.py` (line 217) | Creates super_admin on startup | Change to set `is_platform_admin=true` |
| `core/tenant.py` (line 47) | `is_super_admin()` check | Change to check `is_platform_admin` flag |
| `adapters/http/api/super_admin/routers.py` | `require_role(UserRole.SUPER_ADMIN)` | New `require_platform_admin()` dependency |
| `adapters/http/api/vendors/dashboard_router.py` | SUPER_ADMIN role requirement | Update to platform admin check |
| `adapters/mcp/tools/companies.py` | 5 SUPER_ADMIN checks | Update to platform admin check |
| `src/auth_bc/user/application/commands/change_user_role.py` | Prevents SUPER_ADMIN assignment | Remove guard (not a role anymore) |
| `src/auth_bc/user/application/commands/set_password.py` | Admin role check | Update to membership role + platform admin |
| `src/auth_bc/user/application/commands/password_login.py` | ADMIN/SUPER_ADMIN only | Update to ADMIN + platform admin |
| Test files (10) | Fixtures with SUPER_ADMIN role | Update to `is_platform_admin=true` |

**Note:** This is not listed as a separate section in the requirements. Recommend adding a "SUPER_ADMIN Migration" subsection to the collateral impact or business rules.

---

## Slicing Assessment

**Size:** Large (4 features, 40+ directly affected files, database restructuring, frontend changes)
**Slicing needed:** Yes — already sliced into 4 features
**Feature sequencing is well-designed:**

```
F1 (Slug) — independent, can be done first
    ↓
F2 (Identity/Membership Split + Scoped Auth) — depends on F1 for slug infrastructure
    ↓
F3 (Multi-Company Switcher) — depends on F2 for membership model
F4 (Auth Mode) — depends on F2 for scoped auth + membership checks
```

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|-----------------|-----|
| SAML/SSO integration | No | Slug infrastructure supports it later |
| SCIM provisioning | No | Additive on top of membership model |
| Audit log for memberships | No | Future compliance epic — no architectural dependency |
| Bulk invite | No | CSV import already handles bulk; single invite sufficient |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** N/A
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

| Risk | If deadline missed | Mitigation |
|------|-------------------|------------|
| No deadline specified | No immediate risk | Consider defining a target quarter for planning |

---

## Testing Assessment

**Tests defined:** Yes — 16 unit + 16 integration scenarios

| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes (16 scenarios) | Minor: add `is_platform_admin` creation + revocation, slug edge case for names that are all special chars |
| Integration | Yes | Yes (16 scenarios) | Minor: add platform admin login with/without company context, company creation in membership_only mode |
| E2E | Yes | No | Full login flow with slug → auth → switch company → verify context → logout. Recommended for such a foundational change. |
| UAT | Recommended | No | Auth changes affect every user — pilot with 2-3 companies recommended |

**Critical scenarios identified:** Yes — migration verification, backward compatibility, two-step auth flow, GDPR per-company, lockout prevention.
**Test data requirements:** Partially defined — migration needs existing users with various roles for company_users population. Multi-company tests need same identity in multiple companies.

---

## Definition of Done Assessment

**DoD defined:** Yes — 24 checkboxes

| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes (24 items) | Yes — each is testable and specific |
| Quality gates | Partial | "All tests pass" stated; no explicit code review, performance, or architecture check |
| Sign-off process | No | Not defined — who approves the migration? |
| Training needs | No | Auth flow changes affect all users — no communication plan |

---

## Red Flags

- [x] **Business evidence is subjective** — KPIs are measurable but justification lacks customer-specific data. Acceptable if product owner confirms.
- [ ] **CompanyUser delete strategy undefined** — Only deactivation is described. Hard delete may be needed for GDPR "right to erasure" compliance. Currently flagged as medium priority.
- [ ] **`is_platform_admin` lifecycle not fully defined** — Creation (migration + startup script) is described, but revocation, management endpoints, and edge cases (what if last platform admin is removed?) are not.
- [ ] **No E2E test plan** — Given this restructures the foundational auth layer, E2E testing should be mandatory.

---

## Open Questions for Stakeholder

1. **CompanyUser deletion:** Should membership removal (hard delete) be supported, or is deactivation (is_active=false) always sufficient? Consider GDPR right to erasure.
2. **Platform admin management:** How are new platform admins created after migration? Startup script only, or should there be an API endpoint? Can `is_platform_admin` be revoked, and if so, by whom?
3. **Platform admin in company switcher:** When a platform admin has company memberships, should the switcher show a "Platform" option alongside their company memberships?
4. **Login page for deactivated company:** What should `/login/{slug}` show when the company is deactivated (terminal state)? "Company unavailable" message, or 404?
5. **CompanyUser invited state:** When an admin invites someone, the membership is created immediately as active. Should there be a "pending acceptance" state, or is immediate activation correct?
6. **Business evidence:** Are there specific customer requests, support tickets, or churn data that motivated this epic? Even 2-3 data points would strengthen prioritization.

---

## Checklist Summary

### Business Alignment: 2/4 passed
- [x] Objective clearly stated
- [x] KPIs defined with measurable targets
- [ ] Evidence with specific numbers/customers
- [ ] Revenue/cost impact quantified

### Content Completeness: 8/8 passed
- [x] Problem statement with current situation and pain points
- [x] Proposed solution with clear architecture (identity/membership split)
- [x] Domain model with all entities and field mappings
- [x] Features with user stories (4 features, 17 stories)
- [x] API endpoints defined (12 endpoints)
- [x] Business rules comprehensive (31 rules)
- [x] Migration strategy with phased approach and rollback safety
- [x] GDPR interaction defined (per-company scoping, rule 29)

### Use Case Coverage: 7/8 passed
- [x] Two-step auth flow (identity → membership) for all 4 auth methods
- [x] Domain mode auto-create membership on first login
- [x] Membership-only mode reject non-members
- [x] Mode switching with defined side effects
- [x] Company switcher token exchange
- [x] Backward compatibility for unscoped endpoints
- [x] User invite creates identity + membership
- [ ] CompanyUser hard delete / removal not addressed

### Entity States: 3/4 passed
- [x] Company auth_mode transitions defined with side effects
- [x] Company slug lifecycle (creation, update, reserved words, never released)
- [x] CompanyUser activate/deactivate with lockout prevention
- [ ] `is_platform_admin` lifecycle (creation, revocation) incomplete

### Collateral Impact: 3/4 passed
- [x] All auth flow handlers identified and verified against codebase
- [x] Identity/membership split impact on commands, queries, dependencies verified
- [x] Cross-BC impact (audit_bc GDPR, company_bc ports) included
- [ ] Transitive impact on 65+ domain routers and 12+ MCP tools not explicitly noted (though they need no code changes)

### Slicing: 4/4 passed
- [x] Features are logically ordered with clear dependencies
- [x] F1 can start independently
- [x] Scope boundaries well-defined
- [x] Out-of-scope items don't create blocking dependencies

### Time Constraints: 0/1 passed
- [ ] No deadline specified

### Testing: 2/4 passed
- [x] Unit test scenarios defined (16)
- [x] Integration test scenarios defined (16)
- [ ] E2E test scenarios not defined
- [ ] UAT process not defined

### Definition of Done: 2/4 passed
- [x] Acceptance criteria defined (24 checkboxes)
- [x] Criteria are testable and specific
- [ ] Quality gates beyond "tests pass" not defined
- [ ] Sign-off process not defined

---

## Recommendations

1. **Clarify CompanyUser deletion strategy** — Add a business rule: "Memberships can be deactivated (is_active=false) or hard-deleted. Hard delete is needed for GDPR right to erasure. Deactivation is the default admin action; hard delete requires explicit confirmation." Or decide deactivation is always sufficient and document why.

2. **Define `is_platform_admin` lifecycle** — Add business rules for: (a) how new platform admins are created post-migration, (b) whether `is_platform_admin` can be revoked, (c) what happens to company memberships when platform admin status changes. Also add `require_platform_admin()` dependency to collateral impact.

3. **Add transitive impact note** — Add a note to the collateral impact section explaining that 65+ domain routers transitively depend on `current_user.company_id` and `current_user.role` but need NO code changes because the composite return value preserves these fields.

4. **Add SUPER_ADMIN migration detail** — List the 20 files referencing `UserRole.SUPER_ADMIN` that need updating to `is_platform_admin`. This is a significant cross-cutting change that should be explicit.

5. **Add E2E test plan** — Auth restructuring is high-risk. At minimum: login with slug → use app → switch company → verify context changes → logout.

6. **Add business evidence** — Even 2-3 data points would strengthen the business case. Proceed anyway or add data first?
