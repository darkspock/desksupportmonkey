# Implementation Tasks: Company Switcher

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 11
**Estimated Complexity:** S

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain | 0 | — (no new domain components) |
| Infrastructure | 0 | — (no new infra components) |
| Application - Queries | 1 | M |
| Application - Services | 1 | M |
| HTTP - Schemas | 1 | S |
| HTTP - Router Endpoints | 1 | M |
| Tests - Unit | 1 | M |
| Tests - Integration | 1 | M |
| Frontend - Types | 1 | S |
| Frontend - AuthContext | 1 | M |
| Frontend - Header Dropdown | 1 | M |
| Frontend - Locales | 1 | S |
| Verification | 1 | S |

---

## Phase 1: Application Layer

### TASK-001: Create ListUserCompaniesQuery + Handler

**Phase:** Application - Queries
**Complexity:** M
**Dependencies:** None (uses existing repos from F2)

**Description:**
Create the query and handler that returns all active company memberships for a user, batch-fetching company data to avoid N+1 queries.

**File:** `src/auth_bc/user/application/queries/list_user_companies.py`

**Implementation:**
- `ListUserCompaniesQuery` dataclass with `user_id: str`
- `UserCompanyDto` dataclass with `company_id`, `company_name`, `slug`, `role` (str), `is_current` (bool)
- `ListUserCompaniesQueryHandler(QueryHandler[ListUserCompaniesQuery, list[UserCompanyDto]])`:
  - Dependencies: `CompanyUserRepositoryInterface`, `CompanyRepositoryInterface`, `UserRepositoryInterface`
  - `handle()` method:
    1. Get user to know current `company_id`
    2. Get all active memberships via `company_user_repo.find_active_by_user_id()`
    3. Batch-fetch companies via `company_repo.find_by_ids()`
    4. Filter out inactive companies
    5. Build `UserCompanyDto` list with `is_current` flag

**Acceptance Criteria:**
- [x] Query inherits from `Query` base class
- [x] Handler inherits from `QueryHandler[ListUserCompaniesQuery, list[UserCompanyDto]]`
- [x] Query and Handler in same file
- [x] Returns `UserCompanyDto` list (not entities)
- [x] Batch-fetches companies (no N+1)
- [x] Filters out inactive companies
- [x] `is_current` flag matches user's current `company_id`
- [x] Returns empty list for user not found or no memberships

---

### TASK-002: Create SwitchCompanyService

**Phase:** Application - Services
**Complexity:** M
**Dependencies:** None (uses existing repos from F2)

**Description:**
Create the application service that validates membership, copies membership data to the user row, and issues a new JWT.

**File:** `src/auth_bc/user/application/commands/switch_company.py`

**Implementation:**
- `SwitchCompanyRequest` dataclass with `user_id: str`, `target_company_id: str`
- `SwitchCompanyService`:
  - Dependencies: `UserRepositoryInterface`, `CompanyUserRepositoryInterface`, `JWTService`
  - `handle(request: SwitchCompanyRequest) -> str`:
    1. Get user from repo — raise `MembershipNotFoundError` if not found
    2. Find membership via `company_user_repo.find_by_user_and_company()` — raise `MembershipNotFoundError` if None
    3. Check `membership.is_active` — raise `MembershipDeactivatedError` if inactive
    4. Copy membership data to user row: `company_id`, `role`, `department_id`, `employee_role_id`
    5. Save user
    6. Issue and return new JWT via `jwt_service.create_token()`

**Acceptance Criteria:**
- [x] Returns JWT access_token string (application service pattern, not pure CQRS command)
- [x] Raises `MembershipNotFoundError` when user not found
- [x] Raises `MembershipNotFoundError` when no membership in target company
- [x] Raises `MembershipDeactivatedError` when membership is inactive
- [x] Copies all 4 fields from membership to user row: `company_id`, `role`, `department_id`, `employee_role_id`
- [x] Saves user after copy
- [x] JWT contains updated `company_id` and `role`

---

## Phase 2: HTTP Layer

### TASK-003: Add Auth Schemas for Company Switcher

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** None

**Description:**
Add Pydantic request/response schemas for the company switcher endpoints.

**File:** `adapters/http/api/auth/schemas.py`

**Changes:**
- Add `SwitchCompanyRequest(BaseModel)` with `company_id: str`
- Add `UserCompanyResponse(BaseModel)` with `company_id`, `company_name`, `slug`, `role`, `is_current`

**Acceptance Criteria:**
- [x] `SwitchCompanyRequest` schema with `company_id` field
- [x] `UserCompanyResponse` schema with all 5 fields from design
- [x] Both inherit from `BaseModel`

---

### TASK-004: Add Router Endpoints (my-companies + switch-company)

**Phase:** HTTP - Router Endpoints
**Complexity:** M
**Dependencies:** TASK-001, TASK-002, TASK-003

**Description:**
Add `GET /my-companies` and `POST /switch-company` endpoints to the auth router.

