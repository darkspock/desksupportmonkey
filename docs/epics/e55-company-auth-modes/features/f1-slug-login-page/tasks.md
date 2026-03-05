# Implementation Tasks: F1 — Slug & Login Page

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 17
**Estimated Complexity:** M

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Interfaces | 1 | S |
| Infrastructure - Migration | 1 | M |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Application - Commands | 2 | S + M |
| Application - Queries | 1 | M |
| HTTP - Schemas | 1 | S |
| HTTP - Routers | 2 | M + M |
| Tests - Unit | 3 | M + S + S |
| Tests - Integration | 1 | M |
| Frontend | 3 | M + M + S |

---

## Phase 1: Domain Layer

### TASK-001: Add AuthMode Enum

**Phase:** Domain - Enums
**Complexity:** S
**Dependencies:** None

**Description:**
Add the `AuthMode` enum to the existing company enums file.

**File:** `src/company_bc/company/domain/enums.py`

**Implementation:**
```python
class AuthMode(str, Enum):
    """Authentication mode for a company."""
    DOMAIN = "domain"
    MEMBERSHIP_ONLY = "membership_only"
```

**Acceptance Criteria:**
- [x] `AuthMode` enum with `DOMAIN` and `MEMBERSHIP_ONLY` values
- [x] Inherits from `str, Enum` for JSON serialization
- [x] Added to existing `enums.py` file (do NOT create new file)

---

### TASK-002: Add Slug & Auth Mode to Company Entity

**Phase:** Domain - Entities
**Complexity:** M
**Dependencies:** TASK-001

**Description:**
Modify the existing `Company` entity to add `slug` and `auth_mode` fields, slug generation/validation methods, `update_slug()` method, `RESERVED_SLUGS` constant, and domain exceptions (`InvalidSlugError`, `SlugAlreadyTakenError`).

**File:** `src/company_bc/company/domain/entities.py`

**Implementation:**

New fields on `@dataclass Company`:
```python
slug: Optional[str] = None
auth_mode: AuthMode = AuthMode.DOMAIN
```

New constant:
```python
RESERVED_SLUGS = frozenset({
    'admin', 'api', 'login', 'register', 'reseller', 'app', 'auth', 'super-admin',
})
```

New static methods:
```python
@staticmethod
def generate_slug(name: str) -> str:
    """Generate URL-safe slug from company name. NFKD normalization → ASCII → lowercase + hyphens."""
    normalized = unicodedata.normalize('NFKD', name)
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')
    if len(slug) < 3:
        slug = slug + '-co'
    return slug[:50]

@staticmethod
def validate_slug(slug: str) -> None:
    """Validate slug format. Raises ValueError if invalid."""
    if not slug:
        raise ValueError("Slug is required")
    if len(slug) < 3 or len(slug) > 50:
        raise ValueError("Slug must be between 3 and 50 characters")
    if not re.match(r'^[a-z0-9]+(-[a-z0-9]+)*$', slug):
        raise ValueError("Slug must be lowercase alphanumeric with hyphens only")
    if slug in Company.RESERVED_SLUGS:
        raise ValueError(f"Slug '{slug}' is reserved")
```

New instance method:
```python
def update_slug(self, slug: str) -> None:
    """Update the company slug after validation."""
    Company.validate_slug(slug)
    self.slug = slug
```

New exceptions (in same file):
```python
class InvalidSlugError(Exception):
    pass

class SlugAlreadyTakenError(Exception):
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Slug '{slug}' is already taken")
```

Modify `Company.create()`:
- Add `slug: Optional[str] = None` parameter
- If slug provided, validate and assign
- If not provided, generate from name (collision resolution happens in handler)

**Acceptance Criteria:**
- [x] `slug: Optional[str] = None` field on Company dataclass
- [x] `auth_mode: AuthMode = AuthMode.DOMAIN` field on Company dataclass
- [x] `RESERVED_SLUGS` frozenset constant
- [x] `generate_slug(name)` static method with unicode handling
- [x] `validate_slug(slug)` static method with format + reserved word checks
- [x] `update_slug(slug)` instance method
- [x] `InvalidSlugError` exception
- [x] `SlugAlreadyTakenError` exception
- [x] `Company.create()` accepts optional `slug` parameter
- [x] Imports: `re`, `unicodedata`, `AuthMode`

