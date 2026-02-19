# Tasks: F0 — API Key Management

**Feature:** [requirements.md](requirements.md)
**Epic:** [E35 — MCP Server](../../requirements.md)
**Date:** 2026-02-17

---

## Pre-Implementation Checklist

- [x] Verify `mcp_bc` bounded context does not already exist in `src/`
- [x] Verify `api_keys` table does not already exist in any migration
- [x] Verify no existing API key endpoints in `adapters/http/api/auth/`

---

## Task 1: Create `api_keys` Alembic Migration

**File:** `alembic/versions/{hash}_create_api_keys_table.py`

Create migration following existing patterns (see `alembic/versions/` for reference):

```python
def upgrade() -> None:
    op.create_table('api_keys',
        sa.Column('id', sa.String(length=26), nullable=False),            # ULID PK
        sa.Column('user_id', sa.String(length=26), nullable=False),       # FK → users
        sa.Column('key_hash', sa.String(length=128), nullable=False),     # bcrypt hash
        sa.Column('name', sa.String(length=100), nullable=False),         # human label
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'], unique=False)

def downgrade() -> None:
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
    op.drop_table('api_keys')
```

Generate via: `make revision m="create_api_keys_table"`

### Acceptance Criteria
- [x] Migration runs without errors (`make db-upgrade`)
- [x] Table has all 7 columns with correct types and constraints
- [x] `user_id` index exists
- [x] `is_active` defaults to `true`
- [x] `created_at` defaults to `now()`
- [x] Downgrade drops table cleanly

---

## Task 2: Create `mcp_bc` Domain Layer

### 2.1: Domain Entity

**File:** `src/mcp_bc/server/domain/entities.py`

```python
@dataclass
class ApiKey:
    id: str
    user_id: str
    key_hash: str
    name: str
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    is_active: bool = True

    @classmethod
    def create(cls, user_id: str, key_hash: str, name: str, id: Optional[str] = None) -> "ApiKey":
        if not name or not name.strip():
            raise ValueError("API key name is required")
        if len(name.strip()) > 100:
            raise ValueError("API key name must be 100 characters or less")
        return cls(
            id=id or str(ulid.new()),
            user_id=user_id,
            key_hash=key_hash,
            name=name.strip(),
        )

    def revoke(self) -> None:
        if not self.is_active:
            raise ApiKeyAlreadyRevokedError(self.id)
        self.is_active = False
```

Also define:
- `ApiKeyAlreadyRevokedError(Exception)` in same file

Create package `__init__.py` files:
- `src/mcp_bc/__init__.py`
- `src/mcp_bc/server/__init__.py`
- `src/mcp_bc/server/domain/__init__.py`

### 2.2: Repository Interface

**File:** `src/mcp_bc/server/domain/repository.py`

```python
class ApiKeyRepositoryInterface(ABC):
    @abstractmethod
    def save(self, api_key: ApiKey) -> ApiKey: ...

    @abstractmethod
    def find_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]: ...

    @abstractmethod
    def find_all_by_user(self, user_id: str) -> list[ApiKey]: ...

    @abstractmethod
    def count_active_by_user(self, user_id: str) -> int: ...

    @abstractmethod
    def find_active_by_hash(self, key_hash: str) -> Optional[ApiKey]: ...

    @abstractmethod
    def update_last_used(self, key_id: str) -> None: ...
```

Note: `find_active_by_hash` is needed by F1 (MCP auth middleware) but should be defined now. `update_last_used` is called by F1 but declared in the interface now for completeness.

### Acceptance Criteria
- [x] `ApiKey` entity is a `@dataclass` with public fields (matches project pattern)
- [x] `create()` factory method generates ULID, validates name
- [x] `revoke()` method sets `is_active = False`, raises if already revoked
- [x] Repository interface uses ABC with `@abstractmethod`
- [x] All `__init__.py` files created for package structure

---

## Task 3: Create `mcp_bc` Infrastructure Layer

### 3.1: ORM Model

