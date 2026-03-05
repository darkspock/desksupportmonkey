# Solution Design: Scoped Auth & Membership Registry

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `auth_bc` (primary), `company_bc` (collateral), `audit_bc` (collateral)

## Summary

Create a `CompanyUser` membership registry that enables multi-company support by recording each user's per-company role, department, employee_role, and active status. Rewrite all 5 auth flows to be company-scoped via slug-prefixed endpoints, implementing a two-step flow: authenticate identity globally then resolve/create membership and copy it to the user row. Add dual-writes to 4 existing user management commands plus invite/import/quick-create/create-company flows. Add session invalidation check in `get_current_user()`.

## Architecture Decision

**Approach:** CompanyUser as a new subdomain within `auth_bc`, with a shared `MembershipAuthService` extracted for the two-step auth logic.

**Why this approach:**
- CompanyUser is fundamentally about authentication/authorization scope — belongs in `auth_bc`
- A shared `MembershipAuthService` avoids duplicating the two-step logic across 5 auth flows
- The user row continues to serve as the "active session" representation — `company_id`, `role`, `department_id`, `employee_role_id` on the user row always reflect the currently active company
- CompanyUser is the source of truth for per-company membership data
- Dual-writes are injected via an additional `CompanyUserRepositoryInterface` dependency in existing command handlers

**Alternatives considered:**
- Separate bounded context for memberships — rejected because membership is tightly coupled to auth flow validation
- Replace user row fields with CompanyUser lookups everywhere — rejected because it would require modifying 80+ endpoints that read `current_user.company_id` and `current_user.role`

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| User entity | `src/auth_bc/user/domain/entities.py` | Yes | No changes — user row continues as active session |
| UserRepository | `src/auth_bc/user/domain/repository.py` | Yes | No interface changes |
| MagicLink entity | `src/auth_bc/magic_link/domain/entities.py` | Partial | Add `company_id` field |
| MagicLinkModel | `src/auth_bc/magic_link/infrastructure/models.py` | Partial | Add `company_id` column |
| CompanyLookupInterface | `src/auth_bc/company_lookup/domain/service.py` | Partial | Add `is_email_allowed_in_company()` |
| CompanyLookupService | `src/auth_bc/company_lookup/infrastructure/service.py` | Partial | Implement `is_email_allowed_in_company()` |
| CreateMagicLinkCommand | `src/auth_bc/magic_link/application/commands/create_magic_link.py` | Partial | Accept optional `company_id`, store on MagicLink |
| VerifyMagicLinkService | `src/auth_bc/magic_link/application/commands/verify_magic_link.py` | Partial | Delegate to MembershipAuthService |
| OAuthLoginService | `src/auth_bc/user/application/services/oauth_login_service.py` | Partial | Accept optional `company_id`, delegate to MembershipAuthService |
| PasswordLoginService | `src/auth_bc/user/application/commands/password_login.py` | Partial | Accept optional `company_id`, delegate to MembershipAuthService |
| Auth routers | `adapters/http/api/auth/routers.py` | Partial | Add slug-scoped endpoints, resolve slug |
| Auth dependencies | `adapters/http/api/auth/dependencies.py` | Partial | Add company_id mismatch check |
| ChangeUserRoleCommand | `src/auth_bc/user/application/commands/change_user_role.py` | Partial | Add dual-write |
| DeactivateUserCommand | `src/auth_bc/user/application/commands/deactivate_user.py` | Partial | Add dual-write |
| ActivateUserCommand | `src/auth_bc/user/application/commands/activate_user.py` | Partial | Add dual-write |
| AssignDepartmentCommand | `src/auth_bc/user/application/commands/assign_department.py` | Partial | Add dual-write |
| CreateCompanyCommand | `src/company_bc/company/application/commands/create_company.py` | Partial | Create CompanyUser for initial admin |
| ImportUsersService | `src/auth_bc/user/application/commands/import_users.py` | Partial | Create CompanyUser memberships |
| User routers (invite) | `adapters/http/api/users/routers.py` | Partial | Create CompanyUser on invite/quick-create |
| GDPR anonymize | `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` | Partial | Scope to membership |
| Company entity | `src/company_bc/company/domain/entities.py` | Yes | No changes (slug/auth_mode from F1) |
| CompanyModel | `src/company_bc/company/infrastructure/models.py` | Yes | No changes |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| CompanyUser | `src/auth_bc/company_user/domain/entities.py` | Membership registry record — one per (user, company) |
| MagicLink (modified) | `src/auth_bc/magic_link/domain/entities.py` | Add `company_id: Optional[str]` field |

