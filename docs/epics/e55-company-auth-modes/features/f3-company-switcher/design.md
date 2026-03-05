# Solution Design: Company Switcher

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `auth_bc` (primary)

## Summary

Add two authenticated endpoints (`GET /auth/my-companies` and `POST /auth/switch-company`) that let users list their active company memberships and switch between them. The switch is a token exchange — it copies membership data from the target CompanyUser to the user row, issues a new JWT, and invalidates old sessions via the existing company_id mismatch check. The frontend adds a company dropdown in the header (visible only with 2+ memberships) and a `switchCompany()` method in AuthContext.

## Architecture Decision

**Approach:** One new query (list companies) and one new application service (switch company) in `auth_bc`, reusing the existing `MembershipAuthService._copy_membership_to_user()` pattern from F2. No new entities or database changes required.

**Why this approach:**
- F2 already built the `CompanyUser` membership registry and the copy-on-switch semantics — F3 is purely about exposing them to the user
- The switch endpoint is NOT a full auth flow — it trusts the existing JWT for identity and only validates the target membership
- Reusing `MembershipAuthService._copy_membership_to_user()` ensures consistency with login-time membership resolution
- The company_id mismatch check in `get_current_user()` (F2) automatically invalidates old JWTs after a switch — no new session invalidation code needed

**Alternatives considered:**
- Reuse `MembershipAuthService.resolve_membership()` for switch — rejected because resolve_membership auto-creates memberships for domain-mode companies, which is unwanted for explicit switching. Switch should only work with existing active memberships.
- Store companies list in JWT claims — rejected because JWT would grow and go stale; better to query fresh on demand

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| CompanyUser entity | `src/auth_bc/company_user/domain/entities.py` | Yes | No changes |
| CompanyUserRepository | `src/auth_bc/company_user/infrastructure/repository.py` | Yes | No changes — `find_active_by_user_id()` already exists |
| CompanyRepositoryInterface | `src/company_bc/company/domain/repository.py` | Yes | No changes — `find_by_ids()` already exists |
| User entity | `src/auth_bc/user/domain/entities.py` | Yes | No changes |
| UserRepository | `src/auth_bc/user/infrastructure/repository.py` | Yes | No changes |
| JWTService | `core/jwt.py` | Yes | No changes |
| MembershipAuthService | `src/auth_bc/company_user/domain/membership_auth_service.py` | Partial | Extract `_copy_membership_to_user()` pattern for reuse |
| Auth dependencies | `adapters/http/api/auth/dependencies.py` | Yes | Already provides `get_current_user`, `get_company_user_repo`, `get_company_repo` |
| Auth routers | `adapters/http/api/auth/routers.py` | Partial | Add 2 new endpoints |
| Auth schemas | `adapters/http/api/auth/schemas.py` | Partial | Add request/response schemas |
| AuthContext | `web/app/src/contexts/AuthContext.tsx` | Partial | Add `companies` state and `switchCompany()` |
| Header | `web/app/src/components/layout/Header.tsx` | Partial | Add company dropdown |
| User type | `web/app/src/types/index.ts` | Partial | Add `CompanyMembership` interface |
| Locales | `web/app/src/locales/en.ts`, `es.ts` | Partial | Add switcher i18n keys |

## Implementation Plan

### 1. Domain Layer

No new entities, value objects, or enums. F3 uses existing domain components from F2.

#### Domain Exceptions (reuse existing)

| Exception | Location | Used By |
|-----------|----------|---------|
| `MembershipNotFoundError` | `src/auth_bc/company_user/domain/entities.py` | Switch command — user has no membership in target company |
| `MembershipDeactivatedError` | `src/auth_bc/company_user/domain/entities.py` | Switch command — membership exists but is inactive |

### 2. Application Layer

#### Queries

| Query | Handler | File Path | Description |
|-------|---------|-----------|-------------|
| `ListUserCompaniesQuery` | `ListUserCompaniesQueryHandler` | `src/auth_bc/user/application/queries/list_user_companies.py` | Returns all active company memberships for a user |