**File:** `adapters/http/api/auth/routers.py`

**Changes:**

**GET /my-companies:**
- Requires authentication (`get_current_user`)
- Dependencies: `company_user_repo`, `company_repo`, `user_repo`
- SUPER_ADMIN returns empty list immediately
- Instantiates `ListUserCompaniesQueryHandler`, calls `handle()`, maps DTOs to `UserCompanyResponse`
- Returns `{"data": [...]}`

**POST /switch-company:**
- Requires authentication (`get_current_user`)
- Request body: `SwitchCompanyRequest` (imported from schemas — note: distinct from the application-layer `SwitchCompanyRequest`)
- Dependencies: `user_repo`, `company_user_repo`
- Instantiates `SwitchCompanyService`, calls `handle()`
- Exception mapping:
  - `MembershipNotFoundError` → 404
  - `MembershipDeactivatedError` → 403
- Returns `{"data": {"access_token": "..."}}`

**New imports needed:**
- `ListUserCompaniesQuery`, `ListUserCompaniesQueryHandler` from application queries
- `SwitchCompanyRequest as SwitchCompanyInput`, `SwitchCompanyService` from application commands
- `MembershipNotFoundError`, `MembershipDeactivatedError` from company_user domain
- `SwitchCompanyRequest`, `UserCompanyResponse` from schemas
- `UserRole` from user domain enums

**Acceptance Criteria:**
- [x] `GET /my-companies` returns list of company memberships
- [x] `GET /my-companies` requires authentication (401 without JWT)
- [x] `GET /my-companies` returns empty list for SUPER_ADMIN
- [x] `POST /switch-company` accepts `company_id`, returns new JWT
- [x] `POST /switch-company` returns 404 for no membership
- [x] `POST /switch-company` returns 403 for inactive membership
- [x] All domain exceptions caught and mapped to HTTP errors (no 500s)
- [x] Response wrapped in `{"data": ...}` format

---

## Phase 3: Tests

### TASK-005: Unit Tests — Query Handler + Switch Service

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**Description:**
Create unit tests for `ListUserCompaniesQueryHandler` and `SwitchCompanyService` using mocks.

**Files:**
- `tests/unit/auth_bc/user/application/queries/test_list_user_companies.py`
- `tests/unit/auth_bc/user/application/commands/test_switch_company.py`

**ListUserCompaniesQueryHandler tests:**
- Returns active memberships with company data (name, slug, role, is_current)
- Filters out inactive companies (company.is_active = False)
- Returns empty list for user with no memberships
- Returns empty list for user not found
- `is_current` flag is True only for the user's current company_id
- Batch-fetches companies (verify `find_by_ids()` called once with correct IDs)

**SwitchCompanyService tests:**
- Success: copies membership data to user row, returns JWT
- No membership: raises `MembershipNotFoundError`
- Inactive membership: raises `MembershipDeactivatedError`
- User not found: raises `MembershipNotFoundError`
- JWT contains updated `company_id` and `role` (decode returned token to verify)
- Copies all 4 fields: `company_id`, `role`, `department_id`, `employee_role_id`
- Saves user after copy (`user_repo.save` called)

**Acceptance Criteria:**
- [x] All query handler test cases pass
- [x] All switch service test cases pass
- [x] Uses MagicMock for all repository dependencies
- [x] No database required

---

### TASK-006: Integration Tests — Company Switcher Endpoints

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create integration tests for `GET /my-companies` and `POST /switch-company` endpoints.

**File:** `tests/integration/test_company_switcher_endpoints.py`

**Test cases:**

**GET /my-companies:**
- Returns 401 without authentication
- Returns active memberships for authenticated user (verify response shape)
- SUPER_ADMIN returns empty list
- Only returns active memberships (inactive CompanyUser filtered)
- Only returns active companies (inactive Company filtered)

**POST /switch-company:**
- Success: new JWT returned, user row updated with target company data
- 404 for company user has no membership in
- 403 for inactive membership
- Full flow: login in company A → switch to company B → verify role changed → GET /me shows B's data
- Session invalidation: old JWT returns 401 after switch (company_id mismatch)

**Acceptance Criteria:**
- [x] All endpoint test cases pass
- [x] Uses real database (integration test pattern)
- [x] Tests full HTTP request/response cycle
- [x] Verifies response shapes match schema
- [x] Session invalidation test verifies old JWT rejected

---

## Phase 4: Frontend

### TASK-007: Add CompanyMembership Type

**Phase:** Frontend - Types
**Complexity:** S
**Dependencies:** None

**Description:**
Add the `CompanyMembership` interface to the frontend types.

**File:** `web/app/src/types/index.ts`

**Changes:**
```typescript
export interface CompanyMembership {
  company_id: string;
  company_name: string;
  slug: string;
  role: UserRole;
  is_current: boolean;
}
```

**Acceptance Criteria:**
- [x] `CompanyMembership` interface exported
- [x] All 5 fields present with correct types
- [x] `role` uses `UserRole` type

