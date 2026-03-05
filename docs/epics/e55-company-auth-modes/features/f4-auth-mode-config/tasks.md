# Implementation Tasks: Auth Mode Configuration

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 12
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Entity Changes | 1 | S |
| Application - Commands | 1 | M |
| HTTP - Schema + Endpoint | 1 | S |
| Collateral - Invite Flow Bypass | 1 | M |
| Collateral - Import Users Bypass | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration (endpoint) | 1 | M |
| Tests - Integration (invite flow) | 1 | M |
| Frontend - CompanySettingsPage | 1 | M |
| Frontend - Locales | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Domain Layer

### TASK-001: Add set_auth_mode() + NoAdminMembershipError to Company Entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add a `set_auth_mode()` method to the Company entity and a `NoAdminMembershipError` exception class. The method simply assigns the new auth_mode. Lockout prevention validation is handled in the application layer.

**File:** `src/company_bc/company/domain/entities.py`

**Changes:**
1. Add `NoAdminMembershipError` exception class:
```python
class NoAdminMembershipError(Exception):
    """Cannot switch to membership_only with no admin memberships."""
    pass
```

2. Add `set_auth_mode()` method to Company:
```python
def set_auth_mode(self, mode: AuthMode) -> None:
    """Change the company's authentication mode."""
    self.auth_mode = mode
```

**Acceptance Criteria:**
- [x] `NoAdminMembershipError` exception class defined
- [x] `set_auth_mode(mode: AuthMode)` method added to Company
- [x] Method assigns `self.auth_mode = mode`
- [x] No validation in entity (application-layer concern)

---

## Phase 2: Application Layer

### TASK-002: Create UpdateAuthModeCommand + Handler

**Phase:** Application - Commands
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Create the command and handler that validates lockout prevention and updates the company's auth_mode.

**File:** `src/company_bc/company/application/commands/update_auth_mode.py`

**Implementation:**
- `UpdateAuthModeCommand(Command)` dataclass with `company_id: str`, `auth_mode: str`
- `UpdateAuthModeCommandHandler(CommandHandler[UpdateAuthModeCommand])`:
  - Dependencies: `CompanyRepositoryInterface` (company_bc), `CompanyUserRepositoryInterface` (auth_bc)
  - `execute()` method:
    1. Get company from repo — raise `ValueError("Company not found")` if None
    2. Parse `auth_mode` string → `AuthMode` enum — raise `ValueError("Invalid auth mode")` if invalid
    3. If switching to `membership_only`: check `company_user_repo.count_admins_in_company(company_id) > 0` — raise `NoAdminMembershipError` if zero
    4. Call `company.set_auth_mode(new_mode)`
    5. Save company via repo
    6. Return `None` (CQRS command)

**Acceptance Criteria:**
- [x] Command inherits from `Command` base class
- [x] Handler inherits from `CommandHandler[UpdateAuthModeCommand]`
- [x] Command and Handler in same file
- [x] `execute()` returns `None`
- [x] Raises `ValueError` when company not found
- [x] Raises `ValueError` when auth_mode string is invalid
- [x] Raises `NoAdminMembershipError` when switching to membership_only with zero admin CompanyUser records
- [x] Allows switch to domain without admin count check
- [x] Saves company after setting auth_mode

---

## Phase 3: HTTP Layer

### TASK-003: Add Auth Mode Schema + PATCH Endpoint

**Phase:** HTTP - Schema + Router
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add the `AuthModeUpdateRequest` schema and `PATCH /company-settings/auth-mode` endpoint to the my router.

**Files:**
- `adapters/http/api/my/schemas.py` — add `AuthModeUpdateRequest`
- `adapters/http/api/my/routers.py` — add PATCH endpoint

**Schema:**
```python
class AuthModeUpdateRequest(BaseModel):
    auth_mode: str
```

**Endpoint:**
- `PATCH /api/v1/my/company-settings/auth-mode`
- Requires `require_role(UserRole.ADMIN)`
- Dependencies: `company_repo`, `company_user_repo` (via `get_company_user_repo` from auth dependencies)
- Instantiates `UpdateAuthModeCommandHandler`, calls `execute()`
- Exception mapping:
  - `NoAdminMembershipError` → 409 Conflict
  - `ValueError` → 422 Unprocessable Entity
- Success: `{"data": {"auth_mode": "membership_only"}}`

