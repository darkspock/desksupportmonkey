# Solution Design: F2 — Account Creation

**Requirement:** [requirements.md](requirements.md)
**Validation:** [validation.md](validation.md)
**Date:** 2026-03-03
**Bounded Context:** `reseller_bc` (subdomain: `client`)

---

## Summary

F2 introduces the `ResellerClient` entity as a link between resellers and the companies they create. Two account creation flows are needed: **demo** (company with seed data, Free plan, temporary password) and **normal** (empty company with admin user via magic link). A daily Celery beat task handles demo expiry (suspend at 14 days, purge at 44 days). The seed data script is refactored to accept a `company_id` parameter. The F1 dashboard query is updated to return real `client_count`.

## Architecture Decisions

1. **New subdomain `reseller_bc/client/`** — follows the pattern of `reseller_bc/reseller/` but owns the `ResellerClient` entity and all client management commands/queries.

2. **Cross-BC company creation via `CreateCompanyCommand`** — the demo and normal account commands instantiate `CreateCompanyCommandHandler` directly (same process, same transaction). This follows the existing pattern where routers instantiate handlers inline.

3. **`is_demo` flag on `ResellerClient`** — keeps the demo flag within `reseller_bc` rather than modifying the `Company` entity in `company_bc`.

4. **`demo_expires_at` on `ResellerClient`** — pre-calculated at creation time (created_at + 14 days). The Celery task queries this field directly instead of computing `created_at + 14 days` on every run.

5. **Demo credentials via generated password** — demo accounts create an admin user with a random password (returned once in the response). No magic link is sent for demos.

6. **Normal accounts default to Free plan** — plan selection is deferred. The company is created with the default Free plan. Resellers tell clients to upgrade via the standard billing flow.

7. **Seed data refactored as a callable function** — `scripts/seed_demo_data.py` gets a new `seed_company_data(session, company_id)` function that seeds data for an existing company. The `main()` function continues to work as before.

8. **Company purge** — at 44 days, the Celery task sets the company status to `deactivated` and `is_active=False`. Actual data cascade delete is a future concern (out of scope for F2). The `ResellerClient` record is retained for historical tracking.

---

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| `Reseller` entity | `src/reseller_bc/reseller/domain/entities.py` | Pattern reference | None |
| `ResellerRepository` | `src/reseller_bc/reseller/infrastructure/repository.py` | Pattern reference | None |
| `CreateCompanyCommand` | `src/company_bc/company/application/commands/create_company.py` | Yes — called from demo/normal commands | None |
| `CompanyRepository` | `src/company_bc/company/infrastructure/repository.py` | Yes — used in create commands | None |
| `UserModel` / `User` entity | `src/auth_bc/user/` | Yes — create admin for demo/normal | None |
| Seed data script | `scripts/seed_demo_data.py` | Refactored — extract `seed_company_data()` | Yes |
| Celery beat schedule | `core/celery.py` | Yes — add 2 tasks | Yes |
| `GetResellerDashboardQuery` | `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | Yes — update `client_count` | Yes |
| Reseller HTTP routers | `adapters/http/api/reseller/routers.py` | Yes — add client endpoints | Yes |
| Admin reseller routers | `adapters/http/api/admin/reseller_routers.py` | Yes — add client list endpoint | Yes |
| Reseller dependencies | `adapters/http/api/reseller/dependencies.py` | Yes — `require_active_reseller` | None |

---

## Implementation Plan

### 1. Domain Layer

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| `ClientSource` | `src/reseller_bc/client/domain/enums.py` | `manual`, `referral` |

```python
class ClientSource(str, Enum):
    MANUAL = "manual"
    REFERRAL = "referral"
```

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| `ResellerClient` | `src/reseller_bc/client/domain/entities.py` | Link between reseller and company |

```python
@dataclass
class ResellerClient:
    id: str
    reseller_id: str
    company_id: str
    source: ClientSource
    is_demo: bool
    demo_expires_at: Optional[datetime]  # created_at + 14 days for demos, None for normal
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

#### Exceptions

