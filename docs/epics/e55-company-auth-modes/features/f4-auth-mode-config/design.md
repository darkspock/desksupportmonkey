# Solution Design: Auth Mode Configuration (F4)

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Contexts:** `company_bc` (primary), `auth_bc` (collateral)

## Summary

F4 adds the ability for company admins to toggle between `domain` and `membership_only` auth modes. The core infrastructure already exists from F1 (AuthMode enum, auth_mode column, Company entity field) and F2 (CompanyUser membership registry, MembershipAuthService with membership_only logic). F4 adds three capabilities:

1. **Auth mode toggle** — new command + endpoint to switch modes with lockout prevention
2. **Invite flow bypass** — in `membership_only` mode, skip domain validation so admins can invite users with any email (gmail, outlook, etc.)
3. **Admin settings UI** — replace read-only auth mode display with an interactive toggle + confirmation dialog

No new entities, tables, or migrations are needed.

## Architecture Decision

**Approach:** Minimal, surgical modifications to existing code paths.

The auth mode toggle is a command in `company_bc` (since Company owns the `auth_mode` field), with the lockout prevention check querying `auth_bc`'s CompanyUserRepository. This is a cross-BC dependency, but acceptable since it's a simple scalar query (`count_admins_in_company`) that already exists in the repository interface.

**Alternatives considered:**
- **Domain event approach** — Company emits `AuthModeChanged` event, auth_bc validates. Rejected: over-engineered for a synchronous validation check.
- **Separate auth mode API under /auth** — Rejected: auth_mode belongs to Company entity, so the endpoint belongs in the company settings domain.
- **Modify existing PUT /my/company-settings** — Rejected: auth mode toggle has different validation (lockout prevention) and different UX (confirmation dialog). Separate endpoint is cleaner.

**Key design choice for invite flow:** Rather than modifying `CompanyLookupService.is_email_allowed_in_company()`, F4 modifies the callers — `_validate_invite_email()`, `_validate_row()`, and `quick_create_employee` — to skip domain checks when `auth_mode == membership_only`. This is simpler and more explicit than adding auth_mode awareness to a cross-BC service.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `Company.auth_mode` field | `src/company_bc/company/domain/entities.py` | Yes | Add `set_auth_mode()` method |
| `AuthMode` enum | `src/company_bc/company/domain/enums.py` | Yes | None |
| `CompanyModel.auth_mode` column | `src/company_bc/company/infrastructure/models.py` | Yes | None |
| `CompanyRepository.save()` | `src/company_bc/company/infrastructure/repository.py` | Yes | None (already persists auth_mode) |
| `MembershipAuthService` | `src/auth_bc/company_user/domain/membership_auth_service.py` | Yes | None (already handles membership_only) |
| `CompanyUserRepository.count_admins_in_company()` | `src/auth_bc/company_user/infrastructure/repository.py` | Yes | None |
| `_validate_invite_email()` | `adapters/http/api/users/routers.py` | Yes | Add auth_mode bypass |
| `ImportUsersService._validate_row()` | `src/auth_bc/user/application/commands/import_users.py` | Yes | Add auth_mode bypass |
| `CompanySettingsPage` | `web/app/src/pages/admin/CompanySettingsPage.tsx` | Yes | Replace read-only with toggle |
| `MyCompanySettingsResponse` | `adapters/http/api/my/schemas.py` | Yes | None (already returns auth_mode) |

## Implementation Plan

### 1. Domain Layer

#### Entity Changes

| Entity | File Path | Change |
|--------|-----------|--------|
| `Company` | `src/company_bc/company/domain/entities.py` | Add `set_auth_mode(mode: AuthMode)` method |

**`Company.set_auth_mode()`:**
```python
def set_auth_mode(self, mode: AuthMode) -> None:
    """Change the company's authentication mode."""
    self.auth_mode = mode
```

No validation in the entity — lockout prevention is an application-layer concern that requires querying the CompanyUser repository.

#### New Domain Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| `NoAdminMembershipError` | `src/company_bc/company/domain/entities.py` | Raised when switching to membership_only with zero admin CompanyUser records |

```python
class NoAdminMembershipError(Exception):
    """Cannot switch to membership_only with no admin memberships."""
    pass
```