**Acceptance Criteria:**
- [x] `AuthModeUpdateRequest` schema with `auth_mode: str` field
- [x] `PATCH /company-settings/auth-mode` endpoint added to my router
- [x] Requires admin role (403 for non-admin)
- [x] Returns 401 without auth
- [x] Returns 409 for `NoAdminMembershipError`
- [x] Returns 422 for `ValueError` (invalid mode)
- [x] Returns 200 with updated auth_mode on success
- [x] Response wrapped in `{"data": ...}` format

---

## Phase 4: Collateral Changes

### TASK-004: Modify Invite + Quick-Create to Bypass Domain Validation in membership_only Mode

**Phase:** Collateral - Invite Flow
**Complexity:** M
**Dependencies:** None (no dependency on TASK-001/002/003 — this is an independent code change)

**Description:**
Modify `_validate_invite_email()` to accept an `auth_mode` parameter and skip domain validation when `membership_only`. Update `invite_user` and `quick_create_employee` endpoints to pass the company's `auth_mode`.

**File:** `adapters/http/api/users/routers.py`

**Changes:**

1. **`_validate_invite_email()`** — add `auth_mode` parameter with default `"domain"`:
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

2. **`invite_user` endpoint** — fetch company to get auth_mode, pass to `_validate_invite_email()`:
```python
company = company_repo.find_by_id(company_id)
auth_mode = company.auth_mode.value if company else "domain"
_validate_invite_email(email, company_id, company_repo, auth_mode=auth_mode)
```

3. **`quick_create_employee` endpoint** — same pattern: fetch company, pass auth_mode:
```python
company = company_repo.find_by_id(company_id)
auth_mode = company.auth_mode.value if company else "domain"
_validate_invite_email(email, company_id, company_repo, auth_mode=auth_mode)
```

**Acceptance Criteria:**
- [x] `_validate_invite_email()` skips domain check when `auth_mode == "membership_only"`
- [x] `_validate_invite_email()` preserves existing behavior when `auth_mode == "domain"`
- [x] `invite_user` endpoint passes company's auth_mode to validation
- [x] `quick_create_employee` endpoint passes company's auth_mode to validation
- [x] In membership_only mode: invite with gmail.com email succeeds
- [x] In domain mode: invite with gmail.com email still fails (403)

---

### TASK-005: Modify ImportUsersService to Bypass Domain Validation in membership_only Mode

**Phase:** Collateral - Import Users
**Complexity:** M
**Dependencies:** None (independent code change)

**Description:**
Modify `ImportUsersService._validate_row()` to accept a `skip_domain_check` parameter, and update `confirm()` and `preview()` to pass this flag based on the company's auth_mode.

**File:** `src/auth_bc/user/application/commands/import_users.py`

**Changes:**

1. **`_validate_row()`** — add `skip_domain_check=False` parameter:
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

2. **`confirm()`** — determine skip_domain_check from company.auth_mode:
```python
skip_domain = company.auth_mode.value == "membership_only" if hasattr(company, 'auth_mode') else False
# Pass to _validate_row call:
error = self._validate_row(row, seen_emails, allowed_domains, company_id, skip_domain_check=skip_domain)
```

3. **`preview()`** — same pattern for the preview flow.

**Acceptance Criteria:**
- [x] `_validate_row()` skips domain check when `skip_domain_check=True`
- [x] `_validate_row()` preserves existing behavior when `skip_domain_check=False`
- [x] `confirm()` passes `skip_domain_check` based on company auth_mode
- [x] `preview()` passes `skip_domain_check` based on company auth_mode
- [x] CSV import with public-domain emails succeeds in membership_only mode
- [x] CSV import with public-domain emails still fails in domain mode

---

## Phase 5: Tests

### TASK-006: Unit Tests — UpdateAuthModeCommandHandler

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-002

**Description:**
Create unit tests for UpdateAuthModeCommandHandler using mocks.

**File:** `tests/unit/company_bc/company/application/commands/test_update_auth_mode.py`

**Test cases:**
- Switch domain → membership_only succeeds (with admin memberships)
- Switch membership_only → domain succeeds (no admin count check needed)
- Lockout prevention: zero admin CompanyUser records → raises `NoAdminMembershipError`
- Invalid auth_mode string → raises `ValueError`
- Company not found → raises `ValueError`
- Saves company after successful mode change
- Does not save when validation fails