| Exception | File Path | Description |
|-----------|-----------|-------------|
| `CompanyAlreadyLinkedToResellerException` | `src/reseller_bc/client/domain/exceptions.py` | Company already attributed to another reseller |
| `DemoAccountLimitExceededException` | `src/reseller_bc/client/domain/exceptions.py` | Max active demos per reseller (5) |

#### Repository Interface

| Interface | File Path | Methods |
|-----------|-----------|---------|
| `ResellerClientRepositoryInterface` | `src/reseller_bc/client/domain/repository.py` | See below |

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

### 2. Infrastructure Layer

#### Models

| Model | File Path | Table |
|-------|-----------|-------|
| `ResellerClientModel` | `src/reseller_bc/client/infrastructure/models.py` | `reseller_clients` |

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

Note: `company_id` has `unique=True` to enforce the "one reseller per company" rule.

#### Repository Implementation

| Interface | Implementation | File Path |
|-----------|----------------|-----------|
| `ResellerClientRepositoryInterface` | `ResellerClientRepository` | `src/reseller_bc/client/infrastructure/repository.py` |

Follows the `ResellerRepository` pattern: SQLAlchemy 2.0 style, `_to_entity()` conversion, session-based.

Key queries:
- `find_expired_demos(before)`: `WHERE is_demo = true AND demo_expires_at <= :before AND company status = 'active'` (joins Company)
- `find_purgeable_demos(before)`: `WHERE is_demo = true AND demo_expires_at <= :before - 30 days AND company status = 'suspended'`
- `count_active_demos_by_reseller_id(reseller_id)`: `WHERE reseller_id = :id AND is_demo = true AND demo_expires_at > now()`

#### Migration

| Migration | Description |
|-----------|-------------|
| `add_reseller_clients_table` | Creates `reseller_clients` table with all columns and indexes |

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
```

### 3. Application Layer

#### DTOs

| DTO | File Path | Description |
|-----|-----------|-------------|
| `ResellerClientDto` | `src/reseller_bc/client/application/dtos.py` | Client list item with company info |
| `DemoAccountCreatedDto` | `src/reseller_bc/client/application/dtos.py` | Response with admin credentials |

```python
@dataclass
class ResellerClientDto:
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    source: str  # "manual" or "referral"
    is_demo: bool
    demo_expires_at: Optional[datetime]
    plan: str  # From Company
    company_status: str  # From Company
    created_at: Optional[datetime]

    @classmethod
    def from_entity_with_company(cls, client: ResellerClient, company_name: str, plan: str, company_status: str) -> "ResellerClientDto":
        return cls(
            id=client.id,
            reseller_id=client.reseller_id,
            company_id=client.company_id,
            company_name=company_name,
            source=client.source.value,
            is_demo=client.is_demo,
            demo_expires_at=client.demo_expires_at,
            plan=plan,
            company_status=company_status,
            created_at=client.created_at,
        )


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
    admin_password: str  # Shown once, never stored in plain text after this
```

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| `CreateDemoAccountCommand` | `CreateDemoAccountCommandHandler` | `src/reseller_bc/client/application/commands/create_demo_account.py` | Create demo company with seed data |
| `CreateClientAccountCommand` | `CreateClientAccountCommandHandler` | `src/reseller_bc/client/application/commands/create_client_account.py` | Create normal company with admin user |

##### CreateDemoAccountCommand

```python
@dataclass
class CreateDemoAccountCommand(Command):
    id: str  # Pre-generated ULID for ResellerClient
    reseller_id: str
    company_name: str  # e.g. "TechCorp Demo"
```

**Handler logic:**
1. Validate reseller exists and is ACTIVE
2. Check active demo count < 5 (limit)
3. Generate company_id with ULID
4. Create Company via `CreateCompanyCommandHandler` — pass `admin_email=None` (no magic link), derive email domain from a synthetic demo domain (`demo-{ulid}.dsm.local`)
5. Create admin User directly with generated password (hashed) — email: `admin@demo-{ulid}.dsm.local`, role: ADMIN
6. Call `seed_company_data(session, company_id)` to populate demo data
7. Create `ResellerClient` with `is_demo=True`, `source=MANUAL`
8. Save and return (handler returns None per CQRS)

**Dependencies:**
- `ResellerClientRepositoryInterface`
- `ResellerRepositoryInterface`
- `CompanyRepositoryInterface`
- `UserWriter` (port)
- `Session` (for seed data function)

##### CreateClientAccountCommand

```python
@dataclass
class CreateClientAccountCommand(Command):
    id: str  # Pre-generated ULID for ResellerClient
    reseller_id: str
    company_name: str
    admin_email: str
