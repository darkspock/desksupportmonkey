# E55 Requirements Validation Report

**Date:** 2026-03-02
**Reviewed against:** Existing auth codebase, E54 document format

---

## 1. Contradictions with Existing Auth Architecture

### 1.1 Auth Flow Inventory (Verified)

The document correctly identifies the five auth endpoints that exist in the codebase:

| Flow | Current Endpoint | Source File | E55 Mentions |
|------|-----------------|-------------|--------------|
| Magic link create | `POST /api/v1/auth/magic-link` | `adapters/http/api/auth/routers.py:135` | Yes (F2, API table, collateral) |
| Magic link verify | `POST /api/v1/auth/verify` | `adapters/http/api/auth/routers.py:169` | Yes (F2, API table, collateral) |
| Password login | `POST /api/v1/auth/login` | `adapters/http/api/auth/routers.py:201` | Yes (F2, API table, collateral) |
| Google OAuth | `POST /api/v1/auth/oauth/google` | `adapters/http/api/auth/routers.py:265` | Yes (F2, API table, collateral) |
| Microsoft OAuth | `POST /api/v1/auth/oauth/microsoft` | `adapters/http/api/auth/routers.py:296` | Yes (F2, API table, collateral) |

**Verdict: PASS.** All five endpoints are accounted for in the scoped auth section, the API table, and the collateral impact table.

### 1.2 CompanyLookupService Usage (Verified)

The document correctly states that `CompanyLookupInterface` currently has domain-only methods. Confirmed from `src/auth_bc/company_lookup/domain/service.py`:
- `find_company_id_by_email_domain(email)` -- returns `Optional[str]`
- `find_company_by_email_domain(email)` -- returns `Optional[tuple[str, bool]]`
- `extract_domain(email)` -- static utility

The document proposes adding `is_email_allowed_in_company(email, company_id)`, which is a new method, not a replacement. This is non-contradictory.

**Verdict: PASS.** No contradictions.

### 1.3 User Model Constraints (Verified)

Current constraints from `src/auth_bc/user/infrastructure/models.py`:
- `email`: `unique=True` (global, line 14)
- `google_id`: `unique=True` (global, line 29)
- `microsoft_id`: `unique=True` (global, line 30)

The document correctly identifies these as global constraints that need to become composite. The proposed composite `(email, company_id)` with partial unique for `company_id IS NULL` is the correct PostgreSQL pattern for this use case.

**Verdict: PASS.** Accurately describes the current state and proposed change.

### 1.4 Password Login Scope (Verified)

Current `PasswordLoginService` (`src/auth_bc/user/application/commands/password_login.py`):
- Uses `self.user_repo.find_by_email(command.email)` -- global lookup (line 42)
- Checks `user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)` -- password is admin-only (line 46)
- For non-SUPER_ADMIN: calls `self.company_lookup.find_company_by_email_domain(user.email)` to verify company is active (line 60)

The document says password login will accept `company_id` and scope lookup to company. This is correct and necessary for multi-company support.

**Verdict: PASS.** No contradictions.

### 1.5 OAuth Login Service (Verified)

Current `OAuthLoginService` (`src/auth_bc/user/application/services/oauth_login_service.py`):
1. Finds user by provider ID globally (`find_by_google_id` / `find_by_microsoft_id`)
2. Falls back to `find_by_email` globally
3. If no user found, calls `company_lookup.find_company_by_email_domain` to auto-create

The document proposes:
- Accept `company_id` from slug resolution
- Change lookups to `find_by_google_id_and_company(google_id, company_id)` and `find_by_email_and_company(email, company_id)`
- User creation always sets the `company_id` from the slug

This is internally consistent and non-contradictory with the existing architecture.

**Verdict: PASS.**

### 1.6 Magic Link Flow (Verified)

Current `CreateMagicLinkCommandHandler`:
- Calls `company_lookup.find_company_by_email_domain(email)` (line 52)
- Falls back to checking if user exists in repo (line 56)
- The magic link itself does not store company_id

Current `VerifyMagicLinkService`:
- Finds user by `find_by_email(magic_link.email)` -- global (line 67)
- If new user, resolves company from `find_company_by_email_domain` (line 70)

The document proposes accepting `company_id` from slug in both create and verify flows. This is consistent.