**CompanyUser entity:**
```python
@dataclass
class CompanyUser:
    id: str
    user_id: str
    company_id: str
    role: UserRole
    department_id: Optional[str] = None
    employee_role_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        user_id: str,
        company_id: str,
        role: UserRole = UserRole.EMPLOYEE,
        department_id: Optional[str] = None,
        employee_role_id: Optional[str] = None,
    ) -> "CompanyUser":
        return cls(
            id=str(ulid.new()),
            user_id=user_id,
            company_id=company_id,
            role=role,
            department_id=department_id,
            employee_role_id=employee_role_id,
            is_active=True,
        )

    def change_role(self, new_role: UserRole) -> None:
        self.role = new_role

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def assign_department(self, department_id: Optional[str]) -> None:
        self.department_id = department_id

    def assign_employee_role(self, employee_role_id: Optional[str]) -> None:
        self.employee_role_id = employee_role_id
```

**Domain exceptions** (in same file):
```python
class MembershipNotFoundError(Exception): pass
class MembershipDeactivatedError(Exception): pass
class MembershipNotAllowedError(Exception): pass
class MultipleCompaniesError(Exception):
    """Email matches multiple companies — must use slug-scoped login."""
    def __init__(self, slugs: list[str]):
        self.slugs = slugs
        super().__init__(f"Multiple companies found. Use company login: {', '.join(slugs)}")
```

**MagicLink entity modification:**
```python
# Add to MagicLink dataclass:
company_id: Optional[str] = None

# Modify create():
@classmethod
def create(cls, email: str, ttl_hours: int = 24, company_id: Optional[str] = None) -> "MagicLink":
    now = datetime.now(timezone.utc)
    return cls(
        id=str(ulid.new()),
        email=email.lower().strip(),
        token=secrets.token_urlsafe(48),
        expires_at=now + timedelta(hours=ttl_hours),
        created_at=now,
        company_id=company_id,
    )
```

#### Repository Interfaces

| Interface | File Path | Description |
|-----------|-----------|-------------|
| CompanyUserRepositoryInterface | `src/auth_bc/company_user/domain/repository.py` | CRUD + lookup methods for membership records |

```python
class CompanyUserRepositoryInterface(ABC):
    @abstractmethod
    def save(self, company_user: CompanyUser) -> CompanyUser: ...

    @abstractmethod
    def find_by_user_and_company(self, user_id: str, company_id: str) -> Optional[CompanyUser]: ...

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> list[CompanyUser]: ...

    @abstractmethod
    def find_active_by_user_id(self, user_id: str) -> list[CompanyUser]: ...

    @abstractmethod
    def find_by_company_id(self, company_id: str) -> list[CompanyUser]: ...

    @abstractmethod
    def count_admins_in_company(self, company_id: str) -> int: ...

    @abstractmethod
    def count_active_memberships(self, user_id: str) -> int: ...
```

#### Domain Services

| Service | File Path | Description |
|---------|-----------|-------------|
| MembershipAuthService | `src/auth_bc/company_user/domain/membership_auth_service.py` | Two-step auth: identity → membership → copy-to-user-row |

**MembershipAuthService** — shared logic used by all 5 scoped auth flows:

```python
class MembershipAuthService:
    """Two-step auth flow: resolve membership and copy to user row."""

    def __init__(
        self,
        company_user_repo: CompanyUserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.company_user_repo = company_user_repo
        self.company_lookup = company_lookup
        self.user_repo = user_repo

    def resolve_membership(self, user: User, company_id: str, auth_mode: str) -> User:
        """
        Given an authenticated user and target company_id:
        1. Find CompanyUser for (user_id, company_id)
        2. If found + active → copy membership data to user row
        3. If found + inactive → raise MembershipDeactivatedError
        4. If not found + domain mode → auto-create CompanyUser → copy
        5. If not found + membership_only → raise MembershipNotAllowedError
        Returns the updated user (user row reflects membership data).
        """
        membership = self.company_user_repo.find_by_user_and_company(user.id, company_id)

        if membership is not None:
            if not membership.is_active:
                raise MembershipDeactivatedError("Your account in this company is deactivated")
            self._copy_membership_to_user(user, membership, company_id)
            return user

        # No membership exists
        if auth_mode == "membership_only":
            raise MembershipNotAllowedError("You don't have access to this company")

        # Domain mode: check email domain, auto-create membership
        result = self.company_lookup.is_email_allowed_in_company(user.email, company_id)
        if not result:
            raise MembershipNotAllowedError("Your email domain is not allowed for this company")

        membership = CompanyUser.create(
            user_id=user.id,
            company_id=company_id,
            role=UserRole.EMPLOYEE,
        )
        self.company_user_repo.save(membership)
        self._copy_membership_to_user(user, membership, company_id)
        return user

    def _copy_membership_to_user(self, user: User, membership: CompanyUser, company_id: str) -> None:
        """Copy membership data to user row (copy-on-switch semantics)."""
        user.company_id = company_id
        user.role = membership.role
        user.department_id = membership.department_id
        user.employee_role_id = membership.employee_role_id
        user.is_active = membership.is_active
        self.user_repo.save(user)
```