---

### TASK-003: Add Repository Interface Methods

**Phase:** Domain - Interfaces
**Complexity:** S
**Dependencies:** TASK-002

**Description:**
Add `find_by_slug()` and `slug_exists()` abstract methods to `CompanyRepositoryInterface`.

**File:** `src/company_bc/company/domain/repository.py`

**Implementation:**
```python
@abstractmethod
def find_by_slug(self, slug: str) -> Optional[Company]:
    """Find company by slug (returns company regardless of status)."""
    pass

@abstractmethod
def slug_exists(self, slug: str, exclude_company_id: Optional[str] = None) -> bool:
    """Check if slug is already taken, optionally excluding a company ID (for updates)."""
    pass
```

**Acceptance Criteria:**
- [x] `find_by_slug(slug) -> Optional[Company]` abstract method
- [x] `slug_exists(slug, exclude_company_id=None) -> bool` abstract method
- [x] Added to existing interface (do NOT create new file)

---

## Phase 2: Infrastructure Layer

### TASK-004: Add Slug & Auth Mode Columns to CompanyModel

**Phase:** Infrastructure - Models
**Complexity:** S
**Dependencies:** TASK-001

**Description:**
Add `slug` and `auth_mode` columns to the existing `CompanyModel`.

**File:** `src/company_bc/company/infrastructure/models.py`

**Implementation:**
```python
slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
auth_mode: Mapped[str] = mapped_column(String(20), nullable=False, server_default="domain")
```

**Acceptance Criteria:**
- [x] `slug` column: String(50), unique, indexed
- [x] `auth_mode` column: String(20), nullable=False, server_default="domain"
- [x] SQLAlchemy 2.0 style (`Mapped[str]` + `mapped_column()`)

---

### TASK-005: Create Alembic Migration

**Phase:** Infrastructure - Migration
**Complexity:** M
**Dependencies:** TASK-004

**Description:**
Create Alembic migration to add `slug` and `auth_mode` columns to `companies` table, with data migration to auto-generate slugs for all existing companies.

**File:** `alembic/versions/f1a2b3c4d5e6_add_company_slug_and_auth_mode.py`

**Migration chain:** `down_revision = 'e9f0g1h2i3j4'` (latest from E54 F5)

**Implementation:**
```python
def upgrade():
    # Step 1: Add nullable slug and auth_mode columns
    op.add_column('companies', sa.Column('slug', sa.String(50), nullable=True))
    op.add_column('companies', sa.Column('auth_mode', sa.String(20), nullable=False, server_default='domain'))

    # Step 2: Generate slugs for existing companies
    conn = op.get_bind()
    companies = conn.execute(sa.text("SELECT id, name FROM companies ORDER BY created_at")).fetchall()
    used_slugs = set()
    for company_id, name in companies:
        base = _generate_slug(name)
        slug = base
        counter = 2
        while slug in used_slugs:
            slug = f"{base[:46]}-{counter}"
            counter += 1
        used_slugs.add(slug)
        conn.execute(
            sa.text("UPDATE companies SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": company_id}
        )

    # Step 3: Set NOT NULL and unique index
    op.alter_column('companies', 'slug', nullable=False)
    op.create_unique_constraint('uq_companies_slug', 'companies', ['slug'])
    op.create_index('ix_companies_slug', 'companies', ['slug'])

def downgrade():
    op.drop_index('ix_companies_slug', table_name='companies')
    op.drop_constraint('uq_companies_slug', 'companies', type_='unique')
    op.drop_column('companies', 'auth_mode')
    op.drop_column('companies', 'slug')
```

Include a standalone `_generate_slug(name)` function in the migration file (same logic as `Company.generate_slug()` but self-contained to avoid import dependencies).

**Acceptance Criteria:**
- [x] Adds nullable `slug` column
- [x] Adds `auth_mode` column with server_default `'domain'`
- [x] Data migration generates slugs for all existing companies
- [x] Collision handling with `-2`, `-3` suffixes
- [x] Sets `slug` to NOT NULL after population
- [x] Creates unique constraint on `slug`
- [x] Creates index on `slug`
- [x] Reversible downgrade method
- [x] down_revision chains from `e9f0g1h2i3j4`

