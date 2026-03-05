# Implementation Tasks: Scoped Auth & Membership Registry

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 33
**Estimated Complexity:** XL

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Entities & Exceptions | 1 | M |
| Domain - Repository Interface | 1 | S |
| Domain - Services | 1 | M |
| Domain - Existing Entity Modifications | 2 | S |
| Infrastructure - Model | 1 | S |
| Infrastructure - Migration | 1 | M |
| Infrastructure - Repository | 1 | M |
| Infrastructure - Existing Modifications | 2 | S |
| Application - Auth Flow Modifications | 6 | M-L |
| Application - Dual-Write Commands | 4 | S |
| Application - Collateral Command Modifications | 3 | S-M |
| HTTP - Dependencies | 1 | S |
| HTTP - Slug-Scoped Endpoints | 1 | L |
| HTTP - Multi-Company Detection | 1 | M |
| HTTP - User Router Wiring | 1 | M |
| Tests - Unit (Domain) | 1 | M |
| Tests - Unit (Application) | 1 | L |
| Tests - Integration (Repository) | 1 | M |
| Tests - Integration (Endpoints) | 1 | L |
| Frontend | 1 | M |

---

## Phase 1: Domain Layer

### TASK-001: Create CompanyUser Entity + Domain Exceptions

**Phase:** Domain
**Complexity:** M
**Dependencies:** None

**Description:**
Create the `CompanyUser` membership entity and associated domain exceptions. This is the core domain object that represents a user's membership in a company.

**Files:**
- `src/auth_bc/company_user/__init__.py`
- `src/auth_bc/company_user/domain/__init__.py`
- `src/auth_bc/company_user/domain/entities.py`

**Implementation:**
```python
# src/auth_bc/company_user/domain/entities.py
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
    def create(cls, user_id, company_id, role=UserRole.EMPLOYEE, department_id=None, employee_role_id=None) -> "CompanyUser"

    def change_role(self, new_role: UserRole) -> None
    def deactivate(self) -> None
    def activate(self) -> None
    def assign_department(self, department_id: Optional[str]) -> None
    def assign_employee_role(self, employee_role_id: Optional[str]) -> None

# Domain exceptions (same file)
class MembershipNotFoundError(Exception): pass
class MembershipDeactivatedError(Exception): pass
class MembershipNotAllowedError(Exception): pass
class MultipleCompaniesError(Exception):
    def __init__(self, slugs: list[str]): ...
```

**Acceptance Criteria:**
- [x] `CompanyUser` dataclass with all fields from design (id, user_id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at)
- [x] `create()` factory method generates ULID, defaults role=EMPLOYEE, is_active=True
- [x] `change_role()`, `deactivate()`, `activate()`, `assign_department()`, `assign_employee_role()` methods
- [x] All 4 domain exceptions defined (MembershipNotFoundError, MembershipDeactivatedError, MembershipNotAllowedError, MultipleCompaniesError)
- [x] `MultipleCompaniesError` stores `slugs` list and includes them in message
- [x] Package `__init__.py` files created

---

### TASK-002: Create CompanyUserRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create the repository interface (port) for CompanyUser persistence.

**File:** `src/auth_bc/company_user/domain/repository.py`

**Implementation:**
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

**Acceptance Criteria:**
- [x] ABC interface with all 7 methods exactly as specified in design
- [x] Uses `CompanyUser` entity type in signatures
- [x] Returns `Optional[CompanyUser]`, `list[CompanyUser]`, and `int` as appropriate

---

### TASK-003: Create MembershipAuthService

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**Description:**
Create the shared domain service implementing the two-step auth flow: identity resolution → membership lookup → copy-to-user-row.

**File:** `src/auth_bc/company_user/domain/membership_auth_service.py`

**Implementation:**
```python
class MembershipAuthService:
    def __init__(self, company_user_repo, company_lookup, user_repo): ...

    def resolve_membership(self, user: User, company_id: str, auth_mode: str) -> User:
        """
        1. Find CompanyUser for (user_id, company_id)
        2. Found + active → copy membership data to user row
        3. Found + inactive → raise MembershipDeactivatedError
        4. Not found + domain mode → check email domain → auto-create → copy
        5. Not found + membership_only → raise MembershipNotAllowedError
        """

    def _copy_membership_to_user(self, user, membership, company_id) -> None:
        """Copy membership fields to user row and save."""
```

