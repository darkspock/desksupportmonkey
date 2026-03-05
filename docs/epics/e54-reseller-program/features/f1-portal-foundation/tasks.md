# Implementation Tasks: Portal Foundation (F1)

**Requirement:** [requirements.md](requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-03-02
**Total Tasks:** 27
**Estimated Complexity:** L

## Summary

| Phase | Tasks | Complexity |
|-------|-------|------------|
| Domain - Enums | 1 | S |
| Domain - Exceptions | 1 | S |
| Domain - Entities | 1 | M |
| Domain - Interfaces | 1 | S |
| Infrastructure - Migrations | 1 | S |
| Infrastructure - Models | 1 | S |
| Infrastructure - Repositories | 1 | M |
| Collateral - JWT | 2 | S |
| Application - DTOs | 1 | S |
| Application - Commands | 3 | S-M |
| Application - Queries | 3 | S |
| Application - Services | 3 | M |
| HTTP - Schemas & Mappers | 2 | S |
| HTTP - Dependencies | 1 | M |
| HTTP - Routers | 2 | M |
| Configuration | 1 | S |
| Tests - Unit | 2 | M |
| Tests - Integration | 2 | M |

---

## Phase 1: Domain Layer

### TASK-001: Create ResellerStatus Enum

**Phase:** Domain - Enums
**Complexity:** S
**Dependencies:** None

**File:** `src/reseller_bc/reseller/domain/enums.py`

**Implementation:**
```python
from enum import Enum

class ResellerStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"
```

**Acceptance Criteria:**
- [ ] Enum with 3 values: `active`, `suspended`, `deactivated`
- [ ] Inherits from `str, Enum` for JSON serialization

---

### TASK-002: Create Domain Exceptions

**Phase:** Domain - Exceptions
**Complexity:** S
**Dependencies:** None

**File:** `src/reseller_bc/reseller/domain/exceptions.py`

**Implementation:** Create all 9 exception classes as specified in design:

| Exception | When Raised |
|-----------|-------------|
| `ResellerNotFoundException` | Reseller not found by ID/email/provider |
| `ResellerNotRegisteredException` | OAuth login with email not in resellers table |
| `ResellerDeactivatedException` | Deactivated reseller tries to log in |
| `ResellerSuspendedException` | Suspended reseller tries write operation |
| `ResellerAlreadyExistsException` | Create with duplicate email |
| `InvalidCommissionRateException` | commission_pct outside 0-100 |
| `InvalidMinPayoutException` | min_payout_cents <= 0 |
| `ReferralCodeCollisionException` | Generated referral code already exists |
| `ResellerOAuthProviderAlreadyLinkedError` | Provider ID already linked to different reseller |

**Acceptance Criteria:**
- [ ] All 9 exceptions created as plain `Exception` subclasses
- [ ] Each has a descriptive default message

---

### TASK-003: Create Reseller Entity

**Phase:** Domain - Entities
**Complexity:** M
**Dependencies:** TASK-001, TASK-002

**File:** `src/reseller_bc/reseller/domain/entities.py`

**Implementation:** `@dataclass` entity following the User entity pattern.

**Fields:**
- `id: str` (ULID)
- `email: str`
- `name: str`
- `google_id: Optional[str]`
- `microsoft_id: Optional[str]`
- `avatar_url: Optional[str]`
- `company_name: Optional[str]`
- `tax_id: Optional[str]`
- `commission_pct: int`
- `min_payout_cents: int`
- `referral_code: str`
- `status: ResellerStatus`
- `created_at: datetime`
- `updated_at: Optional[datetime]`

**Factory method `create(email, name, commission_pct, min_payout_cents)`:**
- Validates email (not empty, contains `@`)
- Validates name (not empty)
- Validates commission_pct (0-100) → raises `InvalidCommissionRateException`
- Validates min_payout_cents (> 0) → raises `InvalidMinPayoutException`
- Auto-generates `id` via `str(ulid.new())`
- Auto-generates `referral_code` (8-char alphanumeric, URL-safe)
- Sets `status = ResellerStatus.ACTIVE`

**Business methods:**
- `update_profile(company_name: Optional[str], tax_id: Optional[str])` — reseller self-edit
- `update_settings(commission_pct: Optional[int], min_payout_cents: Optional[int], status: Optional[ResellerStatus])` — super admin edit, validates ranges
- `suspend()` — ACTIVE → SUSPENDED
- `activate()` — SUSPENDED → ACTIVE
- `deactivate()` — ACTIVE|SUSPENDED → DEACTIVATED (terminal)
- `link_google(google_id: str)` — raises `ResellerOAuthProviderAlreadyLinkedError` if already linked to different ID
- `link_microsoft(microsoft_id: str)` — same

**Acceptance Criteria:**
- [ ] `@dataclass` with all fields from design
- [ ] Constructor for repository hydration only (no validation)
- [ ] `create()` factory method with validation
- [ ] `update_profile()` only modifies company_name and tax_id
- [ ] `update_settings()` validates commission_pct and min_payout_cents ranges
- [ ] State transitions enforce valid paths (see state machine in design)
- [ ] `link_google()`/`link_microsoft()` guard against re-linking to different ID
- [ ] Referral code generation produces 8-char URL-safe alphanumeric string

---

### TASK-004: Create ResellerRepositoryInterface

**Phase:** Domain - Interfaces
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/reseller_bc/reseller/domain/repository.py`

**Implementation:** ABC interface with all methods from design.

**Methods:**
```python
class ResellerRepositoryInterface(ABC):
    @abstractmethod
    def save(self, reseller: Reseller) -> None: ...

    @abstractmethod
    def get_by_id(self, reseller_id: str) -> Optional[Reseller]: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Reseller]: ...

    @abstractmethod
    def find_by_google_id(self, google_id: str) -> Optional[Reseller]: ...

    @abstractmethod
    def find_by_microsoft_id(self, microsoft_id: str) -> Optional[Reseller]: ...

    @abstractmethod
    def find_by_referral_code(self, code: str) -> Optional[Reseller]: ...

    @abstractmethod
    def list_all(self, offset: int, limit: int) -> list[Reseller]: ...

    @abstractmethod
    def count_all(self) -> int: ...

    @abstractmethod
    def exists_by_email(self, email: str) -> bool: ...

    @abstractmethod
    def exists_by_referral_code(self, code: str) -> bool: ...