**ListUserCompaniesQuery:**
```python
@dataclass
class ListUserCompaniesQuery(Query):
    user_id: str

@dataclass
class UserCompanyDto:
    company_id: str
    company_name: str
    slug: str
    role: str          # UserRole.value
    is_current: bool   # True if company_id matches the user's current company_id

class ListUserCompaniesQueryHandler(QueryHandler[ListUserCompaniesQuery, list[UserCompanyDto]]):
    def __init__(
        self,
        company_user_repo: CompanyUserRepositoryInterface,
        company_repo: CompanyRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.company_user_repo = company_user_repo
        self.company_repo = company_repo
        self.user_repo = user_repo

    def handle(self, query: ListUserCompaniesQuery) -> list[UserCompanyDto]:
        # 1. Get user to know current company_id
        user = self.user_repo.find_by_id(query.user_id)
        if user is None:
            return []

        # 2. Get all active memberships
        memberships = self.company_user_repo.find_active_by_user_id(query.user_id)
        if not memberships:
            return []

        # 3. Batch-fetch companies (no N+1)
        company_ids = [m.company_id for m in memberships]
        companies = self.company_repo.find_by_ids(company_ids)
        company_map = {c.id: c for c in companies}

        # 4. Build DTOs
        result = []
        for m in memberships:
            company = company_map.get(m.company_id)
            if company is None or not company.is_active:
                continue
            result.append(UserCompanyDto(
                company_id=m.company_id,
                company_name=company.name,
                slug=company.slug or "",
                role=m.role.value,
                is_current=(m.company_id == user.company_id),
            ))
        return result
```

**Key design decisions:**
- Batch-fetches companies using `find_by_ids()` — no N+1 queries
- Filters out inactive companies (a company could be deactivated after the membership was created)
- `is_current` flag lets the frontend highlight the active company without extra state

#### Commands / Application Services

| Service | File Path | Description |
|---------|-----------|-------------|
| `SwitchCompanyService` | `src/auth_bc/user/application/commands/switch_company.py` | Validates membership, copies to user row, issues JWT |

**SwitchCompanyService:**
```python
@dataclass
class SwitchCompanyRequest:
    user_id: str
    target_company_id: str

class SwitchCompanyService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_user_repo: CompanyUserRepositoryInterface,
        jwt_service: JWTService,
    ):
        self.user_repo = user_repo
        self.company_user_repo = company_user_repo
        self.jwt_service = jwt_service

    def handle(self, request: SwitchCompanyRequest) -> str:
        """Switch user's active company. Returns new JWT access_token."""
        # 1. Get user
        user = self.user_repo.find_by_id(request.user_id)
        if user is None:
            raise MembershipNotFoundError("User not found")

        # 2. Find membership in target company
        membership = self.company_user_repo.find_by_user_and_company(
            request.user_id, request.target_company_id
        )
        if membership is None:
            raise MembershipNotFoundError(
                "No membership found in target company"
            )
        if not membership.is_active:
            raise MembershipDeactivatedError(
                "Your membership in this company is deactivated"
            )

        # 3. Copy membership data to user row (same pattern as MembershipAuthService)
        user.company_id = request.target_company_id
        user.role = membership.role
        user.department_id = membership.department_id
        user.employee_role_id = membership.employee_role_id
        self.user_repo.save(user)

        # 4. Issue new JWT with updated company_id
        return self.jwt_service.create_token(
            user_id=user.id,
            company_id=user.company_id,
            role=user.role.value,
        )
```

**Key design decisions:**
- This is an application service (not a pure CQRS command) because it returns a JWT token — same pattern as `PasswordLoginService` and `VerifyMagicLinkService`
- Does NOT auto-create memberships — only switches to existing active ones (unlike `MembershipAuthService.resolve_membership()`)
- Copy-to-user-row is inline (4 field assignments) rather than calling MembershipAuthService, to avoid pulling in the CompanyLookup dependency which is irrelevant for switching
- Old JWT automatically becomes invalid because `get_current_user()` checks `jwt.company_id == user.company_id` — after the switch, the user's company_id has changed, so any old JWT with the previous company_id returns 401

### 3. Infrastructure Layer

No new infrastructure components needed. All repositories and models already exist from F1 and F2.

### 4. HTTP Layer

#### Endpoints

| Method | Route | Description | Auth | Request Body | Response |
|--------|-------|-------------|------|-------------|----------|
| GET | `/api/v1/auth/my-companies` | List user's active company memberships | Required | — | `{"data": [UserCompanyResponse]}` |
| POST | `/api/v1/auth/switch-company` | Switch to a different company | Required | `{"company_id": "..."}` | `{"data": {"access_token": "..."}}` |

#### Schemas (add to `adapters/http/api/auth/schemas.py`)

```python
class SwitchCompanyRequest(BaseModel):
    company_id: str

class UserCompanyResponse(BaseModel):
    company_id: str
    company_name: str
    slug: str
    role: str
    is_current: bool
```

#### Router Implementation (add to `adapters/http/api/auth/routers.py`)

