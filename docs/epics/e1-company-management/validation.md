# Requirement Validation Report

**Document:** E1 - Company Management
**Date:** 2026-02-15
**Type:** Epic
**Status:** Valid (with observations)

---

## Summary

E1 Company Management is well-scoped with 6 user stories covering company CRUD, email domains, status management, departments, user management, and initial admin assignment. All entities are well-defined with clear acceptance criteria. A few gaps exist around cascading effects of status changes and edge cases.

---

## Business Alignment Assessment

**Primary Objective:** Enable multi-company SaaS operation
**Contribution:** Critical — without E1, no company can be properly configured, no users can be managed, and email domain matching remains a stub
**KPIs Defined:** No (backoffice/admin epic — no direct revenue KPI)
**Justification Type:** Objective — E2-E6 all require properly configured companies and users

E1 is the first business-value epic. It transforms the platform from a dev prototype into a usable multi-tenant system.

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|---|---|---|---|
| Company | C: Yes, R: Yes (list+detail), U: Yes, D: No (status management instead) | active/suspended/deactivated | Status-based (deactivation, no physical delete) |
| CompanyEmailDomain | C: Via company create/update, R: Via company detail, U: Via company update, D: Via company update | None (active by association) | Cascade with company update |
| Department | C: Yes, R: Yes (list+detail), U: Yes, D: Soft delete | is_active (boolean) | Soft delete (is_active=false) |
| User (extension) | C: Via magic link (E0), R: Yes (list+detail), U: Yes (role, department, status), D: No (deactivation) | is_active (boolean) | Deactivation (is_active=false) |

### Gaps Found

| Gap | Severity | Recommendation |
|---|---|---|
| Company physical delete not defined | Low | Correct — companies should never be physically deleted, status management is the right pattern |
| CompanyEmailDomain has no independent CRUD | Low | Acceptable — managed through company endpoints to maintain consistency |
| User creation not in E1 | Info | Correct — users are auto-created on first magic link login (E0). E1 only manages existing users |
| No user search across companies for super admin | Medium | Super admin might need to find a user across all companies. Consider adding `GET /api/v1/admin/users?email=...` or defer to E5 (Admin Dashboard) |
| Department deletion cascade not fully specified | Medium | When department is soft-deleted, what happens to users? Recommend: set department_id to NULL (orphan users) |

**Verdict:** All gaps are manageable. The medium-severity ones should be documented as decisions before implementation.

---

## Missing State Information

| Entity | Missing Info | Recommendation |
|---|---|---|
| Company | State transitions diagram | Transitions are defined in US-E1-003 but should be documented as a formal state machine |
| Department | No lifecycle states beyond active/inactive | Sufficient for E1 scope |

### Company State Machine

```
        ┌──────────┐
        │  active   │
        └────┬──┬───┘
   suspend   │  │  deactivate
        ┌────▼──│───┐        ┌──────────────┐
        │suspended│──────────►│ deactivated  │
        └────┬───┘ deactivate └──────────────┘
   reactivate│                (terminal state)
        ┌────▼──────┐
        │  active    │
        └────────────┘
```

Valid transitions:
- active → suspended (reversible)
- active → deactivated (permanent)
- suspended → active (reactivation)
- suspended → deactivated (permanent)
- deactivated → (none — terminal state)

---

## Use Case Coverage

| Pattern | Covered | Notes |
|---|---|---|
| CRUD | Yes | Company, Department, User (read/update) |
| Lifecycle | Yes | Company status management |
| State Machine | Yes | Company status transitions |
| Bulk Operations | No | Could add bulk user import later (not needed for E1) |
| Reporting | No | E5/E6 scope |
| Role-Based Access | Yes | Super admin vs admin separation clear |
| Multi-Tenancy | Yes | Department and user endpoints scoped |

### Missing Use Cases

| Use Case | Priority | Recommendation |
|---|---|---|
| UC: Reactivate company | Low | Covered by reverse transition (suspended → active) in US-E1-003 |
| UC: Transfer user between companies | Low | Edge case, defer to future. Super admin can deactivate + recreate |
| UC: Bulk domain validation | Low | What if admin adds a domain that has existing users in another company? Should validate on add |
| UC: View company as super admin (with users) | Medium | GET /companies/{id} should include user count, department count. Listed in acceptance criteria |

---

## Inverse Operation Check

| Action | Inverse | Status |
|---|---|---|
| Create company | Deactivate company | Defined (US-E1-003) |
| Add email domain | Remove email domain | Via PUT (US-E1-001) |
| Suspend company | Reactivate company | Defined (US-E1-003) |
| Create department | Delete department (soft) | Defined (US-E1-004) |
| Promote user role | Demote user role | Defined (US-E1-005) |
| Deactivate user | Activate user | Defined (US-E1-005) |
| Assign department | Unassign (set to null) | Implied but not explicit |

