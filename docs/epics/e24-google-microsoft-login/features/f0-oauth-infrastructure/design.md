# Solution Design: F0 - Backend OAuth Infrastructure

**Requirement:** [../../requirements.md](../../requirements.md)
**Slicing:** [../../slicing.md](../../slicing.md)
**Date:** 2026-02-22
**Bounded Context:** `auth_bc`

---

## Summary

Extend the User entity with `google_id` and `microsoft_id` fields, add OAuth configuration settings, create the `GET /api/v1/auth/oauth/providers` endpoint, and build the shared OAuth login service that F1 (Google) and F2 (Microsoft) will delegate to.

---

## Architecture Decision

OAuth login reuses the existing auth_bc patterns: command-driven flow, CompanyLookupService for email-domain resolution, JWTService for token issuance. The shared logic lives in a domain service (`OAuthLoginService`) that encapsulates find-or-create-user + account-linking + JWT generation. Each provider (F1, F2) only handles token verification and delegates to this service.

No new bounded context — this extends `auth_bc/user`.

---

## Implementation Plan

### 1. Domain Layer

#### User Entity Extension — `src/auth_bc/user/domain/entities.py`

Add two fields to the `User` dataclass:

```python
@dataclass
class User:
    # ... existing fields ...
    google_id: Optional[str] = None
    microsoft_id: Optional[str] = None

    def link_google(self, google_id: str) -> None:
        self.google_id = google_id

    def link_microsoft(self, microsoft_id: str) -> None:
        self.microsoft_id = microsoft_id
```

#### Repository Interface Extension — `src/auth_bc/user/domain/repository.py`

Add two methods to `UserRepositoryInterface`:

```python
class UserRepositoryInterface(ABC):
    # ... existing methods ...

    @abstractmethod
    def find_by_google_id(self, google_id: str) -> Optional[User]:
        ...

    @abstractmethod
    def find_by_microsoft_id(self, microsoft_id: str) -> Optional[User]:
        ...
```

#### Domain Exceptions — `src/auth_bc/user/domain/exceptions.py`

Add new exceptions (or extend existing):

```python
class OAuthProviderAlreadyLinkedError(Exception):
    """The OAuth provider ID is already linked to a different user."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"This {provider} account is already linked to another user")

class OAuthProviderNotConfiguredError(Exception):
    """The OAuth provider is not configured on this deployment."""
    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(f"{provider} login is not configured")
```

### 2. Application Layer

#### OAuthLoginService — `src/auth_bc/user/application/services/oauth_login_service.py`

Shared service used by both Google and Microsoft login command handlers.

```python
@dataclass
class OAuthUserInfo:
    email: str
    name: Optional[str]
    provider_id: str          # Google sub or Microsoft oid
    provider_field: str       # "google_id" or "microsoft_id"

class OAuthLoginService:
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        company_lookup: CompanyLookupInterface,
        jwt_service: JWTService,
    ):
        self.user_repo = user_repo
        self.company_lookup = company_lookup
        self.jwt_service = jwt_service

    def login_or_create(self, info: OAuthUserInfo) -> str:
        """Returns JWT access_token."""
        # 1. Find user by provider ID
        user = self._find_by_provider_id(info.provider_field, info.provider_id)

        # 2. Fallback: find by email
        if not user:
            user = self.user_repo.find_by_email(info.email)

        # 3. If user found, verify and link
        if user:
            self._verify_existing_user(user, info)
            self._link_provider(user, info)
            self._update_name(user, info.name)
            self.user_repo.save(user)
            return self.jwt_service.create_token(user.id, user.company_id, user.role.value)

        # 4. No user found — auto-create
        user = self._auto_create_user(info)
        return self.jwt_service.create_token(user.id, user.company_id, user.role.value)
```

**Step-by-step logic:**

1. **Find by provider ID** (`find_by_google_id` or `find_by_microsoft_id`)
2. **Fallback to email** — `find_by_email(info.email)`
3. **Existing user checks:**
   - `user.is_active` must be True → else raise 403 "User account is deactivated"
   - If user has a company_id, check company is active via `company_lookup.find_company_by_email_domain` → else raise 403 "Company access is currently restricted"
   - Check provider ID not already linked to a *different* user → else raise 409 `OAuthProviderAlreadyLinkedError`
4. **Link provider** — set `google_id` or `microsoft_id` on user if not already set
5. **Update name** — always overwrite `user.name` from OAuth profile
6. **Auto-create** — if no user found:
   - Extract domain from email
   - `company_lookup.find_company_by_email_domain(email)` → must return active company
   - If no company match → raise 403 "Only corporate email addresses are allowed"
   - Create `User.create(email=info.email, role=UserRole.EMPLOYEE, company_id=company_id)`
   - Set `user.name` from OAuth profile
   - Link provider ID
   - `user_repo.save(user)`

#### Providers Query — `src/auth_bc/user/application/queries/get_oauth_providers.py`

```python
@dataclass
class GetOAuthProvidersQuery(Query):
    pass

class GetOAuthProvidersHandler(QueryHandler[GetOAuthProvidersQuery, dict]):
    def __init__(self, oauth_settings: OAuthSettings):
        self.settings = oauth_settings

    def handle(self, query: GetOAuthProvidersQuery) -> dict:
        return {
            "google": bool(self.settings.GOOGLE_CLIENT_ID),
            "microsoft": bool(self.settings.MICROSOFT_CLIENT_ID),
        }
```

### 3. Infrastructure Layer