**File:** `src/mcp_bc/server/infrastructure/models.py`

```python
from core.base import Base
from core.mixins import ULIDMixin

class ApiKeyModel(ULIDMixin, Base):
    __tablename__ = "api_keys"

    user_id: Mapped[str] = mapped_column(String(26), ForeignKey("users.id"), index=True)
    key_hash: Mapped[str] = mapped_column(String(128))
    name: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=sa.text("true"))
```

Use `Mapped[type]` + `mapped_column()` (SQLAlchemy 2.0 style, project standard). Inherit `ULIDMixin` for `id` field. Do NOT inherit `TimestampMixin` — `api_keys` has no `updated_at` column.

### 3.2: Repository Implementation

**File:** `src/mcp_bc/server/infrastructure/repository.py`

```python
class ApiKeyRepository(ApiKeyRepositoryInterface):
    def __init__(self, session: Session):
        self.session = session

    def save(self, api_key: ApiKey) -> ApiKey:
        # Upsert pattern: check existing, update or insert
        ...

    def find_by_id(self, key_id: str, user_id: str) -> Optional[ApiKey]:
        # Filter by both key_id AND user_id (tenant isolation)
        ...

    def find_all_by_user(self, user_id: str) -> list[ApiKey]:
        # Return all keys (active + revoked) for the user, ordered by created_at desc
        ...

    def count_active_by_user(self, user_id: str) -> int:
        # COUNT where user_id = X and is_active = true
        ...

    def find_active_by_hash(self, key_hash: str) -> Optional[ApiKey]:
        # For F1 auth middleware — find key by hash where is_active = true
        # Note: This does NOT filter by company_id — it's used before user context is resolved
        ...

    def update_last_used(self, key_id: str) -> None:
        # UPDATE api_keys SET last_used_at = now() WHERE id = key_id
        ...

    @staticmethod
    def _to_entity(model: ApiKeyModel) -> ApiKey:
        return ApiKey(
            id=model.id,
            user_id=model.user_id,
            key_hash=model.key_hash,
            name=model.name,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
            is_active=model.is_active,
        )
```

Use SQLAlchemy 2.0 `select()` style. `save()` uses upsert pattern (check existing, update or insert). Use `session.flush()` + `session.refresh()`.

Create `__init__.py`:
- `src/mcp_bc/server/infrastructure/__init__.py`

### Acceptance Criteria
- [x] ORM model uses `Mapped[type]` annotations (project standard)
- [x] Inherits `ULIDMixin` + `Base`
- [x] Repository uses SQLAlchemy 2.0 `select()` style
- [x] `save()` handles both insert and update
- [x] `find_by_id` filters by `user_id` (tenant isolation)
- [x] `find_all_by_user` returns list ordered by `created_at desc`
- [x] `count_active_by_user` returns int
- [x] `_to_entity()` static method converts model → domain entity

---

## Task 4: Create Application Layer — Commands

### 4.1: CreateApiKey Command + Handler

**File:** `src/mcp_bc/server/application/commands/create_api_key.py`

```python
import secrets
import bcrypt
from dataclasses import dataclass
from typing import Optional
from src.framework.application.command_bus import Command, CommandHandler

MAX_ACTIVE_KEYS = 10
KEY_PREFIX = "dsm_"

class MaxApiKeysReachedError(Exception): pass

@dataclass
class CreateApiKeyCommand(Command):
    user_id: str
    name: str
    id: Optional[str] = None  # For tests

class CreateApiKeyCommandHandler(CommandHandler[CreateApiKeyCommand]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, command: CreateApiKeyCommand) -> None:
        # 1. Check active key count
        count = self.api_key_repo.count_active_by_user(command.user_id)
        if count >= MAX_ACTIVE_KEYS:
            raise MaxApiKeysReachedError(f"Maximum {MAX_ACTIVE_KEYS} active API keys allowed")

        # 2. Generate raw key: dsm_ + 40 hex chars
        raw_key = KEY_PREFIX + secrets.token_hex(20)

        # 3. Hash with bcrypt
        key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

        # 4. Create entity
        api_key = ApiKey.create(
            user_id=command.user_id,
            key_hash=key_hash,
            name=command.name,
            id=command.id,
        )

        # 5. Save
        self.api_key_repo.save(api_key)
```

