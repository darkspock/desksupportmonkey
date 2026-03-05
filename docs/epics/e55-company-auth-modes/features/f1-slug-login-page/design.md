# Solution Design: F1 — Slug & Login Page

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-03
**Bounded Context:** `company_bc` (modify)

## Summary

Add `slug` and `auth_mode` fields to the existing `Company` entity. Auto-generate slugs on company creation, migrate existing companies with auto-generated slugs, expose a public slug-resolve endpoint, a slug-update endpoint for admins, and build a frontend login page at `/login/:slug` that fetches company info and displays the appropriate auth methods. The existing unscoped auth endpoints remain the only functioning auth path — this feature does NOT change any auth flow.

## Architecture Decision

**Approach:** Modify the existing `Company` entity, model, and repository rather than creating a new bounded context. The slug is a natural property of the Company aggregate. The `AuthMode` enum is a simple domain enum in `company_bc`.

**Why not a separate entity?** The slug is a direct attribute of Company (like `name` or `status`). Creating a separate entity would violate DDD cohesion — it has no independent lifecycle.

**Slug generation as a static utility:** The `generate_slug()` function is a pure utility (deterministic, stateless), best placed as a static method on the Company entity. Collision resolution requires a repository call, so it happens in the command handler.

**Login page approach:** The frontend `/login/:slug` page fetches company info via a public GET endpoint, then renders the existing auth form with the company name displayed. Auth still goes through the existing unscoped endpoints (`/api/v1/auth/magic-link`, etc.). Slug-scoped auth endpoints come in F2.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| Company entity | `src/company_bc/company/domain/entities.py` | Yes | Add `slug`, `auth_mode` fields + `generate_slug()`, `validate_slug()`, `update_slug()` methods |
| Company enums | `src/company_bc/company/domain/enums.py` | Yes | Add `AuthMode` enum |
| CompanyModel | `src/company_bc/company/infrastructure/models.py` | Yes | Add `slug`, `auth_mode` columns |
| CompanyRepository | `src/company_bc/company/infrastructure/repository.py` | Yes | Add `find_by_slug()`, `slug_exists()`; update `save()`, `_to_entity()` |
| CompanyRepositoryInterface | `src/company_bc/company/domain/repository.py` | Yes | Add `find_by_slug()`, `slug_exists()` abstract methods |
| CreateCompanyCommand | `src/company_bc/company/application/commands/create_company.py` | Yes | Auto-generate slug on creation with collision resolution |
| Company schemas | `adapters/http/api/companies/schemas.py` | Yes | Add `slug`, `auth_mode` to `CompanyResponse` |
| Company router | `adapters/http/api/companies/routers.py` | Yes | Add slug-resolve and slug-update endpoints |
| My company settings schema | `adapters/http/api/my/schemas.py` | Yes | Add `slug`, `auth_mode` to `MyCompanySettingsResponse` |
| My company settings router | `adapters/http/api/my/routers.py` | Yes | Add slug update for admin, return slug in settings |
| OAuthSettings | `core/config.py` | Yes (read-only) | Used by slug-resolve endpoint to return provider availability |
| LoginPage.tsx | `web/app/src/pages/auth/LoginPage.tsx` | Yes | Refactor for slug awareness |
| Router | `web/app/src/router.tsx` | Yes | Add `/login/:slug` route |
| CompanySettingsPage.tsx | `web/app/src/pages/admin/CompanySettingsPage.tsx` | Yes | Add slug display/edit |

## Implementation Plan

### 1. Domain Layer

#### Entities (modified)

| Entity | File Path | Description |
|--------|-----------|-------------|
| Company | `src/company_bc/company/domain/entities.py` | Add `slug: Optional[str]`, `auth_mode: AuthMode` fields. Add `generate_slug(name)` static method, `validate_slug(slug)` static method, `update_slug(slug)` method. |

**Company entity changes:**