**Acceptance Criteria:**
- [x] Constructor accepts `CompanyUserRepositoryInterface`, `CompanyLookupInterface`, `UserRepositoryInterface`
- [x] `resolve_membership()` handles all 5 paths from design
- [x] Path 1: existing active membership → copies data to user row, returns updated user
- [x] Path 2: existing inactive membership → raises `MembershipDeactivatedError`
- [x] Path 3: no membership + domain mode + email allowed → auto-creates CompanyUser with EMPLOYEE role → copies → returns
- [x] Path 4: no membership + domain mode + email NOT allowed → raises `MembershipNotAllowedError`
- [x] Path 5: no membership + membership_only mode → raises `MembershipNotAllowedError`
- [x] `_copy_membership_to_user()` sets user.company_id, user.role, user.department_id, user.employee_role_id, user.is_active from membership, then saves user

---

### TASK-004: Add company_id to MagicLink Entity

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add `company_id: Optional[str]` field to the existing MagicLink entity and update its `create()` factory.

**File:** `src/auth_bc/magic_link/domain/entities.py`

**Changes:**
- Add `company_id: Optional[str] = None` field to MagicLink dataclass
- Add `company_id` parameter to `create()` factory: `company_id: Optional[str] = None`
- Pass `company_id` in the returned instance

**Acceptance Criteria:**
- [x] `company_id` field added (Optional, defaults to None for backward compatibility)
- [x] `create()` accepts optional `company_id` parameter
- [x] `create()` passes `company_id` to the new MagicLink instance
- [x] Existing tests still pass (None default preserves backward compatibility)

---

### TASK-005: Extend CompanyLookupInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Add two new abstract methods to the existing `CompanyLookupInterface`.

**File:** `src/auth_bc/company_lookup/domain/service.py`

**Changes:**
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

**Acceptance Criteria:**
- [x] `is_email_allowed_in_company()` abstract method added with correct signature
- [x] `find_companies_by_email_domain()` abstract method added returning `list[tuple[str, str, bool]]`

---

## Phase 2: Infrastructure Layer

### TASK-006: Create CompanyUserModel

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Create SQLAlchemy 2.0 model for the `company_users` table.

**Files:**
- `src/auth_bc/company_user/infrastructure/__init__.py`
- `src/auth_bc/company_user/infrastructure/models.py`

**Implementation:**
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

**Acceptance Criteria:**
- [x] SQLAlchemy 2.0 style (`Mapped[T]` + `mapped_column()`)
- [x] Uses `ULIDMixin` and `TimestampMixin`
- [x] `UniqueConstraint` on (user_id, company_id)
- [x] Indexes on `user_id` and `company_id`
- [x] All ForeignKey references correct (users.id, companies.id, departments.id, employee_roles.id)
- [x] Package `__init__.py` created

---

### TASK-007: Create Migration — company_users Table + magic_links.company_id

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-006

**Description:**
Create Alembic migration that:
1. Creates the `company_users` table with all columns, constraints, and indexes
2. Populates `company_users` from existing users (data migration)
3. Adds `company_id` column to `magic_links` table

**File:** `alembic/versions/xxx_create_company_users_and_magic_link_company_id.py`

**Schema:**
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

ALTER TABLE magic_links ADD COLUMN company_id VARCHAR(26);
```

**Data migration:**
```sql
INSERT INTO company_users (id, user_id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at)
SELECT generate_ulid(), id, company_id, role, department_id, employee_role_id, is_active, created_at, updated_at
FROM users WHERE company_id IS NOT NULL;
```

**Acceptance Criteria:**
- [x] `company_users` table created with all columns from design
- [x] UniqueConstraint on (user_id, company_id)
- [x] Indexes on user_id and company_id
- [x] Data migration populates from existing users with `company_id IS NOT NULL`
- [x] ULID generation in migration (Python helper, not DB function)
- [x] `magic_links.company_id` column added (nullable)
- [x] Reversible: `downgrade()` drops column and table
- [x] `down_revision` chains from latest F1 migration

---

### TASK-008: Create CompanyUserRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-002, TASK-006

**Description:**
Implement the `CompanyUserRepositoryInterface` using SQLAlchemy.

**File:** `src/auth_bc/company_user/infrastructure/repository.py`

**Implementation:**
All 7 methods from interface:
- `save()` — upsert (check by id, insert or update)
- `find_by_user_and_company()` — composite WHERE
- `find_by_user_id()` — list all memberships for user
- `find_active_by_user_id()` — list active memberships
- `find_by_company_id()` — list all memberships in company
- `count_admins_in_company()` — count WHERE role=admin AND is_active=True
- `count_active_memberships()` — count WHERE user_id AND is_active=True
- `_to_entity()` — model-to-entity conversion

**Acceptance Criteria:**
- [x] Implements `CompanyUserRepositoryInterface`
- [x] `save()` does upsert: check existing by id, update or insert
- [x] `save()` uses `session.flush()` (not commit)
- [x] `find_by_user_and_company()` queries by both user_id AND company_id
- [x] `_to_entity()` converts `UserRole(model.role)` enum
- [x] All 7 interface methods implemented exactly as design

---

### TASK-009: Add company_id to MagicLinkModel + Repository

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-004, TASK-007

**Description:**
Add `company_id` column to MagicLinkModel and update MagicLink repository to map it.

**Files:**
- `src/auth_bc/magic_link/infrastructure/models.py` — add `company_id` column
- `src/auth_bc/magic_link/infrastructure/repository.py` — map `company_id` in save/find

**Changes:**
```python
# MagicLinkModel:
company_id: Mapped[Optional[str]] = mapped_column(String(26), nullable=True)
```

**Acceptance Criteria:**
- [x] `company_id` column added to MagicLinkModel (nullable, String(26))
- [x] Repository `save()` maps `company_id` from entity to model
- [x] Repository `find_by_token()` / `_to_entity()` maps `company_id` from model to entity

---

### TASK-010: Implement CompanyLookupService New Methods

**Phase:** Infrastructure
**Complexity:** S
**Dependencies:** TASK-005

**Description:**
Implement the two new methods on `CompanyLookupService`.

**File:** `src/auth_bc/company_lookup/infrastructure/service.py`

**Implementation:**
```python
def is_email_allowed_in_company(self, email: str, company_id: str) -> bool:
    domain = self.extract_domain(email)
    result = self.session.execute(
        select(CompanyEmailDomainModel.id)
        .where(CompanyEmailDomainModel.company_id == company_id)
        .where(CompanyEmailDomainModel.domain == domain)
    ).first()
    return result is not None