**Acceptance Criteria:**
- [x] All test cases pass
- [x] Uses MagicMock for repository dependencies
- [x] No database required
- [x] Verifies `company.set_auth_mode()` called with correct enum
- [x] Verifies `company_repo.save()` called on success
- [x] Verifies `company_repo.save()` NOT called on validation failure

---

### TASK-007: Integration Tests — Auth Mode PATCH Endpoint

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-003

**Description:**
Create integration tests for `PATCH /my/company-settings/auth-mode`.

**File:** `tests/integration/test_auth_mode_endpoints.py`

**Test cases:**
- Returns 401/403 without authentication
- Returns 403 for non-admin user
- Success: domain → membership_only (with admin CompanyUser)
- Success: membership_only → domain
- Returns 409 when no admin CompanyUser records
- Round-trip: toggle both directions and verify state after each
- Returns 422 for invalid auth_mode value

**Acceptance Criteria:**
- [x] All test cases pass
- [x] Uses real database (integration test pattern)
- [x] Tests full HTTP request/response cycle
- [x] Verifies response shapes match schema
- [x] Creates CompanyUser admin membership for success tests

---

### TASK-008: Integration Tests — Invite Flow in membership_only Mode

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-004, TASK-005

**Description:**
Create integration tests verifying invite and import flows work correctly in both auth modes.

**File:** `tests/integration/test_auth_mode_invite_flow.py`

**Test cases:**
- Invite with public domain (gmail.com) succeeds in membership_only mode
- Invite with public domain (gmail.com) fails in domain mode (existing behavior)
- Quick-create with public domain succeeds in membership_only mode
- CSV import with public domain succeeds in membership_only mode (preview + confirm)

**Acceptance Criteria:**
- [x] All test cases pass
- [x] Tests use real database
- [x] Verifies User + CompanyUser created for invite in membership_only mode
- [x] Verifies 403 for public domain invite in domain mode

---

## Phase 6: Frontend

### TASK-009: Update CompanySettingsPage with Auth Mode Toggle + Confirmation Dialog

**Phase:** Frontend - CompanySettingsPage
**Complexity:** M
**Dependencies:** TASK-003

**Description:**
Replace the read-only auth mode display with an interactive toggle and confirmation dialog.

**File:** `web/app/src/pages/admin/CompanySettingsPage.tsx`

**Changes:**

1. **New state:**
   - `authModeConfirmOpen: boolean` — confirmation dialog visibility
   - `pendingAuthMode: string | null` — the mode user wants to switch to
   - `authModeSaving: boolean` — loading state

2. **New mutation:**
```typescript
const updateAuthMode = useMutation({
  mutationFn: (authMode: string) => api.patch('/my/company-settings/auth-mode', { auth_mode: authMode }),
  onSuccess: (res) => {
    const next = res.data.data;
    queryClient.setQueryData(['my-company-settings'], (old: CompanySettings) => ({
      ...old,
      auth_mode: next.auth_mode,
    }));
    showToast({ title: t('page.company_settings.auth_mode_updated'), variant: 'success' });
    setAuthModeConfirmOpen(false);
    setPendingAuthMode(null);
  },
  onError: (err: any) => {
    const detail = err?.response?.data?.detail;
    if (err?.response?.status === 409) {
      showToast({ title: t('page.company_settings.auth_mode_no_admin_error'), variant: 'error' });
    } else {
      showToast({ title: detail || 'Error', variant: 'error' });
    }
  },
});
```

3. **Replace read-only input** with two radio-style buttons (domain / membership_only):
   - Active mode highlighted with primary color
   - Inactive mode clickable → opens confirmation dialog

4. **Confirmation dialog:**
   - domain → membership_only: warning about self-registration being disabled
   - membership_only → domain: warning about self-registration being re-enabled
   - Confirm button triggers `updateAuthMode.mutate(pendingAuthMode)`
   - Cancel button closes dialog

**Acceptance Criteria:**
- [x] Read-only input replaced with interactive toggle
- [x] Current mode visually highlighted
- [x] Clicking non-active mode opens confirmation dialog
- [x] Confirmation dialog shows appropriate warning message for each direction
- [x] Confirm triggers PATCH API call
- [x] Success: cache updated, toast shown, dialog closed
- [x] Error 409: shows "no admin membership" error toast
- [x] Loading state during API call
- [x] Cancel closes dialog without changes