```python
# New imports
import re
import unicodedata
from src.company_bc.company.domain.enums import AuthMode

# New fields on @dataclass Company:
slug: Optional[str] = None
auth_mode: AuthMode = AuthMode.DOMAIN

# New static method:
@staticmethod
def generate_slug(name: str) -> str:
    """Generate URL-safe slug from company name. Lowercase alphanumeric + hyphens."""
    # Transliterate unicode to ASCII
    normalized = unicodedata.normalize('NFKD', name)
    ascii_name = normalized.encode('ascii', 'ignore').decode('ascii')
    # Lowercase, replace non-alphanumeric with hyphens, collapse multiple hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', ascii_name.lower()).strip('-')
    # Enforce minimum length
    if len(slug) < 3:
        slug = slug + '-co'
    # Enforce maximum length
    return slug[:50]

RESERVED_SLUGS = frozenset({
    'admin', 'api', 'login', 'register', 'reseller', 'app', 'auth', 'super-admin',
})

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

def update_slug(self, slug: str) -> None:
    """Update the company slug after validation."""
    Company.validate_slug(slug)
    self.slug = slug
```

**Company.create() changes:**
- Add `slug: Optional[str] = None` parameter
- If slug provided, validate and assign
- If not provided, generate from name (the handler will handle collision)

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| AuthMode | `src/company_bc/company/domain/enums.py` | `domain`, `membership_only` |

```python
class AuthMode(str, Enum):
    """Authentication mode for a company."""
    DOMAIN = "domain"
    MEMBERSHIP_ONLY = "membership_only"
```

#### Domain Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| InvalidSlugError | `src/company_bc/company/domain/entities.py` | Raised when slug format is invalid (keep with entity like existing exceptions) |
| SlugAlreadyTakenError | `src/company_bc/company/domain/entities.py` | Raised when slug is already used by another company |

```python
class InvalidSlugError(Exception):
    pass

class SlugAlreadyTakenError(Exception):
    def __init__(self, slug: str):
        self.slug = slug
        super().__init__(f"Slug '{slug}' is already taken")
```

### 2. Application Layer

#### Commands

| Command | Handler | File | Description |
|---------|---------|------|-------------|
| UpdateCompanySlugCommand | UpdateCompanySlugCommandHandler | `src/company_bc/company/application/commands/update_company_slug.py` | Admin updates their company's slug |

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
        Company.validate_slug(command.slug)  # raises ValueError
        if self.company_repo.slug_exists(command.slug, exclude_company_id=command.company_id):
            raise SlugAlreadyTakenError(command.slug)
        company.update_slug(command.slug)
        self.company_repo.save(company)
```

#### Queries

| Query | Handler | File | Description |
|-------|---------|------|-------------|
| GetCompanyBySlugQuery | GetCompanyBySlugQueryHandler | `src/company_bc/company/application/queries/get_company_by_slug.py` | Public: resolve slug to company info |

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

**CompanyNotFoundError** — reuse from `get_company.py` if it exists, or create in the query file.

#### Modified Commands

| Command | File | Change |
|---------|------|--------|
| CreateCompanyCommand | `src/company_bc/company/application/commands/create_company.py` | After `Company.create()`, generate slug with collision resolution: call `generate_slug(name)`, then check `slug_exists()`, appending `-2`, `-3`, etc. until unique. Set `company.slug = resolved_slug`. |

### 3. Infrastructure Layer

#### Repository Interface (modified)

| Method | File | Description |
|--------|------|-------------|
| `find_by_slug(slug: str) -> Optional[Company]` | `src/company_bc/company/domain/repository.py` | Find active company by slug |
| `slug_exists(slug: str, exclude_company_id: Optional[str] = None) -> bool` | `src/company_bc/company/domain/repository.py` | Check if slug is taken (exclude own ID for updates) |

#### Repository Implementation (modified)

| Method | File | Description |
|--------|------|-------------|
| `find_by_slug` | `src/company_bc/company/infrastructure/repository.py` | `SELECT ... WHERE slug = :slug` |
| `slug_exists` | `src/company_bc/company/infrastructure/repository.py` | `SELECT EXISTS(SELECT 1 FROM companies WHERE slug = :slug AND id != :exclude_id)` |
| `save` | `src/company_bc/company/infrastructure/repository.py` | Add `slug` and `auth_mode` to both insert and update paths |
| `_to_entity` | `src/company_bc/company/infrastructure/repository.py` | Add `slug=model.slug, auth_mode=AuthMode(model.auth_mode)` |

#### Model (modified)

| Column | File | Description |
|--------|------|-------------|
| `slug` | `src/company_bc/company/infrastructure/models.py` | `Mapped[str] = mapped_column(String(50), unique=True, index=True)` |
| `auth_mode` | `src/company_bc/company/infrastructure/models.py` | `Mapped[str] = mapped_column(String(20), nullable=False, server_default="domain")` |

#### Migration

| Migration | Description |
|-----------|-------------|
| `f1a2b3c4d5e6_add_company_slug_and_auth_mode.py` | 1) Add `slug` column (nullable). 2) Auto-generate slugs for all existing companies (data migration with collision handling). 3) Set `slug` to NOT NULL. 4) Add unique index on `slug`. 5) Add `auth_mode` column (default `domain`). |

**Migration chain:** down_revision = `e9f0g1h2i3j4` (latest from E54 F5)

**Slug generation in migration:**
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
```