**Minor observation:** The document does not explicitly mention whether the `MagicLink` entity itself needs a `company_id` field to carry the company context from create to verify. Currently, the magic link only stores `email` and `token`. If the slug is provided at create time but the user clicks the verify link from email without a slug, the verify endpoint would need the company context somehow. The document's scoped verify endpoint (`/api/v1/auth/{slug}/verify`) implies the slug is in the URL at verify time too, which resolves this, but this is an implementation subtlety worth noting.

**Verdict: PASS with note.** See Issue #1 below.

---

## 2. All Auth Flows Addressed

### Checklist

| Flow | F2 Scoped Auth | API Endpoints Table | Collateral Impact | User Stories | Testing Requirements |
|------|:-:|:-:|:-:|:-:|:-:|
| Magic link create | Yes (line 154) | Yes (line 265) | Yes (line 369) | Yes (F2 story 1) | Yes (integration) |
| Magic link verify | Yes (line 154) | Yes (line 266) | Yes (line 370) | Yes (F2 story 1) | Yes (integration) |
| Password login | Yes (line 154) | Yes (line 267) | Yes (line 371) | Yes (F2 story 3) | Yes (integration) |
| Google OAuth | Yes (line 154) | Yes (line 268) | Yes (line 372) | Yes (F2 story 2) | Yes (integration) |
| Microsoft OAuth | Yes (line 154) | Yes (line 269) | Yes (line 373) | Yes (F2 story 2) | Yes (integration) |

**Verdict: PASS.** All five auth flows are mentioned in every relevant section.

---

## 3. Backward Compatibility Strategy

### 3.1 Unscoped Endpoints (Verified)

The document addresses backward compatibility in multiple places:

- **F2 section (lines 161-163):** "Original unscoped endpoints remain active during a transition period. Unscoped endpoints attempt to resolve the company from the email domain (current behavior). If the email matches exactly one company, proceed; if multiple, return an error directing the user to use the slug-based URL."

- **Business Rule 16 (line 352):** Explicitly restates the single/multiple company resolution behavior.

- **Scope section (line 319):** "Backward-compatible unscoped auth endpoints during transition"

- **DoD (line 450):** "Unscoped auth endpoints remain functional with backward-compatible behavior"

**Verdict: PASS.** Clear and comprehensive backward compatibility plan.

### 3.2 Existing Companies (Verified)

- **Business Rule 1 (line 337):** "Existing companies get auto-generated slugs from their name during migration."
- **Business Rule 4 (line 340):** "Auth mode defaults to `domain` for all existing companies."
- **Migration Strategy (lines 388-403):** Step-by-step migration plan with data safety guarantees.

**Verdict: PASS.** Existing companies are fully addressed.

### 3.3 Data Safety (Verified)

The migration strategy section (lines 399-403) explicitly states:
- Composite unique is less restrictive than global unique, so existing data always satisfies new constraints
- Slug generation is deterministic and idempotent
- No data deletion or modification

**Verdict: PASS.**

---

## 4. E54 Format Comparison

### Section-by-Section Comparison

| Section | E54 | E55 | Match |
|---------|:---:|:---:|:-----:|
| Header (date, priority, status, BC, deps) | Yes | Yes | Yes |
| Business Alignment > Objective | Yes | Yes | Yes |
| Business Alignment > KPI Targets | Yes | Yes | Yes |
| Business Alignment > Evidence | Yes | Yes | Yes |
| Problem Statement > Current Situation | Yes | Yes | Yes |
| Problem Statement > Pain Points (table) | Yes | Yes | Yes |
| Problem Statement > Who Is Affected | Yes | Yes | Yes |
| Proposed Solution > Overview | Yes | Yes | Yes |
| Domain Model | Yes | Yes | Yes |
| Features with User Stories | Yes | Yes | Yes |
| API Endpoints (tables) | Yes | Yes | Yes |
| Scope > In Scope | Yes | Yes | Yes |
| Scope > Out of Scope | Yes | Yes | Yes |
| Business Rules (numbered list) | Yes (20 rules) | Yes (20 rules) | Yes |
| Collateral Impact (table with 3 cols) | Yes | Yes | Yes |
| Testing Requirements > Unit | Yes | Yes | Yes |
| Testing Requirements > Integration | Yes | Yes | Yes |
| Definition of Done (checkboxes) | Yes | Yes | Yes |

