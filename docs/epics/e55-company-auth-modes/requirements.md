# Epic E55 — Company Login Slug, Multi-Company & Auth Mode

**Date:** 2026-03-02
**Priority:** High
**Status:** Pending
**Bounded Context:** `auth_bc` (modify), `company_bc` (modify)
**Dependencies:** E0 (Foundation) — Done, E24 (Google & Microsoft Login) — Done

---

## Business Alignment

### Objective

Enable companies to support diverse authentication scenarios and allow users to belong to multiple companies. Today, a user's email domain determines their company, and there is no way to onboard users whose domains don't match (contractors, consultants, partners). This epic introduces three capabilities: company login slugs (path-based company identification), multi-company user support (same person in multiple companies via a lightweight membership registry), and a configurable auth mode per company (domain matching vs. membership-only).

### KPI Targets

| KPI | Target |
|-----|--------|
| Multi-company adoption | 10% of active users belong to 2+ companies within 6 months |
| Membership-only mode adoption | 20% of companies switch to membership-only mode within 3 months |
| Contractor onboarding time | Reduce from "not possible" to under 5 minutes |
| Login success rate | Maintain 95%+ across all auth flows after migration |

### Evidence

- Customers with contractors and external consultants cannot onboard them because their email domains don't match
- IT consultants managing multiple client companies need separate accounts for each — no way to use one identity
- MSPs and system integrators need a single person to administer multiple client companies
- Email-domain-only matching blocks organizations with heterogeneous email domains (acquisitions, subsidiaries, partners)
- Login slugs are standard practice in B2B SaaS (Slack, Notion, Linear all use workspace slugs)

---

## Problem Statement

### Current Situation

DeskSupportMonkey determines a user's company by matching their email domain against the `company_email_domains` table. This creates three limitations:

1. **Single-company users** — each user row has one `company_id`, so a person can only belong to one company
2. **No membership-only mode** — if a user's email domain doesn't match, they cannot be onboarded (contractors, consultants, partners with gmail.com, outlook.com, or other domains)
3. **No company context in auth flows** — all auth endpoints resolve the company implicitly from the email domain, with no way to target a specific company

### Pain Points

| Problem | Impact |
|---------|--------|
| Single company_id per user | A person can only work in one company — blocks multi-company users |
| Domain-only company resolution | Cannot onboard users with non-matching domains (contractors, consultants) |
| No company context in login | Auth flows guess the company from email domain — ambiguous for multi-company users |
| No branded login page | Companies cannot share a direct login link with their users |
| Public domain blocking | gmail.com, outlook.com, etc. are blocked — no workaround for small orgs using public email |

### Who Is Affected

- **Company admins:** Cannot onboard contractors, consultants, or partners with non-matching email domains
- **Multi-company users:** IT consultants and MSPs who manage multiple client companies need separate identities
- **Employees:** Need a branded login URL to know they're signing in to the right company
- **Super admins:** Need visibility into multi-company users and auth mode configuration

---

## Proposed Solution

### Overview

A **minimal-impact** approach with three interconnected changes:

1. **Company login slug** — Each company gets a unique, URL-safe slug (e.g., `acme-corp`). The login page becomes `/login/{slug}`, giving every auth flow an explicit company context.

2. **Multi-company via membership registry** — A new `company_users` table records which companies each user can access (with role, department, active status per company). The existing `users` table stays **structurally unchanged** — it continues to hold `company_id`, `role`, `department_id`, `employee_role_id`, `is_active`. On login or company switch, the system copies the target company's membership data from `company_users` to the user row. This means **all existing routers, queries, commands, tenant context, and role checks work unchanged** — they still read from the user row.

3. **Auth mode configuration** — Each company chooses between `domain` mode (current behavior) and `membership_only` mode (only users with a `company_users` record can log in — admin must invite them first, public domains like gmail.com allowed via invite).

### Why This Approach

The key insight is that the `users` table always reflects the user's **current active session**. The `company_users` table is the **registry** of all memberships. By copying membership data to the user row on login/switch, we avoid changing:
- `get_current_user()` return type
- `require_role()` logic
- `set_tenant()` calls
- JWT structure (`user_id`, `company_id`, `role`)
- All 80+ routers that read user.company_id or user.role
- All queries that filter by company_id

