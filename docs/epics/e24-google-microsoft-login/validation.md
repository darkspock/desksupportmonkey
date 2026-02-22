# Requirement Validation Report

**Document:** E24 - Google & Microsoft Login
**Date:** 2026-02-22
**Status:** Valid (all open questions resolved, requirements updated)

---

## Summary

The E24 epic is well-structured, clearly scoped, and ready for implementation. It follows the established documentation format, has detailed acceptance criteria, and clearly delineates scope from E42. A few minor gaps were identified (unlinking flow, rate limiting, name population from OAuth profile) that should be decided before implementation but do not block it.

---

## Business Alignment Assessment

**Primary Objective:** Churn reduction / User convenience
**Contribution:** Clear — reduces login friction for organizations using Google Workspace or Microsoft 365
**KPIs Defined:** No (no measurable targets like "reduce login time by X%" or "increase daily active users by Y%")
**Justification Type:** Objective without hard numbers — based on common enterprise IT platform expectations

### Justification Quality

| Criteria | Status | Issue |
|----------|--------|-------|
| Specific numbers | No | No data on how many current/target users use Google/Microsoft |
| Evidence sources | No | No customer requests or ticket IDs cited |
| Revenue impact | No | Not quantified |
| Customer names/tickets | No | Not provided |

### Experimentation Assessment

**Is this an experiment?** No

**RED FLAGS:**
- [x] Missing revenue/cost impact (and not an experiment)
- [x] No evidence provided (and not an experiment)

**Assessment:** This is a standard enterprise platform feature (OAuth login) that is table-stakes for any B2B SaaS product. The business case is self-evident even without hard metrics. The lack of KPIs is acceptable given the nature of the feature — it's infrastructure, not a revenue-generating feature. **Proceed without blocking.**

---

## Entities Identified

| Entity | CRUD Coverage | States Defined | Delete Strategy |
|--------|---------------|----------------|-----------------|
| User (extended) | N/A (no new CRUD, extends existing) | N/A (uses existing active/deactivated) | N/A (existing) |

**Assessment:** Only the User entity is affected. Two new nullable fields (`google_id`, `microsoft_id`) are added. No new entities are created. This is clean and minimal.

---

## Missing Use Cases

| Use Case | Reason | Priority | Question for Stakeholder |
|----------|--------|----------|--------------------------|
| Unlink OAuth provider | No way for user/admin to remove a linked Google/Microsoft ID | Low | Should a user or admin be able to unlink an OAuth provider? E.g., if they switch Google accounts? |
| Email change conflict | If user changes email in the platform, Google/Microsoft email may no longer match | Low | Should OAuth login still work via `google_id`/`microsoft_id` even after email change? (Current design: yes, via provider ID first) |
| Rate limiting on OAuth endpoints | No explicit mention of rate limiting for OAuth verification endpoints | Medium | Should OAuth endpoints have rate limiting to prevent token verification abuse? |
| Google/Microsoft token refresh | Document only covers ID token verification, not refresh token flows | Low | N/A — the platform issues its own JWT; Google/Microsoft tokens are one-time verification only. This is correctly handled. |

---

## Missing State Information

| Entity | Missing Info | Question |
|--------|--------------|----------|
| User | No new states introduced | N/A — OAuth login reuses existing User states (active/deactivated). Correct approach. |

**Assessment:** No state machine changes needed. OAuth login is a new authentication method, not a new entity lifecycle. The existing User active/deactivated states are sufficient.

---

## Step 3: CRUD Check

**User entity extension:**
- **Create:** Covered — new users auto-created via OAuth flow (UC-E24-002, UC-E24-004)
- **Read:** Not applicable — no new read operations needed for OAuth fields
- **Update:** Covered — `google_id`/`microsoft_id` set on first OAuth login (account linking)
- **Delete:** Not explicitly covered — **unlinking an OAuth provider is not in scope**
- **List:** Not applicable

**Assessment:** The missing "unlink" operation is a deliberate scope decision. Users can always fall back to magic link or password. Recommend documenting this as "out of scope for E24" explicitly.

---

## Step 5: Inverse Operation Check

| Action | Inverse | Covered |
|--------|---------|---------|
| Link Google account | Unlink Google account | Not covered |
| Link Microsoft account | Unlink Microsoft account | Not covered |
| Auto-create user via OAuth | Deactivate user | Covered (existing) |
| Enable OAuth provider (env var) | Disable OAuth provider (remove env var) | Covered |

**Assessment:** Unlinking is the only missing inverse. Low priority for initial release — can be added in a follow-up if needed.

---

