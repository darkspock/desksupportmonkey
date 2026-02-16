# Tasks: F0 - Company CRUD + Email Domains

**Feature:** [requirements.md](requirements.md)
**Design:** [design.md](design.md)
**Date:** 2026-02-15

---

## Phase 1: Domain Layer

### T1.1: Create CompanyStatus enum ✅
- **File:** `src/company_bc/company/domain/enums.py` (NEW)
- Create `CompanyStatus(str, Enum)` with values: `ACTIVE = "active"`, `SUSPENDED = "suspended"`, `DEACTIVATED = "deactivated"`
- No transition logic yet (that's F1)

### T1.2: Create Company entity ✅
- **File:** `src/company_bc/company/domain/entities.py` (NEW)
- Dataclass: `id`, `name`, `status` (CompanyStatus), `email_domains` (list[str]), `is_active` (bool), `created_at`, `updated_at`
- `create()` class method: validates name not empty, domains not empty, normalizes domains to lowercase, generates ULID, sets status=ACTIVE, is_active=True
- `update()` method: updates name and/or domains with validation

### T1.3: Create CompanyRepositoryInterface ✅
- **File:** `src/company_bc/company/domain/repository.py` (NEW)
- ABC with methods:
  - `save(company) -> Company`
  - `find_by_id(company_id) -> Optional[Company]`
  - `find_by_name(name) -> Optional[Company]`
  - `find_all(page, page_size, search) -> tuple[list[Company], int]`
  - `find_domain(domain) -> Optional[str]` (returns company_id or None)
  - `save_domains(company_id, domains) -> None`
  - `count_users(company_id) -> int`
  - `count_departments(company_id) -> int`

### T1.4: Create `__init__.py` files for new packages ✅
- Ensure `src/company_bc/company/domain/__init__.py`, `src/company_bc/company/application/__init__.py`, etc. exist

---

## Phase 2: Infrastructure Layer

### T2.1: Extend CompanyModel with status column ✅
- **File:** `src/company_bc/company/infrastructure/models.py` (MODIFY)
- Add `status = Column(String(20), nullable=False, server_default="active")`
- Add relationship to CompanyEmailDomainModel

### T2.2: Create CompanyEmailDomainModel ✅
- **File:** `src/company_bc/company/infrastructure/models.py` (MODIFY - same file)
- `CompanyEmailDomainModel(ULIDMixin, Base)`:
  - `__tablename__ = "company_email_domains"`
  - `company_id`: String(26), FK to companies.id, NOT NULL, indexed
  - `domain`: String(255), UNIQUE, NOT NULL, indexed
  - `created_at`: DateTime, server_default=func.now()

### T2.3: Update models_registry.py ✅
- **File:** `core/models_registry.py` (MODIFY)
- Add import for `CompanyEmailDomainModel`

### T2.4: Create Alembic migration ✅
- Run `alembic revision --autogenerate -m "add_company_status_and_email_domains"`
- Verify: adds `status` to companies, creates `company_email_domains` table, adds indexes
- Test upgrade + downgrade

### T2.5: Implement CompanyRepository ✅
- **File:** `src/company_bc/company/infrastructure/repository.py` (NEW)
- Implements CompanyRepositoryInterface
- `save()`: upsert (check exists by id, update or insert)
- `find_by_id()`: query CompanyModel + join domains
- `find_by_name()`: case-insensitive match using `.ilike()`
- `find_all()`: pagination with offset/limit, optional search on name
- `find_domain()`: query CompanyEmailDomainModel, return company_id
- `save_domains()`: delete existing domains for company, insert new ones
- `count_users()`: COUNT from users where company_id matches
- `count_departments()`: COUNT from departments where company_id matches and is_active (return 0 if table doesn't exist yet, or use try/except)
- `_to_entity()`: static method to convert model(s) to Company entity

### T2.6: Replace CompanyLookupService stub ✅
- **File:** `src/auth_bc/company_lookup/infrastructure/service.py` (MODIFY)
- Replace `query(CompanyModel).filter(is_active).first()` with:
  - Query `CompanyEmailDomainModel` joined with `CompanyModel`
  - Filter by domain match AND `CompanyModel.is_active == True`
  - Return company_id or None

---

## Phase 3: Application Layer

### T3.1: CreateCompanyCommand + Handler ✅
- **File:** `src/company_bc/company/application/commands/create_company.py` (NEW)
- Command: `name`, `email_domains`, `admin_email` (optional)
- Handler dependencies: `CompanyRepositoryInterface`, `UserRepositoryInterface`, `MagicLinkRepositoryInterface`, `EmailServiceInterface`
- Logic:
  1. Check name uniqueness → raise `CompanyNameExistsError`
  2. Check each domain uniqueness → raise `DomainAlreadyTakenError(domain)`
  3. Create Company entity via `Company.create()`
  4. Save company
  5. Save domains
  6. If admin_email:
     a. Check user doesn't exist → raise `UserAlreadyExistsError`
     b. Create User entity (admin role, company_id)
     c. Save user
     d. Create MagicLink, send email
  7. Return company
- Define error classes: `CompanyNameExistsError`, `DomainAlreadyTakenError`, `UserAlreadyExistsError`

### T3.2: UpdateCompanyCommand + Handler ✅
- **File:** `src/company_bc/company/application/commands/update_company.py` (NEW)
- Command: `company_id`, `name` (optional), `email_domains` (optional)
- Handler dependencies: `CompanyRepositoryInterface`
- Logic:
  1. Find company → raise `CompanyNotFoundError`
  2. If name: check uniqueness (exclude self) → raise `CompanyNameExistsError`
  3. If domains: check each uniqueness (exclude company's own domains) → raise `DomainAlreadyTakenError`
  4. Update entity
  5. Save company + domains
  6. Return company

### T3.3: ListCompaniesQuery + Handler ✅
- **File:** `src/company_bc/company/application/queries/list_companies.py` (NEW)
- Query: `page`, `page_size`, `search`
- Handler: calls `company_repo.find_all(page, page_size, search)`
- Returns (companies, total)

### T3.4: GetCompanyQuery + Handler ✅
- **File:** `src/company_bc/company/application/queries/get_company.py` (NEW)
- Query: `company_id`
- Handler: calls `company_repo.find_by_id()`, `count_users()`, `count_departments()`
- Returns company + counts
- Raises `CompanyNotFoundError` if not found

---

## Phase 4: HTTP Layer

### T4.1: Create company schemas ✅
- **File:** `adapters/http/api/companies/schemas.py` (NEW)
- `CreateCompanyRequest`: name (str, min 1, max 255), email_domains (list[str], min 1), admin_email (Optional[EmailStr])
- `UpdateCompanyRequest`: name (Optional[str]), email_domains (Optional[list[str]])
- `CompanyResponse`: id, name, status, email_domains, is_active, created_at, updated_at
- `CompanyDetailResponse(CompanyResponse)`: + user_count, department_count
- `CompanyListParams`: page (int, default 1), page_size (int, default 20), search (Optional[str])

### T4.2: Create company router ✅
- **File:** `adapters/http/api/companies/routers.py` (NEW)
- `POST /api/v1/companies` → create_company
  - Depends: `require_role(UserRole.SUPER_ADMIN)`, `get_db`
  - Instantiates handler with repos + email service
  - Maps domain errors to HTTP errors (409, etc.)
  - Returns `SuccessResponse[CompanyResponse]`
- `GET /api/v1/companies` → list_companies
  - Depends: `require_role(UserRole.SUPER_ADMIN)`, `get_db`
  - Query params: page, page_size, search
  - Returns `ListResponse[CompanyResponse]`
- `GET /api/v1/companies/{id}` → get_company
  - Depends: `require_role(UserRole.SUPER_ADMIN)`, `get_db`
  - Returns `SuccessResponse[CompanyDetailResponse]`
- `PUT /api/v1/companies/{id}` → update_company
  - Depends: `require_role(UserRole.SUPER_ADMIN)`, `get_db`
  - Returns `SuccessResponse[CompanyResponse]`

### T4.3: Create `__init__.py` for adapters/http/api/companies/ ✅

### T4.4: Register company router in app.py ✅
- **File:** `app.py` (MODIFY)
- Add `from adapters.http.api.companies.routers import router as companies_router`
- Add `app.include_router(companies_router)`

---

## Phase 5: Tests

### T5.1: Unit tests - Company entity ✅
- **File:** `tests/unit/company_bc/company/domain/test_entities.py` (NEW)
- Test create with valid data
- Test create with empty name → ValueError
- Test create with no domains → ValueError
- Test create normalizes domains to lowercase
- Test update name
- Test update domains

### T5.2: Unit tests - CreateCompanyCommand ✅
- **File:** `tests/unit/company_bc/company/application/commands/test_create_company.py` (NEW)
- Test successful creation (no admin)
- Test successful creation with admin_email
- Test duplicate name → CompanyNameExistsError
- Test duplicate domain → DomainAlreadyTakenError
- Test admin_email user exists → UserAlreadyExistsError

### T5.3: Unit tests - UpdateCompanyCommand ✅
- **File:** `tests/unit/company_bc/company/application/commands/test_update_company.py` (NEW)
- Test successful update (name only)
- Test successful update (domains only)
- Test company not found → CompanyNotFoundError
- Test duplicate name on update → CompanyNameExistsError
- Test duplicate domain on update → DomainAlreadyTakenError

### T5.4: Unit tests - Queries ✅
- **File:** `tests/unit/company_bc/company/application/queries/test_queries.py` (NEW)
- Test list companies returns paginated results
- Test get company returns detail with counts
- Test get company not found → CompanyNotFoundError

### T5.5: Unit tests - CompanyLookupService (updated) ✅
- **File:** `tests/unit/auth_bc/company_lookup/test_service.py` (NEW)
- Test domain match with active company → returns company_id
- Test domain match with inactive company → returns None
- Test domain not found → returns None

---

## Phase 6: Verification

### T6.1: Run all tests ✅
- `make test` — all tests pass (existing + new)

### T6.2: Run migration ✅
- `alembic upgrade head` — new migration applies
- `alembic downgrade -1` then `alembic upgrade head` — reversible

### T6.3: Manual API verification ✅
- Create company: `POST /api/v1/companies` with JWT
- List companies: `GET /api/v1/companies`
- Get company: `GET /api/v1/companies/{id}`
- Update company: `PUT /api/v1/companies/{id}`
- Test magic link with new domain matching
- Test error cases (duplicate name, duplicate domain, non-super-admin)

---

## Task Summary

| Phase | Tasks | New Files | Modified Files |
|---|---|---|---|
| 1. Domain | T1.1-T1.4 | 3 new + inits | — |
| 2. Infrastructure | T2.1-T2.6 | 1 new (repo) | 3 modified (models, registry, lookup) + migration |
| 3. Application | T3.1-T3.4 | 4 new | — |
| 4. HTTP | T4.1-T4.4 | 2 new + init | 1 modified (app.py) |
| 5. Tests | T5.1-T5.5 | 5 new | — |
| 6. Verification | T6.1-T6.3 | — | — |