The only catch: if a user has an active session in company A and switches to company B, the old session's JWT has company A's `company_id`, but the user row now has company B's. The `get_current_user()` dependency detects this mismatch and returns 401, forcing the old session to re-authenticate.

---

## Domain Model

### Modified Entity: `Company`

Add two fields to the existing `Company` entity.

| Field | Type | Description |
|-------|------|-------------|
| `slug` | String(50), unique, indexed | URL-safe company identifier. Lowercase alphanumeric + hyphens, 3–50 chars. Auto-generated from name, editable by admin. |
| `auth_mode` | Enum(`domain`, `membership_only`), default `domain` | `domain` = current behavior (email domain match). `membership_only` = only users with a `company_users` record can log in. |

### Unchanged Entity: `User`

**The `users` table keeps ALL its current columns — no structural changes.**

| Field | Status | Notes |
|-------|--------|-------|
| `id`, `email`, `name`, `password_hash` | Unchanged | Identity fields |
| `google_id`, `microsoft_id` | Unchanged | OAuth links, globally unique |
| `company_id` | Unchanged | Now represents "current active company" — updated on login/switch |
| `role` | Unchanged | Now represents "role in current active company" — updated on login/switch |
| `department_id` | Unchanged | Department in current active company — updated on login/switch |
| `employee_role_id` | Unchanged | Employee role in current active company — updated on login/switch |
| `is_active` | Unchanged | Active status in current active company — updated on login/switch |
| `is_anonymized` | Unchanged | GDPR flag |
| Address fields, timestamps | Unchanged | |

**Email, google_id, and microsoft_id remain globally unique** — one row per person, one password, one set of OAuth links.

### New Entity: `CompanyUser` (Membership Registry)

One record per person per company. This is the source of truth for "which companies can this user access?" and the allowlist in `membership_only` mode.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ULID | Primary key |
| `user_id` | String(26) FK → users.id | The person |
| `company_id` | String(26) FK → companies.id | The company |
| `role` | String(20) | `admin`, `procurement_manager`, `technician`, `employee` |
| `department_id` | String(26) FK → departments.id, nullable | Department in this company |
| `employee_role_id` | String(26) FK → employee_roles.id, nullable | Role title in this company |
| `is_active` | bool, default true | Active status in this company (independent per company) |
| `created_at` | DateTime | When the membership was created |
| `updated_at` | DateTime | Last update |

**Constraints:** Composite unique on `(user_id, company_id)`. One membership per person per company.

### Modified Entity: `MagicLink`

Add `company_id` field to prevent slug-swapping between magic link creation and verification.

| Field | Type | Description |
|-------|------|-------------|
| `company_id` | String(26), nullable | Company context when the magic link was created. Null for legacy links. |

### SUPER_ADMIN Handling

**No change.** SUPER_ADMIN stays as a `UserRole` enum value. SUPER_ADMIN users have `company_id = NULL` and platform-wide access. They do not use company slugs for login — they use the unscoped login endpoint as today.

---

## Features

### F1 — Company Slug & Login Page

**Overview:** Add a URL-safe slug to every company and create a path-based login page that gives all auth flows an explicit company context.

**Slug Rules:**
- Auto-generated from company name on creation (e.g., "Acme Corp" → `acme-corp`)
- Lowercase alphanumeric + hyphens only, 3–50 characters
- Unique across all companies (including deactivated — slugs are never released)
- Editable by company admin (with uniqueness validation)
- Does NOT auto-update on company rename — stable identifier
- Reserved slugs: `admin`, `api`, `login`, `register`, `reseller`, `app`, `auth`, `super-admin`

**Login Page:**
- `/login/{slug}` shows a company-branded login page (company name displayed)
- Available auth methods shown based on company's OAuth configuration
- `/login` without slug: if the user has exactly one company (from a cookie or prior session), redirect to that company's slug login; otherwise show a "Find your company" input

**Migration:** Auto-generate slugs for all existing companies from their name, with collision handling (append `-2`, `-3`, etc.)

**User Stories:**

1. As a company admin, I can see and edit my company's login slug in company settings so I can share a branded login URL.
2. As a user, I can visit `/login/{slug}` and see my company's name on the login page.
3. As a user, if I visit `/login` without a slug, I can search for my company to find the right login page.
4. As a super_admin, I can see and edit the slug for any company.