---

### TASK-006: Implement Repository Methods

**Phase:** Infrastructure - Repositories
**Complexity:** M
**Dependencies:** TASK-003, TASK-004

**Description:**
Implement `find_by_slug()` and `slug_exists()` in `CompanyRepository`. Update `save()` to include slug and auth_mode in both insert and update paths. Update `_to_entity()` to map slug and auth_mode from model.

**File:** `src/company_bc/company/infrastructure/repository.py`

**Implementation:**

New methods:
```python
def find_by_slug(self, slug: str) -> Optional[Company]:
    stmt = select(CompanyModel).where(CompanyModel.slug == slug)
    model = self.session.execute(stmt).scalar_one_or_none()
    return self._to_entity(model) if model else None

def slug_exists(self, slug: str, exclude_company_id: Optional[str] = None) -> bool:
    stmt = select(exists().where(CompanyModel.slug == slug))
    if exclude_company_id:
        stmt = select(exists().where(
            CompanyModel.slug == slug,
            CompanyModel.id != exclude_company_id
        ))
    return self.session.execute(stmt).scalar()
```

Modified `save()`:
- Add `slug` and `auth_mode` to the model fields in both create (INSERT) and update paths

Modified `_to_entity()`:
- Add `slug=model.slug, auth_mode=AuthMode(model.auth_mode)` to entity construction

**Acceptance Criteria:**
- [x] `find_by_slug()` returns Company entity or None
- [x] `slug_exists()` with optional `exclude_company_id` parameter
- [x] `save()` persists slug and auth_mode on create and update
- [x] `_to_entity()` maps slug and auth_mode from model to entity

---

## Phase 3: Application Layer

### TASK-007: Modify CreateCompanyCommand for Auto-Slug

**Phase:** Application - Commands (modified)
**Complexity:** S
**Dependencies:** TASK-002, TASK-006

**Description:**
Modify the existing `CreateCompanyCommandHandler` to auto-generate a slug on company creation with collision resolution.

**File:** `src/company_bc/company/application/commands/create_company.py`

**Implementation:**
After `Company.create(...)`, add slug generation:
```python
# Generate slug with collision resolution
base_slug = Company.generate_slug(company.name)
slug = base_slug
counter = 2
while self.company_repo.slug_exists(slug):
    slug = f"{base_slug[:46]}-{counter}"
    counter += 1
company.slug = slug
```

Also check reserved slugs during collision resolution loop.

**Acceptance Criteria:**
- [x] Auto-generates slug from company name on creation
- [x] Handles collisions with `-2`, `-3` suffix pattern
- [x] Truncates base slug to 46 chars before appending suffix
- [x] Sets `company.slug` before `company_repo.save()`

---

### TASK-008: Create UpdateCompanySlugCommand

**Phase:** Application - Commands (new)
**Complexity:** M
**Dependencies:** TASK-002, TASK-006

**Description:**
Create `UpdateCompanySlugCommand` and `UpdateCompanySlugCommandHandler` for admin slug updates.

**File:** `src/company_bc/company/application/commands/update_company_slug.py`

**Implementation:**
```python
@dataclass
class UpdateCompanySlugCommand(Command):
    company_id: str
    slug: str

class UpdateCompanySlugCommandHandler(CommandHandler[UpdateCompanySlugCommand]):
    def __init__(self, company_repo: CompanyRepositoryInterface):
        self.company_repo = company_repo

    def handle(self, command: UpdateCompanySlugCommand) -> None:
        company = self.company_repo.find_by_id(command.company_id)
        if not company:
            raise CompanyNotFoundError(command.company_id)
        Company.validate_slug(command.slug)
        if self.company_repo.slug_exists(command.slug, exclude_company_id=command.company_id):
            raise SlugAlreadyTakenError(command.slug)
        company.update_slug(command.slug)
        self.company_repo.save(company)
```