### 2. Infrastructure Layer

#### Models

| Model | File Path | Description |
|-------|-----------|-------------|
| CompanyUserModel | `src/auth_bc/company_user/infrastructure/models.py` | SQLAlchemy model for `company_users` table |

```python
class CompanyUserModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "company_users"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_company_users_user_company"),
    )

    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="employee")
    department_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("departments.id"), nullable=True)
    employee_role_id: Mapped[Optional[str]] = mapped_column(String(26), ForeignKey("employee_roles.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
```

**MagicLinkModel modification:**
```python
# Add to MagicLinkModel:
company_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
```

#### Repository Implementation

| Interface | Implementation | Table |
|-----------|----------------|-------|
| CompanyUserRepositoryInterface | `src/auth_bc/company_user/infrastructure/repository.py` | `company_users` |

```python
class CompanyUserRepository(CompanyUserRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, company_user: CompanyUser) -> CompanyUser:
        existing = self.session.execute(
            select(CompanyUserModel).where(CompanyUserModel.id == company_user.id)
        ).scalar_one_or_none()

        if existing:
            existing.role = company_user.role.value
            existing.department_id = company_user.department_id
            existing.employee_role_id = company_user.employee_role_id
            existing.is_active = company_user.is_active
        else:
            model = CompanyUserModel(
                id=company_user.id,
                user_id=company_user.user_id,
                company_id=company_user.company_id,
                role=company_user.role.value,
                department_id=company_user.department_id,
                employee_role_id=company_user.employee_role_id,
                is_active=company_user.is_active,
            )
            self.session.add(model)
        self.session.flush()
        return company_user

    def find_by_user_and_company(self, user_id: str, company_id: str) -> Optional[CompanyUser]:
        model = self.session.execute(
            select(CompanyUserModel)
            .where(CompanyUserModel.user_id == user_id)
            .where(CompanyUserModel.company_id == company_id)
        ).scalar_one_or_none()
        return self._to_entity(model) if model else None

    def find_by_user_id(self, user_id: str) -> list[CompanyUser]:
        models = self.session.execute(
            select(CompanyUserModel).where(CompanyUserModel.user_id == user_id)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_active_by_user_id(self, user_id: str) -> list[CompanyUser]:
        models = self.session.execute(
            select(CompanyUserModel)
            .where(CompanyUserModel.user_id == user_id)
            .where(CompanyUserModel.is_active == True)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def find_by_company_id(self, company_id: str) -> list[CompanyUser]:
        models = self.session.execute(
            select(CompanyUserModel).where(CompanyUserModel.company_id == company_id)
        ).scalars().all()
        return [self._to_entity(m) for m in models]

    def count_admins_in_company(self, company_id: str) -> int:
        result = self.session.execute(
            select(func.count())
            .select_from(CompanyUserModel)
            .where(CompanyUserModel.company_id == company_id)
            .where(CompanyUserModel.role == UserRole.ADMIN.value)
            .where(CompanyUserModel.is_active == True)
        ).scalar()
        return result or 0

    def count_active_memberships(self, user_id: str) -> int:
        result = self.session.execute(
            select(func.count())
            .select_from(CompanyUserModel)
            .where(CompanyUserModel.user_id == user_id)
            .where(CompanyUserModel.is_active == True)
        ).scalar()
        return result or 0

    def _to_entity(self, model: CompanyUserModel) -> CompanyUser:
        return CompanyUser(
            id=model.id,
            user_id=model.user_id,
            company_id=model.company_id,
            role=UserRole(model.role),
            department_id=model.department_id,
            employee_role_id=model.employee_role_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
```

#### Migrations

| Migration | Description |
|-----------|-------------|
| `xxx_create_company_users_table` | Create `company_users` table, populate from existing users, add `company_id` to `magic_links` |

**Migration steps:**
1. Create `company_users` table with all columns and constraints
2. Populate from existing users: `INSERT INTO company_users (id, user_id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at) SELECT generate_ulid(), id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at FROM users WHERE company_id IS NOT NULL`
3. Add `company_id` column to `magic_links` (nullable)

### 3. Application Layer

#### Services (Modified)

| Service | File Path | Change |
|---------|-----------|--------|
| MembershipAuthService | `src/auth_bc/company_user/domain/membership_auth_service.py` | NEW — two-step auth logic |
| CompanyLookupInterface | `src/auth_bc/company_lookup/domain/service.py` | ADD `is_email_allowed_in_company()` method |
| CompanyLookupService | `src/auth_bc/company_lookup/infrastructure/service.py` | IMPLEMENT `is_email_allowed_in_company()` |

**CompanyLookupInterface addition:**
```python
@abstractmethod
def is_email_allowed_in_company(self, email: str, company_id: str) -> bool:
    """Check if email is allowed in company (domain mode: email domain match)."""
    ...

@abstractmethod
def find_companies_by_email_domain(self, email: str) -> list[tuple[str, str, bool]]:
    """Find ALL companies matching email domain. Returns list of (company_id, slug, is_active)."""
    ...
```