**Additional sections in E55 not in E54:**
- **Migration Strategy** (lines 386-403): E55 includes a dedicated migration strategy section with database migration steps and data safety analysis. E54 does not have this. This is an acceptable addition given E55's migration complexity (changing uniqueness constraints on existing tables), but it breaks the format slightly.

**Sections in E54 not in E55:**
- **Authentication** (dedicated section): E54 has a standalone "Authentication" section (lines 152-177) for the reseller auth flow. E55 covers authentication within F2 (Scoped Authentication) rather than as a standalone section. This is a reasonable structural choice since E55 is about modifying existing auth rather than introducing a new auth flow, but it is a format deviation.
- **Referral Attribution on Registration** (dedicated section): E54 has a standalone section for a specific cross-cutting concern. E55 does not have an equivalent, which is appropriate since E55's cross-cutting concerns are captured in the collateral impact table.

**Verdict: PASS with minor notes.** The overall structure matches E54 closely. The addition of Migration Strategy and omission of a standalone Authentication section are justified by the nature of the epic.

---

## 5. Issues Found

### Issue #1 (Low severity): Magic link company context propagation

The document does not explicitly address how the company context is carried between the magic link creation step and the verification step. Currently, the magic link entity stores only `email` and `token`. The document implies the slug will be in the verify URL (`/api/v1/auth/{slug}/verify`), so the company is re-resolved at verify time from the slug. This works, but there is an edge case: if a user requests a magic link via the slug-scoped endpoint for company A, then clicks the link in a URL that points to company B's slug, they would be verified in company B instead. The document should clarify whether:
- (a) The magic link entity should gain a `company_id` field to bind the link to a specific company at creation time, OR
- (b) The verify endpoint resolves company from the slug and that is the intended behavior (the email link always includes the correct slug)

**Recommendation:** Add a note in F2 or the Domain Model section clarifying that the magic link email template must include the slug in the verification URL, and optionally store `company_id` in the magic link entity for validation.

### Issue #2 (Low severity): `OAuthProviderAlreadyLinkedError` handling in multi-company context

The current codebase raises `OAuthProviderAlreadyLinkedError` when trying to link a Google/Microsoft ID that is already attached to a different `provider_id` value on the same user (see `oauth_login_service.py:99-100`). With composite uniqueness on `(google_id, company_id)`, the same Google account can now be linked to different user records in different companies. The document correctly mentions this in the constraint changes, but the `_link_provider` method's existing conflict check (`current is not None and current != info.provider_id`) is about a *different* Google ID on the same user, not about the same Google ID in a different company. This should still work correctly under the new model, but the collateral impact table does not mention the `OAuthProviderAlreadyLinkedError` exception or the `_link_provider` logic.

**Recommendation:** Add `src/auth_bc/user/domain/exceptions.py` and the `_link_provider` logic to the collateral impact table to ensure it is reviewed during implementation.

### Issue #3 (Medium severity): `find_by_email()` callers outside auth flows

The document mentions changing the repository to add `find_by_email_and_company()`, but there are many other callers of `find_by_email()` throughout the codebase (the `UserRepository.find_by_email` method is used by the magic link create handler, verify handler, password login, OAuth login, and potentially other services). When email uniqueness becomes composite, `find_by_email()` will return ambiguous results (could match multiple users across companies). The document's collateral impact table lists the repository but does not enumerate all callers that will need to switch from `find_by_email()` to `find_by_email_and_company()`.

Key callers that must be updated (verified from source):
- `CreateMagicLinkCommandHandler.handle()` -- line 56 of `create_magic_link.py` uses `self.user_repo.find_by_email(email)`
- `VerifyMagicLinkService.handle()` -- line 67 of `verify_magic_link.py` uses `self.user_repo.find_by_email(magic_link.email)`
- `PasswordLoginService.handle()` -- line 42 of `password_login.py` uses `self.user_repo.find_by_email(command.email)`
- `OAuthLoginService.login_or_create()` -- line 51 of `oauth_login_service.py` uses `self.user_repo.find_by_email(info.email)`

These are all covered implicitly by the collateral impact entries, but the collateral impact table only says "Add `find_by_email_and_company()`" for the repository row without explicitly stating that `find_by_email()` semantics must change (it should return a list or be removed from the unscoped path).