**Acceptance Criteria:**
- [x] `UpdateCompanySlugCommand` dataclass with `company_id` and `slug` fields
- [x] Handler finds company, validates slug, checks uniqueness, updates and saves
- [x] Raises `CompanyNotFoundError` if company not found
- [x] Raises `ValueError` (via `validate_slug`) if slug format invalid
- [x] Raises `SlugAlreadyTakenError` if slug taken by another company
- [x] Command + Handler in same file

---

### TASK-009: Create GetCompanyBySlugQuery

**Phase:** Application - Queries (new)
**Complexity:** M
**Dependencies:** TASK-002, TASK-006

**Description:**
Create `GetCompanyBySlugQuery`, `GetCompanyBySlugQueryHandler`, and `CompanyBySlugDto` for the public slug resolution endpoint.

**File:** `src/company_bc/company/application/queries/get_company_by_slug.py`

**Implementation:**
```python
@dataclass
class CompanyBySlugDto:
    id: str
    name: str
    slug: str
    auth_mode: str
    google_enabled: bool
    microsoft_enabled: bool

@dataclass
class GetCompanyBySlugQuery(Query):
    slug: str

class GetCompanyBySlugQueryHandler(QueryHandler[GetCompanyBySlugQuery, CompanyBySlugDto]):
    def __init__(self, company_repo: CompanyRepositoryInterface, oauth_settings: OAuthSettings):
        self.company_repo = company_repo
        self.oauth_settings = oauth_settings

    def handle(self, query: GetCompanyBySlugQuery) -> CompanyBySlugDto:
        company = self.company_repo.find_by_slug(query.slug)
        if not company:
            raise CompanyNotFoundError(query.slug)
        if not company.is_active:
            raise CompanyNotFoundError(query.slug)  # Don't reveal deactivated companies
        return CompanyBySlugDto(
            id=company.id,
            name=company.name,
            slug=company.slug,
            auth_mode=company.auth_mode.value,
            google_enabled=bool(self.oauth_settings.GOOGLE_CLIENT_ID),
            microsoft_enabled=bool(self.oauth_settings.MICROSOFT_CLIENT_ID),
        )
```

**Acceptance Criteria:**
- [x] `CompanyBySlugDto` with id, name, slug, auth_mode, google_enabled, microsoft_enabled
- [x] `GetCompanyBySlugQuery` with slug field
- [x] Handler resolves slug → company, checks active status, returns DTO with OAuth availability
- [x] Raises `CompanyNotFoundError` for missing or deactivated companies
- [x] Uses `OAuthSettings` to determine provider availability
- [x] Query + Handler + DTO in same file

---

## Phase 4: HTTP Layer

### TASK-010: Add/Modify Schemas

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Add new schemas and modify existing ones to include slug and auth_mode.

**Files:**
- `adapters/http/api/companies/schemas.py` — add `CompanyBySlugResponse`, `UpdateSlugRequest`; add `slug` and `auth_mode` to `CompanyResponse`
- `adapters/http/api/my/schemas.py` — add `slug` and `auth_mode` to `MyCompanySettingsResponse`

**Implementation:**

New schemas in `companies/schemas.py`:
```python
class CompanyBySlugResponse(BaseModel):
    id: str
    name: str
    slug: str
    auth_mode: str
    google_enabled: bool
    microsoft_enabled: bool

class UpdateSlugRequest(BaseModel):
    slug: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-z0-9]+(-[a-z0-9]+)*$')
```

Modified `CompanyResponse`:
- Add `slug: str` and `auth_mode: str` fields

Modified `MyCompanySettingsResponse`:
- Add `slug: str` and `auth_mode: str` fields

**Acceptance Criteria:**
- [x] `CompanyBySlugResponse` schema with all 6 fields
- [x] `UpdateSlugRequest` schema with pattern-validated slug
- [x] `CompanyResponse` has `slug` and `auth_mode`
- [x] `MyCompanySettingsResponse` has `slug` and `auth_mode`

---

### TASK-011: Add Company Router Endpoints

**Phase:** HTTP - Routers
**Complexity:** M
**Dependencies:** TASK-008, TASK-009, TASK-010

**Description:**
Add `GET /by-slug/{slug}` (public, no auth) and `PATCH /{company_id}/slug` (super admin) endpoints to the company router.

