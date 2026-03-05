# Implementation Tasks: Account Creation (F2)

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-03
**Total Tasks:** 22
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | S |
| Domain - Interfaces | 1 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Collateral - Seed Data Refactor | 1 | L |
| Application - DTOs | 1 | S |
| Application - Commands | 2 | M-L |
| Application - Queries | 1 | M |
| Collateral - Dashboard Update | 1 | S |
| Application - Celery Task | 1 | M |
| Collateral - Celery Beat Config | 1 | S |
| HTTP - Schemas | 1 | S |
| HTTP - Mappers | 1 | S |
| HTTP - Reseller Endpoints | 1 | M |
| HTTP - Admin Endpoint | 1 | S |
| Tests - Unit | 1 | L |
| Tests - Integration | 1 | L |
| Configuration - __init__.py | 1 | S |
| Frontend (separate task) | 1 | — |

---

## Phase 1: Domain Layer

### TASK-001: Create ClientSource Enum

**Phase:** Domain - Enums
**Complexity:** S
**Dependencies:** None

**File:** `src/reseller_bc/client/domain/enums.py`

**Implementation:**
```python
from enum import Enum

class ClientSource(str, Enum):
    MANUAL = "manual"
    REFERRAL = "referral"
```

**Acceptance Criteria:**
- [ ] Enum inherits from `str, Enum`
- [ ] Values: `manual`, `referral`

---

### TASK-002: Create Domain Exceptions

**Phase:** Domain - Exceptions
**Complexity:** S
**Dependencies:** None

**File:** `src/reseller_bc/client/domain/exceptions.py`

**Implementation:**
```python
class CompanyAlreadyLinkedToResellerException(Exception):
    def __init__(self, company_id: str):
        self.company_id = company_id
        super().__init__(f"Company {company_id} is already linked to a reseller")

class DemoAccountLimitExceededException(Exception):
    def __init__(self, reseller_id: str, limit: int = 5):
        self.reseller_id = reseller_id
        super().__init__(f"Reseller {reseller_id} has reached the maximum of {limit} active demo accounts")
```

**Acceptance Criteria:**
- [ ] `CompanyAlreadyLinkedToResellerException` with `company_id` attribute
- [ ] `DemoAccountLimitExceededException` with `reseller_id` and `limit` attributes

---

### TASK-003: Create ResellerClient Entity

**Phase:** Domain - Entities
**Complexity:** S
**Dependencies:** TASK-001

**File:** `src/reseller_bc/client/domain/entities.py`

**Implementation:**
```python
@dataclass
class ResellerClient:
    id: str
    reseller_id: str
    company_id: str
    source: ClientSource
    is_demo: bool
    demo_expires_at: Optional[datetime]
    created_at: Optional[datetime]

    @classmethod
    def create(
        cls,
        reseller_id: str,
        company_id: str,
        source: ClientSource,
        is_demo: bool = False,
        id: Optional[str] = None,
    ) -> "ResellerClient":
        now = datetime.utcnow()
        return cls(
            id=id or str(ulid.new()),
            reseller_id=reseller_id,
            company_id=company_id,
            source=source,
            is_demo=is_demo,
            demo_expires_at=now + timedelta(days=14) if is_demo else None,
            created_at=now,
        )
```

**Acceptance Criteria:**
- [ ] Dataclass with all fields from design
- [ ] `create()` factory method
- [ ] `demo_expires_at` auto-calculated as `created_at + 14 days` when `is_demo=True`
- [ ] `demo_expires_at` is `None` when `is_demo=False`
- [ ] ULID auto-generated when `id` not provided

---

### TASK-004: Create ResellerClientRepositoryInterface