```

**Handler logic:**
1. Validate reseller exists and is ACTIVE
2. Derive email domain from admin_email (e.g., `user@acme.com` → `["acme.com"]`)
3. Check company_name uniqueness (via Company create logic)
4. Check company is not already linked to another reseller (via `find_by_company_id`)
5. Create Company via `CreateCompanyCommandHandler` — pass `admin_email` (triggers magic link)
6. Create `ResellerClient` with `is_demo=False`, `source=MANUAL`
7. Save

**Dependencies:**
- `ResellerClientRepositoryInterface`
- `ResellerRepositoryInterface`
- All dependencies of `CreateCompanyCommandHandler`

#### Queries

| Query | Handler | File Path | Return Type |
|-------|---------|-----------|-------------|
| `ListResellerClientsQuery` | `ListResellerClientsQueryHandler` | `src/reseller_bc/client/application/queries/list_reseller_clients.py` | `ResellerClientListDto` |

```python
@dataclass
class ListResellerClientsQuery(Query):
    reseller_id: str
    offset: int = 0
    limit: int = 50
```

**Handler logic:**
1. Get clients from `ResellerClientRepository.find_by_reseller_id()`
2. Get total count from `count_by_reseller_id()`
3. For each client, fetch company name/plan/status from `CompanyRepository` — use a batch query to avoid N+1 (`find_by_ids()`)
4. Map to `ResellerClientDto` list
5. Return `ResellerClientListDto`

**Dependencies:**
- `ResellerClientRepositoryInterface`
- `CompanyRepositoryInterface` (read-only, for company info)

#### Celery Tasks

| Task | File Path | Schedule | Description |
|------|-----------|----------|-------------|
| `expire_demo_accounts` | `core/tasks/reseller.py` | Daily at 03:00 UTC | Suspend expired demos, deactivate purgeable demos |

```python
@celery_app.task(name="core.tasks.reseller.expire_demo_accounts")
def expire_demo_accounts() -> dict:
    """Suspend demos expired >14 days, deactivate demos expired >44 days."""
    from core.database import SessionLocal

    session = SessionLocal()
    try:
        now = datetime.utcnow()

        # Phase 1: Suspend active demos past expiry (14 days)
        client_repo = ResellerClientRepository(session)
        company_repo = CompanyRepository(session)

        expired = client_repo.find_expired_demos(before=now)
        suspended_count = 0
        for client in expired:
            company = company_repo.get_by_id(client.company_id)
            if company and company.status == CompanyStatus.ACTIVE:
                company.change_status(CompanyStatus.SUSPENDED)
                company_repo.save(company)
                suspended_count += 1

        # Phase 2: Deactivate suspended demos past purge window (44 days)
        purge_cutoff = now - timedelta(days=30)  # 30 days after suspension (14+30=44)
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
        logger.info("Demo expiry: suspended=%d, deactivated=%d", suspended_count, deactivated_count)
        return {"suspended": suspended_count, "deactivated": deactivated_count}
    except Exception as e:
        session.rollback()
        logger.error("Demo expiry task failed: %s", str(e))
        raise
    finally:
        session.close()
```

### 4. HTTP Layer

#### Schemas

| Schema | File Path | Description |
|--------|-----------|-------------|
| `CreateDemoAccountRequest` | `adapters/http/api/reseller/schemas.py` | Request body for demo creation |
| `CreateClientAccountRequest` | `adapters/http/api/reseller/schemas.py` | Request body for normal account |
| `DemoAccountCreatedResponse` | `adapters/http/api/reseller/schemas.py` | Response with admin credentials |
| `ResellerClientResponse` | `adapters/http/api/reseller/schemas.py` | Client list item response |
| `ResellerClientListResponse` | `adapters/http/api/reseller/schemas.py` | Paginated client list response |

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

#### Mappers

| Mapper | File Path | Description |
|--------|-----------|-------------|
| `ResellerClientMapper` | `adapters/http/api/reseller/mappers.py` | Add methods for client DTOs → responses |

```python
# Add to existing mappers.py
class ResellerClientMapper:
    @staticmethod
    def dto_to_response(dto: ResellerClientDto) -> ResellerClientResponse: ...

    @staticmethod
    def dto_to_list_response(dto: ResellerClientListDto) -> ResellerClientListResponse: ...

    @staticmethod
    def demo_dto_to_response(dto: DemoAccountCreatedDto) -> DemoAccountCreatedResponse: ...