### 2. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `UpdateAuthModeCommand` | `UpdateAuthModeCommandHandler` | `src/company_bc/company/application/commands/update_auth_mode.py` | Validates lockout prevention, updates company auth_mode |

**`UpdateAuthModeCommand`:**
```python
@dataclass
class UpdateAuthModeCommand(Command):
    company_id: str
    auth_mode: str  # "domain" or "membership_only"
```

**`UpdateAuthModeCommandHandler`:**
- Dependencies: `CompanyRepositoryInterface`, `CompanyUserRepositoryInterface`
- Logic:
  1. Get company — raise ValueError if not found
  2. Parse auth_mode string → `AuthMode` enum — raise ValueError if invalid
  3. If switching to `membership_only`: check `company_user_repo.count_admins_in_company(company_id) > 0` — raise `NoAdminMembershipError` if zero
  4. Call `company.set_auth_mode(new_mode)`
  5. Save company
- Returns: `None` (CQRS command)

### 3. Infrastructure Layer

No infrastructure changes needed. All models, repositories, and migrations already exist.

### 4. HTTP Layer

#### Endpoints

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| `PATCH` | `/api/v1/my/company-settings/auth-mode` | Switch auth mode | Admin only |

**Design note:** Use `/my/company-settings/auth-mode` (under the existing `/my/` prefix) rather than `/companies/{id}/auth-mode`. The `my` pattern is consistent with existing company settings endpoints (`GET /my/company-settings`, `PUT /my/company-settings`) and avoids exposing company IDs in URLs. The current user's company_id is derived from the JWT.

**PATCH /my/company-settings/auth-mode:**
- Request: `AuthModeUpdateRequest` with `auth_mode: str`
- Success: `200 {"data": {"auth_mode": "membership_only"}}`
- Errors:
  - `NoAdminMembershipError` → 409 Conflict
  - `ValueError` (invalid mode) → 422
- Response: current auth_mode after update

#### Schemas

| Schema | File | Fields |
|--------|------|--------|
| `AuthModeUpdateRequest` | `adapters/http/api/my/schemas.py` | `auth_mode: str` |

#### Router Changes

| File | Change |
|------|--------|
| `adapters/http/api/my/routers.py` | Add `PATCH /company-settings/auth-mode` endpoint |