All inverse operations are covered or have reasonable paths.

---

## Collateral Impact Assessment

| Component | Type | Impact | Action Required |
|---|---|---|---|
| `CompanyLookupService` | Existing (stub) | Must be replaced with real domain matching | High priority - affects auth flow |
| `CompanyModel` | Existing | Add `status` column | Migration required |
| `UserModel` | Existing | Add `department_id` column | Migration required |
| `VerifyMagicLink` handler | Existing | Must check company status before login | Update handler |
| `models_registry.py` | Existing | Add CompanyEmailDomainModel, DepartmentModel | Update imports |
| Auth flow | Existing | Company status check during magic link verify | Critical integration point |

**Risk:** Modifying the auth flow (adding company status check) must be done carefully to not break existing functionality. Recommend comprehensive tests before and after.

---

## Slicing Assessment

**Size:** Large (6 user stories, 3+ entities, 9+ endpoints)
**Slicing needed:** Yes — recommended 3 features

Suggested slicing:
1. **F0: Company CRUD + Email Domains** (US-E1-001, US-E1-002, US-E1-006) — Foundation: companies exist with domains
2. **F1: Company Status + Auth Integration** (US-E1-003, UC-E1-004 update) — Status management, auth flow update
3. **F2: Departments + User Management** (US-E1-004, US-E1-005) — Organization structure

This slicing ensures each feature is independently deployable and testable:
- After F0: companies can be created with domains, magic link works with real domain matching
- After F1: companies can be suspended/deactivated, auth respects company status
- After F2: full user and department management

---

## Testing Assessment

| Test Type | Required | Gap |
|---|---|---|
| Unit | Yes — entity business rules, status transitions | None |
| Integration | Yes — repository operations, domain matching | None |
| API/E2E | Yes — all endpoints (CRUD + error cases) | None |
| Auth integration | Yes — verify magic link with various company statuses | Critical test |

**Critical test scenarios:**
1. Magic link for user with domain matching active company → success
2. Magic link for user with domain matching suspended company → 403
3. Magic link for user with domain matching deactivated company → 403
4. Create company with duplicate name → 409
5. Create company with domain already taken → 409
6. Admin tries to manage user in different company → 404 (tenant isolation)
7. Admin tries to promote user to super_admin → 403
8. Delete department with assigned users → 409

---

## Red Flags

- [ ] ~~Subjective justification~~ — Clear dependency chain
- [ ] ~~Missing revenue impact~~ — Infrastructure epic, justified
- [ ] ~~Scope creep~~ — Well bounded by user stories
- [x] **Email domain uniqueness validation timing** — When is domain uniqueness checked? Only on company creation, or also when updating? Both should be checked.
- [x] **Company status cascading effects** — What happens to active JWT tokens when a company is suspended? Tokens remain valid until expiry but /me and other endpoints should check company status. This needs a decision.

---

## Questions for Stakeholder

1. **Active JWT tokens on company suspension:** Should we invalidate existing tokens (complex) or let them expire naturally but check company status on each request (simpler)? **Recommend:** Check company status on each authenticated request via the get_current_user dependency. Simpler, more secure.

2. **Department deletion with assigned users:** Set department_id to NULL, or block deletion? **Recommend:** Block deletion (409) if users are assigned. Admin should reassign users first.

3. **Super admin user search across companies:** Should super admin be able to search users across all companies? **Recommend:** Defer to E5 (Admin Dashboard). Not critical for E1.

---

## Checklist Summary

| Area | Score | Status |
|---|---|---|
| Business Alignment | 9/10 | Clear dependency, no direct KPI (justified) |
| Content Completeness | 9/10 | Comprehensive entities and acceptance criteria |
| Use Case Coverage | 8/10 | Missing edge cases documented above |
| Entity States | 9/10 | Company state machine well-defined |
| Collateral Impact | 9/10 | Auth flow integration identified |
| Slicing | 9/10 | Clean 3-feature split |
| Time Constraints | 10/10 | No deadline, reasonable scope |
| Testing | 9/10 | Critical scenarios identified |
| Definition of Done | 9/10 | Comprehensive checklist |

**Overall: Valid — ready for slicing and design phase**

---

## Recommendations

1. **Document decision on JWT + company status:** Add company status check to `get_current_user` dependency so suspended companies are blocked on every request, not just at login.
2. **Document department deletion behavior:** Block deletion if users are assigned (409 error).
3. **Add email domain uniqueness check on update**, not just creation.
4. **Write auth integration tests before modifying auth flow** to ensure no regressions.
5. Proceed to slicing and feature-level design.