```

#### Endpoints

| Method | Route | Handler | Auth | Description |
|--------|-------|---------|------|-------------|
| `POST` | `/reseller/clients/demo` | `CreateDemoAccountCommandHandler` | `require_active_reseller` | Create demo account |
| `POST` | `/reseller/clients/account` | `CreateClientAccountCommandHandler` | `require_active_reseller` | Create normal account |
| `GET` | `/reseller/clients` | `ListResellerClientsQueryHandler` | `get_current_reseller` | List reseller's clients |
| `GET` | `/admin/resellers/{id}/clients` | `ListResellerClientsQueryHandler` | `require_role(SUPER_ADMIN)` | Admin: list reseller's clients |

All reseller endpoints are added to `adapters/http/api/reseller/routers.py`.
The admin endpoint is added to `adapters/http/api/admin/reseller_routers.py`.

##### POST /reseller/clients/demo

```python
@router.post("/clients/demo", status_code=201)
def create_demo_account(
    body: CreateDemoAccountRequest,
    reseller: Reseller = Depends(require_active_reseller),
    db: Session = Depends(get_db),
):
    client_repo = ResellerClientRepository(db)
    reseller_repo = ResellerRepository(db)
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)
    # ... instantiate other repos needed by CreateCompanyCommandHandler

    client_id = str(ulid.new())
    handler = CreateDemoAccountCommandHandler(
        client_repo=client_repo,
        reseller_repo=reseller_repo,
        company_repo=company_repo,
        user_repo=user_repo,
        session=db,
    )

    try:
        handler.handle(CreateDemoAccountCommand(
            id=client_id,
            reseller_id=reseller.id,
            company_name=body.company_name,
        ))
    except DemoAccountLimitExceededException as e:
        raise HTTPException(status_code=429, detail=str(e))
    except CompanyNameExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Since commands return None, query back the created data
    # The handler stores the demo credentials in a side-channel (instance variable)
    return {"data": handler.result.model_dump()}
```

**Note on demo credentials:** Since commands return None per CQRS, the `CreateDemoAccountCommandHandler` stores the `DemoAccountCreatedDto` as `self._result` after creation. The router reads `handler.result` to return the one-time credentials. This is a pragmatic deviation — the alternative (querying back) would lose the plain-text password.

##### POST /reseller/clients/account

```python
@router.post("/clients/account", status_code=201)
def create_client_account(
    body: CreateClientAccountRequest,
    reseller: Reseller = Depends(require_active_reseller),
    db: Session = Depends(get_db),
):
    # ... similar pattern: instantiate repos, create handler, execute command
    # Catch: CompanyNameExistsError (409), DomainAlreadyTakenError (409),
    #        UserAlreadyExistsError (409), CompanyAlreadyLinkedToResellerException (409)

    # Query back the created client
    query_handler = ListResellerClientsQueryHandler(client_repo=client_repo, company_repo=company_repo)
    # ... or use a GetResellerClientByIdQuery
```

##### GET /reseller/clients

```python
@router.get("/clients")
def list_clients(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    reseller: Reseller = Depends(get_current_reseller),
    db: Session = Depends(get_db),
):
    client_repo = ResellerClientRepository(db)
    company_repo = CompanyRepository(db)
    handler = ListResellerClientsQueryHandler(client_repo=client_repo, company_repo=company_repo)
    dto = handler.handle(ListResellerClientsQuery(
        reseller_id=reseller.id,
        offset=offset,
        limit=limit,
    ))
    return {"data": ResellerClientMapper.dto_to_list_response(dto).model_dump()}