**CompanyLookupService implementation:**
```python
def is_email_allowed_in_company(self, email: str, company_id: str) -> bool:
    """For domain mode: check if email domain matches company's registered domains."""
    domain = self.extract_domain(email)
    result = self.session.execute(
        select(CompanyEmailDomainModel.id)
        .where(CompanyEmailDomainModel.company_id == company_id)
        .where(CompanyEmailDomainModel.domain == domain)
    ).first()
    return result is not None

def find_companies_by_email_domain(self, email: str) -> list[tuple[str, str, bool]]:
    """Find ALL companies matching email domain (for backward-compat multi-company detection)."""
    domain = self.extract_domain(email)
    results = self.session.execute(
        select(CompanyEmailDomainModel.company_id, CompanyModel.slug, CompanyModel.is_active)
        .join(CompanyModel, CompanyEmailDomainModel.company_id == CompanyModel.id)
        .where(CompanyEmailDomainModel.domain == domain)
    ).all()
    return [(r[0], r[1], r[2]) for r in results]
```

#### Commands (Modified — Dual-Writes)

| Command | File Path | Change |
|---------|-----------|--------|
| ChangeUserRoleCommand | `src/auth_bc/user/application/commands/change_user_role.py` | Add `CompanyUserRepositoryInterface` dependency; after updating user role, also update `CompanyUser.role` |
| DeactivateUserCommand | `src/auth_bc/user/application/commands/deactivate_user.py` | Add `CompanyUserRepositoryInterface` dependency; after deactivating user, also set `CompanyUser.is_active = False` |
| ActivateUserCommand | `src/auth_bc/user/application/commands/activate_user.py` | Add `CompanyUserRepositoryInterface` dependency; after activating user, also set `CompanyUser.is_active = True` |
| AssignDepartmentCommand | `src/auth_bc/user/application/commands/assign_department.py` | Add `CompanyUserRepositoryInterface` dependency; after assigning department, also update `CompanyUser.department_id` |

**Dual-write pattern** (same for all 4 commands):
```python
# After updating user row:
user.change_role(new_role)
self.user_repo.save(user)

# Dual-write: update membership too
membership = self.company_user_repo.find_by_user_and_company(user.id, command.company_id)
if membership:
    membership.change_role(new_role)
    self.company_user_repo.save(membership)
```

**Constructor changes** — each handler gets an optional `CompanyUserRepositoryInterface`:
```python
def __init__(
    self,
    user_repo: UserRepositoryInterface,
    company_user_repo: Optional[CompanyUserRepositoryInterface] = None,  # NEW
    email_service: Optional[EmailServiceInterface] = None,
):
```
Making it `Optional` preserves backward compatibility for existing tests and callers that don't pass it.

#### Auth Flow Modifications

| Service | File Path | Change |
|---------|-----------|--------|
| CreateMagicLinkCommand | `src/auth_bc/magic_link/application/commands/create_magic_link.py` | Accept optional `company_id` on command; pass to `MagicLink.create()` |
| VerifyMagicLinkService | `src/auth_bc/magic_link/application/commands/verify_magic_link.py` | Accept `MembershipAuthService`; if magic_link.company_id is set, call `resolve_membership()` after identity auth |
| OAuthLoginService | `src/auth_bc/user/application/services/oauth_login_service.py` | Accept optional `company_id` and `MembershipAuthService`; if company_id is set, call `resolve_membership()` after identity auth |
| PasswordLoginService | `src/auth_bc/user/application/commands/password_login.py` | Accept optional `company_id` and `MembershipAuthService`; if company_id is set, call `resolve_membership()` after identity auth |

**CreateMagicLinkCommand modification:**
```python
@dataclass
class CreateMagicLinkCommand(Command):
    email: str
    company_id: Optional[str] = None  # NEW — set when called from slug-scoped endpoint
```

Handler changes:
- If `command.company_id` is set: validate email is allowed via `is_email_allowed_in_company()` (domain mode) or membership exists (membership_only mode via CompanyUser check)
- Pass `company_id` to `MagicLink.create()` so the link carries company context
- Existing unscoped behavior preserved when `company_id` is None

**VerifyMagicLinkService modification:**
```python
def __init__(
    self,
    magic_link_repo: MagicLinkRepositoryInterface,
    user_repo: UserRepositoryInterface,
    company_lookup: CompanyLookupInterface,
    jwt_service: JWTService,
    membership_auth: Optional[MembershipAuthService] = None,  # NEW
):
```

In `handle()`:
- After finding/creating user, if `magic_link.company_id` is not None and `membership_auth` is not None:
  - Look up company to get `auth_mode`
  - Call `membership_auth.resolve_membership(user, magic_link.company_id, company.auth_mode)`
  - Issue JWT with the updated user data (which now reflects the membership)

