# Feature: Scoped Auth & Membership Registry

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F2
**Dependencies:** F1
**Complexity:** L

## Scope

### Included

- **New `CompanyUser` entity** (membership registry) — one record per person per company
  - Fields: id (ULID), user_id (FK), company_id (FK), role, department_id, employee_role_id, is_active, created_at, updated_at
  - Constraint: unique on (user_id, company_id)
  - Domain entity, infrastructure model, repository interface + implementation
- **Data migration** — populate `company_users` from existing users: for each user with `company_id IS NOT NULL`, insert a record with user's current company_id, role, department_id, employee_role_id, is_active
- **MagicLink.company_id** — add company_id field to MagicLink entity and model (nullable for legacy links)
- **Slug-scoped auth endpoints** (all 5 auth flows):
  - `POST /api/v1/auth/{slug}/magic-link` — request magic link scoped to company
  - `POST /api/v1/auth/{slug}/verify` — verify magic link scoped to company
  - `POST /api/v1/auth/{slug}/login` — password login scoped to company
  - `POST /api/v1/auth/{slug}/oauth/google` — Google OAuth scoped to company
  - `POST /api/v1/auth/{slug}/oauth/microsoft` — Microsoft OAuth scoped to company
- **Two-step auth flow** in all scoped endpoints:
  1. Resolve slug → company_id (404 if not found)
  2. Authenticate identity (global lookup on users table — same as today)
  3. If no user: create user row (email, name, company_id = this company, role = EMPLOYEE)
  4. Find `CompanyUser` for (user_id, company_id):
     - Found + active → copy membership data to user row
     - Found + inactive → reject ("Your account in this company is deactivated")
     - Not found (domain mode) → check email domain match → auto-create CompanyUser with EMPLOYEE role → copy to user row
     - Not found (membership_only mode) → reject ("You don't have access to this company")
  5. Issue JWT with (user_id, company_id, role) from updated user row
- **Copy-on-switch semantics** — UPDATE users SET company_id=X, role=Y, department_id=Z, employee_role_id=W, is_active=A
- **Session invalidation** — `get_current_user()` adds check: if JWT's `company_id` ≠ user row's `company_id`, return 401 (skip for SUPER_ADMIN where company_id is NULL)
- **Backward compatibility** — existing unscoped endpoints remain:
  - If email domain resolves to exactly one company → proceed (current behavior)
  - If email matches multiple companies → return error with available company slugs
  - SUPER_ADMIN login unaffected (company_id = NULL)
- **Billing suspension checks** on all slug-scoped endpoints
- **Dual-writes on existing user commands** (to keep `company_users` in sync):
  - `change_user_role` → also update `company_users.role`
  - `deactivate_user` → also set `company_users.is_active = false`
  - `activate_user` → also set `company_users.is_active = true`
  - `assign_department` → also update `company_users.department_id`
- **Create company** → also create CompanyUser for initial admin
- **Invite user** → also create CompanyUser membership
- **Import users (CSV)** → also create CompanyUser memberships
- **Quick-create user** → also create CompanyUser membership
- **CompanyLookupInterface** — add `is_email_allowed_in_company(email, company_id) -> bool` method
  - For `domain` mode: checks email domain match (existing logic)
  - For `membership_only` mode: checks if any user with this email has a CompanyUser record in this company
- **GDPR scoping** — export and anonymize scoped to current company context; anonymize deactivates membership; anonymize identity only if zero active memberships remain
- **Frontend**: update login page to POST to slug-scoped endpoints when slug is present in URL

### Excluded (in other features)

- Company slug field, migration, slug resolve endpoint → F1 (already done)
- Company switcher API and UI → F3
- Auth mode toggle in admin settings → F4
- Invite flow changes for public-domain emails in membership_only mode → F4

## User Value

When this feature is complete:
- Users can authenticate via any auth method from the slug-scoped login page, and their identity is correctly bound to the target company
- First-time users in `domain` mode auto-get a membership (same as current behavior)
- Users who belong to a company see the correct role, department, and permissions
- Existing unscoped auth endpoints continue working for single-company users
- User management commands (role changes, deactivation, department assignment) keep the membership registry in sync
- GDPR operations are correctly scoped per company
- Session invalidation prevents stale sessions after company switch (prepares for F3)

## Acceptance Criteria