def find_companies_by_email_domain(self, email: str) -> list[tuple[str, str, bool]]:
    domain = self.extract_domain(email)
    results = self.session.execute(
        select(CompanyEmailDomainModel.company_id, CompanyModel.slug, CompanyModel.is_active)
        .join(CompanyModel, CompanyEmailDomainModel.company_id == CompanyModel.id)
        .where(CompanyEmailDomainModel.domain == domain)
    ).all()
    return [(r[0], r[1], r[2]) for r in results]
```

**Acceptance Criteria:**
- [x] `is_email_allowed_in_company()` checks email domain against company's registered domains
- [x] `find_companies_by_email_domain()` returns ALL matching companies as `list[tuple[company_id, slug, is_active]]`
- [x] Both use `CompanyEmailDomainModel` and `CompanyModel`

---

## Phase 3: Application Layer

### TASK-011: Modify CreateMagicLinkCommand — Accept company_id

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-004, TASK-005, TASK-010

**Description:**
Add optional `company_id` to the CreateMagicLinkCommand and modify the handler to validate and store it.

**File:** `src/auth_bc/magic_link/application/commands/create_magic_link.py`

**Changes:**
- Add `company_id: Optional[str] = None` to `CreateMagicLinkCommand` dataclass
- In handler: if `company_id` is set, validate email via `is_email_allowed_in_company()`
- Pass `company_id` to `MagicLink.create()`

**Acceptance Criteria:**
- [x] `CreateMagicLinkCommand` has `company_id: Optional[str] = None`
- [x] Handler validates email against company when `company_id` is set
- [x] `MagicLink.create()` receives `company_id`
- [x] Existing unscoped behavior preserved when `company_id` is None

---

### TASK-012: Modify VerifyMagicLinkService — Membership Resolution

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003, TASK-009

**Description:**
Add `MembershipAuthService` dependency to VerifyMagicLinkService. After identity auth, if `magic_link.company_id` is set, call `resolve_membership()`.

**File:** `src/auth_bc/magic_link/application/commands/verify_magic_link.py`

**Changes:**
- Add `membership_auth: Optional[MembershipAuthService] = None` to constructor
- After finding/creating user: if `magic_link.company_id` is not None and `membership_auth` is not None:
  - Look up company to get `auth_mode`
  - Call `membership_auth.resolve_membership(user, magic_link.company_id, company.auth_mode)`
  - Issue JWT with updated user data

**Acceptance Criteria:**
- [x] Constructor accepts optional `MembershipAuthService`
- [x] When `magic_link.company_id` is set: resolves membership via `MembershipAuthService`
- [x] JWT issued with data from updated user row (after copy-on-switch)
- [x] When `magic_link.company_id` is None: existing behavior unchanged
- [x] Needs access to CompanyRepository to look up `auth_mode` — accept via constructor or injection

---

### TASK-013: Modify OAuthLoginService — Accept company_id + Membership

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003

**Description:**
Add optional `company_id` parameter and `MembershipAuthService` dependency to OAuthLoginService.

**File:** `src/auth_bc/user/application/services/oauth_login_service.py`

**Changes:**
- Add `membership_auth: Optional[MembershipAuthService] = None` to constructor
- Add `company_id: Optional[str] = None` parameter to `login_or_create()`
- After finding/creating user: if `company_id` is set, call `membership_auth.resolve_membership()`
- Issue JWT with updated user data

**Acceptance Criteria:**
- [x] Constructor accepts optional `MembershipAuthService`
- [x] `login_or_create()` accepts optional `company_id`
- [x] When `company_id` is set: resolves membership, issues JWT with updated data
- [x] When `company_id` is None: existing behavior unchanged
- [x] Needs access to CompanyRepository to look up `auth_mode` — accept via constructor or injection

---

### TASK-014: Modify PasswordLoginService — Accept company_id + Membership

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-003

**Description:**
Add optional `company_id` and `MembershipAuthService` to PasswordLoginService.

**File:** `src/auth_bc/user/application/commands/password_login.py`

**Changes:**
- Add `company_id: Optional[str] = None` to `PasswordLoginRequest`
- Add `membership_auth: Optional[MembershipAuthService] = None` to constructor
- After password validation: if `command.company_id` is set, call `membership_auth.resolve_membership()`
- Issue JWT with updated user data

**Acceptance Criteria:**
- [x] `PasswordLoginRequest` has `company_id: Optional[str] = None`
- [x] Constructor accepts optional `MembershipAuthService`
- [x] When `company_id` is set: resolves membership, issues JWT with updated data
- [x] When `company_id` is None: existing behavior unchanged
- [x] Needs access to CompanyRepository to look up `auth_mode`

---

### TASK-015: Modify GoogleOAuthLogin — Pass company_id

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-013

**Description:**
Modify GoogleOAuthLoginService to accept and pass `company_id` to OAuthLoginService.

**File:** `src/auth_bc/user/application/commands/google_oauth_login.py`

**Changes:**
- Add `company_id: Optional[str] = None` to `GoogleOAuthLoginRequest`
- Pass `company_id` to `self.oauth_service.login_or_create(info, company_id=request.company_id)`

**Acceptance Criteria:**
- [x] `GoogleOAuthLoginRequest` has `company_id: Optional[str] = None`
- [x] `company_id` passed through to `OAuthLoginService.login_or_create()`

---

### TASK-016: Modify MicrosoftOAuthLogin — Pass company_id

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-013

**Description:**
Modify MicrosoftOAuthLoginService to accept and pass `company_id` to OAuthLoginService.

**File:** `src/auth_bc/user/application/commands/microsoft_oauth_login.py`

**Changes:**
- Add `company_id: Optional[str] = None` to `MicrosoftOAuthLoginRequest`
- Pass `company_id` to `self.oauth_service.login_or_create(info, company_id=request.company_id)`

**Acceptance Criteria:**
- [x] `MicrosoftOAuthLoginRequest` has `company_id: Optional[str] = None`
- [x] `company_id` passed through to `OAuthLoginService.login_or_create()`

---

### TASK-017: Dual-Write — ChangeUserRoleCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-008

**Description:**
Add `CompanyUserRepositoryInterface` dependency to ChangeUserRoleCommandHandler and dual-write role changes.

**File:** `src/auth_bc/user/application/commands/change_user_role.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After `user.change_role()` + `user_repo.save()`:
  ```python
  if self.company_user_repo:
      membership = self.company_user_repo.find_by_user_and_company(user.id, command.company_id)
      if membership:
          membership.change_role(new_role)
          self.company_user_repo.save(membership)
  ```

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] After user role change: also updates CompanyUser.role
- [x] Existing behavior preserved when `company_user_repo` is None