## Step 6: User Journey Check

| Journey | Preconditions | Postconditions | Error Recovery | Undo/Cancel |
|---------|---------------|----------------|----------------|-------------|
| Google login (existing user) | Active user, active company | JWT issued, google_id linked | Clear error messages (401, 403, 409) | N/A |
| Google login (new user) | Email domain matches active company | User created, JWT issued | 403 if domain not found | N/A (auto-created user can be deactivated by admin) |
| Microsoft login (existing user) | Active user, active company | JWT issued, microsoft_id linked | Clear error messages | N/A |
| Microsoft login (new user) | Email domain matches active company | User created, JWT issued | 403 if domain not found | N/A |
| Provider not configured | Missing env var | 501 response, button hidden | Frontend hides button | N/A |

**Assessment:** All happy paths and error paths are well-defined. Alternative flows cover all edge cases (invalid token, domain not found, company suspended, user deactivated, ID conflict).

---

## Collateral Impact

| Component | Type | Impact | Action Required |
|-----------|------|--------|-----------------|
| `UserModel` | Schema change | Add 2 nullable columns | Alembic migration |
| `User` entity | Code change | Add 2 fields + methods | Update dataclass |
| `UserRepositoryInterface` | Interface change | Add 2 new find methods | Extend interface |
| `UserRepository` (impl) | Code change | Implement new find methods | Add queries |
| `auth/routers.py` | Code change | Add 3 new endpoints | New routes |
| `auth/schemas.py` | Code change | Add OAuth request/response schemas | New schemas |
| `LoginPage.tsx` | UI change | Add 2 OAuth buttons | Update component |
| `.env.example` | Config change | Add 3 new variables | Document |
| `core/config.py` / settings | Config change | Add OAuth settings | New settings class/fields |
| `CompanyLookupService` | No change | Already handles domain matching | Reuse as-is |
| `JWTService` | No change | Already issues JWT tokens | Reuse as-is |
| `get_current_user` dependency | No change | Existing JWT validation works | No action |
| i18n files | Content change | Add OAuth button/error translations | EN + ES |
| `package.json` (frontend) | Dependency | Google Identity Services SDK, MSAL.js | New npm packages |
| `pyproject.toml` (backend) | Dependency | `google-auth` and/or `PyJWT` (already present?) | Check existing deps |
| MCP Server (E35) | No impact | Auth tools use JWT, not auth method | No action needed |
| Seed data | Potential | Demo users might benefit from mock OAuth IDs | Optional, low priority |

**Assessment:** The collateral impact section in the requirements covers the core impacts. Two items are missing from the requirements document:

1. **`core/config.py` / settings** — needs OAuth config fields added (not mentioned)
2. **Frontend dependencies** — `@react-oauth/google` or Google Identity Services SDK, `@azure/msal-browser` (not mentioned)
3. **Backend dependencies** — `google-auth` library (mentioned in Open Questions but not in Collateral Impact)

**Recommendation:** Add these to the Collateral Impact table.

---

## Slicing Assessment

**Size:** Medium
**Slicing needed:** Yes (already done)
**Slicing quality:** Good

The slicing into F0 (infrastructure), F1 (Google), F2 (Microsoft) is clean:
- F0 delivers shared value (entity fields, config, providers endpoint)
- F1 and F2 are independent, can be implemented in parallel
- Each feature is vertical (backend + frontend)
- Dependency graph is unidirectional

**Out of scope dependencies:**

| Item | Info Needed Now | Why |
|------|----------------|-----|
| E42 (SSO & Directory Sync) | No | E24 is self-contained; E42 builds on top later |
| Unlinking OAuth accounts | No | Can be added as follow-up |
| Profile picture storage | No | Explicitly deferred |

---

## Time Constraints Assessment

**Deadline:** Not specified
**Type:** None
**Reason:** N/A
**Realistic:** Yes — medium complexity, well-understood patterns
**Calendar conflicts:** None
**Buffer included:** N/A

### Deadline Risk Analysis

No deadline defined. No risk.

---

## Testing Assessment

**Tests defined:** Yes
| Test Type | Required | Defined | Gap |
|-----------|----------|---------|-----|
| Unit | Yes | Yes | None — "Unit tests for OAuth token verification and login logic" |
| Integration | Yes | Yes | None — "Integration tests for OAuth endpoints (mocked token verification)" |
| Frontend | Yes | Yes | None — "Frontend tests for OAuth button visibility and flow" |
| UAT | No | No | N/A for this feature type |

**Critical scenarios identified:** Yes — covered in use cases and alternative flows
**Test data requirements:** Mocked OAuth tokens (Google and Microsoft ID tokens for testing)