**OAuthLoginService modification:**
```python
def login_or_create(self, info: OAuthUserInfo, company_id: Optional[str] = None) -> str:
```

- If `company_id` is set after finding/creating user:
  - Look up company to get `auth_mode`
  - Call `membership_auth.resolve_membership(user, company_id, company.auth_mode)`
  - Issue JWT with updated user data

**PasswordLoginService modification:**
```python
@dataclass
class PasswordLoginRequest:
    email: str
    password: str
    company_id: Optional[str] = None  # NEW
```

- If `command.company_id` is set after password validation:
  - Look up company to get `auth_mode`
  - Call `membership_auth.resolve_membership(user, command.company_id, company.auth_mode)`
  - Issue JWT with updated user data

#### Backward Compatibility (Unscoped Endpoints)

The existing unscoped endpoints (`POST /api/v1/auth/magic-link`, etc.) continue to work:
- If email domain resolves to exactly one company → proceed as today (existing behavior)
- If email matches multiple companies (via `find_companies_by_email_domain()`) → return error with available slugs: `{"detail": "multiple_companies", "slugs": ["acme-corp", "beta-inc"]}`
- SUPER_ADMIN login remains unaffected (company_id = NULL)

This check is added at the **router level** in the existing unscoped endpoints, not in the services. The services remain unchanged for the unscoped path.

### 4. HTTP Layer

#### New Endpoints (Slug-Scoped Auth)

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/auth/{slug}/magic-link` | Request magic link scoped to company | None |
| POST | `/api/v1/auth/{slug}/verify` | Verify magic link scoped to company | None |
| POST | `/api/v1/auth/{slug}/login` | Password login scoped to company | None |
| POST | `/api/v1/auth/{slug}/oauth/google` | Google OAuth scoped to company | None |
| POST | `/api/v1/auth/{slug}/oauth/microsoft` | Microsoft OAuth scoped to company | None |

**Implementation pattern** — each slug-scoped endpoint:
1. Resolve `slug` → company via `CompanyRepository.find_by_slug(slug)` → 404 if not found
2. Check company `is_active` → 403 if not active
3. Check billing not suspended → 402 if suspended
4. Delegate to the same service/handler but with `company_id` parameter
5. Map domain exceptions to HTTP responses

**Slug resolution helper** (in auth routers):
```python
def _resolve_slug(slug: str, company_repo: CompanyRepository) -> Company:
    """Resolve slug to active company, or raise HTTPException."""
    company = company_repo.find_by_slug(slug)
    if not company or not company.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    return company
```

**New exception mappings:**
```python
except MembershipDeactivatedError:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Your account in this company is deactivated")
except MembershipNotAllowedError:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don't have access to this company")
```

#### Modified Endpoints

| Method | Route | Change |
|--------|-------|--------|
| POST | `/api/v1/auth/magic-link` | Add multi-company detection for email |
| POST | `/api/v1/auth/verify` | Add multi-company detection (if MagicLink has no company_id) |
| POST | `/api/v1/auth/login` | Add multi-company detection for email |
| POST | `/api/v1/auth/oauth/google` | Add multi-company detection |
| POST | `/api/v1/auth/oauth/microsoft` | Add multi-company detection |

**Multi-company detection pattern** (in existing unscoped endpoints):
```python
# Before calling the service, check if email matches multiple companies
companies = company_lookup.find_companies_by_email_domain(body.email)
active_companies = [(cid, slug, active) for cid, slug, active in companies if active]
if len(active_companies) > 1:
    slugs = [slug for _, slug, _ in active_companies]
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=json.dumps({"error": "multiple_companies", "slugs": slugs}),
    )
```

#### Modified Dependencies

| Dependency | File Path | Change |
|------------|-----------|--------|
| `get_current_user` | `adapters/http/api/auth/dependencies.py` | Add JWT company_id mismatch check |

**Session invalidation check** — add after user lookup:
```python
# Session invalidation: JWT company_id must match user row's company_id
# Skip for SUPER_ADMIN (company_id is NULL in both JWT and user row)
jwt_company_id = payload.get("company_id")
if jwt_company_id is not None and user.company_id != jwt_company_id:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired — please log in again",
    )
```

#### New Dependencies

| Dependency | File Path | Description |
|------------|-----------|-------------|
| `get_company_user_repo` | `adapters/http/api/auth/dependencies.py` | Provide CompanyUserRepository instance |
| `get_membership_auth_service` | `adapters/http/api/auth/dependencies.py` | Provide MembershipAuthService instance |

```python
def get_company_user_repo(db: Session = Depends(get_db)) -> CompanyUserRepository:
    from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
    return CompanyUserRepository(db)