```

**Acceptance Criteria:**
- [ ] ABC with `@abstractmethod` for all 10 methods
- [ ] Uses domain types only (Reseller entity, str, Optional, list)
- [ ] No SQLAlchemy imports

---

## Phase 2: Infrastructure Layer

### TASK-005: Create Alembic Migration for `resellers` Table

**Phase:** Infrastructure - Migrations
**Complexity:** S
**Dependencies:** TASK-003

**File:** `alembic/versions/XXX_create_resellers_table.py`

**Schema (from design):**
```sql
CREATE TABLE resellers (
    id VARCHAR(26) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    microsoft_id VARCHAR(255) UNIQUE,
    avatar_url VARCHAR(500),
    company_name VARCHAR(255),
    tax_id VARCHAR(100),
    commission_pct INTEGER NOT NULL DEFAULT 20,
    min_payout_cents INTEGER NOT NULL DEFAULT 5000,
    referral_code VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

**Indexes:** `ix_resellers_email`, `ix_resellers_google_id`, `ix_resellers_microsoft_id`, `ix_resellers_referral_code`

**Acceptance Criteria:**
- [ ] All columns from design with correct types and constraints
- [ ] Unique constraints on email, google_id, microsoft_id, referral_code
- [ ] All 4 indexes created
- [ ] Reversible (downgrade drops table)
- [ ] `make db-upgrade` succeeds

---

### TASK-006: Create ResellerModel

**Phase:** Infrastructure - Models
**Complexity:** S
**Dependencies:** TASK-005

**File:** `src/reseller_bc/reseller/infrastructure/models.py`

**Implementation:** SQLAlchemy 2.0 model with `ULIDMixin, TimestampMixin, Base`.

```python
class ResellerModel(ULIDMixin, TimestampMixin, Base):
    __tablename__ = "resellers"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    microsoft_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True, index=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    commission_pct: Mapped[int] = mapped_column(Integer, default=20)
    min_payout_cents: Mapped[int] = mapped_column(Integer, default=5000)
    referral_code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")
```

**Acceptance Criteria:**
- [ ] Inherits `ULIDMixin, TimestampMixin, Base`
- [ ] SQLAlchemy 2.0 `Mapped[T] = mapped_column()` syntax only
- [ ] All columns match migration schema
- [ ] No bare `Column()` usage

---

### TASK-007: Create ResellerRepository Implementation

**Phase:** Infrastructure - Repositories
**Complexity:** M
**Dependencies:** TASK-004, TASK-006

**File:** `src/reseller_bc/reseller/infrastructure/repository.py`

**Implementation:** Follows `UserRepository` pattern — session injected, `_to_entity()` static method, `save()` with upsert, `session.flush()`.

**Methods to implement:**
- `save(reseller)` — upsert pattern (select existing → update fields or add new)
- `get_by_id(reseller_id)` — select by ID, return entity or None
- `find_by_email(email)` — select by email
- `find_by_google_id(google_id)` — select by google_id
- `find_by_microsoft_id(microsoft_id)` — select by microsoft_id
- `find_by_referral_code(code)` — select by referral_code
- `list_all(offset, limit)` — paginated select with offset/limit
- `count_all()` — count query
- `exists_by_email(email)` — exists check
- `exists_by_referral_code(code)` — exists check
- `_to_entity(model)` — static method, ResellerModel → Reseller

**Acceptance Criteria:**
- [ ] Implements `ResellerRepositoryInterface`
- [ ] `session: Session` injected via constructor
- [ ] `_to_entity()` static method converts model → entity
- [ ] `save()` uses upsert pattern with `session.flush()`
- [ ] All 10 interface methods implemented
- [ ] Uses SQLAlchemy 2.0 `select()` style queries

---

## Phase 3: Collateral Changes (JWT)

### TASK-008: Modify JWTService to Support `type` Claim

**Phase:** Collateral
**Complexity:** S
**Dependencies:** None (can be done in parallel with domain)

**File:** `core/jwt.py`

**Changes:**
- Add optional `type: str = "user"` parameter to `create_token()`
- Include `"type": type` in the JWT payload
- No changes to `decode_token()` — the `type` is just another field in the decoded dict

```python
def create_token(
    self,
    user_id: str,
    company_id: Optional[str],
    role: str,
    type: str = "user",  # NEW — default "user" for backward compat
) -> str:
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "role": role,
        "type": type,  # NEW
        "exp": ...,
        "iat": ...,
    }
```

**Acceptance Criteria:**
- [ ] `create_token()` accepts optional `type` parameter (default `"user"`)
- [ ] `type` included in JWT payload
- [ ] Existing callers unaffected (backward compatible)
- [ ] Existing tokens without `type` still decode correctly

---

### TASK-009: Add JWT Type Check to `get_current_user()`

**Phase:** Collateral
**Complexity:** S
**Dependencies:** TASK-008

**File:** `adapters/http/api/auth/dependencies.py`

**Changes:** In `get_current_user()`, after decoding the token, check:
```python
token_type = payload.get("type", "user")  # default "user" for old tokens
if token_type != "user":
    raise HTTPException(status_code=401, detail="Invalid token type")
```

**Acceptance Criteria:**
- [ ] Reseller JWT (type=reseller) rejected with 401 on user endpoints
- [ ] Tokens without `type` field treated as `"user"` (backward compatible)
- [ ] Existing user auth flow unchanged

---

## Phase 4: Application Layer

### TASK-010: Create DTOs

**Phase:** Application - DTOs
**Complexity:** S
**Dependencies:** TASK-003

**File:** `src/reseller_bc/reseller/application/dtos.py`

**DTOs to create:**

**ResellerDto:**
```python
@dataclass
class ResellerDto:
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    company_name: Optional[str]
    tax_id: Optional[str]
    commission_pct: int
    min_payout_cents: int
    referral_code: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_entity(cls, entity: Reseller) -> "ResellerDto": ...
```

**ResellerDashboardDto:**
```python
@dataclass
class ResellerDashboardDto:
    reseller_id: str
    name: str
    referral_code: str
    status: str
    client_count: int          # 0 in F1
    total_commissions_cents: int  # 0 in F1
    available_balance_cents: int  # 0 in F1
    pending_payout_cents: int    # 0 in F1
```

**ResellerListDto:**
```python
@dataclass
class ResellerListDto:
    items: list[ResellerDto]
    total: int
```

**Acceptance Criteria:**
- [ ] All 3 DTOs as `@dataclass`
- [ ] `ResellerDto.from_entity()` factory method
- [ ] Fields match design exactly

---

### TASK-011: Create CreateResellerCommand + Handler

**Phase:** Application - Commands
**Complexity:** M
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/commands/create_reseller.py`

**Command fields:** `id: str`, `email: str`, `name: str`, `commission_pct: int`, `min_payout_cents: int`

**Handler logic:**
1. Check `exists_by_email(email)` → raise `ResellerAlreadyExistsException`
2. Call `Reseller.create(email, name, commission_pct, min_payout_cents)` with provided `id`
3. Check `exists_by_referral_code(reseller.referral_code)` → retry with new code (max 3 times), raise `ReferralCodeCollisionException` on failure
4. Call `repo.save(reseller)`

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command + Handler in same file
- [ ] Handler returns `None`
- [ ] Validates email uniqueness
- [ ] Handles referral code collision with retry
- [ ] Uses repository interface (not implementation)

---

### TASK-012: Create UpdateResellerCommand + Handler

**Phase:** Application - Commands
**Complexity:** S
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/commands/update_reseller.py`

**Command fields:** `reseller_id: str`, `commission_pct: Optional[int]`, `min_payout_cents: Optional[int]`, `status: Optional[str]`

**Handler logic:**
1. Load reseller by ID → raise `ResellerNotFoundException` if not found
2. Call `reseller.update_settings(commission_pct, min_payout_cents, status)`
3. Call `repo.save(reseller)`

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command + Handler in same file
- [ ] Handler returns `None`
- [ ] Raises `ResellerNotFoundException` if not found

---

### TASK-013: Create UpdateResellerProfileCommand + Handler

**Phase:** Application - Commands
**Complexity:** S
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/commands/update_reseller_profile.py`

**Command fields:** `reseller_id: str`, `company_name: Optional[str]`, `tax_id: Optional[str]`

**Handler logic:**
1. Load reseller by ID → raise `ResellerNotFoundException`
2. Call `reseller.update_profile(company_name, tax_id)`
3. Call `repo.save(reseller)`

**Acceptance Criteria:**
- [ ] Inherits from `Command` / `CommandHandler`
- [ ] Command + Handler in same file
- [ ] Handler returns `None`
- [ ] Only modifies company_name and tax_id (not commission_pct, status, etc.)

---

### TASK-014: Create GetResellerByIdQuery + Handler

**Phase:** Application - Queries
**Complexity:** S
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/queries/get_reseller_by_id.py`

**Query fields:** `reseller_id: str`
**Returns:** `Optional[ResellerDto]`

**Handler logic:**
1. Load reseller by ID from repository
2. Return `ResellerDto.from_entity(reseller)` or `None`

**Acceptance Criteria:**
- [ ] Inherits from `Query` / `QueryHandler`
- [ ] Query + Handler in same file
- [ ] Returns `Optional[ResellerDto]`

---

### TASK-015: Create ListResellersQuery + Handler

**Phase:** Application - Queries
**Complexity:** S
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/queries/list_resellers.py`

**Query fields:** `offset: int = 0`, `limit: int = 50`
**Returns:** `ResellerListDto`

**Handler logic:**
1. `items = repo.list_all(offset, limit)` → map to `ResellerDto` list
2. `total = repo.count_all()`
3. Return `ResellerListDto(items=items, total=total)`

**Acceptance Criteria:**
- [ ] Inherits from `Query` / `QueryHandler`
- [ ] Query + Handler in same file
- [ ] Returns paginated `ResellerListDto`

---

### TASK-016: Create GetResellerDashboardQuery + Handler

**Phase:** Application - Queries
**Complexity:** S
**Dependencies:** TASK-004, TASK-010

**File:** `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py`

**Query fields:** `reseller_id: str`
**Returns:** `ResellerDashboardDto`

**Handler logic:**
1. Load reseller by ID → raise `ResellerNotFoundException` if not found
2. Return `ResellerDashboardDto` with placeholder zeros for client_count, total_commissions_cents, available_balance_cents, pending_payout_cents (real data comes in F2/F4/F5)

**Acceptance Criteria:**
- [ ] Inherits from `Query` / `QueryHandler`
- [ ] Returns `ResellerDashboardDto` with zeros for financial fields
- [ ] Raises `ResellerNotFoundException` if reseller not found

---

### TASK-017: Create ResellerOAuthLoginService

**Phase:** Application - Services
**Complexity:** M
**Dependencies:** TASK-004, TASK-002

**File:** `src/reseller_bc/reseller/application/services/reseller_oauth_login.py`

**Implementation:** Shared OAuth logic, reuses `OAuthUserInfo` dataclass pattern.

**Constructor dependencies:** `ResellerRepositoryInterface`, `JWTService`

**Method `login(info: OAuthUserInfo) -> str`:**
1. Find reseller by provider ID (`google_id` / `microsoft_id`)
2. Fallback: find by email
3. If not found: raise `ResellerNotRegisteredException`
4. If `status == DEACTIVATED`: raise `ResellerDeactivatedException`
5. Link provider if not yet linked (guard against re-linking to different ID)
6. Update avatar if provided
7. Save reseller
8. Return `jwt_service.create_token(reseller.id, None, "reseller", type="reseller")`

**Acceptance Criteria:**
- [ ] Plain class (not Command/Query — it's a service that returns a JWT string)
- [ ] Constructor-injected dependencies
- [ ] Handles find-by-provider → fallback-to-email flow
- [ ] Raises `ResellerNotRegisteredException` for unknown emails (no auto-creation)
- [ ] Raises `ResellerDeactivatedException` for deactivated resellers
- [ ] Links OAuth provider on first login
- [ ] JWT created with `type="reseller"`

---

### TASK-018: Create ResellerGoogleOAuthService

**Phase:** Application - Services
**Complexity:** S
**Dependencies:** TASK-017

**File:** `src/reseller_bc/reseller/application/services/reseller_google_oauth.py`

**Implementation:** Follows `GoogleOAuthLoginService` pattern from `auth_bc`.

**Constructor dependencies:** `ResellerRepositoryInterface`, `JWTService`, `OAuthSettings`

**Method `handle(request: GoogleOAuthLoginRequest) -> str`:**
1. Check Google OAuth configured → raise `GoogleNotConfiguredError`
2. Verify ID token via `GoogleTokenVerifier`
3. Build `OAuthUserInfo(email, name, provider_id, provider_field="google_id")`
4. Delegate to `ResellerOAuthLoginService.login(info)`

**Acceptance Criteria:**
- [ ] Reuses `GoogleTokenVerifier` from `auth_bc`
- [ ] Delegates to `ResellerOAuthLoginService` for reseller lookup
- [ ] Raises `GoogleNotConfiguredError` if not configured
- [ ] Raises `GoogleTokenInvalidError` / `GoogleEmailNotVerified` on verification failure

---

### TASK-019: Create ResellerMicrosoftOAuthService

**Phase:** Application - Services
**Complexity:** S
**Dependencies:** TASK-017

**File:** `src/reseller_bc/reseller/application/services/reseller_microsoft_oauth.py`

**Implementation:** Same pattern as TASK-018 but for Microsoft.

**Constructor dependencies:** `ResellerRepositoryInterface`, `JWTService`, `OAuthSettings`

**Method `handle(request: MicrosoftOAuthLoginRequest) -> str`:**
1. Check Microsoft OAuth configured
2. Verify token via `MicrosoftTokenVerifier`
3. Build `OAuthUserInfo(email, name, provider_id, provider_field="microsoft_id")`
4. Delegate to `ResellerOAuthLoginService.login(info)`

**Acceptance Criteria:**
- [ ] Reuses `MicrosoftTokenVerifier` from `auth_bc`
- [ ] Delegates to `ResellerOAuthLoginService` for reseller lookup
- [ ] Raises provider-specific errors on verification failure

---

## Phase 5: HTTP Layer

### TASK-020: Create Request/Response Schemas

**Phase:** HTTP - Schemas
**Complexity:** S
**Dependencies:** None (can be done in parallel with domain)

**File:** `adapters/http/api/reseller/schemas.py`

**Schemas:**

```python
# Auth
class OAuthLoginRequest(BaseModel):
    id_token: str

class TokenResponse(BaseModel):
    access_token: str

# Reseller profile
class ResellerResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    company_name: Optional[str]
    tax_id: Optional[str]
    commission_pct: int
    min_payout_cents: int
    referral_code: str
    status: str
    created_at: str
    updated_at: Optional[str]

class UpdateResellerProfileRequest(BaseModel):
    company_name: Optional[str] = None
    tax_id: Optional[str] = None

# Dashboard
class ResellerDashboardResponse(BaseModel):
    reseller_id: str
    name: str
    referral_code: str
    status: str
    client_count: int
    total_commissions_cents: int
    available_balance_cents: int
    pending_payout_cents: int

# Admin
class CreateResellerRequest(BaseModel):
    email: str
    name: str
    commission_pct: int
    min_payout_cents: int

class UpdateResellerSettingsRequest(BaseModel):
    commission_pct: Optional[int] = None
    min_payout_cents: Optional[int] = None
    status: Optional[str] = None

class ResellerListResponse(BaseModel):
    items: list[ResellerResponse]
    total: int
```

**Acceptance Criteria:**
- [ ] All schemas use primitives only (str, int, Optional[str])
- [ ] No `field_validator` or `ConfigDict`
- [ ] Matches design endpoint specifications

---

### TASK-021: Create ResellerMapper

**Phase:** HTTP - Mappers
**Complexity:** S
**Dependencies:** TASK-010, TASK-020

**File:** `adapters/http/api/reseller/mappers.py`

**Methods:**
```python
class ResellerMapper:
    @staticmethod
    def dto_to_response(dto: ResellerDto) -> ResellerResponse: ...

    @staticmethod
    def dto_to_dashboard_response(dto: ResellerDashboardDto) -> ResellerDashboardResponse: ...

    @staticmethod
    def dto_to_list_response(dto: ResellerListDto) -> ResellerListResponse: ...
```

**Acceptance Criteria:**
- [ ] Explicit conversion (no magic `model_validate`)
- [ ] Converts datetime → ISO string, enum → string value

---

### TASK-022: Create Reseller Dependencies

**Phase:** HTTP - Dependencies
**Complexity:** M
**Dependencies:** TASK-007, TASK-008, TASK-009

**File:** `adapters/http/api/reseller/dependencies.py`

**Dependencies to create:**

**`get_current_reseller()`:**
1. Extract Bearer token via `HTTPBearer`
2. Decode JWT via `JWTService`
3. Check `payload.get("type") == "reseller"` → 401 if not
4. Load reseller by `payload["sub"]` from repository
5. Check `status != DEACTIVATED` → 401 if deactivated
6. Return `Reseller` entity

**`require_active_reseller()`:**
- Wraps `get_current_reseller()`, raises 403 if `status == SUSPENDED`

**Factory functions:**
- `get_reseller_repo(db) -> ResellerRepository`
- `get_reseller_google_oauth_service(db) -> ResellerGoogleOAuthService`
- `get_reseller_microsoft_oauth_service(db) -> ResellerMicrosoftOAuthService`

**Acceptance Criteria:**
- [ ] `get_current_reseller()` validates JWT type claim
- [ ] Deactivated resellers get 401
- [ ] `require_active_reseller()` gives suspended resellers 403
- [ ] All factory functions use `Depends(get_db)` for session

---

### TASK-023: Create Reseller Portal Router

**Phase:** HTTP - Routers
**Complexity:** M
**Dependencies:** TASK-017, TASK-018, TASK-019, TASK-020, TASK-021, TASK-022

**File:** `adapters/http/api/reseller/routers.py`

**Router:** `APIRouter(prefix="/api/v1/reseller", tags=["reseller"])`

**Endpoints:**

| Method | Route | Handler/Service | Auth | Error Mapping |
|--------|-------|-----------------|------|---------------|
| POST | `/auth/google` | ResellerGoogleOAuthService | None | GoogleNotConfigured→501, TokenInvalid→401, NotRegistered→401, Deactivated→401 |
| POST | `/auth/microsoft` | ResellerMicrosoftOAuthService | None | MicrosoftNotConfigured→501, TokenInvalid→401, NotRegistered→401, Deactivated→401 |
| GET | `/me` | GetResellerByIdQuery | `get_current_reseller` | ResellerNotFound→404 |
| PUT | `/profile` | UpdateResellerProfileCommand | `require_active_reseller` | ResellerNotFound→404, Suspended→403 |
| GET | `/dashboard` | GetResellerDashboardQuery | `get_current_reseller` | ResellerNotFound→404 |

**Response envelope:** All responses wrapped in `{"data": ...}`

**Acceptance Criteria:**
- [ ] All 5 endpoints from design implemented
- [ ] Auth endpoints require no authentication
- [ ] Profile/dashboard endpoints use `get_current_reseller`
- [ ] Profile update uses `require_active_reseller` (403 for suspended)
- [ ] ALL domain exceptions caught and mapped to HTTP status codes
- [ ] Responses wrapped in `{"data": ...}` envelope

---

### TASK-024: Create Admin Reseller Router

**Phase:** HTTP - Routers
**Complexity:** M
**Dependencies:** TASK-011, TASK-012, TASK-014, TASK-015, TASK-020, TASK-021

**File:** `adapters/http/api/admin/reseller_routers.py`

**Router:** `APIRouter(prefix="/api/v1/admin/resellers", tags=["admin-resellers"])`

**Endpoints:**

| Method | Route | Handler | Auth | Error Mapping |
|--------|-------|---------|------|---------------|
| POST | `/` | CreateResellerCommand | `require_role(SUPER_ADMIN)` | AlreadyExists→409, InvalidCommission→422, InvalidMinPayout→422, ReferralCodeCollision→500 |
| GET | `/` | ListResellersQuery | `require_role(SUPER_ADMIN)` | None |
| GET | `/{reseller_id}` | GetResellerByIdQuery | `require_role(SUPER_ADMIN)` | NotFound→404 |
| PATCH | `/{reseller_id}` | UpdateResellerCommand | `require_role(SUPER_ADMIN)` | NotFound→404, InvalidCommission→422, InvalidMinPayout→422 |

**Response envelope:** All responses wrapped in `{"data": ...}`

**Acceptance Criteria:**
- [ ] All 4 endpoints from design implemented
- [ ] All endpoints require `SUPER_ADMIN` role
- [ ] ALL domain exceptions caught and mapped to HTTP status codes
- [ ] Create returns 201
- [ ] Responses wrapped in `{"data": ...}` envelope

---

## Phase 6: Configuration

### TASK-025: Register Routers in `app.py`

**Phase:** Configuration
**Complexity:** S
**Dependencies:** TASK-023, TASK-024

**File:** `app.py`

**Changes:**
```python
from adapters.http.api.reseller.routers import router as reseller_router
from adapters.http.api.admin.reseller_routers import router as admin_reseller_router

application.include_router(reseller_router)
application.include_router(admin_reseller_router)
```

**Acceptance Criteria:**
- [ ] Both routers registered
- [ ] Application starts without errors
- [ ] Endpoints appear in OpenAPI docs

---

## Phase 7: Tests

### TASK-026: Unit Tests

**Phase:** Tests - Unit
**Complexity:** M
**Dependencies:** TASK-003, TASK-011, TASK-012, TASK-013, TASK-017

**Files:**
- `tests/unit/reseller_bc/reseller/domain/test_entities.py`
- `tests/unit/reseller_bc/reseller/application/commands/test_create_reseller.py`
- `tests/unit/reseller_bc/reseller/application/commands/test_update_reseller.py`
- `tests/unit/reseller_bc/reseller/application/commands/test_update_reseller_profile.py`
- `tests/unit/reseller_bc/reseller/application/services/test_reseller_oauth_login.py`
- `tests/unit/reseller_bc/reseller/application/queries/test_get_reseller_dashboard.py`

**Test cases — Entity:**
- `test_create_reseller_happy_path` — valid inputs
- `test_create_reseller_invalid_email` — raises on empty/malformed
- `test_create_reseller_invalid_commission_pct` — raises on <0 or >100
- `test_create_reseller_invalid_min_payout` — raises on <=0
- `test_update_profile` — only company_name and tax_id change
- `test_update_settings` — commission_pct and min_payout_cents validated
- `test_suspend_from_active` — ACTIVE → SUSPENDED
- `test_activate_from_suspended` — SUSPENDED → ACTIVE
- `test_deactivate_from_active` — ACTIVE → DEACTIVATED
- `test_deactivate_from_suspended` — SUSPENDED → DEACTIVATED
- `test_cannot_activate_from_deactivated` — terminal state
- `test_link_google` — links provider ID
- `test_link_google_already_linked_different` — raises error

**Test cases — CreateResellerCommandHandler:**
- `test_create_success` — saves reseller
- `test_create_duplicate_email` — raises `ResellerAlreadyExistsException`
- `test_create_referral_code_collision_retries` — retries on collision

**Test cases — UpdateResellerCommandHandler:**
- `test_update_settings_success`
- `test_update_not_found` — raises `ResellerNotFoundException`

**Test cases — UpdateResellerProfileCommandHandler:**
- `test_update_profile_success`

**Test cases — ResellerOAuthLoginService:**
- `test_login_existing_reseller_by_provider` — found by google_id
- `test_login_existing_reseller_by_email` — fallback to email
- `test_login_not_registered` — raises `ResellerNotRegisteredException`
- `test_login_deactivated` — raises `ResellerDeactivatedException`
- `test_login_suspended_allowed` — suspended can login
- `test_login_links_provider_on_first_use`

**Acceptance Criteria:**
- [ ] All entity factory + business method tests
- [ ] All command handler tests with MagicMock
- [ ] OAuth login service tests with MagicMock
- [ ] `make test` passes

---

### TASK-027: Integration Tests

**Phase:** Tests - Integration
**Complexity:** M
**Dependencies:** TASK-023, TASK-024, TASK-025

**Files:**
- `tests/integration/test_reseller_auth_endpoints.py`
- `tests/integration/test_reseller_profile_endpoints.py`
- `tests/integration/test_admin_reseller_endpoints.py`
- `tests/integration/test_jwt_type_isolation.py`

**Test cases — Reseller Auth:**
- `test_google_oauth_login_success` (may need mocking of GoogleTokenVerifier)
- `test_google_oauth_not_registered` → 401
- `test_google_oauth_deactivated` → 401

**Test cases — Reseller Profile:**
- `test_get_me` — returns reseller data
- `test_update_profile` — updates company_name and tax_id
- `test_update_profile_suspended` → 403
- `test_get_dashboard` — returns dashboard with zeros
- `test_reseller_jwt_required` — user JWT rejected → 401

**Test cases — Admin CRUD:**
- `test_create_reseller` → 201
- `test_create_reseller_duplicate_email` → 409
- `test_list_resellers` — paginated response
- `test_get_reseller_by_id` — returns reseller
- `test_get_reseller_not_found` → 404
- `test_update_reseller_settings` — modifies commission_pct/min_payout_cents/status
- `test_non_super_admin_rejected` → 403

**Test cases — JWT Isolation:**
- `test_reseller_token_rejected_on_user_endpoints` → 401
- `test_user_token_rejected_on_reseller_endpoints` → 401
- `test_old_token_without_type_works_on_user_endpoints` (backward compat)

**Acceptance Criteria:**
- [ ] All endpoint happy paths tested
- [ ] Error paths tested (401, 403, 404, 409, 422)
- [ ] JWT type isolation verified
- [ ] `make test-integration` passes

---

## Dependency Graph

```
TASK-001 (Enum) ─────────────────┐
TASK-002 (Exceptions) ───────────┤
                                 ▼
                        TASK-003 (Entity)
                         │       │
                         ▼       ▼
              TASK-004 (Repo IF) TASK-010 (DTOs)
                │        │       │
                ▼        │       ├── TASK-011 (CreateCmd)
         TASK-005 (Migration)    ├── TASK-012 (UpdateCmd)
                │                ├── TASK-013 (UpdateProfile)
                ▼                ├── TASK-014 (GetQuery)
         TASK-006 (Model)        ├── TASK-015 (ListQuery)
                │                └── TASK-016 (DashboardQuery)
                ▼
         TASK-007 (Repository)
                │
                ▼
TASK-008 (JWT mod) ──► TASK-009 (User dep mod)
                │
                ▼
         TASK-017 (OAuthService)
          │           │
          ▼           ▼
   TASK-018       TASK-019
   (Google)       (Microsoft)

TASK-020 (Schemas) ── independent
TASK-021 (Mappers) ── depends on TASK-010, TASK-020

TASK-022 (Dependencies) ── depends on TASK-007, TASK-008, TASK-009
TASK-023 (Reseller Router) ── depends on TASK-017-022
TASK-024 (Admin Router) ── depends on TASK-011-015, TASK-020-021
TASK-025 (app.py) ── depends on TASK-023, TASK-024
TASK-026 (Unit Tests) ── depends on TASK-003, TASK-011-013, TASK-017
TASK-027 (Integration Tests) ── depends on TASK-025
```

## Execution Order

**Batch 1 (Parallel — no dependencies):**
- TASK-001: ResellerStatus enum
- TASK-002: Domain exceptions
- TASK-008: JWTService `type` param modification
- TASK-020: Request/Response schemas

**Batch 2 (depends on Batch 1):**
- TASK-003: Reseller entity
- TASK-009: get_current_user() type check

**Batch 3 (depends on Batch 2):**
- TASK-004: ResellerRepositoryInterface
- TASK-005: Alembic migration
- TASK-010: DTOs

**Batch 4 (depends on Batch 3):**
- TASK-006: ResellerModel
- TASK-011: CreateResellerCommand + Handler
- TASK-012: UpdateResellerCommand + Handler
- TASK-013: UpdateResellerProfileCommand + Handler
- TASK-014: GetResellerByIdQuery + Handler
- TASK-015: ListResellersQuery + Handler
- TASK-016: GetResellerDashboardQuery + Handler
- TASK-021: ResellerMapper

**Batch 5 (depends on Batch 4):**
- TASK-007: ResellerRepository
- TASK-017: ResellerOAuthLoginService

**Batch 6 (depends on Batch 5):**
- TASK-018: ResellerGoogleOAuthService
- TASK-019: ResellerMicrosoftOAuthService
- TASK-022: Reseller dependencies

**Batch 7 (depends on Batch 6):**
- TASK-023: Reseller portal router
- TASK-024: Admin reseller router

**Batch 8 (depends on Batch 7):**
- TASK-025: Register routers in app.py

**Batch 9 (depends on all):**
- TASK-026: Unit tests
- TASK-027: Integration tests

## Final Checklist

- [x] All 27 tasks completed (backend — TASK-001 through TASK-027)
- [x] All unit tests passing (46 tests)
- [x] All integration tests passing (17 tests)
- [ ] mypy passes (`make lint`)
- [ ] All acceptance criteria from requirements.md verified
- [ ] New routers visible in OpenAPI docs
- [x] Frontend: TASK-028 — Reseller portal UI (login, dashboard, profile, admin CRUD, i18n EN/ES)