---

### TASK-018: Dual-Write — DeactivateUserCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-008

**Description:**
Add dual-write to DeactivateUserCommandHandler.

**File:** `src/auth_bc/user/application/commands/deactivate_user.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After `user.deactivate()` + `user_repo.save()`:
  ```python
  if self.company_user_repo:
      membership = self.company_user_repo.find_by_user_and_company(user.id, command.company_id)
      if membership:
          membership.deactivate()
          self.company_user_repo.save(membership)
  ```

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] After user deactivate: also sets CompanyUser.is_active = False
- [x] Existing behavior preserved when `company_user_repo` is None

---

### TASK-019: Dual-Write — ActivateUserCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-008

**Description:**
Add dual-write to ActivateUserCommandHandler.

**File:** `src/auth_bc/user/application/commands/activate_user.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After `user.activate()` + `user_repo.save()`:
  ```python
  if self.company_user_repo:
      membership = self.company_user_repo.find_by_user_and_company(user.id, command.company_id)
      if membership:
          membership.activate()
          self.company_user_repo.save(membership)
  ```

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] After user activate: also sets CompanyUser.is_active = True
- [x] Existing behavior preserved when `company_user_repo` is None

---

### TASK-020: Dual-Write — AssignDepartmentCommand

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-008

**Description:**
Add dual-write to AssignDepartmentCommandHandler.