def get_membership_auth_service(db: Session = Depends(get_db)):
    from src.auth_bc.company_user.infrastructure.repository import CompanyUserRepository
    from src.auth_bc.company_user.domain.membership_auth_service import MembershipAuthService
    from src.auth_bc.company_lookup.infrastructure.service import CompanyLookupService
    return MembershipAuthService(
        company_user_repo=CompanyUserRepository(db),
        company_lookup=CompanyLookupService(db),
        user_repo=UserRepository(db),
    )
```

#### Router Wiring for Dual-Write Commands

All user management endpoints in `adapters/http/api/users/routers.py` must pass `CompanyUserRepository` to command handlers:

```python
# Example: change_role endpoint
handler = ChangeUserRoleCommandHandler(
    user_repo=user_repo,
    company_user_repo=CompanyUserRepository(db),  # NEW
    email_service=get_email_service(),
)
```

Similarly for deactivate, activate, assign_department handlers.

#### Invite and Quick-Create Modifications

In `adapters/http/api/users/routers.py`:

**`_ensure_user_for_invite()`** — after creating/updating user, also create CompanyUser:
```python
# After user creation:
company_user_repo = CompanyUserRepository(session)
existing_membership = company_user_repo.find_by_user_and_company(user.id, company_id)
if not existing_membership:
    membership = CompanyUser.create(user_id=user.id, company_id=company_id, role=role)
    company_user_repo.save(membership)
```

**`quick_create_employee()`** — after creating user, also create CompanyUser membership.

#### Import Users Modifications

In `src/auth_bc/user/application/commands/import_users.py`:

**`ImportUsersService.__init__()`** — accept optional `CompanyUserRepositoryInterface`:
```python
def __init__(
    self,
    user_repo: UserRepositoryInterface,
    department_repo: DepartmentRepositoryInterface,
    company_repo: CompanyRepositoryInterface,
    employee_role_repo: Optional[EmployeeRoleRepositoryInterface] = None,
    company_user_repo: Optional[CompanyUserRepositoryInterface] = None,  # NEW
):
```

**In `confirm()` method** — after saving new/updated users, create CompanyUser memberships:
```python
# After creating new user:
if self.company_user_repo:
    membership = CompanyUser.create(
        user_id=user.id, company_id=company_id, role=role,
        department_id=department_id, employee_role_id=employee_role_id,
    )
    self.company_user_repo.save(membership)

# After updating existing user:
if self.company_user_repo:
    membership = self.company_user_repo.find_by_user_and_company(existing_user.id, company_id)
    if membership:
        membership.assign_department(department_id)
        membership.assign_employee_role(employee_role_id)
        self.company_user_repo.save(membership)
```

#### Create Company Modification

In `src/company_bc/company/application/commands/create_company.py`:

**`CreateCompanyCommandHandler.__init__()`** — accept optional `CompanyUserRepositoryInterface` via a port interface:
```python
company_user_writer: Optional["CompanyUserWriter"] = None  # NEW
```

Add a port in `src/company_bc/company/application/ports.py`:
```python
class CompanyUserWriter(ABC):
    @abstractmethod
    def save(self, company_user) -> None: ...

    @abstractmethod
    def find_by_user_and_company(self, user_id: str, company_id: str) -> Optional[object]: ...
```

**In `handle()` method** — after creating initial admin user, also create CompanyUser:
```python
if command.admin_email:
    # ... existing user creation code ...
    if self.company_user_writer:
        from src.auth_bc.company_user.domain.entities import CompanyUser
        membership = CompanyUser.create(
            user_id=user.id,
            company_id=company.id,
            role=UserRole.ADMIN,
        )
        self.company_user_writer.save(membership)