### F2 — Scoped Authentication

**Overview:** All auth flows accept company context via the login slug. The auth process becomes two-step: (1) authenticate identity, (2) verify/create membership + copy to user row.

**Auth Flow (slug-scoped):**
1. Resolve slug → company_id
2. Authenticate identity (find user by email/OAuth ID — global lookup on users table, same as today)
3. If no user exists: create user row (email, name, password/OAuth, company_id = this company, role = EMPLOYEE)
4. Find `company_users` record for (user.id, company_id):
   - **Found + active:** Copy membership data (company_id, role, department_id, employee_role_id, is_active) from `company_users` → user row
   - **Found + inactive:** Reject — "Your account in this company is deactivated"
   - **Not found + domain mode:** Check email domain match → auto-create `company_users` record with EMPLOYEE role → copy to user row
   - **Not found + membership_only mode:** Reject — "You don't have access to this company. Contact your admin."
5. Issue JWT with (user_id, company_id, role) — all from the now-updated user row

**Copy-on-Switch Semantics:**
- The user row always reflects the **current active company** after login
- Copying is a simple UPDATE on the users table: `SET company_id=X, role=Y, department_id=Z, employee_role_id=W, is_active=A`
- This happens atomically during the auth flow or company switch

**Session Invalidation:**
- `get_current_user()` adds one check: if JWT's `company_id` ≠ user row's `company_id`, return 401
- This means switching companies invalidates all existing sessions for that user
- The frontend handles 401 by redirecting to login or showing "You've switched to another company"

**Backward Compatibility:**
- Original unscoped endpoints (`/api/v1/auth/magic-link`, etc.) remain active during transition
- Unscoped endpoints resolve company from email domain (current behavior) — if email matches exactly one company, proceed; if multiple, return error with company slugs
- SUPER_ADMIN login is unaffected (continues via unscoped endpoints, company_id = NULL)

**User Stories:**

1. As a user, I can log in via magic link from my company's slug login page and be authenticated in the correct company.
2. As a user, I can log in via Google/Microsoft OAuth from my company's slug login page.
3. As an admin, I can log in via password from my company's slug login page.
4. As a user, my password and OAuth links work across all my companies — I set them once.

### F3 — Multi-Company User Support

**Overview:** One person can have memberships in multiple companies. A company switcher lets them move between companies.

**Company Switcher:**
- `GET /api/v1/auth/my-companies` — returns all companies where this user has an active `company_users` record (company name, slug, role in each)
- `POST /api/v1/auth/switch-company` — accepts `company_id`, verifies active membership, copies membership data to user row, issues new JWT. This is a token exchange + user row update, not a full re-authentication.
- UI: company dropdown in the app header (visible only if user has 2+ active memberships)
- Switching invalidates all existing sessions (JWT company_id mismatch)

**User Stories:**

1. As a user, I can belong to multiple companies with the same email, each with its own role and permissions.
2. As a user, I can see a company switcher in the app header showing all my companies.
3. As a user, I can switch to another company without re-entering my credentials.
4. As an admin in company A and employee in company B, my role changes automatically when I switch.

### F4 — Auth Mode Configuration (domain / membership_only)

**Overview:** Each company can choose between `domain` mode and `membership_only` mode.

**Domain Mode (default — current behavior):**
- Anyone whose email domain matches the company's registered domains can sign in
- First login auto-creates a `company_users` record with EMPLOYEE role
- Public domains (gmail.com, outlook.com, etc.) remain blocked in domain registration
- Functionally unchanged from today

**Membership-Only Mode:**
- Only users with a `company_users` record can log in — no self-registration
- Domain matching is disabled for this company
- Public domains ARE allowed — the admin invites contractors by email
- The `company_users` table IS the allowlist — no separate table
- Admin adds people via existing flows: user invite, CSV import, quick-create

**Mode Switching:**
- `domain` → `membership_only`: No data migration. All existing users already have `company_users` records. Self-registration is simply disabled.
- `membership_only` → `domain`: Warn admin that anyone with a matching email domain can self-register again. Existing memberships preserved.