**File:** `src/auth_bc/user/application/commands/assign_department.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After `user.assign_department()` + `user_repo.save()`:
  ```python
  if self.company_user_repo:
      membership = self.company_user_repo.find_by_user_and_company(user.id, command.company_id)
      if membership:
          membership.assign_department(command.department_id)
          self.company_user_repo.save(membership)
  ```

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] After user assign_department: also updates CompanyUser.department_id
- [x] Existing behavior preserved when `company_user_repo` is None

---

### TASK-021: Modify CreateCompanyCommand — Create CompanyUser for Admin

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-001, TASK-008

**Description:**
After creating the initial admin user in CreateCompanyCommand, also create a CompanyUser membership.

**Files:**
- `src/company_bc/company/application/ports.py` — add `CompanyUserWriter` port
- `src/company_bc/company/application/commands/create_company.py` — accept + use port

**Changes:**
Add port:
```python
class CompanyUserWriter(ABC):
    @abstractmethod
    def save(self, company_user) -> None: ...
    @abstractmethod
    def find_by_user_and_company(self, user_id: str, company_id: str) -> Optional[object]: ...
```

In handler: add `company_user_writer: Optional[CompanyUserWriter] = None` to constructor. After creating admin user:
```python
if self.company_user_writer:
    membership = CompanyUser.create(user_id=user.id, company_id=company.id, role=UserRole.ADMIN)
    self.company_user_writer.save(membership)
```

**Acceptance Criteria:**
- [x] `CompanyUserWriter` port added to `ports.py`
- [x] `CreateCompanyCommandHandler` accepts optional `company_user_writer`
- [x] After admin user creation: CompanyUser membership created with ADMIN role
- [x] Existing behavior preserved when writer is None

---

### TASK-022: Modify ImportUsersService — Create CompanyUser Memberships

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-001, TASK-002, TASK-008

**Description:**
After creating/updating users in ImportUsersService.confirm(), also create/update CompanyUser memberships.

**File:** `src/auth_bc/user/application/commands/import_users.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After creating new user: create CompanyUser with same role, department_id, employee_role_id
- After updating existing user: find and update CompanyUser membership

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] New users: CompanyUser created with matching role, department_id, employee_role_id
- [x] Updated users: CompanyUser membership updated (department_id, employee_role_id)
- [x] Existing behavior preserved when repo is None

---

### TASK-023: Modify GDPR Anonymize — Scope to Membership

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-002, TASK-008

**Description:**
Modify `RequestGdprAnonymizeHandler` to deactivate membership and only anonymize identity if zero active memberships remain.

**File:** `src/audit_bc/audit/application/commands/request_gdpr_anonymize.py`

**Changes:**
- Add `company_user_repo: Optional[CompanyUserRepositoryInterface] = None` to constructor
- After creating GDPR request:
  - Find membership, deactivate it
  - Check `count_active_memberships(user_id)` — only anonymize identity if == 0

**Acceptance Criteria:**
- [x] Optional `CompanyUserRepositoryInterface` in constructor
- [x] Deactivates user's membership in the target company
- [x] Checks remaining active memberships before anonymizing identity
- [x] Existing behavior preserved when repo is None

---

## Phase 4: HTTP Layer

### TASK-024: Auth Dependencies — Session Invalidation + New Factories

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-003, TASK-008

**Description:**
Add session invalidation check to `get_current_user()` and add new DI factories.

**File:** `adapters/http/api/auth/dependencies.py`

**Changes:**
1. **Session invalidation** — after user lookup in `get_current_user()`:
```python
jwt_company_id = payload.get("company_id")
if jwt_company_id is not None and user.company_id != jwt_company_id:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired — please log in again")
```

2. **New dependency factories:**
```python
def get_company_user_repo(db) -> CompanyUserRepository: ...
def get_membership_auth_service(db) -> MembershipAuthService: ...
```

**Acceptance Criteria:**
- [x] JWT company_id mismatch check added (after user lookup, before company status check)
- [x] SUPER_ADMIN exempt (jwt_company_id is None when company_id is NULL)
- [x] `get_company_user_repo()` factory added
- [x] `get_membership_auth_service()` factory added

---

### TASK-025: Add Slug-Scoped Auth Endpoints (5 Endpoints)

**Phase:** HTTP
**Complexity:** L
**Dependencies:** TASK-011, TASK-012, TASK-013, TASK-014, TASK-015, TASK-016, TASK-024

**Description:**
Add 5 slug-scoped auth endpoints to the auth router. Each resolves slug → company, checks billing, delegates to existing service with `company_id`.

**File:** `adapters/http/api/auth/routers.py`