**GET /my-companies:**
```python
@router.get("/my-companies")
def list_my_companies(
    current_user: User = Depends(get_current_user),
    company_user_repo: CompanyUserRepository = Depends(get_company_user_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
    user_repo: UserRepository = Depends(get_user_repo),
):
    # SUPER_ADMIN has no company memberships
    if current_user.role == UserRole.SUPER_ADMIN:
        return {"data": []}

    handler = ListUserCompaniesQueryHandler(
        company_user_repo=company_user_repo,
        company_repo=company_repo,
        user_repo=user_repo,
    )
    dtos = handler.handle(ListUserCompaniesQuery(user_id=current_user.id))
    return {"data": [
        UserCompanyResponse(
            company_id=d.company_id,
            company_name=d.company_name,
            slug=d.slug,
            role=d.role,
            is_current=d.is_current,
        ).model_dump()
        for d in dtos
    ]}
```

**POST /switch-company:**
```python
@router.post("/switch-company")
def switch_company(
    body: SwitchCompanyRequest,
    current_user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    company_user_repo: CompanyUserRepository = Depends(get_company_user_repo),
):
    handler = SwitchCompanyService(
        user_repo=user_repo,
        company_user_repo=company_user_repo,
        jwt_service=JWTService(),
    )
    try:
        access_token = handler.handle(SwitchCompanyRequest(
            user_id=current_user.id,
            target_company_id=body.company_id,
        ))
    except MembershipNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active membership found in target company",
        )
    except MembershipDeactivatedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your membership in this company is deactivated",
        )
    return {"data": {"access_token": access_token}}
```

**Exception mapping:**

| Domain Exception | HTTP Status | Detail |
|-----------------|-------------|--------|
| `MembershipNotFoundError` | 404 | "No active membership found in target company" |
| `MembershipDeactivatedError` | 403 | "Your membership in this company is deactivated" |

### 5. Frontend

#### Types (modify `web/app/src/types/index.ts`)

```typescript
export interface CompanyMembership {
  company_id: string;
  company_name: string;
  slug: string;
  role: UserRole;
  is_current: boolean;
}
```

#### AuthContext (modify `web/app/src/contexts/AuthContext.tsx`)

**New state and methods:**
```typescript
interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  companies: CompanyMembership[];  // NEW
}

interface AuthContextType extends AuthState {
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  isRole: (...roles: string[]) => boolean;
  switchCompany: (companyId: string) => Promise<void>;  // NEW
}
```

**Implementation:**
```typescript
// Fetch companies after user is loaded
const fetchCompanies = useCallback(async () => {
  try {
    const { data } = await api.get('/auth/my-companies');
    setState(s => ({ ...s, companies: data.data }));
  } catch {
    setState(s => ({ ...s, companies: [] }));
  }
}, []);

// Call fetchCompanies after fetchUser succeeds
const fetchUser = useCallback(async (token: string) => {
  try {
    const { data } = await api.get('/auth/me');
    setState({ user: data.data, token, loading: false, companies: [] });
    // Fetch companies in background (non-blocking)
    fetchCompanies();
  } catch {
    localStorage.removeItem('token');
    setState({ user: null, token: null, loading: false, companies: [] });
  }
}, [fetchCompanies]);

// Switch company: call API, replace token, reload user
const switchCompany = async (companyId: string) => {
  const { data } = await api.post('/auth/switch-company', { company_id: companyId });
  const newToken = data.data.access_token;
  localStorage.setItem('token', newToken);
  await fetchUser(newToken);
};
```

**Key decisions:**
- `companies` is fetched after user loads (non-blocking, in background)
- `switchCompany()` replaces the token and re-fetches user + companies
- On switch failure, the error propagates to the caller (Header component handles it)

#### Header Company Dropdown (modify `web/app/src/components/layout/Header.tsx`)

Replace the static company name badge with a clickable dropdown when `companies.length >= 2`:

```typescript
// In Header component, add:
const { user, logout, refreshUser, companies, switchCompany } = useAuth();
const [switching, setSwitching] = useState(false);
const [companyDropdownOpen, setCompanyDropdownOpen] = useState(false);
const companyRef = useRef<HTMLDivElement>(null);

const handleSwitch = async (companyId: string) => {
  if (switching) return;
  setSwitching(true);
  setCompanyDropdownOpen(false);
  try {
    await switchCompany(companyId);
    window.location.href = '/';  // Full reload to reset all cached state
  } catch {
    setSwitching(false);
    // Error handled — user stays on current company
  }
};
```

**UI behavior:**
- If `companies.length <= 1`: show current company name as a static badge (existing behavior, unchanged)
- If `companies.length >= 2`: show current company name with a chevron-down icon; clicking opens a dropdown listing all companies; the current company is highlighted; clicking another company triggers `handleSwitch()`
- While switching: show a loading spinner on the badge, disable the dropdown
- After switch: full page reload (`window.location.href = '/'`) to reset all cached React Query data, WebSocket connections, etc.