**File:** `adapters/http/api/companies/routers.py`

**Implementation:**

`GET /by-slug/{slug}`:
- Public endpoint (no auth required)
- Call `GetCompanyBySlugQuery` via query bus
- Map DTO to `CompanyBySlugResponse`
- Error handling: `CompanyNotFoundError` → 404

`PATCH /{company_id}/slug`:
- Requires SUPER_ADMIN role
- Accept `UpdateSlugRequest` body
- Call `UpdateCompanySlugCommand` via command bus
- Error handling: `SlugAlreadyTakenError` → 409, `ValueError` → 422, `CompanyNotFoundError` → 404

**Acceptance Criteria:**
- [x] `GET /api/v1/companies/by-slug/{slug}` — public, returns `CompanyBySlugResponse`
- [x] `PATCH /api/v1/companies/{company_id}/slug` — SUPER_ADMIN, accepts `UpdateSlugRequest`
- [x] `CompanyNotFoundError` → 404
- [x] `SlugAlreadyTakenError` → 409
- [x] `ValueError` (slug validation) → 422

---

### TASK-012: Add My Settings Router Endpoint

**Phase:** HTTP - Routers
**Complexity:** M
**Dependencies:** TASK-008, TASK-010

**Description:**
Add `PATCH /company-settings/slug` endpoint to the my-settings router. Update `_to_company_settings()` to include slug and auth_mode.

**File:** `adapters/http/api/my/routers.py`

**Implementation:**

`PATCH /company-settings/slug`:
- Requires ADMIN role
- Accept `UpdateSlugRequest` body
- Call `UpdateCompanySlugCommand` with current user's company_id
- Return updated `MyCompanySettingsResponse`
- Error handling: `SlugAlreadyTakenError` → 409, `ValueError` → 422

`_to_company_settings()`:
- Add `slug=company.slug` and `auth_mode=company.auth_mode.value` (or `company.auth_mode` depending on entity type) to response mapping

**Acceptance Criteria:**
- [x] `PATCH /api/v1/my/company-settings/slug` — ADMIN, accepts `UpdateSlugRequest`
- [x] Returns updated `MyCompanySettingsResponse`
- [x] `_to_company_settings()` includes slug and auth_mode
- [x] `SlugAlreadyTakenError` → 409
- [x] `ValueError` → 422

---

## Phase 5: Tests

### TASK-013: Unit Tests — Slug Domain Logic

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-002

**Description:**
Create unit tests for slug generation, validation, reserved slug rejection, and Company entity slug methods.

**File:** `tests/unit/company_bc/company/domain/test_company_slug.py`

**Test Cases:**
- `generate_slug("Acme Corp")` → `"acme-corp"`
- `generate_slug("Ñoño & Friends S.A.")` → unicode handling
- `generate_slug("AB")` → short name gets `-co` suffix
- `generate_slug("a" * 100)` → truncation to 50 chars
- `validate_slug("acme-corp")` → passes
- `validate_slug("UPPER")` → raises ValueError
- `validate_slug("ab")` → raises ValueError (too short)
- `validate_slug("admin")` → raises ValueError (reserved)
- `validate_slug("login")` → raises ValueError (reserved)
- `validate_slug("slug with spaces")` → raises ValueError
- `update_slug("valid-slug")` → updates entity slug
- `update_slug("admin")` → raises ValueError

**Acceptance Criteria:**
- [x] Tests for `generate_slug()` — normal names, unicode, short names, long names
- [x] Tests for `validate_slug()` — valid slugs, invalid format, reserved slugs, boundary lengths
- [x] Tests for `update_slug()` — happy path, invalid slug
- [x] All 8 reserved slugs tested

---

### TASK-014: Unit Tests — UpdateCompanySlugCommand

**Phase:** Tests - Unit
**Complexity:** S
**Dependencies:** TASK-008

**Description:**
Create unit tests for the UpdateCompanySlugCommand handler.

**File:** `tests/unit/company_bc/company/application/test_update_company_slug.py`