```

### 5. GDPR Modifications

| Command | File Path | Change |
|---------|-----------|--------|
| RequestGdprAnonymizeCommand | `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` | Scope to company membership; deactivate membership on anonymize |

**Modification:**
- Accept optional `CompanyUserRepositoryInterface`
- After creating GDPR request, deactivate the membership: `membership.deactivate()`
- Only anonymize identity (email, name, etc.) if `count_active_memberships(user_id) == 0`

### 6. Frontend

| File | Change |
|------|--------|
| `web/app/src/pages/auth/LoginPage.tsx` | Post to slug-scoped endpoints when slug param is present |

**LoginPage modification:**
- When `slug` is present in URL params:
  - POST `/api/v1/auth/{slug}/magic-link` instead of `/api/v1/auth/magic-link`
  - POST `/api/v1/auth/{slug}/verify` instead of `/api/v1/auth/verify`
  - POST `/api/v1/auth/{slug}/login` instead of `/api/v1/auth/login`
  - POST `/api/v1/auth/{slug}/oauth/google` instead of `/api/v1/auth/oauth/google`
  - POST `/api/v1/auth/{slug}/oauth/microsoft` instead of `/api/v1/auth/oauth/microsoft`
- Handle new error response for multi-company: display available company slugs as links

### 7. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/auth_bc/magic_link/domain/entities.py` | MODIFY | Add `company_id` field to MagicLink |
| `src/auth_bc/magic_link/infrastructure/models.py` | MODIFY | Add `company_id` column to MagicLinkModel |
| `src/auth_bc/magic_link/infrastructure/repository.py` | MODIFY | Map `company_id` in save/find methods |
| `src/auth_bc/magic_link/application/commands/create_magic_link.py` | MODIFY | Accept `company_id`, pass to MagicLink.create() |
| `src/auth_bc/magic_link/application/commands/verify_magic_link.py` | MODIFY | Accept MembershipAuthService, use for scoped auth |
| `src/auth_bc/company_lookup/domain/service.py` | MODIFY | Add `is_email_allowed_in_company()` and `find_companies_by_email_domain()` |
| `src/auth_bc/company_lookup/infrastructure/service.py` | MODIFY | Implement new methods |
| `src/auth_bc/user/application/services/oauth_login_service.py` | MODIFY | Accept `company_id` + MembershipAuthService |
| `src/auth_bc/user/application/commands/password_login.py` | MODIFY | Accept `company_id` + MembershipAuthService |
| `src/auth_bc/user/application/commands/google_oauth_login.py` | MODIFY | Pass `company_id` to OAuthLoginService |
| `src/auth_bc/user/application/commands/microsoft_oauth_login.py` | MODIFY | Pass `company_id` to OAuthLoginService |
| `src/auth_bc/user/application/commands/change_user_role.py` | MODIFY | Add dual-write via CompanyUserRepo |
| `src/auth_bc/user/application/commands/deactivate_user.py` | MODIFY | Add dual-write |
| `src/auth_bc/user/application/commands/activate_user.py` | MODIFY | Add dual-write |
| `src/auth_bc/user/application/commands/assign_department.py` | MODIFY | Add dual-write |
| `src/auth_bc/user/application/commands/import_users.py` | MODIFY | Create CompanyUser memberships |
| `src/company_bc/company/application/commands/create_company.py` | MODIFY | Create CompanyUser for initial admin |
| `src/company_bc/company/application/ports.py` | MODIFY | Add CompanyUserWriter port |
| `adapters/http/api/auth/routers.py` | MODIFY | Add 5 slug-scoped endpoints + multi-company detection |
| `adapters/http/api/auth/dependencies.py` | MODIFY | Add session invalidation + new DI factories |
| `adapters/http/api/auth/schemas.py` | MODIFY | Add MultipleCompaniesError response schema |
| `adapters/http/api/users/routers.py` | MODIFY | Pass CompanyUserRepo to handlers; create memberships on invite/quick-create |
| `adapters/http/api/users/dependencies.py` | MODIFY | Add `get_company_user_repo` |
| `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py` | MODIFY | Scope to membership |
| `web/app/src/pages/auth/LoginPage.tsx` | MODIFY | Post to slug-scoped endpoints |

#### New Files

| File | Description |
|------|-------------|
| `src/auth_bc/company_user/__init__.py` | Package init |
| `src/auth_bc/company_user/domain/__init__.py` | Package init |
| `src/auth_bc/company_user/domain/entities.py` | CompanyUser entity + exceptions |
| `src/auth_bc/company_user/domain/repository.py` | CompanyUserRepositoryInterface |
| `src/auth_bc/company_user/domain/membership_auth_service.py` | MembershipAuthService |
| `src/auth_bc/company_user/infrastructure/__init__.py` | Package init |
| `src/auth_bc/company_user/infrastructure/models.py` | CompanyUserModel |
| `src/auth_bc/company_user/infrastructure/repository.py` | CompanyUserRepository |
| `alembic/versions/xxx_create_company_users_and_magic_link_company_id.py` | Migration |

#### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| JWT company_id mismatch → 401 | Existing sessions where user switched company externally will be invalidated | Users re-login; expected behavior |
| Multi-company email → 409 on unscoped endpoints | Users whose email domain matches multiple companies can no longer use unscoped endpoints | Error includes slugs to redirect to |

## Database Schema