```

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `scripts/seed_demo_data.py` | Refactor | Extract `seed_company_data(session, company_id)` function |
| `core/celery.py` | Add | Register `expire-demo-accounts` beat schedule entry |
| `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | Modify | Use `ResellerClientRepository.count_by_reseller_id()` for real `client_count` |
| `adapters/http/api/reseller/routers.py` | Add | Client creation and list endpoints |
| `adapters/http/api/reseller/schemas.py` | Add | New request/response schemas for clients |
| `adapters/http/api/reseller/mappers.py` | Add | `ResellerClientMapper` class |
| `adapters/http/api/admin/reseller_routers.py` | Add | `GET /resellers/{id}/clients` endpoint |

#### Seed Data Refactor

The `seed_demo_data.py` script is refactored to extract per-company seeding into a reusable function:

```python
def seed_company_data(session, company_id: str, company_name: str = "Demo Company") -> dict:
    """Seed demo data for a single existing company. Returns metadata about seeded data."""
    # Create departments
    dept_map = seed_departments_for_company(session, company_id)
    # Create locations
    loc_map = seed_locations_for_company(session, company_id)
    # Create users (admin + employees)
    users = seed_users_for_company(session, company_id, company_name, dept_map)
    # Create asset type definitions
    seed_asset_type_definitions_for_company(session, company_id)
    # Create assets
    seed_assets_for_company(session, company_id, users, loc_map)
    # Create workflow templates
    seed_workflow_templates_for_company(session, company_id)
    # Create service requests
    seed_requests_for_company(session, company_id, users)
    # Create custom field definitions
    seed_custom_fields_for_company(session, company_id)
    # Create reports
    seed_reports_for_company(session, company_id, users)

    session.flush()
    return {"admin_user_id": users[0]["id"], "admin_email": users[0]["email"]}
```

The existing `main()` function is updated to call `seed_company_data()` per company instead of the old per-table approach.

#### Dashboard Query Update

```python
# In GetResellerDashboardQueryHandler.handle():
client_count = self.client_repo.count_by_reseller_id(query.reseller_id)
# Replace hardcoded 0 with real count
```

This requires adding `ResellerClientRepositoryInterface` as a dependency to `GetResellerDashboardQueryHandler`.

#### Celery Beat Registration

```python
# In core/celery.py beat_schedule:
"expire-demo-accounts": {
    "task": "core.tasks.reseller.expire_demo_accounts",
    "schedule": crontab(hour=3, minute=0),  # Daily at 03:00 UTC
},
```

#### Breaking Changes

None. All changes are additive.

---

## Database Schema

```sql
CREATE TABLE reseller_clients (
    id VARCHAR(26) PRIMARY KEY,
    reseller_id VARCHAR(26) NOT NULL REFERENCES resellers(id),
    company_id VARCHAR(26) NOT NULL UNIQUE REFERENCES companies(id),
    source VARCHAR(20) NOT NULL,  -- 'manual' or 'referral'
    is_demo BOOLEAN NOT NULL DEFAULT FALSE,
    demo_expires_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_reseller_clients_reseller_id ON reseller_clients(reseller_id);
CREATE INDEX ix_reseller_clients_demo_expires ON reseller_clients(demo_expires_at) WHERE is_demo = TRUE;
```

---

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| F1 (Portal Foundation) | Feature | Reseller entity, auth, HTTP layer |
| `CreateCompanyCommand` | Cross-BC | Company creation with seeding |
| `CompanyRepository` | Cross-BC | Read company info for client list |
| `UserRepository` | Cross-BC | Create admin user for demo accounts |
| Celery + Redis | Infrastructure | Beat schedule for demo expiry |
| `scripts/seed_demo_data.py` | Collateral | Refactored for per-company seeding |

---

## Testing Strategy

