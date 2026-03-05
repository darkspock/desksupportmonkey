# Feature: Slug & Login Page

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F1
**Dependencies:** None
**Complexity:** S

## Scope

### Included

- Add `slug` field to `Company` entity (domain + infrastructure + migration)
- Slug auto-generation from company name on creation (lowercase, alphanumeric + hyphens, 3–50 chars)
- Slug uniqueness enforcement (including deactivated companies — slugs never released)
- Reserved slug list: `admin`, `api`, `login`, `register`, `reseller`, `app`, `auth`, `super-admin`
- Slug does NOT auto-update on company rename — stable identifier
- Migration: auto-generate slugs for all existing companies with collision handling (append `-2`, `-3`, etc.)
- `GET /api/v1/companies/by-slug/{slug}` — resolve slug to company info (name, auth mode, available OAuth providers)
- `PATCH /api/v1/companies/{company_id}/slug` — admin can edit slug
- Super admin can edit slug for any company
- Company slug shown in company settings page (admin UI)
- Frontend: `/login/{slug}` shows company-branded login page (company name displayed, available auth methods)
- Frontend: `/login` without slug shows a "Find your company" input or redirects if user has a prior session cookie
- Add `auth_mode` column to Company (default `domain`) — needed for the login page to know which auth methods to show

### Excluded (in other features)

- Slug-scoped auth endpoints (`POST /api/v1/auth/{slug}/magic-link`, etc.) → F2
- `CompanyUser` membership registry → F2
- Two-step auth flow (identity → membership → copy) → F2
- Dual-writes to user commands → F2
- Company switcher API and UI → F3
- Auth mode switching logic and membership_only enforcement → F4
- Invite flow changes for public domains → F4

## User Value

When this feature is complete:
- Every company has a unique, branded login URL (e.g., `/login/acme-corp`)
- Users visiting the URL see their company's name on the login page
- Available auth methods (magic link, password, Google, Microsoft) are displayed
- Authentication itself still uses the existing unscoped endpoints — this feature does NOT change how auth works
- Users visiting `/login` without a slug can search for their company
- Company admins can view and edit their company's slug in settings
- Super admins can edit slugs for any company

## Acceptance Criteria

- [ ] `Company` entity has `slug` field (String 50, unique, indexed)
- [ ] `Company` entity has `auth_mode` field (Enum: `domain`/`membership_only`, default `domain`)
- [ ] Slug auto-generated from company name on creation (`"Acme Corp"` → `acme-corp`)
- [ ] Slug validated: lowercase alphanumeric + hyphens, 3–50 chars
- [ ] Reserved slugs rejected (admin, api, login, register, reseller, app, auth, super-admin)
- [ ] Slug uniqueness enforced (including deactivated companies)
- [ ] Collision handling: if `acme-corp` exists, auto-generate `acme-corp-2`, `acme-corp-3`, etc.
- [ ] Migration: all existing companies have auto-generated slugs
- [ ] `GET /api/v1/companies/by-slug/{slug}` returns company name, auth_mode, available OAuth providers
- [ ] `PATCH /api/v1/companies/{company_id}/slug` allows admin to change slug with uniqueness validation
- [ ] Frontend: `/login/{slug}` renders company-branded login page with correct auth method buttons
- [ ] Frontend: `/login` without slug shows company search (or redirects if single company in cookie)
- [ ] Company settings page shows slug field (editable by admin)
- [ ] All existing auth flows continue working via unscoped endpoints (no regression)
- [ ] Unit tests for slug generation, validation, collision handling, reserved words
- [ ] Integration test for slug resolve endpoint and slug update endpoint

## Technical Scope

### Entities (owned by this feature)

- `Company.slug` — new field on existing entity
- `Company.auth_mode` — new field on existing entity (Enum: `domain`, `membership_only`, default `domain`)

### Entities (used from dependencies)

- None (this is the foundation feature)

### Key Components

**Backend:**
- `src/company_bc/company/domain/entities.py` — add `slug`, `auth_mode` fields; add `generate_slug()`, `validate_slug()`, `update_slug()` methods
- `src/company_bc/company/domain/enums.py` — add `AuthMode` enum
- `src/company_bc/company/infrastructure/models.py` — add `slug` column (String 50, unique, indexed), `auth_mode` column (String 20, default 'domain')
- `src/company_bc/company/application/commands/create_company.py` — auto-generate slug on company creation
- `alembic/versions/` — migration: add slug (nullable) → populate → set NOT NULL + unique index; add auth_mode column
- `adapters/http/api/` — new slug resolve endpoint; slug update endpoint; modify company settings response to include slug
- `adapters/http/api/auth/schemas.py` — add `CompanyBySlugResponse` schema

**Frontend:**
- `web/app/src/router.tsx` — add `/login/:slug` route
- `web/app/src/pages/auth/LoginPage.tsx` — refactor: if slug param present, fetch company info and display name; if no slug, show company search
- `web/app/src/pages/admin/CompanySettingsPage.tsx` — add slug display and edit

## Notes

- The `auth_mode` field is created here (with default `domain`) so the login page can show the correct auth methods, but the enforcement logic (blocking non-members in `membership_only` mode) is in F4. In F1, `auth_mode` is read-only display information.
- The existing unscoped auth endpoints remain the only functioning auth path after F1. The slug login page uses them. Slug-scoped auth endpoints come in F2.
- Slug generation must handle unicode company names gracefully (transliterate or strip to ASCII).