**New Endpoints:**
1. `POST /api/v1/auth/{slug}/magic-link`
2. `POST /api/v1/auth/{slug}/verify`
3. `POST /api/v1/auth/{slug}/login`
4. `POST /api/v1/auth/{slug}/oauth/google`
5. `POST /api/v1/auth/{slug}/oauth/microsoft`

**Shared pattern:**
```python
def _resolve_slug(slug: str, company_repo: CompanyRepository) -> Company:
    company = company_repo.find_by_slug(slug)
    if not company or not company.is_active:
        raise HTTPException(status_code=404, detail="Company not found")
    return company
```

Each endpoint:
1. Resolve slug → company (404 if not found)
2. Check company is_active (403 if not)
3. Check billing not suspended (402)
4. Call existing service/handler with `company_id`
5. Map domain exceptions (MembershipDeactivatedError → 403, MembershipNotAllowedError → 403)

**Acceptance Criteria:**
- [x] All 5 slug-scoped endpoints work
- [x] `_resolve_slug()` helper resolves and validates
- [x] Billing suspension check on all slug-scoped endpoints
- [x] `MembershipDeactivatedError` mapped to 403
- [x] `MembershipNotAllowedError` mapped to 403
- [x] MembershipAuthService injected via `get_membership_auth_service()`
- [x] CompanyUserRepository injected where needed

---

### TASK-026: Add Multi-Company Detection to Unscoped Endpoints

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-010, TASK-025

**Description:**
Add multi-company detection to the 5 existing unscoped auth endpoints. If an email domain matches multiple active companies, return 409 with available slugs.

**File:** `adapters/http/api/auth/routers.py`

**Changes:**
Before calling auth services in each unscoped endpoint:
```python
companies = company_lookup.find_companies_by_email_domain(body.email)
active_companies = [(cid, slug, active) for cid, slug, active in companies if active]
if len(active_companies) > 1:
    slugs = [slug for _, slug, _ in active_companies]
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=json.dumps({"error": "multiple_companies", "slugs": slugs}),
    )
```

**Apply to:**
1. `POST /api/v1/auth/magic-link` — check email
2. `POST /api/v1/auth/verify` — check if magic_link has no company_id
3. `POST /api/v1/auth/login` — check email
4. `POST /api/v1/auth/oauth/google` — check after token decode
5. `POST /api/v1/auth/oauth/microsoft` — check after token decode

**Acceptance Criteria:**
- [x] Single-company email → proceeds as today (no behavior change)
- [x] Multi-company email → 409 with `{"error": "multiple_companies", "slugs": [...]}`
- [x] SUPER_ADMIN unaffected (company_id = NULL)
- [x] All 5 unscoped endpoints have the check

---

### TASK-027: Wire Dual-Write Repos + Membership into User Management Routers

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-017, TASK-018, TASK-019, TASK-020, TASK-021, TASK-022

**Description:**
Pass `CompanyUserRepository` to all command handlers in user management routers. Add CompanyUser creation for invite and quick-create.

**File:** `adapters/http/api/users/routers.py`

**Changes:**
1. **Dual-write wiring** — pass `CompanyUserRepository(db)` to:
   - `ChangeUserRoleCommandHandler`
   - `DeactivateUserCommandHandler`
   - `ActivateUserCommandHandler`
   - `AssignDepartmentCommandHandler`

2. **Invite membership** — in `_ensure_user_for_invite()`:
   - After creating/updating user, create CompanyUser if not exists

3. **Quick-create membership** — in `quick_create_employee()`:
   - After creating user, create CompanyUser membership

4. **Import users** — pass `CompanyUserRepository` to `ImportUsersService`

**Also modify:** `adapters/http/api/users/dependencies.py` — add `get_company_user_repo`

**Acceptance Criteria:**
- [x] All 4 dual-write command handlers receive `company_user_repo`
- [x] Invite creates CompanyUser membership
- [x] Quick-create creates CompanyUser membership
- [x] Import users passes CompanyUserRepository
- [x] `get_company_user_repo` added to users dependencies

---

## Phase 5: Tests

### TASK-028: Unit Tests — Domain Layer

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-001, TASK-002, TASK-003, TASK-004, TASK-005

**Description:**
Unit tests for all new domain objects.

**Files:**
- `tests/unit/auth_bc/company_user/test_company_user_entity.py`
- `tests/unit/auth_bc/company_user/test_membership_auth_service.py`
- `tests/unit/auth_bc/magic_link/test_magic_link_entity.py` (add company_id tests)

**Test cases:**
1. **CompanyUser entity:**
   - `create()` generates ULID, defaults EMPLOYEE role, is_active=True
   - `change_role()` updates role
   - `deactivate()` sets is_active=False
   - `activate()` sets is_active=True
   - `assign_department()` sets department_id
   - `assign_employee_role()` sets employee_role_id