```sql
CREATE TABLE company_users (
    id VARCHAR(26) PRIMARY KEY,
    user_id VARCHAR(26) NOT NULL REFERENCES users(id),
    company_id VARCHAR(26) NOT NULL REFERENCES companies(id),
    role VARCHAR(30) NOT NULL DEFAULT 'employee',
    department_id VARCHAR(26) REFERENCES departments(id),
    employee_role_id VARCHAR(26) REFERENCES employee_roles(id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_company_users_user_company UNIQUE (user_id, company_id)
);

CREATE INDEX ix_company_users_user_id ON company_users(user_id);
CREATE INDEX ix_company_users_company_id ON company_users(company_id);

-- Add to existing magic_links table:
ALTER TABLE magic_links ADD COLUMN company_id VARCHAR(26);
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F1 (Slug & Login Page) | Feature | Provides `Company.slug`, `Company.auth_mode`, `find_by_slug()` endpoint |
| `UserRole` enum | Existing | Reused for CompanyUser.role |
| `CompanyLookupService` | Existing | Extended with new methods |
| `JWTService` | Existing | JWT now carries company_id for mismatch check |
| `UserRepository` | Existing | Used by MembershipAuthService for copy-on-switch |

## Testing Strategy

| Test Type | Scope | Priority |
|-----------|-------|----------|
| Unit | CompanyUser entity (create, change_role, deactivate, activate) | High |
| Unit | MembershipAuthService (all 5 paths: active membership, inactive, domain auto-create, membership_only reject, no domain match) | High |
| Unit | CompanyLookupService.is_email_allowed_in_company() | High |
| Unit | CreateMagicLinkCommand with company_id | High |
| Unit | VerifyMagicLinkService with membership resolution | High |
| Unit | OAuthLoginService with company_id + membership | High |
| Unit | PasswordLoginService with company_id + membership | High |
| Unit | Dual-write commands (change_role, deactivate, activate, assign_department) | High |
| Unit | CreateCompany with CompanyUser creation | High |
| Unit | ImportUsers with CompanyUser creation | Medium |
| Unit | GDPR anonymize with membership deactivation | Medium |
| Integration | CompanyUserRepository CRUD | High |
| Integration | Slug-scoped auth endpoints (all 5) | High |
| Integration | Unscoped endpoints with multi-company detection | High |
| Integration | Session invalidation (JWT mismatch) | High |
| Integration | Billing suspension on slug-scoped endpoints | Medium |

## Implementation Order

1. [ ] Domain: CompanyUser entity + exceptions (`src/auth_bc/company_user/domain/entities.py`)
2. [ ] Domain: CompanyUserRepositoryInterface (`src/auth_bc/company_user/domain/repository.py`)
3. [ ] Domain: MembershipAuthService (`src/auth_bc/company_user/domain/membership_auth_service.py`)
4. [ ] Infrastructure: CompanyUserModel (`src/auth_bc/company_user/infrastructure/models.py`)
5. [ ] Infrastructure: CompanyUserRepository (`src/auth_bc/company_user/infrastructure/repository.py`)
6. [ ] Infrastructure: Migration — create company_users + populate + magic_link.company_id
7. [ ] Domain: MagicLink.company_id field addition
8. [ ] Domain: CompanyLookupInterface — add `is_email_allowed_in_company()`, `find_companies_by_email_domain()`
9. [ ] Infrastructure: CompanyLookupService — implement new methods
10. [ ] Application: Modify CreateMagicLinkCommand — accept company_id
11. [ ] Application: Modify VerifyMagicLinkService — membership resolution
12. [ ] Application: Modify OAuthLoginService — accept company_id + membership
13. [ ] Application: Modify PasswordLoginService — accept company_id + membership
14. [ ] Application: Modify GoogleOAuthLogin — pass company_id
15. [ ] Application: Modify MicrosoftOAuthLogin — pass company_id
16. [ ] Application: Dual-write ChangeUserRoleCommand
17. [ ] Application: Dual-write DeactivateUserCommand
18. [ ] Application: Dual-write ActivateUserCommand
19. [ ] Application: Dual-write AssignDepartmentCommand
20. [ ] Application: Modify CreateCompanyCommand — create CompanyUser for admin
21. [ ] Application: Modify ImportUsersService — create CompanyUser memberships
22. [ ] Application: Modify GDPR anonymize — scope to membership
23. [ ] HTTP: Add slug-scoped auth endpoints (5 endpoints)
24. [ ] HTTP: Add multi-company detection to unscoped endpoints
25. [ ] HTTP: Session invalidation in get_current_user()
26. [ ] HTTP: New dependencies (get_company_user_repo, get_membership_auth_service)
27. [ ] HTTP: Wire dual-write repos into user management routers
28. [ ] HTTP: Modify invite/quick-create to create CompanyUser
29. [ ] Tests: Unit tests for domain layer
30. [ ] Tests: Unit tests for application layer
31. [ ] Tests: Integration tests for repository
32. [ ] Tests: Integration tests for endpoints
33. [ ] Frontend: LoginPage posts to slug-scoped endpoints

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| JWT company_id mismatch invalidates active sessions after deploy | Medium | Medium | Company_id in JWT already matches user.company_id for single-company users — only affects edge cases |
| Data migration creates inconsistent CompanyUser records | Low | High | Migration copies exact data from user row; add validation query after migration |
| Dual-write missed in some code path | Medium | Medium | Search for all `user_repo.save()` calls to ensure CompanyUser is also updated |
| Unscoped endpoint regression for single-company users | Low | High | Existing unscoped flow only changes when multi-company detected; single-company path is identical |
| Performance: MembershipAuthService adds DB queries to every auth flow | Low | Low | Only 1 additional query (find_by_user_and_company) per auth — indexed on composite key |