**Phase:** Domain - Interfaces
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/reseller_bc/client/domain/repository.py`

**Implementation:**
```python
class ResellerClientRepositoryInterface(ABC):
    @abstractmethod
    def save(self, client: ResellerClient) -> None: ...

    @abstractmethod
    def get_by_id(self, client_id: str) -> Optional[ResellerClient]: ...

    @abstractmethod
    def find_by_company_id(self, company_id: str) -> Optional[ResellerClient]: ...

    @abstractmethod
    def find_by_reseller_id(self, reseller_id: str, offset: int = 0, limit: int = 50) -> list[ResellerClient]: ...

    @abstractmethod
    def count_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def count_active_demos_by_reseller_id(self, reseller_id: str) -> int: ...

    @abstractmethod
    def find_expired_demos(self, before: datetime) -> list[ResellerClient]: ...

    @abstractmethod
    def find_purgeable_demos(self, before: datetime) -> list[ResellerClient]: ...
```

**Acceptance Criteria:**
- [ ] ABC with all 8 abstract methods exactly as in design
- [ ] Uses domain entity `ResellerClient` in signatures
- [ ] `find_expired_demos` and `find_purgeable_demos` accept `datetime` parameter

---

## Phase 2: Infrastructure Layer

### TASK-005: Create Alembic Migration for `reseller_clients` Table

**Phase:** Infrastructure - Migrations
**Complexity:** S
**Dependencies:** TASK-003

**File:** `alembic/versions/XXX_add_reseller_clients_table.py`

**Schema:**
```sql
CREATE TABLE reseller_clients (
    id VARCHAR(26) PRIMARY KEY,
    reseller_id VARCHAR(26) NOT NULL REFERENCES resellers(id),
    company_id VARCHAR(26) NOT NULL UNIQUE REFERENCES companies(id),
    source VARCHAR(20) NOT NULL,
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    demo_expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_reseller_clients_reseller_id ON reseller_clients(reseller_id);
CREATE INDEX ix_reseller_clients_demo_expires ON reseller_clients(demo_expires_at) WHERE is_demo = TRUE;
```

**Acceptance Criteria:**
- [ ] All columns from design
- [ ] `company_id` has UNIQUE constraint (one reseller per company)
- [ ] Foreign keys to `resellers(id)` and `companies(id)`
- [ ] Index on `reseller_id`
- [ ] Partial index on `demo_expires_at` where `is_demo = TRUE`
- [ ] Reversible (`downgrade` drops table)

---

### TASK-006: Create ResellerClientModel

**Phase:** Infrastructure - Models
**Complexity:** S
**Dependencies:** TASK-005

**File:** `src/reseller_bc/client/infrastructure/models.py`

**Implementation:**
```python
class ResellerClientModel(ULIDMixin, Base):
    __tablename__ = "reseller_clients"

    reseller_id: Mapped[str] = mapped_column(String(26), ForeignKey("resellers.id"), nullable=False, index=True)
    company_id: Mapped[str] = mapped_column(String(26), ForeignKey("companies.id"), nullable=False, unique=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    demo_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
```

**Acceptance Criteria:**
- [ ] Inherits `ULIDMixin`, `Base`
- [ ] SQLAlchemy 2.0 style (`Mapped[type]` + `mapped_column()`)
- [ ] All columns mapped from design
- [ ] `company_id` unique constraint
- [ ] `reseller_id` indexed

---

### TASK-007: Create ResellerClientRepository Implementation

**Phase:** Infrastructure - Repositories
**Complexity:** M
**Dependencies:** TASK-004, TASK-006

**File:** `src/reseller_bc/client/infrastructure/repository.py`

**Implementation:** Follow `ResellerRepository` pattern (SQLAlchemy 2.0 style, session-based).

Implement all 8 methods from `ResellerClientRepositoryInterface`:
- `save()` — insert or update (merge pattern)
- `get_by_id()` — single lookup by id
- `find_by_company_id()` — single lookup by company_id
- `find_by_reseller_id()` — paginated list with offset/limit
- `count_by_reseller_id()` — total count for a reseller
- `count_active_demos_by_reseller_id()` — count where `is_demo=True AND demo_expires_at > now()`
- `find_expired_demos(before)` — join with CompanyModel, filter `is_demo=True AND demo_expires_at <= before AND company.status = 'active'`
- `find_purgeable_demos(before)` — join with CompanyModel, filter `is_demo=True AND demo_expires_at <= before AND company.status = 'suspended'`

Include `_to_entity()` static method for model → entity conversion.

**Acceptance Criteria:**
- [ ] Implements `ResellerClientRepositoryInterface`
- [ ] All 8 methods implemented
- [ ] `_to_entity()` static method
- [ ] Uses `select()` with SQLAlchemy 2.0 API
- [ ] `find_expired_demos` and `find_purgeable_demos` join with `CompanyModel` for status filtering

---

## Phase 3: Collateral — Seed Data Refactor

### TASK-008: Refactor Seed Script to Extract `seed_company_data()`

**Phase:** Collateral
**Complexity:** L
**Dependencies:** None (independent of domain layer)

**File:** `scripts/seed_demo_data.py`

**Changes:**
1. Extract per-company seeding functions:
   - `seed_departments_for_company(session, company_id) -> dict`
   - `seed_locations_for_company(session, company_id) -> dict`
   - `seed_users_for_company(session, company_id, company_name, dept_map) -> list`
   - `seed_asset_type_definitions_for_company(session, company_id)`
   - `seed_assets_for_company(session, company_id, users, loc_map)`
   - `seed_workflow_templates_for_company(session, company_id)`
   - `seed_requests_for_company(session, company_id, users)`
   - `seed_custom_fields_for_company(session, company_id)`
   - `seed_reports_for_company(session, company_id, users)`

2. Create orchestrating function:
```python
def seed_company_data(session, company_id: str, company_name: str = "Demo Company") -> dict:
    """Seed demo data for a single existing company. Returns metadata."""
    dept_map = seed_departments_for_company(session, company_id)
    loc_map = seed_locations_for_company(session, company_id)
    users = seed_users_for_company(session, company_id, company_name, dept_map)
    seed_asset_type_definitions_for_company(session, company_id)
    seed_assets_for_company(session, company_id, users, loc_map)
    seed_workflow_templates_for_company(session, company_id)
    seed_requests_for_company(session, company_id, users)
    seed_custom_fields_for_company(session, company_id)
    seed_reports_for_company(session, company_id, users)
    session.flush()
    return {"admin_user_id": users[0]["id"], "admin_email": users[0]["email"]}
```

3. Update `main()` to use `seed_company_data()` per company instead of old per-table approach.

4. Verify `make seed` still works identically.

**Acceptance Criteria:**
- [ ] `seed_company_data(session, company_id, company_name)` function exists and is callable
- [ ] `make seed` produces identical results as before
- [ ] Function returns `{"admin_user_id": ..., "admin_email": ...}`
- [ ] No user creation step happens outside `seed_company_data` (except company creation itself)
- [ ] Each per-company function accepts `company_id` parameter

---

## Phase 4: Application Layer

### TASK-009: Create Client DTOs

**Phase:** Application - DTOs
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/reseller_bc/client/application/dtos.py`

**Implementation:**
```python
@dataclass
class ResellerClientDto:
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    source: str
    is_demo: bool
    demo_expires_at: Optional[datetime]
    plan: str
    company_status: str
    created_at: Optional[datetime]

    @classmethod
    def from_entity_with_company(cls, client: ResellerClient, company_name: str, plan: str, company_status: str) -> "ResellerClientDto": ...

@dataclass
class ResellerClientListDto:
    items: list[ResellerClientDto]
    total: int

@dataclass
class DemoAccountCreatedDto:
    client_id: str
    company_id: str
    company_name: str
    admin_email: str
    admin_password: str
```

**Acceptance Criteria:**
- [ ] Three dataclasses exactly as in design
- [ ] `ResellerClientDto` has `from_entity_with_company()` class method
- [ ] `DemoAccountCreatedDto` includes `admin_password` field

---

### TASK-010: Create CreateDemoAccountCommand + Handler

**Phase:** Application - Commands
**Complexity:** L
**Dependencies:** TASK-004, TASK-007, TASK-008, TASK-009

**File:** `src/reseller_bc/client/application/commands/create_demo_account.py`

**Command:**
```python
@dataclass
class CreateDemoAccountCommand(Command):
    id: str
    reseller_id: str
    company_name: str
```

**Handler logic:**
1. Validate reseller exists and is ACTIVE (from `ResellerRepositoryInterface`)
2. Check active demo count < 5 via `count_active_demos_by_reseller_id()` — raise `DemoAccountLimitExceededException` if exceeded
3. Generate `company_id` with ULID
4. Create Company via `CreateCompanyCommandHandler` with:
   - `name` = `"{company_name} (Demo)"`
   - `email_domains` = `["demo-{ulid}.dsm.local"]` (synthetic domain)
   - `admin_email` = `None` (no magic link)
   - `id` = generated company_id
5. Create admin User directly with:
   - `email` = `"admin@demo-{ulid}.dsm.local"`
   - `password` = `secrets.token_urlsafe(12)` (hashed with bcrypt)
   - `role` = `ADMIN`
   - `company_id` = generated company_id
6. Call `seed_company_data(session, company_id, company_name)` from refactored seed script
7. Create `ResellerClient.create(reseller_id, company_id, ClientSource.MANUAL, is_demo=True)`
8. Save `ResellerClient` via repo
9. Store `DemoAccountCreatedDto` in `self._result` (for router to read)

**Dependencies (constructor):**
- `client_repo: ResellerClientRepositoryInterface`
- `reseller_repo: ResellerRepositoryInterface`
- `company_repo: CompanyRepositoryInterface`
- `user_repo: UserWriter`
- `session: Session` (for seed data function)
- Plus all deps of `CreateCompanyCommandHandler` (email_service, stripe_client, asset repos, etc.)

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command and handler in same file
- [ ] `handle()` returns `None`
- [ ] Validates reseller is ACTIVE — raise `ResellerNotFoundException` or `ResellerSuspendedException`
- [ ] Enforces 5-demo limit
- [ ] Creates company via `CreateCompanyCommandHandler`
- [ ] Creates admin user with random password
- [ ] Calls `seed_company_data()` for demo data population
- [ ] Creates `ResellerClient` with `is_demo=True`
- [ ] Stores `DemoAccountCreatedDto` in `self._result` for credentials retrieval

---

### TASK-011: Create CreateClientAccountCommand + Handler

**Phase:** Application - Commands
**Complexity:** M
**Dependencies:** TASK-004, TASK-007, TASK-009

**File:** `src/reseller_bc/client/application/commands/create_client_account.py`

**Command:**
```python
@dataclass
class CreateClientAccountCommand(Command):
    id: str
    reseller_id: str
    company_name: str
    admin_email: str
```

**Handler logic:**
1. Validate reseller exists and is ACTIVE
2. Derive email domain from `admin_email` (e.g., `"user@acme.com"` → `["acme.com"]`)
3. Create Company via `CreateCompanyCommandHandler` with:
   - `name` = `company_name`
   - `email_domains` = derived domains list
   - `admin_email` = `admin_email` (triggers magic link)
4. Create `ResellerClient.create(reseller_id, company_id, ClientSource.MANUAL, is_demo=False)`
5. Save `ResellerClient` via repo

**Dependencies (constructor):**
- `client_repo: ResellerClientRepositoryInterface`
- `reseller_repo: ResellerRepositoryInterface`
- All deps of `CreateCompanyCommandHandler`

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command and handler in same file
- [ ] `handle()` returns `None`
- [ ] Validates reseller is ACTIVE
- [ ] Derives email domain from admin email
- [ ] Creates company via `CreateCompanyCommandHandler` (admin receives magic link)
- [ ] Creates `ResellerClient` with `is_demo=False`, `source=MANUAL`
- [ ] Propagates `CompanyNameExistsError`, `DomainAlreadyTakenError`, `UserAlreadyExistsError` from company creation

---

### TASK-012: Create ListResellerClientsQuery + Handler

**Phase:** Application - Queries
**Complexity:** M
**Dependencies:** TASK-004, TASK-007, TASK-009

**File:** `src/reseller_bc/client/application/queries/list_reseller_clients.py`

**Query:**
```python
@dataclass
class ListResellerClientsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50
```

**Handler logic:**
1. `find_by_reseller_id(reseller_id, offset, limit)` → list of `ResellerClient`
2. `count_by_reseller_id(reseller_id)` → total count
3. Batch fetch companies by IDs from `CompanyRepositoryInterface` (avoid N+1)
4. Map each client + company to `ResellerClientDto.from_entity_with_company()`
5. Return `ResellerClientListDto(items, total)`

**Dependencies (constructor):**
- `client_repo: ResellerClientRepositoryInterface`
- `company_repo: CompanyRepositoryInterface`

**Acceptance Criteria:**
- [ ] Inherits from `Query` / `QueryHandler`
- [ ] Query and handler in same file
- [ ] Returns `ResellerClientListDto`
- [ ] Batch fetches companies (no N+1 queries)
- [ ] Supports pagination via offset/limit
- [ ] Maps to `ResellerClientDto` with company info (name, plan, status)

---

### TASK-013: Update GetResellerDashboardQueryHandler — Real `client_count`

**Phase:** Collateral - Dashboard Update
**Complexity:** S
**Dependencies:** TASK-007

**File:** `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py`

**Changes:**
1. Add `ResellerClientRepositoryInterface` as constructor dependency
2. Replace hardcoded `client_count=0` with `self.client_repo.count_by_reseller_id(query.reseller_id)`

**Also update:**
- The reseller router (`adapters/http/api/reseller/routers.py`) where the handler is instantiated — pass `ResellerClientRepository(db)` as the new dependency
- The admin router if it also uses the dashboard handler

**Acceptance Criteria:**
- [ ] `client_count` returns real count from `ResellerClientRepository`
- [ ] Handler constructor accepts `client_repo: ResellerClientRepositoryInterface`
- [ ] Routers updated to pass `client_repo` when instantiating handler

---

### TASK-014: Create Demo Expiry Celery Task

**Phase:** Application - Celery Task
**Complexity:** M
**Dependencies:** TASK-007

**File:** `core/tasks/reseller.py`

**Implementation:**
```python
@celery_app.task(name="core.tasks.reseller.expire_demo_accounts")
def expire_demo_accounts() -> dict:
    """Suspend demos expired >14 days, deactivate demos expired >44 days."""
    from core.database import SessionLocal

    session = SessionLocal()
    try:
        now = datetime.utcnow()

        client_repo = ResellerClientRepository(session)
        company_repo = CompanyRepository(session)

        # Phase 1: Suspend active demos past expiry
        expired = client_repo.find_expired_demos(before=now)
        suspended_count = 0
        for client in expired:
            company = company_repo.get_by_id(client.company_id)
            if company and company.status == CompanyStatus.ACTIVE:
                company.change_status(CompanyStatus.SUSPENDED)
                company_repo.save(company)
                suspended_count += 1

        # Phase 2: Deactivate suspended demos past purge window (30 days after suspension)
        purge_cutoff = now - timedelta(days=30)
        purgeable = client_repo.find_purgeable_demos(before=purge_cutoff)
        deactivated_count = 0
        for client in purgeable:
            company = company_repo.get_by_id(client.company_id)
            if company and company.status == CompanyStatus.SUSPENDED:
                company.change_status(CompanyStatus.DEACTIVATED)
                company.is_active = False
                company_repo.save(company)
                deactivated_count += 1

        session.commit()
        return {"suspended": suspended_count, "deactivated": deactivated_count}
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

**Acceptance Criteria:**
- [ ] Decorated with `@celery_app.task`
- [ ] Follows existing Celery task pattern (local imports, try/except/finally, session management)
- [ ] Phase 1: suspends demos where `demo_expires_at <= now` and company is ACTIVE
- [ ] Phase 2: deactivates demos where `demo_expires_at <= now - 30 days` and company is SUSPENDED
- [ ] Returns dict with counts
- [ ] Logging for monitoring

---

### TASK-015: Register Demo Expiry in Celery Beat Schedule

**Phase:** Collateral - Configuration
**Complexity:** S
**Dependencies:** TASK-014

**File:** `core/celery.py`

**Changes:**
Add to `beat_schedule`:
```python
"expire-demo-accounts": {
    "task": "core.tasks.reseller.expire_demo_accounts",
    "schedule": crontab(hour=3, minute=0),
},
```

Also add `"core.tasks.reseller"` to `autodiscover_tasks` list if not already autodiscovered.

**Acceptance Criteria:**
- [ ] Task registered in beat_schedule
- [ ] Runs daily at 03:00 UTC
- [ ] Task module is autodiscovered

---

## Phase 5: HTTP Layer

### TASK-016: Add Client Schemas to Reseller API

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** TASK-009

**File:** `adapters/http/api/reseller/schemas.py`

**Add these schemas:**
```python
class CreateDemoAccountRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)

class CreateClientAccountRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    admin_email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")

class DemoAccountCreatedResponse(BaseModel):
    client_id: str
    company_id: str
    company_name: str
    admin_email: str
    admin_password: str

class ResellerClientResponse(BaseModel):
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    source: str
    is_demo: bool
    demo_expires_at: Optional[str]
    plan: str
    company_status: str
    created_at: Optional[str]

class ResellerClientListResponse(BaseModel):
    items: list[ResellerClientResponse]
    total: int
```

**Acceptance Criteria:**
- [ ] All 5 schemas from design
- [ ] `CreateDemoAccountRequest` validates company_name length
- [ ] `CreateClientAccountRequest` validates email pattern
- [ ] Response schemas use `Optional[str]` for datetime fields (ISO format)

---

### TASK-017: Add ResellerClientMapper

**Phase:** HTTP - Mappers
**Complexity:** S
**Dependencies:** TASK-009, TASK-016

**File:** `adapters/http/api/reseller/mappers.py`

**Add `ResellerClientMapper` class** (in same file as existing `ResellerMapper`):
```python
class ResellerClientMapper:
    @staticmethod
    def dto_to_response(dto: ResellerClientDto) -> ResellerClientResponse: ...

    @staticmethod
    def dto_to_list_response(dto: ResellerClientListDto) -> ResellerClientListResponse: ...

    @staticmethod
    def demo_dto_to_response(dto: DemoAccountCreatedDto) -> DemoAccountCreatedResponse: ...
```

**Acceptance Criteria:**
- [ ] Three static methods exactly as design
- [ ] Handles datetime → ISO string conversion for `demo_expires_at` and `created_at`
- [ ] Maps all DTO fields to response fields

---

### TASK-018: Add Client Endpoints to Reseller Router

**Phase:** HTTP - Reseller Endpoints
**Complexity:** M
**Dependencies:** TASK-010, TASK-011, TASK-012, TASK-016, TASK-017

**File:** `adapters/http/api/reseller/routers.py`

**Add 3 endpoints:**

1. `POST /clients/demo` — Create demo account
   - Auth: `require_active_reseller`
   - Body: `CreateDemoAccountRequest`
   - Response: `DemoAccountCreatedResponse` (201)
   - Catch: `DemoAccountLimitExceededException` (429), `CompanyNameExistsError` (409)

2. `POST /clients/account` — Create normal account
   - Auth: `require_active_reseller`
   - Body: `CreateClientAccountRequest`
   - Response: `ResellerClientResponse` (201)
   - Catch: `CompanyNameExistsError` (409), `DomainAlreadyTakenError` (409), `UserAlreadyExistsError` (409), `CompanyAlreadyLinkedToResellerException` (409)

3. `GET /clients` — List reseller's clients
   - Auth: `get_current_reseller`
   - Query params: `offset` (default 0), `limit` (default 50)
   - Response: `ResellerClientListResponse`

**Pattern:** Follow existing reseller routers — inline repo instantiation, handler creation, try/except for domain exceptions, mapper for response.

**Acceptance Criteria:**
- [ ] Three endpoints added
- [ ] All domain exceptions caught and mapped to HTTP status codes
- [ ] Uses `require_active_reseller` for write endpoints
- [ ] Uses `get_current_reseller` for read endpoint
- [ ] Demo endpoint returns `handler.result` for one-time credentials
- [ ] Normal account endpoint queries back created client for response

---

### TASK-019: Add Admin Client List Endpoint

**Phase:** HTTP - Admin Endpoint
**Complexity:** S
**Dependencies:** TASK-012, TASK-017

**File:** `adapters/http/api/admin/reseller_routers.py`

**Add endpoint:**

`GET /resellers/{reseller_id}/clients` — List a reseller's clients (admin view)
- Auth: `require_role(UserRole.SUPER_ADMIN)`
- Query params: `offset` (default 0), `limit` (default 50)
- Response: `ResellerClientListResponse`
- Uses `ListResellerClientsQueryHandler`

**Acceptance Criteria:**
- [ ] Endpoint added to existing admin reseller router
- [ ] Requires SUPER_ADMIN role
- [ ] Accepts `reseller_id` path param
- [ ] Returns paginated client list with company info

---

## Phase 6: Tests

### TASK-020: Unit Tests

**Phase:** Tests - Unit
**Complexity:** L
**Dependencies:** TASK-003, TASK-010, TASK-011, TASK-012, TASK-014

**Files:**
- `tests/unit/reseller_bc/client/domain/test_entities.py`
- `tests/unit/reseller_bc/client/application/test_create_demo_account.py`
- `tests/unit/reseller_bc/client/application/test_create_client_account.py`
- `tests/unit/reseller_bc/client/application/test_list_reseller_clients.py`
- `tests/unit/reseller_bc/client/application/test_demo_expiry.py`

**Test Scenarios:**

**Entity tests:**
- Create ResellerClient with `is_demo=True` → `demo_expires_at` is ~14 days from now
- Create ResellerClient with `is_demo=False` → `demo_expires_at` is None
- Create with explicit `id` → uses provided id
- Create without `id` → auto-generates ULID
- Source enum values preserved

**CreateDemoAccountCommand tests:**
- Happy path: creates company, user, seed data, ResellerClient
- Reseller not found → raises `ResellerNotFoundException`
- Reseller suspended → raises `ResellerSuspendedException`
- Demo limit exceeded (5 active) → raises `DemoAccountLimitExceededException`
- Company name conflict → raises `CompanyNameExistsError`

**CreateClientAccountCommand tests:**
- Happy path: creates company with admin, ResellerClient
- Reseller not found → raises
- Reseller suspended → raises
- Domain already taken → propagates `DomainAlreadyTakenError`
- Admin email already exists → propagates `UserAlreadyExistsError`

**ListResellerClientsQuery tests:**
- Empty list → returns 0 items, total=0
- With clients → maps company info correctly
- Pagination → offset/limit honored

**Demo expiry task tests:**
- Expired demo (>14 days) with active company → suspended
- Purgeable demo (>44 days) with suspended company → deactivated
- Already suspended company → no double-processing
- No expired demos → counts are 0

**Acceptance Criteria:**
- [ ] All test scenarios covered
- [ ] Mock repositories used
- [ ] Tests pass with `make test`

---

### TASK-021: Integration Tests

**Phase:** Tests - Integration
**Complexity:** L
**Dependencies:** TASK-018, TASK-019

**File:** `tests/integration/test_reseller_client_endpoints.py`

**Test Scenarios:**

1. `POST /reseller/clients/demo` — happy path:
   - Creates company with seed data
   - Returns admin credentials (email + password)
   - ResellerClient created with `is_demo=True`
   - Company has Free plan

2. `POST /reseller/clients/demo` — suspended reseller:
   - Returns 403

3. `POST /reseller/clients/demo` — demo limit exceeded:
   - Returns 429 after 5 active demos

4. `POST /reseller/clients/account` — happy path:
   - Creates company with admin user
   - Admin receives magic link (or at least user is created)
   - ResellerClient created with `is_demo=False`

5. `POST /reseller/clients/account` — duplicate company name:
   - Returns 409

6. `GET /reseller/clients` — empty list:
   - Returns `{items: [], total: 0}`

7. `GET /reseller/clients` — with items:
   - Returns client list with company names, plans, statuses

8. `GET /admin/resellers/{id}/clients` — admin access:
   - Returns reseller's client list
   - Requires super_admin auth

9. Dashboard `client_count` — after creating clients:
   - `GET /reseller/dashboard` returns real client_count

**Acceptance Criteria:**
- [ ] All 9 scenarios tested
- [ ] Uses test database with fixtures
- [ ] Tests pass with `make test-integration`
- [ ] No test data leakage between tests

---

## Phase 7: Configuration

### TASK-022: Create `__init__.py` Files for New Modules

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-001

**Files to create (empty `__init__.py`):**
- `src/reseller_bc/client/__init__.py`
- `src/reseller_bc/client/domain/__init__.py`
- `src/reseller_bc/client/infrastructure/__init__.py`
- `src/reseller_bc/client/application/__init__.py`
- `src/reseller_bc/client/application/commands/__init__.py`
- `src/reseller_bc/client/application/queries/__init__.py`

**Acceptance Criteria:**
- [ ] All `__init__.py` files exist
- [ ] Python module resolution works for all new paths

---

## Dependency Graph

```
TASK-001 (Enum) ─────────────────────────────────────────┐
TASK-002 (Exceptions) ──────────────────────────────────────┤
                                                         │
TASK-003 (Entity) ←── TASK-001                           │
    │                                                    │
TASK-004 (RepoInterface) ←── TASK-003                    │
    │                                                    │
TASK-005 (Migration) ←── TASK-003                        │
    │                                                    │
TASK-006 (Model) ←── TASK-005                            │
    │                                                    │
TASK-007 (RepoImpl) ←── TASK-004, TASK-006               │
    │                                                    │
TASK-008 (Seed Refactor) [independent]                   │
    │                                                    │
TASK-009 (DTOs) ←── TASK-003                             │
    │                                                    │
TASK-010 (CreateDemo) ←── TASK-004, TASK-007, TASK-008, TASK-009
TASK-011 (CreateAccount) ←── TASK-004, TASK-007, TASK-009│
TASK-012 (ListClients) ←── TASK-004, TASK-007, TASK-009  │
TASK-013 (Dashboard) ←── TASK-007                        │
TASK-014 (CeleryTask) ←── TASK-007                       │
TASK-015 (CeleryBeat) ←── TASK-014                       │
    │                                                    │
TASK-016 (Schemas) ←── TASK-009                          │
TASK-017 (Mappers) ←── TASK-009, TASK-016                │
TASK-018 (ResellerEndpoints) ←── TASK-010..012, TASK-016, TASK-017
TASK-019 (AdminEndpoint) ←── TASK-012, TASK-017          │
    │                                                    │
TASK-020 (UnitTests) ←── TASK-003, TASK-010..012, TASK-014
TASK-021 (IntegrationTests) ←── TASK-018, TASK-019       │
TASK-022 (__init__.py) ←── TASK-001                      │
```

## Execution Order

**Batch 1 (Parallel — no deps):** TASK-001, TASK-002, TASK-008, TASK-022
**Batch 2:** TASK-003 (depends on TASK-001)
**Batch 3 (Parallel):** TASK-004, TASK-005, TASK-009
**Batch 4:** TASK-006 (depends on TASK-005)
**Batch 5:** TASK-007 (depends on TASK-004, TASK-006)
**Batch 6 (Parallel):** TASK-010, TASK-011, TASK-012, TASK-013, TASK-014, TASK-016
**Batch 7 (Parallel):** TASK-015, TASK-017
**Batch 8 (Parallel):** TASK-018, TASK-019
**Batch 9 (Parallel):** TASK-020, TASK-021

---

## Final Checklist

- [x] All 22 tasks completed (backend — TASK-001 through TASK-022)
- [x] All unit tests passing (28 unit tests)
- [x] All integration tests passing (13 integration tests)
- [ ] mypy passes (`make lint`)
- [x] All acceptance criteria from requirements.md verified
- [x] New endpoints visible in OpenAPI docs
- [x] `make seed` still works correctly after refactor
- [x] Dashboard `client_count` returns real data
- [x] Demo expiry Celery task registered and functional
- [ ] Frontend: TASK-023 (separate task)