2. **MembershipAuthService (5 paths):**
   - Active membership → copies data to user, returns user
   - Inactive membership → raises MembershipDeactivatedError
   - No membership + domain mode + email allowed → auto-creates, copies, returns
   - No membership + domain mode + email not allowed → raises MembershipNotAllowedError
   - No membership + membership_only mode → raises MembershipNotAllowedError

3. **MagicLink.create() with company_id:**
   - company_id=None → backward compatible
   - company_id="abc" → stored on entity

4. **Domain exceptions:**
   - MultipleCompaniesError stores slugs

**Acceptance Criteria:**
- [x] All CompanyUser entity methods tested
- [x] All 5 MembershipAuthService paths tested (using mocks for repos)
- [x] MagicLink company_id backward compatibility tested
- [x] All tests pass

---

### TASK-029: Unit Tests — Application Layer

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-011 through TASK-023

**Description:**
Unit tests for all modified application services and commands.

**Files:**
- `tests/unit/auth_bc/magic_link/test_create_magic_link.py` (add company_id tests)
- `tests/unit/auth_bc/magic_link/test_verify_magic_link.py` (add membership tests)
- `tests/unit/auth_bc/user/test_oauth_login_service.py` (add company_id tests)
- `tests/unit/auth_bc/user/test_password_login.py` (add company_id tests)
- `tests/unit/auth_bc/user/test_change_user_role.py` (add dual-write tests)
- `tests/unit/auth_bc/user/test_deactivate_user.py` (add dual-write tests)
- `tests/unit/auth_bc/user/test_activate_user.py` (add dual-write tests)
- `tests/unit/auth_bc/user/test_assign_department.py` (add dual-write tests)
- `tests/unit/company_bc/test_create_company.py` (add CompanyUser tests)
- `tests/unit/auth_bc/user/test_import_users.py` (add CompanyUser tests)

**Test cases:**
1. **CreateMagicLink with company_id** — validates email, stores company_id on link
2. **VerifyMagicLink with membership** — resolves membership, issues correct JWT
3. **OAuthLogin with company_id** — resolves membership after identity auth
4. **PasswordLogin with company_id** — resolves membership after password check
5. **Dual-write commands** — each confirms CompanyUser updated after user updated
6. **CreateCompany** — confirms CompanyUser created for admin
7. **ImportUsers** — confirms CompanyUser memberships created

**Acceptance Criteria:**
- [x] All modified services tested with company_id present and absent
- [x] Dual-write tests verify both user repo and company_user repo called
- [x] Backward compatibility tested (company_id=None → existing behavior)
- [x] All tests pass

---

### TASK-030: Integration Tests — CompanyUserRepository

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-007, TASK-008

**Description:**
Integration tests for CompanyUserRepository against test database.

**File:** `tests/integration/auth_bc/test_company_user_repository.py`

**Test cases:**
1. `save()` — insert new CompanyUser, verify persisted
2. `save()` — update existing CompanyUser, verify fields changed
3. `find_by_user_and_company()` — found and not found
4. `find_by_user_id()` — multiple memberships returned
5. `find_active_by_user_id()` — only active returned
6. `find_by_company_id()` — all memberships for company
7. `count_admins_in_company()` — counts correctly
8. `count_active_memberships()` — counts correctly
9. Unique constraint violation on (user_id, company_id) duplicate

**Acceptance Criteria:**
- [x] All 7 repository methods tested
- [x] Uses test database with transaction rollback
- [x] Unique constraint tested

---

### TASK-031: Integration Tests — Slug-Scoped Auth Endpoints

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-025, TASK-026, TASK-024

**Description:**
Integration tests for the 5 slug-scoped auth endpoints, multi-company detection, and session invalidation.

**File:** `tests/integration/auth_bc/test_scoped_auth_endpoints.py`

**Test cases:**
1. **Slug-scoped magic-link** — valid slug, email allowed → 200
2. **Slug-scoped magic-link** — invalid slug → 404
3. **Slug-scoped verify** — membership auto-created for domain mode
4. **Slug-scoped verify** — inactive membership → 403
5. **Slug-scoped verify** — membership_only + no membership → 403
6. **Slug-scoped login** — password login scoped to company
7. **Slug-scoped OAuth** — Google/Microsoft with membership resolution
8. **Multi-company detection** — email matches 2 companies → 409 with slugs
9. **Single-company** — unscoped endpoint → works as today
10. **Session invalidation** — JWT company_id mismatch → 401
11. **Session invalidation** — SUPER_ADMIN exempt
12. **Billing suspension** — slug-scoped endpoint with suspended company → 402

**Acceptance Criteria:**
- [x] All 5 slug-scoped endpoints tested
- [x] Multi-company detection tested
- [x] Session invalidation tested (both reject and exempt cases)
- [x] Billing suspension tested

---

## Phase 6: Frontend