**Recommendation:** The collateral impact row for `repository.py` should explicitly state: "Existing `find_by_email()` must be preserved for backward-compatible (unscoped) flows but must handle the case where multiple users match. Consider changing the return type to `list[User]` or adding a `find_all_by_email()` variant."

### Issue #4 (Low severity): Missing `set-password` endpoint in scoped endpoints

The current auth router includes `POST /api/v1/auth/set-password` (line 234 of `routers.py`). This endpoint is not mentioned in the E55 scoped endpoints list, nor in the collateral impact table. While `set-password` requires an authenticated user (it uses `get_current_user`), it does not need slug scoping because the user is already authenticated with a company-scoped JWT. However, for completeness, it should be mentioned as "no change needed" in the collateral analysis to confirm it was not overlooked.

**Recommendation:** Add a note in collateral impact or scope that `set-password` requires no changes since it operates on the authenticated user's JWT context.

### Issue #5 (Low severity): Missing `GET /oauth/providers` in scoped endpoints

The current auth router includes `GET /api/v1/auth/oauth/providers` (line 126 of `routers.py`), which returns which OAuth providers are enabled. The login page at `/login/{slug}` would need to know which providers are available. The document mentions "Available auth methods shown based on company's OAuth configuration" in F1, but there is no scoped version of the providers endpoint. The existing endpoint returns deployment-wide configuration, which may be sufficient, but the document implies per-company provider configuration.

**Recommendation:** Clarify whether OAuth provider availability is per-deployment (current) or per-company (new). If per-deployment, the unscoped `/oauth/providers` endpoint is sufficient and should be mentioned as unchanged. If per-company (future), it should be added to Out of Scope.

### Issue #6 (Low severity): `CompanyEmailDomainModel.domain` has `unique=True`

From `src/company_bc/company/infrastructure/models.py:48`, the `domain` column in `company_email_domains` has `unique=True`. This means each domain can only belong to one company. The E55 document's allowlist mode and multi-company support does not change this constraint, and it is orthogonal (domains stay unique per company; it is emails that become composite). This is fine, but the document could clarify that in `domain` mode, the one-domain-to-one-company mapping is intentionally preserved.

**Recommendation:** Minor clarification, no action needed.

### Issue #7 (Medium severity): Password login is admin-only but the document's user story says "As an admin"

The document's F2 user story 3 says "As an admin, I can log in via password from my company's slug login page." This correctly reflects the current behavior (`password_login.py` line 46: role must be ADMIN or SUPER_ADMIN). However, the document does not explicitly state that password login remains admin-only in the new system. Since E55 is changing auth fundamentals, it would be prudent to restate this constraint explicitly.

**Recommendation:** Add a business rule or note in F2 clarifying that password login remains restricted to ADMIN and SUPER_ADMIN roles, matching the existing behavior.

### Issue #8 (Low severity): No mention of `_check_billing_not_suspended` in scoped endpoints

The router's billing suspension check (`_check_billing_not_suspended`, line 90 of `routers.py`) runs after every successful authentication. The new slug-scoped endpoints must also include this check. The collateral impact table mentions `routers.py` but only says "Add slug-scoped endpoint variants" without noting that the billing check must be replicated.

**Recommendation:** Add a note to the router collateral impact entry that billing suspension checks must be applied to all new slug-scoped endpoints.

---

## 6. Summary

| Category | Verdict |
|----------|---------|
| No contradictions with existing auth architecture | **PASS** |
| All four auth flows addressed (5 endpoints) | **PASS** |
| Backward compatibility strategy | **PASS** |
| E54 format adherence | **PASS** (minor deviations justified) |
| Issues found | 8 issues (2 medium, 6 low severity) |

### Overall Assessment

The E55 requirements document is **well-structured, thorough, and architecturally sound**. It correctly identifies all existing auth flows, proposes non-contradictory changes, and includes a comprehensive backward compatibility strategy. The document follows the E54 format closely with justified structural additions.

The two medium-severity issues (#3 and #7) are about explicitness rather than correctness -- the document's intent is clear, but implementation teams would benefit from more explicit guidance on `find_by_email()` migration strategy and the admin-only password login constraint.