**IMPORTANT — Returning the raw key:** Commands return `None` per CQRS rules. The raw key must be accessible to the router. Two options:
- **Option A (recommended):** The router generates the raw key and hash itself, then passes both to the command. The command just validates + saves. The router already has the raw key to return.
- **Option B:** Move key generation to the router, pass `key_hash` into the command.

**Go with Option A:** The router generates the raw key, computes the bcrypt hash, and passes both the raw key and hash to the handler. The handler validates the limit, creates the entity with the hash, and saves. The router returns the raw key in the response.

Adjust the command to accept `key_hash` as a parameter:

```python
@dataclass
class CreateApiKeyCommand(Command):
    user_id: str
    name: str
    key_hash: str      # bcrypt hash, computed by the router
    id: Optional[str] = None
```

Key generation utility (in same file or separate):

```python
def generate_api_key() -> tuple[str, str]:
    """Returns (raw_key, key_hash)."""
    raw_key = "dsm_" + secrets.token_hex(20)
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()
    return raw_key, key_hash
```

### 4.2: RevokeApiKey Command + Handler

**File:** `src/mcp_bc/server/application/commands/revoke_api_key.py`

```python
class ApiKeyNotFoundError(Exception): pass

@dataclass
class RevokeApiKeyCommand(Command):
    key_id: str
    user_id: str

class RevokeApiKeyCommandHandler(CommandHandler[RevokeApiKeyCommand]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, command: RevokeApiKeyCommand) -> None:
        api_key = self.api_key_repo.find_by_id(command.key_id, command.user_id)
        if not api_key:
            raise ApiKeyNotFoundError(f"API key '{command.key_id}' not found")
        api_key.revoke()  # Sets is_active = False, raises if already revoked
        self.api_key_repo.save(api_key)
```

Create `__init__.py`:
- `src/mcp_bc/server/application/__init__.py`
- `src/mcp_bc/server/application/commands/__init__.py`

### Acceptance Criteria
- [x] Both commands inherit from `Command` (`src.framework.application.command_bus`)
- [x] Both handlers inherit from `CommandHandler[T]`
- [x] Both handlers have `handle()` method returning `None`
- [x] `CreateApiKeyCommandHandler` checks active key count, raises `MaxApiKeysReachedError` at 10
- [x] `generate_api_key()` produces `dsm_` + 40 hex chars and bcrypt hash
- [x] `RevokeApiKeyCommandHandler` finds key by id+user_id, calls `revoke()`, saves
- [x] `RevokeApiKeyCommandHandler` raises `ApiKeyNotFoundError` for missing/other-user keys

---

## Task 5: Create Application Layer — Query

**File:** `src/mcp_bc/server/application/queries/list_api_keys.py`

```python
@dataclass
class ListApiKeysQuery(Query):
    user_id: str

class ListApiKeysQueryHandler(QueryHandler[ListApiKeysQuery, list[ApiKey]]):
    def __init__(self, api_key_repo: ApiKeyRepositoryInterface):
        self.api_key_repo = api_key_repo

    def handle(self, query: ListApiKeysQuery) -> list[ApiKey]:
        return self.api_key_repo.find_all_by_user(query.user_id)
```

Create `__init__.py`:
- `src/mcp_bc/server/application/queries/__init__.py`

### Acceptance Criteria
- [x] Query inherits from `Query` (`src.framework.application.query_bus`)
- [x] Handler inherits from `QueryHandler[ListApiKeysQuery, list[ApiKey]]`
- [x] Returns list of `ApiKey` entities (not ORM models)
- [x] Handler delegates to repository

---

## Task 6: Create HTTP Endpoints