### TASK-032: LoginPage — Post to Slug-Scoped Endpoints

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-025

**Description:**
Update LoginPage to POST to slug-scoped endpoints when slug param is present in URL.

**File:** `web/app/src/pages/auth/LoginPage.tsx`

**Changes:**
- When `slug` is present:
  - `POST /api/v1/auth/${slug}/magic-link` instead of `/api/v1/auth/magic-link`
  - `POST /api/v1/auth/${slug}/verify` instead of `/api/v1/auth/verify`
  - `POST /api/v1/auth/${slug}/login` instead of `/api/v1/auth/login`
  - `POST /api/v1/auth/${slug}/oauth/google` instead of `/api/v1/auth/oauth/google`
  - `POST /api/v1/auth/${slug}/oauth/microsoft` instead of `/api/v1/auth/oauth/microsoft`
- Handle `409` multi-company error: display available slugs as links
- Handle `403` membership errors: display user-friendly messages

**Acceptance Criteria:**
- [x] All 5 auth API calls use slug-scoped URLs when slug is present
- [x] Multi-company error (409) displays company slug links
- [x] Membership errors (403) show user-friendly messages
- [x] Non-slug login still works as before

---

## Phase 7: Verification

### TASK-033: Run Full Test Suite + Linter

**Phase:** Verification
**Complexity:** S
**Dependencies:** All previous tasks

**Description:**
Run the full test suite, linter, and type checker to verify no regressions.

**Commands:**
```bash
make test          # Unit tests
make test-integration  # Integration tests
make lint          # mypy + flake8
```

**Acceptance Criteria:**
- [x] All unit tests pass (including pre-existing)
- [x] All integration tests pass
- [x] mypy passes
- [x] flake8 passes
- [x] No regressions in existing functionality

---

## Dependency Graph

```
TASK-001 (Entity) ─────┬──> TASK-002 (RepoInterface) ──> TASK-008 (RepoImpl)
                        │                                      │
                        ├──> TASK-003 (MembershipAuthSvc) ─────┤
                        │         │                            │
                        │         ├──> TASK-012 (VerifyML) ────┤
                        │         ├──> TASK-013 (OAuth) ───────┤
                        │         └──> TASK-014 (Password) ────┤
                        │                                      │
                        └──> TASK-006 (Model) ──> TASK-007 (Migration)
                                                       │
TASK-004 (ML entity) ──> TASK-009 (ML model+repo) ─────┘
                              │
TASK-005 (LookupIface) ──> TASK-010 (LookupImpl)
                              │
                        TASK-011 (CreateML cmd)

TASK-013 ──> TASK-015 (Google)
TASK-013 ──> TASK-016 (Microsoft)

TASK-008 ──> TASK-017 (DW ChangeRole)
TASK-008 ──> TASK-018 (DW Deactivate)
TASK-008 ──> TASK-019 (DW Activate)
TASK-008 ──> TASK-020 (DW AssignDept)
TASK-008 ──> TASK-021 (CreateCompany)
TASK-008 ──> TASK-022 (Import)
TASK-008 ──> TASK-023 (GDPR)

TASK-024 (Dependencies) ──> TASK-025 (Slug endpoints)
                              │
                        TASK-026 (Multi-company)
                        TASK-027 (User router wiring)

TASK-028..031 (Tests) depend on implementation tasks
TASK-032 (Frontend) depends on TASK-025
TASK-033 (Verification) depends on ALL
```

## Execution Order

**Batch 1 (Parallel — Domain Layer, no dependencies):**
TASK-001, TASK-004, TASK-005

**Batch 2 (Parallel — Domain depends on Batch 1):**
TASK-002, TASK-003, TASK-006

**Batch 3 (Parallel — Infrastructure):**
TASK-007, TASK-008, TASK-009, TASK-010

**Batch 4 (Parallel — Application auth flows):**
TASK-011, TASK-012, TASK-013, TASK-014

**Batch 5 (Parallel — Application pass-through + dual-writes):**
TASK-015, TASK-016, TASK-017, TASK-018, TASK-019, TASK-020, TASK-021, TASK-022, TASK-023

**Batch 6 (Sequential — HTTP layer):**
TASK-024 → TASK-025 → TASK-026, TASK-027 (parallel)

**Batch 7 (Parallel — Tests):**
TASK-028, TASK-029, TASK-030, TASK-031

**Batch 8:**
TASK-032 (Frontend)

**Batch 9:**
TASK-033 (Verification)

## Final Checklist

- [ ] All 33 tasks completed
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] mypy passes
- [ ] flake8 passes
- [ ] Migration runs successfully (upgrade + downgrade)
- [ ] Data migration verified: existing users have CompanyUser records
- [ ] No regressions in existing auth flows
- [ ] Frontend compiles and builds