**Test Cases:**
- Happy path: company found, slug valid, slug unique → updates and saves
- Company not found → raises CompanyNotFoundError
- Invalid slug format → raises ValueError
- Slug already taken → raises SlugAlreadyTakenError
- Same slug as current (own company) → succeeds (exclude_company_id)

**Acceptance Criteria:**
- [x] Tests for success case
- [x] Tests for company not found
- [x] Tests for invalid slug
- [x] Tests for slug collision
- [x] Uses mocks for CompanyRepositoryInterface

---

### TASK-015: Unit Tests — GetCompanyBySlugQuery

**Phase:** Tests - Unit
**Complexity:** S
**Dependencies:** TASK-009

**Description:**
Create unit tests for the GetCompanyBySlugQuery handler.

**File:** `tests/unit/company_bc/company/application/test_get_company_by_slug.py`

**Test Cases:**
- Happy path: active company found → returns DTO with OAuth availability
- Company not found → raises CompanyNotFoundError
- Company deactivated → raises CompanyNotFoundError
- OAuth settings with Google only → google_enabled=True, microsoft_enabled=False
- OAuth settings with neither → both False

**Acceptance Criteria:**
- [x] Tests for success case with DTO fields
- [x] Tests for company not found
- [x] Tests for deactivated company
- [x] Tests for OAuth settings mapping
- [x] Uses mocks for CompanyRepositoryInterface and OAuthSettings

---

### TASK-016: Integration Tests — Slug Endpoints

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-011, TASK-012

**Description:**
Create integration tests for all slug-related endpoints.

**File:** `tests/integration/test_company_slug_endpoints.py`

**Test Cases:**
- `GET /api/v1/companies/by-slug/{slug}` — success returns company info
- `GET /api/v1/companies/by-slug/{slug}` — 404 for non-existent slug
- `GET /api/v1/companies/by-slug/{slug}` — 404 for deactivated company
- `PATCH /api/v1/companies/{company_id}/slug` — super admin updates slug
- `PATCH /api/v1/companies/{company_id}/slug` — 409 for duplicate slug
- `PATCH /api/v1/companies/{company_id}/slug` — 422 for invalid slug
- `PATCH /api/v1/companies/{company_id}/slug` — 403 for non-super-admin
- `PATCH /api/v1/my/company-settings/slug` — admin updates own company slug
- `PATCH /api/v1/my/company-settings/slug` — 409 for duplicate slug
- Create company → verify slug auto-generated
- Create two companies with same name → verify collision handling

**Acceptance Criteria:**
- [x] All endpoint success and error cases tested
- [x] Uses test database with proper fixtures
- [x] Tests auth requirements (public vs admin vs super_admin)
- [x] Tests slug collision handling on create

---

## Phase 6: Frontend

### TASK-017: Add `/login/:slug` Route and Refactor LoginPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-011

**Description:**
Add the `/login/:slug` route to the router and refactor `LoginPage.tsx` to be slug-aware: when slug param is present, fetch company info via `GET /api/v1/companies/by-slug/{slug}` and display company name with available auth methods. When no slug, show a "Find your company" search input.

**Files:**
- `web/app/src/router.tsx` — add `/login/:slug` route
- `web/app/src/pages/auth/LoginPage.tsx` — slug-aware refactor

**Implementation:**

Router: Add `/login/:slug` pointing to `LoginPage`.

LoginPage:
- Use `useParams()` to get optional `slug`
- If slug present: `GET /api/v1/companies/by-slug/{slug}` → display company name, show auth buttons based on `google_enabled`, `microsoft_enabled`
- If no slug: show search input where user can type company slug
- Auth still uses existing unscoped endpoints (no change to auth flow)

**Acceptance Criteria:**
- [x] `/login/:slug` route renders LoginPage
- [x] LoginPage fetches company by slug and displays company name
- [x] Auth method buttons shown based on company info (google_enabled, microsoft_enabled)
- [x] `/login` without slug shows company search/finder
- [x] Existing auth flow unchanged (uses unscoped endpoints)
- [x] 404 slug shows appropriate error message

---

### TASK-018: Add Slug Field to CompanySettingsPage

**Phase:** Frontend
**Complexity:** M
**Dependencies:** TASK-012

**Description:**
Add slug display and edit functionality to the admin CompanySettingsPage.

