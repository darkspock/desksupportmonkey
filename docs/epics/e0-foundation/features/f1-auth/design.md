# Solution Design: F1 - Authentication & Authorization

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-02-15
**Bounded Context:** `auth_bc`

---

## Summary

Implement magic link authentication (request + verify), JWT generation, RBAC middleware, multi-tenancy base repository, super admin auto-creation, and email sending via SMTP. Follows DDD + CQRS patterns from the framework.

---

## Architecture Decision

Auth is implemented as the `auth_bc` bounded context with two aggregates: `user` and `magic_link`. The auth flow is command-driven (create magic link, verify magic link, create user). The `/me` endpoint is a query. RBAC and tenant scoping are cross-cutting concerns implemented as FastAPI dependencies.

No event bus in E0 - domain events will be added in E4 (Real-time & Notifications).

---

## Implementation Plan

### 1. Domain Layer

#### Enums

**UserRole** - `src/auth_bc/user/domain/enums.py`
```python
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    TECHNICIAN = "technician"
    EMPLOYEE = "employee"
```

Role hierarchy (for RBAC): super_admin > admin > technician > employee

#### Entities

**User** - `src/auth_bc/user/domain/entities.py`
- Properties: id, email, name, role (UserRole), company_id, is_active, created_at, updated_at
- Factory: `User.create(email, role, company_id)` - generates ULID, sets is_active=True
- Methods: `deactivate()`, `change_role(new_role)`

**MagicLink** - `src/auth_bc/magic_link/domain/entities.py`
- Properties: id, email, token, expires_at, used_at, created_at
- Factory: `MagicLink.create(email, token, ttl_hours=24)` - generates ULID, sets expires_at
- Methods: `mark_used()`, `is_expired()`, `is_used()`
- State: pending (created) -> used (mark_used) / expired (is_expired check)

#### Repository Interfaces

**UserRepositoryInterface** - `src/auth_bc/user/domain/repository.py`
- `save(user: User) -> None`
- `find_by_id(user_id: str) -> Optional[User]`
- `find_by_email(email: str) -> Optional[User]`

**MagicLinkRepositoryInterface** - `src/auth_bc/magic_link/domain/repository.py`
- `save(magic_link: MagicLink) -> None`
- `find_by_token(token: str) -> Optional[MagicLink]`
- `count_recent_by_email(email: str, since: datetime) -> int`
- `delete_older_than(days: int) -> int`

#### Domain Services

**CompanyDomainLookup** - `src/auth_bc/company_lookup/domain/service.py`
- `find_company_by_email_domain(email: str) -> Optional[Company]`
- Reads from companies table + company_domains (E1 will add domains, for now check if any company exists with a matching pattern)

Note: For E0, company-domain matching will be simplified. A `company_email_domains` table will be added in E1. For now, we seed a company and match by convention.

### 2. Application Layer (CQRS)

#### Commands

**CreateMagicLink** - `src/auth_bc/magic_link/application/commands/create_magic_link.py`
- Command: `CreateMagicLinkCommand(email: str)`
- Handler:
  1. Check email domain matches a company (find_company_by_email_domain)
  2. Check rate limit (count_recent_by_email < 5 in last hour)
  3. Generate token (random URL-safe string)
  4. Create MagicLink entity
  5. Save to repository
  6. Send email via EmailService
- Exceptions: `InvalidEmailDomainError`, `RateLimitExceededError`, `EmailSendError`

**VerifyMagicLink** - `src/auth_bc/magic_link/application/commands/verify_magic_link.py`
- Command: `VerifyMagicLinkCommand(token: str)`
- Handler:
  1. Find magic link by token
  2. Validate not used, not expired
  3. Mark as used
  4. Find or create user (find_by_email, or create with employee role)
  5. Generate JWT (user_id, company_id, role, exp=24h)
  6. Return JWT (exception to "commands return None" - auth commands return tokens)
- Exceptions: `InvalidTokenError`, `ExpiredTokenError`, `UsedTokenError`

#### Queries

