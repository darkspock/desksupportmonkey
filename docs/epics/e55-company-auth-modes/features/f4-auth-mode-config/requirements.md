# Feature: Auth Mode Configuration

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** F4
**Dependencies:** F2
**Complexity:** M

## Scope

### Included

- **Auth mode toggle endpoints:**
  - `GET /api/v1/companies/{company_id}/auth-mode` — return current auth mode
  - `PATCH /api/v1/companies/{company_id}/auth-mode` — switch between `domain` and `membership_only` (admin only)
- **Mode switching logic:**
  - `domain` → `membership_only`: no data migration needed (all existing users already have CompanyUser records from F2). Self-registration via domain match is simply disabled.
  - `membership_only` → `domain`: warn admin that anyone with a matching email domain can self-register again. Existing memberships preserved.
- **Invite flow changes for membership_only mode:**
  - In `membership_only` mode, the email domain validation that blocks public domains (gmail.com, outlook.com, etc.) is bypassed — admins can invite anyone by email
  - Invite creates User identity (if not exists) + CompanyUser membership + sends magic link
  - CSV import also creates identities + memberships without domain restriction in membership_only mode
  - Quick-create also bypasses domain restriction in membership_only mode
- **CompanyLookupService enhancement** (if not fully done in F2):
  - `is_email_allowed_in_company()` for `membership_only` mode: checks CompanyUser record exists
  - Ensure scoped auth endpoints correctly enforce membership_only — reject users without CompanyUser record
- **Admin settings UI:**
  - Auth mode toggle in company settings page
  - Confirmation dialog when switching modes (especially membership_only → domain)
  - Display current mode with description of what it means
- **Lockout prevention:**
  - Cannot switch to membership_only if there are zero CompanyUser records with ADMIN role (unlikely after F2 migration, but safety check)
  - Cannot remove last admin CompanyUser in membership_only mode

### Excluded (in other features)

- Company slug and login page → F1 (already done)
- CompanyUser entity, scoped auth, dual-writes → F2 (already done)
- Company switcher → F3
- SAML/SSO integration → out of scope for entire epic
- LDAP/Active Directory sync → out of scope for entire epic

## User Value

When this feature is complete:
- Company admins can switch their company to `membership_only` mode to control exactly who has access
- In `membership_only` mode, admins can invite contractors with gmail.com, outlook.com, or any other email — no domain restriction
- Invited contractors can log in via magic link, Google, or Microsoft OAuth
- Admins can switch back to `domain` mode if needed, with a warning about re-enabling self-registration
- Public-domain users who were invited in `membership_only` mode continue to work even after switching back to `domain` mode (their CompanyUser records persist)

## Acceptance Criteria

- [ ] `GET /api/v1/companies/{company_id}/auth-mode` returns current auth mode (admin only)
- [ ] `PATCH /api/v1/companies/{company_id}/auth-mode` switches mode (admin only)
- [ ] Domain → membership_only: succeeds, no data migration, self-registration disabled
- [ ] Membership_only → domain: succeeds with warning, self-registration re-enabled
- [ ] Lockout prevention: cannot switch to membership_only if zero admin CompanyUser records
- [ ] In membership_only mode: invite user with public domain email (gmail.com) succeeds
- [ ] In membership_only mode: invite creates User identity + CompanyUser membership + sends magic link
- [ ] In membership_only mode: CSV import creates identities + memberships without domain restriction
- [ ] In membership_only mode: quick-create bypasses domain restriction
- [ ] In membership_only mode: slug-scoped auth rejects users without CompanyUser record
- [ ] In domain mode: behavior unchanged (email domain match → auto-create CompanyUser on first login)
- [ ] In domain mode: public domain emails still blocked in domain registration (existing behavior)
- [ ] Frontend: auth mode toggle in company settings with descriptions
- [ ] Frontend: confirmation dialog when switching modes
- [ ] Cannot remove last admin CompanyUser in membership_only mode
- [ ] Unit tests for mode switching, invite in both modes, lockout prevention
- [ ] Integration tests for full invite flow in membership_only mode, mode switch round-trip

## Technical Scope

### Entities (owned by this feature)

- None (auth_mode field on Company was created in F1; CompanyUser was created in F2)

### Entities (used from dependencies)

- `Company.auth_mode` — from F1 (toggle value)
- `CompanyUser` — from F2 (check for membership in membership_only mode; count admins for lockout prevention)

### Key Components

**Backend — New:**
- `src/company_bc/company/application/commands/update_auth_mode.py` — command + handler: validate mode switch, check admin count for lockout prevention

**Backend — Modified:**
- `adapters/http/api/companies/routers.py` (or equivalent) — add auth mode endpoints
- `adapters/http/api/users/routers.py` — modify invite flow: bypass domain validation when company auth_mode = membership_only
- `src/auth_bc/user/application/commands/import_users.py` — bypass domain validation when company auth_mode = membership_only
- `web/app/src/pages/admin/CompanySettingsPage.tsx` — add auth mode toggle with descriptions and confirmation dialog
- `web/app/src/locales/en.ts` — add i18n keys for auth mode settings
- `web/app/src/locales/es.ts` — add Spanish translations

## Notes

- The `is_email_allowed_in_company()` method in CompanyLookupService should already handle both modes from F2. F4 primarily adds the toggle endpoint and the invite flow bypass — it does NOT rewrite auth flows.
- The domain validation bypass in the invite flow is the most critical change. Currently, `_ensure_user_for_invite` in `adapters/http/api/users/routers.py` validates that the user's email domain matches the company's registered domains. In `membership_only` mode, this check must be skipped.
- The "warn admin" behavior for membership_only → domain switch is a frontend confirmation dialog, not a server-side blocking mechanism. The backend allows the switch regardless.