**Assessment:** Testing requirements are adequate. Key point: OAuth token verification MUST be mocked in tests (cannot call real Google/Microsoft APIs in CI). The requirements implicitly address this with "mocked token verification" in integration tests.

---

## Definition of Done Assessment

**DoD defined:** Yes
| Criteria | Defined | Clear |
|----------|---------|-------|
| Acceptance criteria | Yes | Yes — 16 testable DoD items |
| Quality gates | Yes | Unit + Integration + Frontend tests |
| Sign-off process | No | Not defined (standard for this project) |
| Training needs | No | N/A — OAuth login is self-explanatory UX |

---

## Red Flags

- [ ] No KPIs or metrics defined (acceptable for infrastructure feature)
- [ ] OAuth unlinking not addressed (low priority, can defer)
- [x] Missing backend/frontend dependency declarations in Collateral Impact
- [ ] No rate limiting mentioned for OAuth endpoints
- [ ] Open Question #2 (name population from OAuth profile) should be decided before implementation to avoid inconsistent behavior

---

## Open Questions for Stakeholder

1. **Unlink OAuth:** Should users or admins be able to unlink a Google/Microsoft account? Recommend: defer to follow-up, not needed for initial release.
2. **Name from OAuth profile:** The requirements mention this as an open question. Recommend: Yes, populate `name` from OAuth profile if currently NULL. This avoids showing blank names for OAuth-created users.
3. **Rate limiting:** Should OAuth verification endpoints have specific rate limits? Recommend: Apply the same rate limiting as other auth endpoints.
4. **Microsoft tenant mode:** Open Question #4 — `common` vs specific tenant. Recommend: Support `common` as default, validate email domain against companies regardless.
5. **Backend dependencies:** Confirm `google-auth` library is acceptable, or prefer raw JWKS verification for both providers for consistency?

---

## Checklist Summary

### Business Alignment: 2/4 passed
- [x] Objective identified (user convenience, enterprise readiness)
- [x] Contribution clear (reduces login friction)
- [ ] KPIs defined (no metrics — acceptable for infra feature)
- [ ] Evidence provided (no customer data — acceptable)

### Content Completeness: 6/6 passed
- [x] Problem statement clear
- [x] Solution described with user stories
- [x] Acceptance criteria testable and specific
- [x] Entities defined with field types
- [x] Bounded context mapped
- [x] Out of scope clearly delineated (E42)

### Use Case Coverage: 4/5 passed
- [x] Existing user login (Google + Microsoft)
- [x] New user auto-creation (Google + Microsoft)
- [x] Account linking
- [x] Configuration/provider availability
- [ ] Unlinking (not covered — low priority)

### Entity States: 1/1 passed
- [x] No new states — reuses existing User active/deactivated

### Collateral Impact: 5/7 passed
- [x] User model/entity changes identified
- [x] Repository changes identified
- [x] Auth router changes identified
- [x] Frontend login page changes identified
- [x] CompanyLookupService reuse confirmed
- [ ] Backend dependency (`google-auth`) not in collateral table
- [ ] Frontend dependencies (Google SDK, MSAL.js) not in collateral table

### Slicing: 5/5 passed
- [x] Features identified and scoped
- [x] Dependencies clear
- [x] Each feature independently deployable
- [x] No circular dependencies
- [x] All scope covered

### Time Constraints: 1/1 passed
- [x] No deadline — no risk

### Testing: 3/3 passed
- [x] Unit tests defined
- [x] Integration tests defined
- [x] Frontend tests defined

### Definition of Done: 3/3 passed
- [x] Acceptance criteria testable
- [x] Quality gates (tests)
- [x] DoD items comprehensive (16 items)

---

## Recommendations

1. **Decide Open Question #2 now** — Name population from OAuth profile should be decided before implementation. Recommend: Yes, set `name` from OAuth claims when user's `name` is NULL. Add this to US-E24-001 and US-E24-002 acceptance criteria.
2. **Add missing dependencies to Collateral Impact** — Add `google-auth` (backend), `@react-oauth/google` (frontend), `@azure/msal-browser` (frontend), and `core/config.py` settings changes.
3. **Add rate limiting note** — Even if using existing middleware, mention it explicitly for OAuth endpoints.
4. **Document unlinking as "out of E24 scope"** — Currently not mentioned anywhere. Add a line to "What E24 Does NOT Deliver" to make it explicit.
5. **Proceed with implementation** — The epic is well-defined and ready. The gaps identified are minor and can be addressed incrementally.