**GetCurrentUser** - `src/auth_bc/user/application/queries/get_current_user.py`
- Query: `GetCurrentUserQuery(user_id: str)`
- Handler: Find user by ID, return UserDto
- Returns: `UserDto(id, email, name, role, company_id, is_active)`

### 3. Infrastructure Layer

#### Repositories

**UserRepository** - `src/auth_bc/user/infrastructure/repository.py`
- Implements UserRepositoryInterface
- Uses UserModel from F0
- Model-to-entity and entity-to-model conversion

**MagicLinkRepository** - `src/auth_bc/magic_link/infrastructure/repository.py`
- Implements MagicLinkRepositoryInterface
- Uses MagicLinkModel from F0
- `count_recent_by_email`: COUNT WHERE email = X AND created_at > (now - 1h)
- `delete_older_than`: DELETE WHERE created_at < (now - N days)

#### Services

**EmailService** - `core/email.py`
- Interface: `EmailServiceInterface.send(to, subject, html_body)`
- Implementation: `SMTPEmailService` using `smtplib`
- Connects to Mailpit in dev (localhost:1027)
- Magic link email template (simple HTML)

**JWTService** - `core/jwt.py`
- `create_token(user_id, company_id, role, expires_hours=24) -> str`
- `decode_token(token: str) -> dict` (raises InvalidTokenError)
- Uses PyJWT with HS256

### 4. HTTP Layer

#### Auth Router - `adapters/http/api/auth/routers.py`

| Method | Route | Handler | Auth Required |
|---|---|---|---|
| POST | `/api/v1/auth/magic-link` | CreateMagicLink | No |
| POST | `/api/v1/auth/verify` | VerifyMagicLink | No |
| GET | `/api/v1/auth/me` | GetCurrentUser | Yes |

#### Schemas - `adapters/http/api/auth/schemas.py`

```python
class MagicLinkRequest(BaseModel):
    email: EmailStr

class VerifyRequest(BaseModel):
    token: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    company_id: Optional[str]
    is_active: bool
```

#### Dependencies - `adapters/http/api/auth/dependencies.py`

**get_current_user(token: str = Depends(oauth2_scheme))**
1. Decode JWT
2. Find user by ID
3. Verify is_active
4. Return user context (user_id, company_id, role)

**require_role(minimum_role: UserRole)**
- Returns a dependency that checks `current_user.role >= minimum_role`
- Role hierarchy: super_admin(4) > admin(3) > technician(2) > employee(1)

#### Tenant Context - `core/tenant.py`

**TenantContext** - dataclass with `company_id`, `user_id`, `role`
- Extracted from JWT in `get_current_user`
- Injected into handlers via FastAPI dependency

**TenantBaseRepository** - extends BaseRepository
- Overrides `get_all()`, `get_by_id()` etc. to add `WHERE company_id = X`
- Super admin bypasses filter

### 5. Startup Event

**Super admin auto-creation** in `app.py` startup:
1. Check `SUPER_ADMIN_EMAIL` env var
2. If set, check if user exists
3. If not, create user with super_admin role, no company_id
4. Log "Super admin created: {email}" or "Super admin already exists"

---

## State Machine: MagicLink

```
[Created] ──── verify ────► [Used]
    │
    │ (time passes)
    ▼
[Expired]
```

- Created: `used_at` is None, `expires_at` > now
- Used: `used_at` is set
- Expired: `expires_at` <= now (checked at read time, not stored)

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Unit | User entity (create, deactivate, change_role) | High |
| Unit | MagicLink entity (create, mark_used, is_expired) | High |
| Unit | JWT service (create, decode, expired) | High |
| Integration | Magic link flow (request → verify → JWT) | High |
| Integration | RBAC (role hierarchy enforcement) | High |
| Integration | Multi-tenancy (company isolation) | High |
| Integration | Rate limiting (6th request blocked) | Medium |
| Integration | Super admin bootstrap | Medium |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Company-domain matching without email_domains table | Medium | Medium | Seed a test company, add proper domain matching in E1 |
| VerifyMagicLink returns a value (breaks CQRS rule) | N/A | N/A | Documented exception for auth commands |