### 4. HTTP Layer

#### Endpoints

| Method | Route | Auth | Schema In | Schema Out | Description |
|--------|-------|------|-----------|------------|-------------|
| GET | `/api/v1/companies/by-slug/{slug}` | Public (no auth) | Path param `slug` | `CompanyBySlugResponse` | Resolve slug to company info for login page |
| PATCH | `/api/v1/my/company-settings/slug` | ADMIN | `UpdateSlugRequest` | `MyCompanySettingsResponse` | Admin updates own company slug |
| PATCH | `/api/v1/companies/{company_id}/slug` | SUPER_ADMIN | `UpdateSlugRequest` | `CompanyDetailResponse` | Super admin updates any company slug |

#### Schemas (new)

| Schema | File | Fields |
|--------|------|--------|
| `CompanyBySlugResponse` | `adapters/http/api/companies/schemas.py` | `id`, `name`, `slug`, `auth_mode`, `google_enabled`, `microsoft_enabled` |
| `UpdateSlugRequest` | `adapters/http/api/companies/schemas.py` | `slug: str` (3-50 chars, pattern validated) |

#### Schemas (modified)

| Schema | File | Change |
|--------|------|--------|
| `CompanyResponse` | `adapters/http/api/companies/schemas.py` | Add `slug: str`, `auth_mode: str` |
| `CompanyDetailResponse` | `adapters/http/api/companies/schemas.py` | Inherits from CompanyResponse, gets slug/auth_mode automatically |
| `MyCompanySettingsResponse` | `adapters/http/api/my/schemas.py` | Add `slug: str`, `auth_mode: str` |

#### Routers (modified)

| File | Change |
|------|--------|
| `adapters/http/api/companies/routers.py` | Add `GET /by-slug/{slug}` (public, no auth) and `PATCH /{company_id}/slug` (super_admin). Catch `SlugAlreadyTakenError` → 409, `ValueError` (slug validation) → 422, `CompanyNotFoundError` → 404. |
| `adapters/http/api/my/routers.py` | Add `PATCH /company-settings/slug` (admin). Include `slug` and `auth_mode` in `_to_company_settings()`. Catch `SlugAlreadyTakenError` → 409, `ValueError` → 422. |

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `src/company_bc/company/domain/entities.py` | Modify | Add `slug`, `auth_mode` fields, `generate_slug()`, `validate_slug()`, `update_slug()`, exceptions |
| `src/company_bc/company/domain/enums.py` | Modify | Add `AuthMode` enum |
| `src/company_bc/company/domain/repository.py` | Modify | Add `find_by_slug()`, `slug_exists()` abstract methods |
| `src/company_bc/company/infrastructure/models.py` | Modify | Add `slug`, `auth_mode` columns |
| `src/company_bc/company/infrastructure/repository.py` | Modify | Add `find_by_slug()`, `slug_exists()`; update `save()`, `_to_entity()` |
| `src/company_bc/company/application/commands/create_company.py` | Modify | Auto-generate slug with collision resolution |
| `adapters/http/api/companies/schemas.py` | Modify | Add `CompanyBySlugResponse`, `UpdateSlugRequest`; add slug/auth_mode to existing responses |
| `adapters/http/api/companies/routers.py` | Modify | Add 2 new endpoints |
| `adapters/http/api/my/schemas.py` | Modify | Add slug/auth_mode to `MyCompanySettingsResponse` |
| `adapters/http/api/my/routers.py` | Modify | Add slug update endpoint; include slug/auth_mode in settings response |
| `web/app/src/router.tsx` | Modify | Add `/login/:slug` route |
| `web/app/src/pages/auth/LoginPage.tsx` | Modify | Add slug awareness: fetch company by slug, display name, show auth methods |
| `web/app/src/pages/admin/CompanySettingsPage.tsx` | Modify | Add slug field (editable) |
| `web/app/src/locales/en.ts` | Modify | Add i18n keys for slug-related UI |
| `web/app/src/locales/es.ts` | Modify | Add Spanish translations |