**How Invite Works in Membership-Only Mode:**
- Admin invites `contractor@gmail.com` via existing `POST /api/v1/users/invite`
- System creates User identity (if not exists) + CompanyUser membership + sends magic link
- Contractor clicks magic link → identity authenticated → membership found → user row updated → JWT issued

**Company Lookup Changes:**
- `CompanyLookupInterface` gains: `is_email_allowed_in_company(email, company_id) -> bool`
- For `domain` mode: checks if email domain matches any registered company domain
- For `membership_only` mode: checks if a `company_users` record exists for any user with this email in this company

**User Stories:**

1. As a company admin, I can see the current auth mode in company settings.
2. As a company admin, I can switch from domain to membership-only to control exactly who has access.
3. As a company admin, I can switch from membership-only back to domain, with a warning about self-registration re-enabling.
4. As a contractor with a gmail.com address, I can log in to a company that my admin invited me to.

---

## API Endpoints

### Slug-Scoped Auth

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/companies/by-slug/{slug}` | Resolve slug to company info (name, auth mode, available providers) |
| POST | `/api/v1/auth/{slug}/magic-link` | Request magic link scoped to company |
| POST | `/api/v1/auth/{slug}/verify` | Verify magic link token scoped to company |
| POST | `/api/v1/auth/{slug}/login` | Password login scoped to company |
| POST | `/api/v1/auth/{slug}/oauth/google` | Google OAuth login scoped to company |
| POST | `/api/v1/auth/{slug}/oauth/microsoft` | Microsoft OAuth login scoped to company |

### Company Switcher

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/auth/my-companies` | List all companies where user has active membership |
| POST | `/api/v1/auth/switch-company` | Exchange JWT for new one targeting another company (updates user row) |

### Auth Mode Configuration (Admin)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/companies/{company_id}/auth-mode` | Get current auth mode |
| PATCH | `/api/v1/companies/{company_id}/auth-mode` | Switch auth mode (domain ↔ membership_only) |

### Company Slug Management

| Method | Path | Description |
|--------|------|-------------|
| PATCH | `/api/v1/companies/{company_id}/slug` | Update company slug (admin only) |

---

## Scope

### In Scope

- Company slug field with auto-generation, uniqueness, and admin editing
- Path-based login page (`/login/{slug}`) with company name display
- New `company_users` membership registry table (source of truth for multi-company access)
- Copy-on-switch: login and company switch copy membership data from `company_users` to user row
- All four auth flows (magic link, verify, password, OAuth) accept company context via slug
- Two-step auth: authenticate identity → verify/create membership → copy to user row → issue JWT
- Multi-company user support — same email in multiple companies with different roles
- Company switcher API and UI (dropdown in app header)
- Session invalidation via JWT company_id mismatch check
- Auth mode enum (`domain`, `membership_only`) on Company entity
- `domain` mode: current behavior (auto-create membership on first login)
- `membership_only` mode: only existing members can log in (invite to add)
- Invite auto-creates identity + membership (no separate allowlist table)
- Dual-write: commands that change role/department/is_active update both user row and company_users
- Migration: create `company_users` from existing user data, generate slugs
- Backward-compatible unscoped auth endpoints during transition

### Out of Scope (future)

- Company logo/branding on login page (only name for now)
- SAML/SSO integration
- Automatic provisioning via SCIM
- LDAP/Active Directory sync
- Audit log for membership changes (future compliance epic)
- Custom login page themes
- Concurrent multi-company sessions (only one active session per user)

---

## Business Rules