### 5. Collateral Changes — Invite Flow Bypass

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/users/routers.py` — `_validate_invite_email()` | Modify | Accept `auth_mode` parameter; skip domain check when `membership_only` |
| `adapters/http/api/users/routers.py` — `invite_user` | Modify | Pass company's `auth_mode` to `_validate_invite_email()` |
| `adapters/http/api/users/routers.py` — `quick_create_employee` | Modify | Pass company's `auth_mode` to `_validate_invite_email()` |
| `src/auth_bc/user/application/commands/import_users.py` — `_validate_row()` | Modify | Accept `skip_domain_check` parameter; skip domain validation when True |
| `src/auth_bc/user/application/commands/import_users.py` — `confirm()` | Modify | Pass `skip_domain_check` based on company's auth_mode |
| `src/auth_bc/user/application/commands/import_users.py` — `preview()` | Modify | Pass `skip_domain_check` based on company's auth_mode |

**`_validate_invite_email()` change:**
```python
def _validate_invite_email(email: str, company_id: str, company_repo: CompanyRepository, auth_mode: str = "domain") -> None:
    if auth_mode == "membership_only":
        return  # Skip domain validation — admin can invite anyone
    company = company_repo.find_by_id(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    domain = email.split("@", 1)[-1]
    if domain not in [d.lower() for d in company.email_domains]:
        raise HTTPException(status_code=403, detail="Email domain is not allowed for this company")
```

**`_validate_row()` change:**
```python
def _validate_row(self, row, seen_emails, allowed_domains, company_id, skip_domain_check=False):
    ...
    # Domain check
    if not skip_domain_check:
        domain = email.split("@", 1)[-1].lower()
        if domain not in allowed_domains:
            return f"Email domain '{domain}' is not allowed for this company"
    ...
```

### 6. Frontend

#### CompanySettingsPage Changes

| Component | File | Change |
|-----------|------|--------|
| Auth mode section | `web/app/src/pages/admin/CompanySettingsPage.tsx` | Replace read-only input with toggle button + confirmation dialog |

**UI Design:**
1. Replace `<input readOnly>` with two radio-style buttons (domain / membership_only)
2. Clicking the non-active option opens a confirmation dialog:
   - **domain → membership_only:** "Switch to membership-only mode? Self-registration via email domain will be disabled. Only pre-approved users can sign in."
   - **membership_only → domain:** "Switch to domain-based mode? Anyone with a matching email domain (e.g. @acme.com) will be able to sign in automatically."
3. Confirm triggers `PATCH /my/company-settings/auth-mode`
4. Success: update cached data, show toast
5. Error (409 - no admin memberships): show error toast

**New state:**
- `authModeConfirmOpen: boolean` — confirmation dialog visibility
- `pendingAuthMode: string | null` — the mode user wants to switch to
- `authModeSaving: boolean` — loading state

**New mutation:**
```typescript
const updateAuthMode = useMutation({
  mutationFn: (authMode: string) => api.patch('/my/company-settings/auth-mode', { auth_mode: authMode }),
  onSuccess: ...
});
```

#### Locales

| File | New Keys |
|------|----------|
| `web/app/src/locales/en.ts` | `page.company_settings.auth_mode_switch_to_membership`, `page.company_settings.auth_mode_switch_to_domain`, `page.company_settings.auth_mode_confirm_membership`, `page.company_settings.auth_mode_confirm_domain`, `page.company_settings.auth_mode_updated`, `page.company_settings.auth_mode_no_admin_error` |
| `web/app/src/locales/es.ts` | Same keys with Spanish translations |

**Updated description key:**
- Remove "Contact support to change." from `page.company_settings.auth_mode_desc`

## Testing Strategy

### Unit Tests

| Test File | Scope | Cases |
|-----------|-------|-------|
| `tests/unit/company_bc/company/application/commands/test_update_auth_mode.py` | UpdateAuthModeCommandHandler | switch domain→membership_only succeeds, switch membership_only→domain succeeds, lockout prevention (zero admins → error), invalid mode → error, company not found → error |

### Integration Tests

| Test File | Scope | Cases |
|-----------|-------|-------|
| `tests/integration/test_auth_mode_endpoints.py` | PATCH endpoint | 401 without auth, 403 for non-admin, success domain→membership_only, success membership_only→domain, 409 when no admin memberships, round-trip (toggle both directions) |
| `tests/integration/test_auth_mode_invite_flow.py` | Invite in membership_only | invite with public domain succeeds in membership_only, invite with public domain fails in domain mode, quick-create with public domain succeeds in membership_only, CSV import with public domain succeeds in membership_only |

### Existing Test Verification

Run full suites to verify no regressions:
- `make test` — all unit tests
- `make test-integration` — all integration tests
- `npx tsc --noEmit` — TypeScript check

## Implementation Order

1. Domain: Add `set_auth_mode()` method + `NoAdminMembershipError` exception to Company entity
2. Application: Create `UpdateAuthModeCommand` + handler
3. HTTP: Add schema + PATCH endpoint to `my/routers.py`
4. Collateral: Modify `_validate_invite_email()` to accept auth_mode bypass
5. Collateral: Modify `ImportUsersService._validate_row()` and `confirm()`/`preview()` for domain skip
6. Tests: Unit tests for command handler
7. Tests: Integration tests for endpoint + invite flow
8. Frontend: Types already exist (no changes)
9. Frontend: Update CompanySettingsPage with toggle + confirmation dialog
10. Frontend: Add i18n keys (en.ts, es.ts)
11. Verification: Full test suite + linter + TypeScript check

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Invite bypass allows unintended access | Low | Medium | The bypass only removes domain validation for invites — users still need an explicit invitation from an admin. CompanyUser membership is created at invite time. |
| Lockout: switch to membership_only with no admin memberships | Low | High | Command handler checks `count_admins_in_company() > 0` before allowing switch |
| Import flow domain bypass creates users without CompanyUser | Low | Medium | ImportUsersService already creates CompanyUser records for imported users (F2 dual-write) |
| Frontend cache stale after auth mode change | Low | Low | Invalidate `my-company-settings` query cache on success |

## Open Technical Questions

None — all infrastructure exists from F1/F2, and the implementation is straightforward.
