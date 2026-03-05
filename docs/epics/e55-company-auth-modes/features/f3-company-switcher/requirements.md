# Feature: Company Switcher

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F3
**Dependencies:** F2
**Complexity:** S

## Scope

### Included

- `GET /api/v1/auth/my-companies` — returns all companies where the authenticated user has an active `CompanyUser` record (company name, slug, role, is_current)
- `POST /api/v1/auth/switch-company` — accepts `company_id`, verifies active membership, copies membership data from CompanyUser to user row, issues new JWT. Token exchange + user row update, NOT full re-authentication.
- Frontend: company dropdown in app header (visible only if user has 2+ active memberships)
- Frontend: dropdown shows company name + role in each company; current company highlighted
- Frontend: clicking a different company calls switch-company → replaces JWT → page reloads with new company context
- Frontend: handle 401 from session invalidation (JWT company_id mismatch after switch) — redirect to login or show "session expired" message
- AuthContext: add `companies` state and `switchCompany()` method

### Excluded (in other features)

- CompanyUser entity and membership registry → F2 (already done)
- Scoped auth endpoints → F2 (already done)
- Session invalidation logic in `get_current_user()` → F2 (already done)
- Auth mode toggle → F4
- Concurrent multi-company sessions → out of scope for entire epic

## User Value

When this feature is complete:
- Users with memberships in multiple companies see a company dropdown in the app header
- Switching to another company is instant — no re-authentication, just a token exchange
- The user's role, department, and permissions change automatically to match the target company
- Single-company users see no change — the dropdown is hidden when ≤1 membership
- If a user had tabs open in company A and switches to company B, the old tabs get a 401 and redirect to login

## Acceptance Criteria

- [ ] `GET /api/v1/auth/my-companies` returns list of {company_id, company_name, slug, role, is_current} for active memberships only
- [ ] `GET /api/v1/auth/my-companies` requires authentication (returns 401 if no valid JWT)
- [ ] `POST /api/v1/auth/switch-company` accepts {company_id}, validates active membership, returns new JWT
- [ ] `POST /api/v1/auth/switch-company` copies membership data (company_id, role, department_id, employee_role_id, is_active) from CompanyUser to user row
- [ ] Switch-company returns 404 if user has no active membership in target company
- [ ] Switch-company returns 403 if target membership is inactive
- [ ] After switch, old JWT returns 401 on any endpoint (company_id mismatch)
- [ ] Frontend: company dropdown visible in header when user has 2+ active memberships
- [ ] Frontend: dropdown hidden when user has ≤1 membership
- [ ] Frontend: clicking company triggers switch → JWT replaced → page reloads
- [ ] Frontend: 401 from company_id mismatch handled gracefully (redirect to login or show message)
- [ ] SUPER_ADMIN users: my-companies returns empty list (they don't use company memberships)
- [ ] Unit tests for switch-company command (success, no membership, inactive membership)
- [ ] Integration tests for full switch flow (auth in A → switch to B → verify B's role)

## Technical Scope

### Entities (owned by this feature)

- None (this feature creates no new entities)

### Entities (used from dependencies)

- `CompanyUser` — from F2 (read memberships, copy to user row)
- `User` — existing entity (updated via copy-on-switch)
- `Company` — from F1 (slug, name for dropdown)

### Key Components

**Backend — New:**
- `src/auth_bc/user/application/queries/list_user_companies.py` — query: find all active CompanyUser records for user_id, join with companies for name/slug
- `src/auth_bc/user/application/commands/switch_company.py` — command: verify membership, copy to user row, issue JWT

**Backend — Modified:**
- `adapters/http/api/auth/routers.py` — add `GET /my-companies` and `POST /switch-company` endpoints

**Frontend — Modified:**
- `web/app/src/contexts/AuthContext.tsx` — add `companies` state, `switchCompany()` method, fetch companies on login
- `web/app/src/components/layout/Header.tsx` — add company dropdown (conditionally visible)
- `web/app/src/locales/en.ts` — add i18n keys for company switcher
- `web/app/src/locales/es.ts` — add Spanish translations

## Notes

- The switch-company endpoint is a token exchange, not a full auth flow. It trusts the existing JWT for identity and only verifies the target membership.
- The switch must be atomic: copy membership data to user row AND issue JWT in the same transaction.
- The frontend should optimistically update the UI (show loading state) and handle failures gracefully (revert to current company).
- Consider debouncing rapid company switches to prevent race conditions.