- [ ] `CompanyUser` entity created with all fields (id, user_id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at)
- [ ] `CompanyUser` model with composite unique on (user_id, company_id)
- [ ] `CompanyUserRepository` with methods: save, find_by_user_and_company, find_by_user_id, find_by_company_id, count_admins_in_company
- [ ] Migration: all existing users with company_id have CompanyUser records
- [ ] MagicLink entity and model have company_id field (nullable for legacy)
- [ ] `POST /api/v1/auth/{slug}/magic-link` works — resolves slug, validates email, stores company_id on MagicLink
- [ ] `POST /api/v1/auth/{slug}/verify` works — two-step: authenticate identity → find/create membership → copy to user row → issue JWT
- [ ] `POST /api/v1/auth/{slug}/login` works — password login scoped to company
- [ ] `POST /api/v1/auth/{slug}/oauth/google` works — Google OAuth scoped to company
- [ ] `POST /api/v1/auth/{slug}/oauth/microsoft` works — Microsoft OAuth scoped to company
- [ ] Two-step auth: new user in domain mode → user created + CompanyUser auto-created + user row updated
- [ ] Two-step auth: existing user with active membership → CompanyUser data copied to user row
- [ ] Two-step auth: existing user with inactive membership → rejected with "deactivated" message
- [ ] Two-step auth: existing user with no membership in membership_only mode → rejected with "no access" message
- [ ] Copy-on-switch: user row reflects membership data after login
- [ ] Session invalidation: JWT company_id ≠ user.company_id → 401 (SUPER_ADMIN exempt)
- [ ] Unscoped endpoints: single-company email → works as today
- [ ] Unscoped endpoints: multi-company email → error with available slugs
- [ ] Billing suspension checks on all slug-scoped endpoints
- [ ] Dual-write: change_role updates both user row and CompanyUser
- [ ] Dual-write: deactivate_user sets both user.is_active and CompanyUser.is_active to false
- [ ] Dual-write: activate_user sets both to true
- [ ] Dual-write: assign_department updates both
- [ ] Create company: initial admin gets CompanyUser record
- [ ] Invite user: creates CompanyUser membership
- [ ] Import users: creates CompanyUser memberships
- [ ] Quick-create user: creates CompanyUser membership
- [ ] `is_email_allowed_in_company()` works for domain mode (email domain match)
- [ ] `is_email_allowed_in_company()` works for membership_only mode (CompanyUser exists)
- [ ] GDPR export scoped to current company
- [ ] GDPR anonymize: deactivates membership; anonymizes identity only if zero active memberships remain
- [ ] Frontend: slug login page posts to slug-scoped endpoints
- [ ] All unit and integration tests pass

## Technical Scope

### Entities (owned by this feature)

- `CompanyUser` — new entity (membership registry)
- `MagicLink.company_id` — new field on existing entity

### Entities (used from dependencies)

- `Company.slug` — from F1 (for slug resolution)
- `Company.auth_mode` — from F1 (for domain vs membership_only check in auth flow)
- `User` — unchanged structurally, but user row is now updated via copy-on-switch

### Key Components

**Backend — New:**
- `src/auth_bc/company_user/domain/entities.py` — CompanyUser dataclass
- `src/auth_bc/company_user/domain/repository.py` — CompanyUserRepositoryInterface
- `src/auth_bc/company_user/infrastructure/models.py` — CompanyUserModel
- `src/auth_bc/company_user/infrastructure/repository.py` — CompanyUserRepository
- `alembic/versions/` — migration: create company_users table + populate from existing users; add company_id to magic_links

**Backend — Modified:**
- `src/auth_bc/company_lookup/domain/service.py` — add `is_email_allowed_in_company()` to interface
- `src/auth_bc/company_lookup/infrastructure/service.py` — implement `is_email_allowed_in_company()` for both modes
- `src/auth_bc/magic_link/domain/entities.py` — add `company_id` field
- `src/auth_bc/magic_link/infrastructure/models.py` — add `company_id` column
- `src/auth_bc/magic_link/application/commands/create_magic_link.py` — accept `company_id`, validate via `is_email_allowed_in_company()`, store on MagicLink
- `src/auth_bc/magic_link/application/commands/verify_magic_link.py` — two-step: identity → membership → copy
- `src/auth_bc/user/application/services/oauth_login_service.py` — accept `company_id`, two-step flow
- `src/auth_bc/user/application/commands/password_login.py` — accept `company_id`, two-step flow
- `src/auth_bc/user/application/commands/google_oauth_login.py` — pass `company_id` to OAuthLoginService
- `src/auth_bc/user/application/commands/microsoft_oauth_login.py` — pass `company_id` to OAuthLoginService
- `src/auth_bc/user/application/commands/change_user_role.py` — dual-write: also update CompanyUser.role
- `src/auth_bc/user/application/commands/deactivate_user.py` — dual-write: also set CompanyUser.is_active = false
- `src/auth_bc/user/application/commands/activate_user.py` — dual-write: also set CompanyUser.is_active = true
- `src/auth_bc/user/application/commands/assign_department.py` — dual-write: also update CompanyUser.department_id
- `src/auth_bc/user/application/commands/import_users.py` — also create CompanyUser memberships
- `src/company_bc/company/application/commands/create_company.py` — also create CompanyUser for initial admin
- `adapters/http/api/auth/routers.py` — add slug-scoped auth endpoints
- `adapters/http/api/auth/dependencies.py` — add JWT company_id mismatch check in `get_current_user()`
- `adapters/http/api/users/routers.py` — invite and quick-create also create CompanyUser
- `src/audit_bc/audit/application/commands/request_gdpr_export.py` — scope to current company
- `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` — deactivate membership; anonymize identity only if zero active memberships

**Frontend:**
- `web/app/src/pages/auth/LoginPage.tsx` — post to slug-scoped endpoints when slug param is present

## Notes

- This is the largest and most complex feature in the epic. It touches 20+ existing files. The two-step auth flow is the core architectural change.
- The `company_users` data migration must be the FIRST operation in the Alembic migration file — all subsequent auth flows depend on memberships existing.
- Dual-writes must be atomic (same DB transaction). Use the existing session/UoW pattern.
- The session invalidation check in `get_current_user()` must explicitly exempt SUPER_ADMIN users (company_id = NULL in JWT and user row).
- The backward-compatible unscoped endpoints must detect multi-company scenarios and return a useful error directing the user to the slug-based login.