#### New Files

| File | Description |
|------|-------------|
| `src/company_bc/company/application/commands/update_company_slug.py` | UpdateCompanySlugCommand + Handler |
| `src/company_bc/company/application/queries/get_company_by_slug.py` | GetCompanyBySlugQuery + Handler + DTO |
| `alembic/versions/f1a2b3c4d5e6_add_company_slug_and_auth_mode.py` | Migration |

#### Breaking Changes

None. All changes are additive. Existing endpoints continue to work unchanged. The slug field is auto-generated for existing companies in the migration. The `auth_mode` column defaults to `domain` (current behavior).

## Database Schema

```sql
-- Modified table: companies (add columns)
ALTER TABLE companies ADD COLUMN slug VARCHAR(50);
-- ... data migration to populate slugs ...
ALTER TABLE companies ALTER COLUMN slug SET NOT NULL;
ALTER TABLE companies ADD CONSTRAINT uq_companies_slug UNIQUE (slug);
CREATE INDEX ix_companies_slug ON companies (slug);

ALTER TABLE companies ADD COLUMN auth_mode VARCHAR(20) NOT NULL DEFAULT 'domain';
```

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| `OAuthSettings` | Read-only | Used by GetCompanyBySlugQuery to return provider availability |
| `CompanyRepository` | Modified | Add `find_by_slug()`, `slug_exists()` |

## Testing Strategy

| Test Type | Scope | File | Priority |
|-----------|-------|------|----------|
| Unit | Slug generation (Company.generate_slug) | `tests/unit/company_bc/company/domain/test_company_slug.py` | High |
| Unit | Slug validation (Company.validate_slug) | Same file | High |
| Unit | Reserved slugs rejected | Same file | High |
| Unit | UpdateCompanySlugCommand handler | `tests/unit/company_bc/company/application/test_update_company_slug.py` | High |
| Unit | GetCompanyBySlugQuery handler | `tests/unit/company_bc/company/application/test_get_company_by_slug.py` | Medium |
| Integration | Slug resolve endpoint | `tests/integration/test_company_slug_endpoints.py` | High |
| Integration | Slug update endpoint (admin + super admin) | Same file | High |
| Integration | Create company auto-generates slug | Same file | Medium |
| Integration | Slug collision handling | Same file | Medium |

## Implementation Order

1. Domain: Add `AuthMode` enum to `enums.py`
2. Domain: Add `slug`, `auth_mode` fields + exceptions + slug methods to `entities.py`
3. Infrastructure: Add columns to `CompanyModel`
4. Infrastructure: Add `find_by_slug()`, `slug_exists()` to repository interface + implementation
5. Infrastructure: Update `save()` and `_to_entity()` in repository
6. Infrastructure: Create Alembic migration (with data migration)
7. Application: Modify `CreateCompanyCommand` handler for auto-slug generation
8. Application: Create `UpdateCompanySlugCommand` + handler
9. Application: Create `GetCompanyBySlugQuery` + handler + DTO
10. HTTP: Add schemas (`CompanyBySlugResponse`, `UpdateSlugRequest`)
11. HTTP: Modify existing schemas to include slug/auth_mode
12. HTTP: Add endpoints to company router and my-settings router
13. Tests: Unit tests for slug generation, validation, commands, queries
14. Tests: Integration tests for endpoints
15. Frontend: Add `/login/:slug` route and refactor LoginPage
16. Frontend: Add slug field to CompanySettingsPage
17. Frontend: Add i18n keys (en + es)

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Slug collisions during migration | Low | Low | Collision handling with `-2`, `-3` suffixes. Deterministic and idempotent. |
| Unicode company names produce empty slugs | Low | Medium | `generate_slug()` handles unicode via NFKD normalization + ASCII fallback. If result < 3 chars, append `-co`. |
| Existing tests break from new required slug field | Medium | Low | Slug defaults to `None` on entity. Migration ensures all DB rows have slugs. Test fixtures may need update. |
| Login page regressions | Low | High | Existing auth flow is unchanged. `/login/:slug` is additive. Old `/auth/login` route stays. |