1. Every company **must have a slug**. Existing companies get auto-generated slugs during migration. New companies get slugs on creation.
2. Slugs must be **lowercase alphanumeric + hyphens**, 3–50 characters, **unique** across all companies.
3. Reserved slugs (`admin`, `api`, `login`, `register`, `reseller`, `app`, `auth`, `super-admin`) **cannot be used**.
4. Slugs are **never released** — a deactivated company's slug remains reserved.
5. Slugs do **not auto-update** on company rename. Admin can change the slug explicitly.
6. Auth mode defaults to `domain` for all existing and new companies.
7. In `domain` mode, existing behavior is unchanged: email domain match → auto-create `company_users` record with EMPLOYEE role on first login → copy to user row.
8. In `membership_only` mode, **only users with a `company_users` record** can authenticate. No self-registration. Admin must invite first.
9. In `membership_only` mode, **public domains are allowed** (gmail.com, etc.) — admins can invite anyone by email.
10. The `company_users` table **IS the allowlist** in `membership_only` mode. No separate table.
11. **Inviting a user** creates both the User identity (if not exists) and a CompanyUser membership. Works in both modes.
12. **CSV import** creates User identities + CompanyUser memberships. Works in both modes.
13. Switching `domain` → `membership_only`: no data migration needed. Self-registration is simply disabled.
14. Switching `membership_only` → `domain`: warn admin that self-registration re-enables. Existing memberships preserved.
15. **Email remains globally unique** on the `users` table — one row per person.
16. **OAuth IDs remain globally unique** — one Google/Microsoft account per person.
17. **Password is set once** — works across all company memberships.
18. A person can have **one membership per company** — unique on `(user_id, company_id)`.
19. Each membership has its own **role, department, employee_role, and is_active** — independent per company.
20. **The user row always reflects the current active company.** On login or switch, membership data is copied from `company_users` to the user row.
21. **Session invalidation**: if JWT's `company_id` ≠ user row's `company_id`, the session is invalid (401). Only one active company session per user.
22. The company switcher performs a **token exchange + user row update**, not a full re-authentication.
23. If a user has **only one active membership**, the company switcher is hidden in the UI.
24. Company switcher only shows companies where `company_users.is_active = true`.
25. **Dual-write**: commands that modify role, department_id, employee_role_id, or is_active update BOTH the user row (if it's the active company) AND the company_users record.
26. Unscoped auth endpoints remain functional: if email domain resolves to **exactly one** company, proceed; if multiple, return error with company slugs.
27. **Password login remains restricted** to ADMIN and SUPER_ADMIN roles only.
28. The `MagicLink` entity gains a `company_id` field. Verify uses the stored `company_id`, **not** the URL slug, to prevent slug-swapping.
29. **Billing suspension checks** must be applied to all slug-scoped auth endpoints.
30. The `GET /api/v1/companies/by-slug/{slug}` endpoint returns which auth providers are configured at the deployment level.
31. **GDPR operations** are **per-company**: export/anonymize operate on the user's data within the current company context. Multi-company users must request GDPR per company.
32. **Deactivation** is per-membership (`company_users.is_active = false`). The identity remains intact. A person deactivated in one company can still access others.
33. **SUPER_ADMIN** stays as `UserRole` enum value. SUPER_ADMIN users have `company_id = NULL` and platform-wide access. They do not use company slugs.
34. When creating a new company, the initial admin user gets both a user row update (or creation) AND a `company_users` record.

---

## Collateral Impact

### Components That Change

| Component | Impact | Action |
|-----------|--------|--------|
| `src/company_bc/company/domain/entities.py` | No slug or auth_mode fields | Add `slug` and `auth_mode` fields with validation methods |
| `src/company_bc/company/infrastructure/models.py` | No slug or auth_mode columns | Add slug column (String 50, unique, indexed), auth_mode column (Enum, default 'domain') |
| `src/company_bc/company/application/commands/create_company.py` | Creates admin user with company_id on user | Also create CompanyUser membership record (dual-write) |
| `src/auth_bc/company_lookup/domain/service.py` | Interface has domain-only methods | Add `is_email_allowed_in_company(email, company_id)` method |
| `src/auth_bc/company_lookup/infrastructure/service.py` | Only checks domain matching | Add membership_only mode: check company_users table instead of email domain |
| `src/auth_bc/magic_link/domain/entities.py` | No company context | Add `company_id` field |
| `src/auth_bc/magic_link/infrastructure/models.py` | No company_id column | Add `company_id` column (nullable for legacy links) |
| `src/auth_bc/magic_link/application/commands/create_magic_link.py` | Resolves company from email domain | Accept `company_id` from slug, validate via `is_email_allowed_in_company()`, store on MagicLink |
| `src/auth_bc/magic_link/application/commands/verify_magic_link.py` | Creates user with domain-resolved company | Two-step: authenticate identity → find/create membership → copy to user row |
| `src/auth_bc/user/application/services/oauth_login_service.py` | Global user lookup, single-step | Accept `company_id`, two-step: find/create identity → find/create membership → copy to user row |
| `src/auth_bc/user/application/commands/password_login.py` | Global email lookup | Accept `company_id`, two-step: find identity → find membership → copy to user row → check ADMIN role from membership |
| `src/auth_bc/user/application/commands/google_oauth_login.py` | No company context | Pass `company_id` to OAuthLoginService |
| `src/auth_bc/user/application/commands/microsoft_oauth_login.py` | No company context | Pass `company_id` to OAuthLoginService |
| `src/auth_bc/user/application/commands/change_user_role.py` | Changes user.role only | Dual-write: also update company_users.role |
| `src/auth_bc/user/application/commands/deactivate_user.py` | Sets user.is_active = false only | Dual-write: also set company_users.is_active = false |
| `src/auth_bc/user/application/commands/activate_user.py` | Sets user.is_active = true only | Dual-write: also set company_users.is_active = true |
| `src/auth_bc/user/application/commands/assign_department.py` | Sets user.department_id only | Dual-write: also update company_users.department_id |
| `adapters/http/api/auth/routers.py` | All endpoints unscoped | Add slug-scoped auth endpoints + company switcher endpoints |
| `adapters/http/api/auth/dependencies.py` | `get_current_user()` trusts JWT blindly | Add check: JWT company_id ≠ user.company_id → 401 |
| `adapters/http/api/auth/schemas.py` | No company context in requests | Add slug path parameter schema, company switcher request/response schemas |
| `adapters/http/api/users/routers.py` | Invite creates user without CompanyUser | Also create CompanyUser on invite (dual-write) |
| `src/audit_bc/audit/application/commands/request_gdpr_export.py` | Uses `find_by_email()` globally | Scope to current company context |
| `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` | Uses `find_by_email()` globally | Scope to current company — deactivate membership; anonymize identity only if zero active memberships remain |
| `core/jwt.py` | `create_token(user_id, company_id, role)` | No structural change — values now sourced from updated user row (which was copied from company_users) |
| `web/app/src/router.tsx` | No `/login/:slug` route | Add slug-parameterized login route |
| `web/app/src/pages/auth/LoginPage.tsx` | No company context | Refactor for slug-aware login with company name display |
| `web/app/src/components/layout/Header.tsx` | No company switcher | Add company dropdown when user has 2+ memberships |
| `web/app/src/pages/admin/CompanySettingsPage.tsx` | No slug or auth_mode | Add slug display/edit, auth mode toggle |
| `web/app/src/contexts/AuthContext.tsx` | No multi-company support | Add company switching, handle 401 from company_id mismatch |

### Components That Do NOT Change

| Component | Why |
|-----------|-----|
| `src/auth_bc/user/domain/entities.py` | User entity keeps all fields unchanged (company_id, role, etc. remain) |
| `src/auth_bc/user/infrastructure/models.py` | UserModel schema unchanged — no column adds, removes, or constraint changes |
| `src/auth_bc/user/domain/enums.py` | UserRole enum unchanged — SUPER_ADMIN stays |
| `src/auth_bc/user/domain/repository.py` | Existing interface methods unchanged — add new methods for CompanyUser separately |
| `src/auth_bc/user/application/queries/list_users.py` | Still queries users WHERE company_id = tenant company — unchanged |
| `src/auth_bc/user/application/queries/get_user_detail.py` | Still reads from user row — unchanged |
| `src/auth_bc/user/application/queries/get_current_user.py` | Still reads from user row — unchanged |
| `src/auth_bc/user/application/commands/set_password.py` | Password is identity-level, stays on user row — unchanged |
| `core/tenant.py` | `set_tenant()` still reads from user row — unchanged |
| `adapters/http/api/auth/dependencies.py` → `require_role()` | Still checks user.role — unchanged (role is on user row, copied from company_users on login/switch) |
| All 80+ existing routers | Read user.company_id, user.role from user row — unchanged |

---

## Migration Strategy

### Database Migration Steps

1. **Create `company_users` table** with columns: id, user_id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at — unique on `(user_id, company_id)`
2. **Populate `company_users`** from existing users: for each user with `company_id IS NOT NULL`, insert a record with the user's current company_id, role, department_id, employee_role_id, is_active
3. **Add `slug` column** to `companies` table (nullable initially)
4. **Auto-generate slugs** for all existing companies from their name (collision handling: append `-2`, `-3`, etc.)
5. **Set `slug` to NOT NULL** and add unique index
6. **Add `auth_mode` column** to `companies` table with default `domain`
7. **Add `company_id` column** to `magic_links` table (nullable for existing links)

### Data Safety

- All steps are **additive** — no columns removed, no constraints changed on existing tables
- The `users` table is **completely untouched** by the migration
- Slug generation is deterministic and idempotent
- No data deletion
- `email`, `google_id`, `microsoft_id` remain globally unique on `users` — no constraint changes
- If rollback needed, simply drop `company_users` table and the new columns — existing behavior restored

---

## Testing Requirements

### Unit Tests

- Slug generation from company name (spaces, special chars, unicode, collision handling)
- Slug validation (length, format, reserved words)
- CompanyUser creation and lookup (find_membership, find_memberships_by_user)
- Copy-on-switch: membership data correctly copied to user row
- Auth flow two-step: identity found → membership found → copy → JWT
- Auth flow two-step: identity found → no membership → domain mode → auto-create membership → copy
- Auth flow two-step: identity found → no membership → membership_only mode → reject
- Auth mode switching (domain ↔ membership_only)
- `is_email_allowed_in_company()` for both modes
- Session invalidation: JWT company_id ≠ user.company_id → 401
- Company switcher token exchange + user row update
- Dual-write: change_role updates both user and company_users
- Dual-write: deactivate updates both user and company_users
- Lockout prevention: cannot deactivate last admin membership in a company
- GDPR anonymization per-company: deactivate membership, anonymize identity only if zero memberships remain

### Integration Tests

- Full magic link flow via slug-scoped endpoints (domain mode)
- Full magic link flow via slug-scoped endpoints (membership_only mode — pre-invited user)
- Magic link in membership_only mode — non-member → rejected
- Full Google OAuth flow via slug-scoped endpoints
- Full Microsoft OAuth flow via slug-scoped endpoints
- Full password login flow via slug-scoped endpoints
- OAuth in membership_only mode — non-member → rejected
- Unscoped endpoint with single-company email → success
- Unscoped endpoint with multi-company email → error with company slugs
- Company switcher: authenticate in company A, switch to company B, verify JWT has B's role and user row updated
- Session invalidation: after switch to B, old JWT for A → 401
- User invite in membership_only mode: creates identity + membership + magic link works
- Deactivate user in company A → still active in company B
- GDPR anonymize in company A → membership deactivated, identity intact (still has company B)
- Slug collision during company creation
- Migration test: existing users correctly have company_users records

---

## Definition of Done

- [ ] `company_users` table created with all membership fields
- [ ] All existing users with company_id have corresponding `company_users` records (migration)
- [ ] `users` table structurally unchanged — no columns added or removed
- [ ] UserRole.SUPER_ADMIN unchanged
- [ ] Company slug field added with auto-generation, validation, uniqueness
- [ ] All existing companies have auto-generated slugs (migration)
- [ ] Auth mode field added to Company with default `domain`
- [ ] Login page at `/login/{slug}` shows company name and available auth methods
- [ ] `/login` without slug redirects or shows company search
- [ ] All four auth flows work via slug-scoped endpoints with two-step (identity → membership → copy)
- [ ] Copy-on-switch: login and switch update user row from company_users
- [ ] Session invalidation: JWT company_id mismatch → 401
- [ ] Unscoped auth endpoints remain functional with backward-compatible behavior
- [ ] Password and OAuth links shared across companies (identity-level)
- [ ] Company switcher API: `GET /my-companies` and `POST /switch-company`
- [ ] Company switcher UI: dropdown in app header (hidden when ≤1 membership)
- [ ] Domain mode works exactly as current behavior (auto-create membership)
- [ ] Membership-only mode: only existing members can log in
- [ ] User invite in membership_only mode creates identity + membership
- [ ] Mode switch domain → membership_only disables self-registration
- [ ] Mode switch membership_only → domain shows warning
- [ ] Dual-write: role/department/is_active changes update both user row and company_users
- [ ] GDPR operations scoped per company
- [ ] Billing suspension checks on all slug-scoped endpoints
- [ ] MagicLink stores company_id to prevent slug-swapping
- [ ] All unit and integration tests pass
- [ ] Migration is safe (additive only, users table untouched, no data loss)