### 6.1: Dependencies

**File:** `adapters/http/api/auth/api_keys_dependencies.py`

```python
from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db
from src.mcp_bc.server.infrastructure.repository import ApiKeyRepository

def get_api_key_repo(db: Session = Depends(get_db)) -> ApiKeyRepository:
    return ApiKeyRepository(db)
```

### 6.2: Schemas

**File:** `adapters/http/api/auth/api_keys_schemas.py`

```python
from pydantic import BaseModel, Field
from typing import Optional

class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class ApiKeyResponse(BaseModel):
    id: str
    name: str
    created_at: str
    last_used_at: Optional[str] = None
    is_active: bool

class CreateApiKeyResponse(BaseModel):
    id: str
    name: str
    raw_key: str        # Only returned at creation time
    created_at: str
    is_active: bool
```

### 6.3: Router

**File:** `adapters/http/api/auth/api_keys_router.py`

Three endpoints:

**POST `/api/v1/auth/api-keys`** — Create API key
- Auth: `require_role(UserRole.EMPLOYEE)` (any authenticated user)
- Generate raw key + bcrypt hash in router
- Instantiate `CreateApiKeyCommandHandler`, call `handle()`
- On success: fetch the created key via query, return `CreateApiKeyResponse` with `raw_key`
- Catch `MaxApiKeysReachedError` → 409 Conflict
- Catch `ValueError` (name validation) → 422

**GET `/api/v1/auth/api-keys`** — List user's API keys
- Auth: `require_role(UserRole.EMPLOYEE)`
- Instantiate `ListApiKeysQueryHandler`, call `handle()`
- Return list of `ApiKeyResponse` (no raw key, no hash)

**DELETE `/api/v1/auth/api-keys/{key_id}`** — Revoke API key
- Auth: `require_role(UserRole.EMPLOYEE)`
- Instantiate `RevokeApiKeyCommandHandler`, call `handle()`
- Catch `ApiKeyNotFoundError` → 404
- Catch `ApiKeyAlreadyRevokedError` → 409
- Return 204 No Content

### 6.4: Register Router

**File:** `app.py` (or wherever routers are registered)

Add: `app.include_router(api_keys_router.router)`

### Acceptance Criteria
- [x] All 3 endpoints under `/api/v1/auth/api-keys`
- [x] POST returns raw key only once in `CreateApiKeyResponse`
- [x] GET never returns `raw_key` or `key_hash`
- [x] DELETE returns 204 on success
- [x] All endpoints require authentication (any role)
- [x] Error responses use correct HTTP status codes (409, 404, 422)
- [x] Dependencies file provides `get_api_key_repo`
- [x] Router registered in `app.py`
- [x] Responses wrapped in `{"data": ...}` (project convention)

---

## Task 7: Unit Tests

**File:** `tests/unit/mcp_bc/server/application/commands/test_create_api_key.py`

Test cases:
- [x] `test_create_api_key_success` — Happy path, verify `repo.save` called
- [x] `test_create_api_key_max_keys_reached` — 10 active keys, raises `MaxApiKeysReachedError`
- [x] `test_create_api_key_validates_name` — Empty name raises `ValueError`

**File:** `tests/unit/mcp_bc/server/application/commands/test_revoke_api_key.py`

Test cases:
- [x] `test_revoke_api_key_success` — Happy path, verify `repo.save` called with `is_active=False`
- [x] `test_revoke_api_key_not_found` — Key doesn't exist, raises `ApiKeyNotFoundError`
- [x] `test_revoke_api_key_already_revoked` — Key already revoked, raises `ApiKeyAlreadyRevokedError`
- [x] `test_revoke_api_key_other_user` — Key belongs to different user, raises `ApiKeyNotFoundError`

**File:** `tests/unit/mcp_bc/server/application/queries/test_list_api_keys.py`

Test cases:
- [x] `test_list_api_keys_returns_all` — Returns list of keys from repo
- [x] `test_list_api_keys_empty` — Returns empty list when no keys