---

### TASK-010: Add i18n Keys for Auth Mode Settings

**Phase:** Frontend - Locales
**Complexity:** S
**Dependencies:** None

**Description:**
Add internationalization keys for the auth mode toggle UI.

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**English keys:**
```
'page.company_settings.auth_mode_switch_to_membership': 'Switch to membership only',
'page.company_settings.auth_mode_switch_to_domain': 'Switch to domain-based',
'page.company_settings.auth_mode_confirm_membership': 'Switch to membership-only mode? Self-registration via email domain will be disabled. Only pre-approved users will be able to sign in.',
'page.company_settings.auth_mode_confirm_domain': 'Switch to domain-based mode? Anyone with a matching email domain will be able to sign in automatically.',
'page.company_settings.auth_mode_updated': 'Authentication mode updated',
'page.company_settings.auth_mode_no_admin_error': 'Cannot switch to membership-only mode: no admin memberships found. Create at least one admin membership first.',
```

**Spanish keys:**
```
'page.company_settings.auth_mode_switch_to_membership': 'Cambiar a solo membresía',
'page.company_settings.auth_mode_switch_to_domain': 'Cambiar a basado en dominio',
'page.company_settings.auth_mode_confirm_membership': '¿Cambiar a modo de solo membresía? El auto-registro por dominio de email se desactivará. Solo los usuarios pre-aprobados podrán iniciar sesión.',
'page.company_settings.auth_mode_confirm_domain': '¿Cambiar a modo basado en dominio? Cualquier persona con un dominio de email coincidente podrá iniciar sesión automáticamente.',
'page.company_settings.auth_mode_updated': 'Modo de autenticación actualizado',
'page.company_settings.auth_mode_no_admin_error': 'No se puede cambiar a modo de solo membresía: no se encontraron membresías de administrador. Cree al menos una membresía de administrador primero.',
```

**Updated key:**
- `page.company_settings.auth_mode_desc` — remove "Contact support to change." text

**Acceptance Criteria:**
- [x] 6 new keys added to `en.ts`
- [x] 6 new keys added to `es.ts`
- [x] `auth_mode_desc` updated to remove "Contact support" text
- [x] Keys used in CompanySettingsPage component

---

## Phase 7: Verification

### TASK-011: Run Full Test Suite + Linter + TypeScript Check

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Run the full test suite, linter, and TypeScript compiler to verify no regressions.

**Commands:**
```bash
make test              # Unit tests
make test-integration  # Integration tests
make lint              # mypy + flake8
cd web/app && npx tsc --noEmit  # TypeScript check
```

**Acceptance Criteria:**
- [x] All unit tests pass (including pre-existing)
- [x] All integration tests pass
- [x] mypy passes (no new errors)
- [x] flake8 passes
- [x] TypeScript compiles cleanly
- [x] No regressions in existing functionality

---

## Dependency Graph

```
TASK-001 (Domain: set_auth_mode + exception)
  └──> TASK-002 (Application: command + handler)
         └──> TASK-003 (HTTP: schema + endpoint)
                ├──> TASK-007 (Integration: endpoint tests)
                └──> TASK-009 (Frontend: settings page)

TASK-004 (Collateral: invite bypass)  ← independent
TASK-005 (Collateral: import bypass)  ← independent

TASK-004 + TASK-005 ──> TASK-008 (Integration: invite flow tests)

TASK-010 (Locales) ← independent

TASK-011 (Verification) depends on ALL
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-004, TASK-005, TASK-010
- Domain entity change, invite bypass, import bypass, and locales — all independent

**Batch 2 (Parallel):** TASK-002, TASK-006
- Application command + handler, unit tests (both depend on TASK-001)

**Batch 3 (Parallel):** TASK-003, TASK-008
- HTTP endpoint (depends on TASK-002), invite flow integration tests (depends on TASK-004+005)

**Batch 4 (Parallel):** TASK-007, TASK-009
- Endpoint integration tests (depends on TASK-003), Frontend settings page (depends on TASK-003)

**Batch 5:** TASK-011
- Verification — depends on all

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (`make test`, `make test-integration`)
- [x] mypy passes (`make lint`)
- [x] TypeScript compiles (`npx tsc --noEmit`)
- [x] No regressions in existing functionality
- [x] `slicing.md` updated — F4 marked as Done