---

### TASK-008: Extend AuthContext with Companies State + switchCompany

**Phase:** Frontend - AuthContext
**Complexity:** M
**Dependencies:** TASK-007

**Description:**
Extend `AuthContext` with `companies` state, `fetchCompanies()` helper, and `switchCompany()` method.

**File:** `web/app/src/contexts/AuthContext.tsx`

**Changes:**
1. Add `companies: CompanyMembership[]` to `AuthState` (default: `[]`)
2. Add `switchCompany: (companyId: string) => Promise<void>` to `AuthContextType`
3. Add `fetchCompanies()` callback — calls `GET /auth/my-companies`, updates state
4. Modify `fetchUser()` — after successful user fetch, call `fetchCompanies()` (non-blocking)
5. Add `switchCompany()` — calls `POST /auth/switch-company`, stores new token, re-fetches user
6. Update `logout()` — reset `companies` to `[]`
7. Update initial state — include `companies: []`
8. Pass `companies` and `switchCompany` in context value

**Acceptance Criteria:**
- [x] `companies` state initialized as empty array
- [x] `fetchCompanies()` calls `GET /auth/my-companies` and updates state
- [x] `fetchUser()` triggers `fetchCompanies()` after success (non-blocking)
- [x] `switchCompany()` calls POST, stores new token, re-fetches user
- [x] `logout()` clears companies
- [x] `switchCompany` available in context value

---

### TASK-009: Add Company Dropdown to Header

**Phase:** Frontend - Header Dropdown
**Complexity:** M
**Dependencies:** TASK-008

**Description:**
Replace the static company name badge with a clickable dropdown when the user has 2+ active memberships.

**File:** `web/app/src/components/layout/Header.tsx`

**Changes:**
1. Destructure `companies` and `switchCompany` from `useAuth()`
2. Add state: `switching` (boolean), `companyDropdownOpen` (boolean)
3. Add `companyRef` for click-outside detection
4. Add `handleSwitch(companyId)` — sets switching, calls `switchCompany()`, redirects to `/` on success
5. Replace company badge section:
   - If `companies.length <= 1`: keep existing static badge (no changes)
   - If `companies.length >= 2`: render clickable badge with chevron-down icon → dropdown with company list
6. Dropdown items: company name + role badge, current company highlighted
7. While `switching`: show loading text, disable dropdown
8. Click-outside closes dropdown (add to existing `useEffect` or new one)

**Acceptance Criteria:**
- [x] Dropdown hidden when ≤1 membership (existing behavior preserved)
- [x] Dropdown visible when 2+ memberships
- [x] Current company highlighted in dropdown
- [x] Each company shows name and role
- [x] Clicking a company triggers switch → JWT replaced → page reloads (`window.location.href = '/'`)
- [x] Loading state shown while switching
- [x] Click-outside closes dropdown

---

### TASK-010: Add i18n Keys for Company Switcher

**Phase:** Frontend - Locales
**Complexity:** S
**Dependencies:** None

**Description:**
Add internationalization keys for the company switcher UI.

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**English keys:**
```
'header.switch_company': 'Switch company',
'header.switching': 'Switching...',
'header.current_company': 'Current',
```

**Spanish keys:**
```
'header.switch_company': 'Cambiar empresa',
'header.switching': 'Cambiando...',
'header.current_company': 'Actual',
```

**Acceptance Criteria:**
- [x] 3 new keys added to `en.ts`
- [x] 3 new keys added to `es.ts`
- [x] Keys used in Header component

---

## Phase 5: Verification

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
TASK-001 (ListQuery) ──┬──> TASK-004 (Router) ──> TASK-006 (Integration Tests)
                       │         ↑
TASK-002 (SwitchSvc) ──┤    TASK-003 (Schemas)
                       │
                       └──> TASK-005 (Unit Tests)

TASK-007 (TS Types) ──> TASK-008 (AuthContext) ──> TASK-009 (Header Dropdown)

TASK-010 (Locales)  ← independent

TASK-011 (Verification) depends on ALL
```

## Execution Order

**Batch 1 (Parallel):** TASK-001, TASK-002, TASK-003, TASK-007, TASK-010
- Application query, application service, schemas, frontend type, locales — all independent

**Batch 2 (Parallel):** TASK-004, TASK-005, TASK-008
- Router endpoints (depends on 001+002+003), unit tests (depends on 001+002), AuthContext (depends on 007)

**Batch 3 (Parallel):** TASK-006, TASK-009
- Integration tests (depends on 004), Header dropdown (depends on 008)

**Batch 4:** TASK-011
- Verification — depends on all

## Final Checklist

- [x] All tasks completed
- [x] All tests passing (`make test`, `make test-integration`)
- [x] mypy passes (`make lint`)
- [x] TypeScript compiles (`npx tsc --noEmit`)
- [x] No regressions in existing functionality
- [x] `slicing.md` updated — F3 marked as Done