**File:** `web/app/src/pages/admin/CompanySettingsPage.tsx`

**Implementation:**
- Show current slug in company settings
- Allow editing with save (calls `PATCH /api/v1/my/company-settings/slug`)
- Show validation errors (invalid format, duplicate slug)
- Show the company login URL (`/login/{slug}`) as a copyable link

**Acceptance Criteria:**
- [x] Slug field displayed in company settings
- [x] Editable with save button
- [x] Validation error messages (format, duplicate)
- [x] Login URL shown as copyable text
- [x] `auth_mode` displayed (read-only for F1, editable in F4)

---

### TASK-019: Add i18n Keys

**Phase:** Frontend
**Complexity:** S
**Dependencies:** TASK-017, TASK-018

**Description:**
Add internationalization keys for all slug-related UI text in English and Spanish.

**Files:**
- `web/app/src/locales/en.ts`
- `web/app/src/locales/es.ts`

**Keys to add:**
- Company settings: slug label, slug description, login URL label, auth mode label, auth mode descriptions
- Login page: company name header, find your company placeholder, company not found error
- Validation errors: slug format, slug taken, slug reserved

**Acceptance Criteria:**
- [x] English translations added
- [x] Spanish translations added
- [x] All slug-related UI text uses i18n keys

---

## Dependency Graph

```
TASK-001 (AuthMode enum)
  ├──→ TASK-002 (Company entity changes)
  │      ├──→ TASK-003 (Repository interface)
  │      │      └──→ TASK-006 (Repository implementation)
  │      │             ├──→ TASK-007 (Modify CreateCompanyCommand)
  │      │             ├──→ TASK-008 (UpdateCompanySlugCommand)
  │      │             └──→ TASK-009 (GetCompanyBySlugQuery)
  │      └──→ TASK-013 (Unit tests - domain slug logic)
  └──→ TASK-004 (CompanyModel columns)
         └──→ TASK-005 (Migration)
         └──→ TASK-006 (Repository implementation)

TASK-009 ──→ TASK-010 (Schemas)
TASK-008 + TASK-010 ──→ TASK-011 (Company router endpoints)
TASK-008 + TASK-010 ──→ TASK-012 (My settings router endpoint)

TASK-008 ──→ TASK-014 (Unit tests - UpdateCompanySlugCommand)
TASK-009 ──→ TASK-015 (Unit tests - GetCompanyBySlugQuery)
TASK-011 + TASK-012 ──→ TASK-016 (Integration tests)

TASK-011 ──→ TASK-017 (LoginPage + route)
TASK-012 ──→ TASK-018 (CompanySettingsPage slug field)
TASK-017 + TASK-018 ──→ TASK-019 (i18n keys)
```

## Execution Order

**Batch 1 (Parallel):** TASK-001 (AuthMode enum)
**Batch 2 (Parallel):** TASK-002 (Company entity), TASK-004 (CompanyModel)
**Batch 3 (Parallel):** TASK-003 (Repository interface), TASK-005 (Migration), TASK-013 (Unit tests - domain)
**Batch 4:** TASK-006 (Repository implementation)
**Batch 5 (Parallel):** TASK-007 (CreateCompanyCommand), TASK-008 (UpdateCompanySlugCommand), TASK-009 (GetCompanyBySlugQuery)
**Batch 6 (Parallel):** TASK-010 (Schemas), TASK-014 (Unit tests - update slug cmd), TASK-015 (Unit tests - get by slug query)
**Batch 7 (Parallel):** TASK-011 (Company router), TASK-012 (My settings router)
**Batch 8:** TASK-016 (Integration tests)
**Batch 9 (Parallel):** TASK-017 (LoginPage), TASK-018 (CompanySettingsPage)
**Batch 10:** TASK-019 (i18n keys)

## Final Checklist

- [x] All 19 tasks completed
- [x] All unit tests passing (`make test`)
- [x] All integration tests passing (`make test-integration`)
- [x] mypy passes (`make lint`)
- [x] flake8 passes (`make lint`)
- [x] Migration runs cleanly (`make db-upgrade`)
- [x] Existing auth flows not regressed
- [x] Frontend compiles without errors