**File:** `tests/unit/mcp_bc/server/domain/test_entities.py`

Test cases:
- [x] `test_api_key_create` — Factory method creates valid entity
- [x] `test_api_key_create_validates_name` — Empty name raises ValueError
- [x] `test_api_key_create_name_too_long` — Name > 100 chars raises ValueError
- [x] `test_api_key_revoke` — Sets `is_active` to False
- [x] `test_api_key_revoke_already_revoked` — Raises `ApiKeyAlreadyRevokedError`

Create `__init__.py` files:
- `tests/unit/mcp_bc/__init__.py`
- `tests/unit/mcp_bc/server/__init__.py`
- `tests/unit/mcp_bc/server/application/__init__.py`
- `tests/unit/mcp_bc/server/application/commands/__init__.py`
- `tests/unit/mcp_bc/server/application/queries/__init__.py`
- `tests/unit/mcp_bc/server/domain/__init__.py`

### Acceptance Criteria
- [x] All unit tests use `MagicMock` for repository (no DB)
- [x] All tests follow project pattern: class-based, `test_` prefix
- [x] Happy paths and error paths covered
- [x] `make test` passes with no regressions (459 tests)

---

## Task 8: Integration Tests

**File:** `tests/integration/test_api_keys_endpoints.py`

Test cases:
- [x] `test_create_api_key` — POST returns 201, response contains `raw_key` starting with `dsm_` (44 chars total)
- [x] `test_create_api_key_returns_key_once` — POST returns raw_key, subsequent GET does not include raw_key
- [x] `test_list_api_keys` — GET returns list with `name`, `created_at`, `is_active`, no `key_hash`
- [x] `test_list_api_keys_empty` — GET returns empty list for user with no keys
- [x] `test_revoke_api_key` — DELETE returns 204, subsequent GET shows `is_active: false`
- [x] `test_revoke_nonexistent_key` — DELETE returns 404
- [x] `test_revoke_already_revoked` — DELETE returns 409
- [x] `test_max_10_keys` — Create 10 keys (201), 11th returns 409
- [x] `test_tenant_isolation` — User A cannot revoke User B's key (returns 404)
- [x] `test_unauthenticated_rejected` — No auth token returns 401/403

Use fixtures from `tests/conftest.py`: `client`, `auth_as`, `employee_user`, `admin_user`, `make_user`.

### Acceptance Criteria
- [x] All integration tests hit real PostgreSQL via `TestClient`
- [x] Use `auth_as()` fixture for authentication
- [x] Tests verify response structure (`{"data": ...}`)
- [x] Tenant isolation verified
- [x] `make test-integration` passes with no regressions (137 tests)

---

## Task 9: Verify & Run Full Test Suite

- [x] `make test` — All unit tests pass (459 passed)
- [x] `make test-integration` — All integration tests pass (137 passed)
- [x] `make lint` — mypy clean (0 issues in 178 files), flake8 only pre-existing E501s
- [x] `make db-upgrade` — Migration applies cleanly

---

## Implementation Order

1. Task 1 (Migration) — Foundation, everything needs the table
2. Task 2 (Domain) — Entity + repository interface
3. Task 3 (Infrastructure) — ORM model + repository implementation
4. Task 4 (Commands) — CreateApiKey + RevokeApiKey
5. Task 5 (Query) — ListApiKeys
6. Task 6 (HTTP) — Router + schemas + register
7. Task 7 (Unit Tests) — Can start after Task 4-5
8. Task 8 (Integration Tests) — Needs all of Tasks 1-6
9. Task 9 (Verification) — Final check

---

## Post-Implementation Checklist

- [x] All 10 acceptance criteria from requirements.md verified
- [x] `make test` passes (459 unit tests)
- [x] `make test-integration` passes (137 integration tests)
- [x] `make lint` passes (mypy clean)
- [x] Update `docs/epics/e35-mcp-server/slicing.md` — Mark F0 status as "Done"