| Test Type | Scope | File Path | Priority |
|-----------|-------|-----------|----------|
| Unit | `ResellerClient` entity — create, is_demo, demo_expires_at | `tests/unit/reseller_bc/client/domain/test_entities.py` | High |
| Unit | `CreateDemoAccountCommandHandler` — happy path, limit, suspended | `tests/unit/reseller_bc/client/application/test_create_demo_account.py` | High |
| Unit | `CreateClientAccountCommandHandler` — happy path, duplicate company | `tests/unit/reseller_bc/client/application/test_create_client_account.py` | High |
| Unit | `ListResellerClientsQueryHandler` — empty, with items, pagination | `tests/unit/reseller_bc/client/application/test_list_reseller_clients.py` | Medium |
| Unit | `expire_demo_accounts` task — suspend, deactivate | `tests/unit/reseller_bc/client/application/test_demo_expiry.py` | High |
| Integration | `POST /reseller/clients/demo` — full flow with seed data | `tests/integration/test_reseller_client_endpoints.py` | High |
| Integration | `POST /reseller/clients/account` — company + user creation | `tests/integration/test_reseller_client_endpoints.py` | High |
| Integration | `GET /reseller/clients` — list with company info | `tests/integration/test_reseller_client_endpoints.py` | Medium |
| Integration | `GET /admin/resellers/{id}/clients` — admin access | `tests/integration/test_reseller_client_endpoints.py` | Medium |
| Integration | Dashboard `client_count` — real count after client creation | `tests/integration/test_reseller_client_endpoints.py` | Medium |

---

## Implementation Order

1. [ ] Domain: `ClientSource` enum
2. [ ] Domain: `ResellerClient` entity with `create()` factory
3. [ ] Domain: Exceptions (`CompanyAlreadyLinkedToResellerException`, `DemoAccountLimitExceededException`)
4. [ ] Domain: `ResellerClientRepositoryInterface`
5. [ ] Infrastructure: Alembic migration for `reseller_clients` table
6. [ ] Infrastructure: `ResellerClientModel` (SQLAlchemy)
7. [ ] Infrastructure: `ResellerClientRepository` implementation
8. [ ] Collateral: Refactor `scripts/seed_demo_data.py` — extract `seed_company_data()`
9. [ ] Application: DTOs (`ResellerClientDto`, `ResellerClientListDto`, `DemoAccountCreatedDto`)
10. [ ] Application: `CreateDemoAccountCommand` + handler
11. [ ] Application: `CreateClientAccountCommand` + handler
12. [ ] Application: `ListResellerClientsQuery` + handler
13. [ ] Collateral: Update `GetResellerDashboardQueryHandler` — real `client_count`
14. [ ] Application: Celery task `expire_demo_accounts` in `core/tasks/reseller.py`
15. [ ] Collateral: Register task in `core/celery.py` beat schedule
16. [ ] HTTP: Request/response schemas in `adapters/http/api/reseller/schemas.py`
17. [ ] HTTP: `ResellerClientMapper` in `adapters/http/api/reseller/mappers.py`
18. [ ] HTTP: Reseller endpoints in `adapters/http/api/reseller/routers.py`
19. [ ] HTTP: Admin endpoint in `adapters/http/api/admin/reseller_routers.py`
20. [ ] Tests: Unit tests (entity, commands, queries, task)
21. [ ] Tests: Integration tests (endpoints, full flows)
22. [ ] Configuration: Verify `__init__.py` files for new modules
23. [ ] Frontend: Client pages (separate task)

---

## Open Technical Questions

1. **Demo admin password generation** — Use `secrets.token_urlsafe(12)` for random password. Hash with bcrypt before storing in User. Return plain text once in response.

2. **Seed data session sharing** — The `CreateDemoAccountCommandHandler` receives the same session. The seed function operates on that session. All changes commit together. If seeding fails, the entire transaction rolls back.

3. **Company name for demos** — Append " (Demo)" suffix to distinguish in admin views. E.g., "TechCorp" → "TechCorp (Demo)".

---

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Seed data function fails for some companies | Low | Medium | Transaction rollback; unit test seed function independently |
| Demo expiry task takes too long with many demos | Low | Low | Indexed query on `demo_expires_at`; batch processing |
| Cross-BC dependency on `CreateCompanyCommand` changes | Low | High | CreateCompanyCommand is stable; pin to current interface |
| Demo limit bypass via race condition | Very Low | Low | DB unique constraint on `company_id` prevents duplicate links |