**Why full reload instead of React Query invalidation:**
- Switching companies changes the tenant context — every cached query result is now invalid
- A full reload is the simplest and most reliable approach
- The user expects a fresh page when switching companies (like switching Slack workspaces)

#### Locales

**English (`web/app/src/locales/en.ts`):**
```
'header.switch_company': 'Switch company',
'header.switching': 'Switching...',
'header.current_company': 'Current',
```

**Spanish (`web/app/src/locales/es.ts`):**
```
'header.switch_company': 'Cambiar empresa',
'header.switching': 'Cambiando...',
'header.current_company': 'Actual',
```

### 6. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `adapters/http/api/auth/routers.py` | Add endpoints | `GET /my-companies`, `POST /switch-company` |
| `adapters/http/api/auth/schemas.py` | Add schemas | `SwitchCompanyRequest`, `UserCompanyResponse` |
| `web/app/src/contexts/AuthContext.tsx` | Extend | Add `companies` state, `switchCompany()`, `fetchCompanies()` |
| `web/app/src/components/layout/Header.tsx` | Extend | Company dropdown (conditional on 2+ memberships) |
| `web/app/src/types/index.ts` | Add type | `CompanyMembership` interface |
| `web/app/src/locales/en.ts` | Add keys | 3 i18n keys for switcher |
| `web/app/src/locales/es.ts` | Add keys | 3 i18n keys for switcher |

#### Breaking Changes

None. All changes are additive. Existing endpoints and behavior are unchanged.

## Testing Strategy

### Unit Tests

| Test | File | Priority |
|------|------|----------|
| ListUserCompaniesQueryHandler — returns active memberships with company data | `tests/unit/auth_bc/user/application/queries/test_list_user_companies.py` | High |
| ListUserCompaniesQueryHandler — filters inactive companies | Same | High |
| ListUserCompaniesQueryHandler — returns empty for user with no memberships | Same | Medium |
| ListUserCompaniesQueryHandler — is_current flag matches user's company_id | Same | High |
| SwitchCompanyService — success: copies membership, returns JWT | `tests/unit/auth_bc/user/application/commands/test_switch_company.py` | High |
| SwitchCompanyService — no membership: raises MembershipNotFoundError | Same | High |
| SwitchCompanyService — inactive membership: raises MembershipDeactivatedError | Same | High |
| SwitchCompanyService — JWT contains updated company_id and role | Same | High |

### Integration Tests

| Test | File | Priority |
|------|------|----------|
| GET /my-companies — returns 401 without auth | `tests/integration/test_company_switcher_endpoints.py` | High |
| GET /my-companies — returns memberships for authenticated user | Same | High |
| GET /my-companies — SUPER_ADMIN returns empty list | Same | Medium |
| POST /switch-company — success: new JWT, user row updated | Same | High |
| POST /switch-company — 404 for non-member company | Same | High |
| POST /switch-company — 403 for inactive membership | Same | High |
| Full flow: login in A → switch to B → verify role changed | Same | High |
| Session invalidation: old JWT rejected after switch | Same | High |

### Frontend Tests

TypeScript compilation check (`npx tsc --noEmit`) after all frontend changes.

## Implementation Order

1. [ ] Application: `ListUserCompaniesQuery` + `ListUserCompaniesQueryHandler`
2. [ ] Application: `SwitchCompanyService`
3. [ ] HTTP: schemas (`SwitchCompanyRequest`, `UserCompanyResponse`)
4. [ ] HTTP: router endpoints (`GET /my-companies`, `POST /switch-company`)
5. [ ] Unit tests (query handler + switch service)
6. [ ] Integration tests (endpoint-level)
7. [ ] Frontend: types (`CompanyMembership`)
8. [ ] Frontend: AuthContext (companies state + switchCompany)
9. [ ] Frontend: Header dropdown
10. [ ] Frontend: locales (en + es)
11. [ ] Verification: full test suite + linter + TypeScript check

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Race condition: rapid company switches | Low | Medium | Full page reload resets all state; debounce not needed since redirect prevents re-clicking |
| Stale companies list after admin adds user to new company | Low | Low | `fetchCompanies()` runs on every `fetchUser()` call, so login/refresh picks up changes |
| Old tabs getting 401 after switch | Expected | Low | Existing auth interceptor in `api.ts` handles 401 → dispatches `AUTH_UNAUTHORIZED_EVENT` → AuthContext clears state → redirect to login. Already working from F2. |