#### UserModel Extension — `src/auth_bc/user/infrastructure/models.py`

```python
class UserModel(ULIDMixin, TimestampMixin, Base):
    # ... existing columns ...
    google_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True,
    )
    microsoft_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True,
    )
```

#### UserRepository Extension — `src/auth_bc/user/infrastructure/repository.py`

```python
def find_by_google_id(self, google_id: str) -> Optional[User]:
    model = self.session.query(UserModel).filter(
        UserModel.google_id == google_id
    ).first()
    return self._to_entity(model) if model else None

def find_by_microsoft_id(self, microsoft_id: str) -> Optional[User]:
    model = self.session.query(UserModel).filter(
        UserModel.microsoft_id == microsoft_id
    ).first()
    return self._to_entity(model) if model else None
```

Also update `_to_entity` and `save` to include `google_id` and `microsoft_id` mapping.

#### Alembic Migration

Single migration adding both columns:

```python
def upgrade():
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('microsoft_id', sa.String(255), nullable=True))
    op.create_unique_constraint('uq_users_google_id', 'users', ['google_id'])
    op.create_unique_constraint('uq_users_microsoft_id', 'users', ['microsoft_id'])
    op.create_index('ix_users_google_id', 'users', ['google_id'])
    op.create_index('ix_users_microsoft_id', 'users', ['microsoft_id'])
```

Non-breaking: both columns are nullable, no data migration needed.

#### Configuration — `core/config.py`

```python
class OAuthSettings(BaseSettings):
    GOOGLE_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_TENANT_ID: str = "common"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
```

Add to `Settings`:

```python
class Settings(BaseSettings):
    # ... existing ...
    oauth: OAuthSettings = OAuthSettings()
```

#### `.env.example` Update

```bash
# OAuth (leave empty to disable provider)
# GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
# MICROSOFT_CLIENT_ID=your-microsoft-app-client-id
# MICROSOFT_TENANT_ID=common
```

### 4. HTTP Layer

#### Providers Endpoint — `adapters/http/api/auth/routers.py`

```python
@router.get("/auth/oauth/providers")
def get_oauth_providers(oauth: OAuthSettings = Depends(get_oauth_settings)):
    return SingleResponse(data={
        "google": bool(oauth.GOOGLE_CLIENT_ID),
        "microsoft": bool(oauth.MICROSOFT_CLIENT_ID),
    })
```

Public endpoint (no auth required) — frontend calls it to know which buttons to show.

#### Schemas — `adapters/http/api/auth/schemas.py`

```python
class OAuthLoginRequest(BaseModel):
    id_token: str

class OAuthProvidersResponse(BaseModel):
    google: bool
    microsoft: bool
```

#### Dependencies — `adapters/http/api/auth/dependencies.py`

```python
def get_oauth_settings() -> OAuthSettings:
    return settings.oauth

def get_oauth_login_service(db: Session = Depends(get_db)) -> OAuthLoginService:
    return OAuthLoginService(
        user_repo=UserRepository(db),
        company_lookup=CompanyLookupService(db),
        jwt_service=JWTService(),
    )
```

---

## Files Created / Modified

| File | Action | Description |
|---|---|---|
| `src/auth_bc/user/domain/entities.py` | Modify | Add `google_id`, `microsoft_id` fields + `link_google()`, `link_microsoft()` |
| `src/auth_bc/user/domain/repository.py` | Modify | Add `find_by_google_id`, `find_by_microsoft_id` |
| `src/auth_bc/user/domain/exceptions.py` | Modify | Add `OAuthProviderAlreadyLinkedError`, `OAuthProviderNotConfiguredError` |
| `src/auth_bc/user/application/services/oauth_login_service.py` | Create | Shared OAuth login logic |
| `src/auth_bc/user/application/queries/get_oauth_providers.py` | Create | Provider availability query |
| `src/auth_bc/user/infrastructure/models.py` | Modify | Add `google_id`, `microsoft_id` columns |
| `src/auth_bc/user/infrastructure/repository.py` | Modify | Implement new find methods + entity mapping |
| `alembic/versions/xxx_add_oauth_ids_to_users.py` | Create | Migration |
| `core/config.py` | Modify | Add `OAuthSettings` |
| `.env.example` | Modify | Add OAuth variables |
| `adapters/http/api/auth/routers.py` | Modify | Add `/auth/oauth/providers` |
| `adapters/http/api/auth/schemas.py` | Modify | Add `OAuthLoginRequest`, `OAuthProvidersResponse` |
| `adapters/http/api/auth/dependencies.py` | Modify | Add `get_oauth_settings`, `get_oauth_login_service` |

---

## Testing Strategy

| Test Type | Scope | Priority |
|---|---|---|
| Unit | User entity — `link_google()`, `link_microsoft()` | High |
| Unit | OAuthLoginService — existing user login, new user creation, deactivated user, invalid domain, provider already linked | High |
| Unit | GetOAuthProvidersHandler — enabled/disabled states | Medium |
| Integration | `GET /api/v1/auth/oauth/providers` — returns correct booleans | Medium |
| Integration | UserRepository — `find_by_google_id`, `find_by_microsoft_id` | High |

---

## Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| OAuthLoginService returns JWT (breaks strict CQRS) | N/A | N/A | Documented exception — same pattern as VerifyMagicLink |
| Unique constraint on google_id/microsoft_id blocks concurrent linking | Low | Low | Database handles race condition via unique constraint; returns 409 |
