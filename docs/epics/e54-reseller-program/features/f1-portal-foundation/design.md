# Solution Design: Portal Foundation (F1)

**Requirement:** [requirements.md](requirements.md)
**Date:** 2026-03-02
**Bounded Context:** `reseller_bc` (new)

## Summary

Create a new `reseller_bc` bounded context with the `Reseller` entity, OAuth-only authentication (Google + Microsoft), a reseller portal shell (login, dashboard, profile), and super admin CRUD. Resellers are a completely separate identity from users — they have their own table, their own OAuth login flow, and their own JWT with a `type: reseller` claim that prevents cross-boundary access.

## Architecture Decision

**Approach:** Separate bounded context with independent auth flow.

**Why:** Resellers are not users of any company — they are external partners who manage client accounts. Their identity, authentication, and authorization are completely independent from the main user system. A separate BC ensures clean domain boundaries and avoids polluting `auth_bc` with reseller concerns.

**Key decisions:**

1. **Separate table, separate entity** — `resellers` table, not a row in `users`. Resellers have fields users don't (commission_pct, min_payout_cents, referral_code, tax_id) and lack fields users have (company_id, role, password_hash).

2. **JWT with `type` claim** — Extend `JWTService.create_token()` to accept an optional `type` parameter (default `"user"` for backward compatibility). Reseller tokens include `type: "reseller"`. The `get_current_user()` dependency rejects tokens with `type != "user"`, and `get_current_reseller()` rejects tokens with `type != "reseller"`.

3. **Reuse existing OAuth token verifiers** — The `GoogleTokenVerifier` and `MicrosoftTokenVerifier` are provider-level utilities. The reseller OAuth login services reuse them but look up the `resellers` table instead of `users`.

4. **Super admin endpoints in a new router** — `adapters/http/api/admin/reseller_routers.py` keeps admin reseller management separate from the main super_admin router.

## Existing Code Analysis

| Component | Location | Reusable | Modifications Needed |
|-----------|----------|----------|---------------------|
| JWTService | `core/jwt.py` | Yes | Add optional `type` param to `create_token()`, check `type` in `decode_token()` return |
| GoogleTokenVerifier | `src/auth_bc/user/application/services/google_token_verifier.py` | Yes (as-is) | None — verifies Google ID token, provider-agnostic |
| MicrosoftTokenVerifier | `src/auth_bc/user/application/services/microsoft_token_verifier.py` | Yes (as-is) | None |
| OAuthSettings | `core/config.py` | Yes (as-is) | None — same Google/Microsoft client IDs |
| ULIDMixin, TimestampMixin | `core/mixins.py` | Yes (as-is) | None |
| Base (SQLAlchemy) | `core/database.py` | Yes (as-is) | None |
| get_current_user() | `adapters/http/api/auth/dependencies.py` | Reference pattern | Add `type` check to reject reseller tokens |
| require_role() | `adapters/http/api/auth/dependencies.py` | Reference pattern | Reseller has `get_current_reseller()` instead |
| Super admin router | `adapters/http/api/super_admin/routers.py` | Reference pattern | New admin router for reseller CRUD |

## Implementation Plan

### 1. Domain Layer

#### Entities

| Entity | File Path | Description |
|--------|-----------|-------------|
| Reseller | `src/reseller_bc/reseller/domain/entities.py` | Reseller identity with OAuth, commission settings, referral code, status |

**Reseller entity fields:**
- `id: str` (ULID)
- `email: str`
- `name: str`
- `google_id: Optional[str]`
- `microsoft_id: Optional[str]`
- `avatar_url: Optional[str]`
- `company_name: Optional[str]`
- `tax_id: Optional[str]`
- `commission_pct: int` (basis points or percentage integer, e.g. 20 = 20%)
- `min_payout_cents: int` (minimum payout threshold)
- `referral_code: str` (unique, URL-safe, auto-generated)
- `status: ResellerStatus`
- `created_at: datetime`
- `updated_at: Optional[datetime]`

**Factory method `create()`:**
- Validates email, name, commission_pct (0-100), min_payout_cents (> 0)
- Auto-generates `referral_code` (8-char alphanumeric, URL-safe)
- Sets `status = ACTIVE`

**Business methods:**
- `update_profile(company_name, tax_id)` — reseller self-edit
- `update_settings(commission_pct, min_payout_cents, status)` — super admin edit
- `suspend()` / `activate()` / `deactivate()` — status transitions
- `link_google(google_id)` / `link_microsoft(microsoft_id)` — OAuth provider linking

#### Value Objects

None beyond existing `Ulid` base class. Reseller uses `str` IDs (matching existing User pattern with `@dataclass` entities and `ULIDMixin` on model).

#### Enums

| Enum | File Path | Values |
|------|-----------|--------|
| ResellerStatus | `src/reseller_bc/reseller/domain/enums.py` | `active`, `suspended`, `deactivated` |

#### Domain Exceptions

| Exception | File Path | When Raised |
|-----------|-----------|-------------|
| ResellerNotFoundException | `src/reseller_bc/reseller/domain/exceptions.py` | Reseller not found by ID/email/provider |
| ResellerNotRegisteredException | `src/reseller_bc/reseller/domain/exceptions.py` | OAuth login with email not in resellers table |
| ResellerDeactivatedException | `src/reseller_bc/reseller/domain/exceptions.py` | Deactivated reseller tries to log in |
| ResellerSuspendedException | `src/reseller_bc/reseller/domain/exceptions.py` | Suspended reseller tries write operation |
| ResellerAlreadyExistsException | `src/reseller_bc/reseller/domain/exceptions.py` | Create with duplicate email |
| InvalidCommissionRateException | `src/reseller_bc/reseller/domain/exceptions.py` | commission_pct outside 0-100 |
| InvalidMinPayoutException | `src/reseller_bc/reseller/domain/exceptions.py` | min_payout_cents <= 0 |
| ReferralCodeCollisionException | `src/reseller_bc/reseller/domain/exceptions.py` | Generated code already exists (retry) |
| ResellerOAuthProviderAlreadyLinkedError | `src/reseller_bc/reseller/domain/exceptions.py` | Provider ID already linked to different reseller |

#### Domain Events

None for F1. Events will be added in F2+ when cross-BC communication is needed.

#### Repository Interface

| Interface | File Path | Methods |
|-----------|-----------|---------|
| ResellerRepositoryInterface | `src/reseller_bc/reseller/domain/repository.py` | `save(reseller)`, `get_by_id(id)`, `find_by_email(email)`, `find_by_google_id(gid)`, `find_by_microsoft_id(mid)`, `find_by_referral_code(code)`, `list_all(offset, limit)`, `count_all()`, `exists_by_email(email)`, `exists_by_referral_code(code)` |

### 2. Application Layer

#### Commands

| Command | Handler | File Path | Description |
|---------|---------|-----------|-------------|
| CreateResellerCommand | CreateResellerCommandHandler | `src/reseller_bc/reseller/application/commands/create_reseller.py` | Super admin creates a new reseller |
| UpdateResellerCommand | UpdateResellerCommandHandler | `src/reseller_bc/reseller/application/commands/update_reseller.py` | Super admin updates reseller settings |
| UpdateResellerProfileCommand | UpdateResellerProfileCommandHandler | `src/reseller_bc/reseller/application/commands/update_reseller_profile.py` | Reseller updates own company_name and tax_id |

**CreateResellerCommand fields:** `id: str`, `email: str`, `name: str`, `commission_pct: int`, `min_payout_cents: int`
- Handler: validates email uniqueness, calls `Reseller.create()`, generates referral_code (retry on collision), saves.

**UpdateResellerCommand fields:** `reseller_id: str`, `commission_pct: Optional[int]`, `min_payout_cents: Optional[int]`, `status: Optional[str]`
- Handler: loads reseller, calls `update_settings()`, saves.

**UpdateResellerProfileCommand fields:** `reseller_id: str`, `company_name: Optional[str]`, `tax_id: Optional[str]`
- Handler: loads reseller, calls `update_profile()`, saves.

#### Queries

| Query | Handler | File Path | Return Type | Description |
|-------|---------|-----------|-------------|-------------|
| GetResellerByIdQuery | Handler | `src/reseller_bc/reseller/application/queries/get_reseller_by_id.py` | `Optional[ResellerDto]` | Get reseller by ID |
| ListResellersQuery | Handler | `src/reseller_bc/reseller/application/queries/list_resellers.py` | `ResellerListDto` | Paginated list for super admin |
| GetResellerDashboardQuery | Handler | `src/reseller_bc/reseller/application/queries/get_reseller_dashboard.py` | `ResellerDashboardDto` | Dashboard data (placeholder zeros for F1) |

**ResellerDto fields:** `id`, `email`, `name`, `avatar_url`, `company_name`, `tax_id`, `commission_pct`, `min_payout_cents`, `referral_code`, `status`, `created_at`, `updated_at`

**ResellerDashboardDto fields:** `reseller_id`, `name`, `referral_code`, `status`, `client_count: int` (0 in F1), `total_commissions_cents: int` (0), `available_balance_cents: int` (0), `pending_payout_cents: int` (0)

**ResellerListDto fields:** `items: list[ResellerDto]`, `total: int`

#### Application Services

| Service | File Path | Description |
|---------|-----------|-------------|
| ResellerGoogleOAuthService | `src/reseller_bc/reseller/application/services/reseller_google_oauth.py` | Verifies Google token, finds/links reseller, returns JWT |
| ResellerMicrosoftOAuthService | `src/reseller_bc/reseller/application/services/reseller_microsoft_oauth.py` | Verifies Microsoft token, finds/links reseller, returns JWT |
| ResellerOAuthLoginService | `src/reseller_bc/reseller/application/services/reseller_oauth_login.py` | Shared OAuth logic: find reseller by provider/email, link provider, issue JWT |

**ResellerOAuthLoginService.login(info: OAuthUserInfo) -> str:**
1. Find reseller by provider ID (`google_id` / `microsoft_id`)
2. Fallback: find by email
3. If not found: raise `ResellerNotRegisteredException` (resellers are created by super admin, not auto-created)
4. If deactivated: raise `ResellerDeactivatedException`
5. Link provider if not yet linked, update avatar
6. Return JWT with `type="reseller"`, `sub=reseller.id`, `role="reseller"`, `company_id=None`

### 3. Infrastructure Layer

#### Repository

| Interface | Implementation | File Path |
|-----------|----------------|-----------|
| ResellerRepositoryInterface | ResellerRepository | `src/reseller_bc/reseller/infrastructure/repository.py` |

**ResellerRepository pattern:** Same as `UserRepository` — session injected, `_to_entity()` static method, `save()` with upsert, `session.flush()`.

#### Model

| Model | File Path | Table |
|-------|-----------|-------|
| ResellerModel | `src/reseller_bc/reseller/infrastructure/models.py` | `resellers` |

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

#### Migrations

| Migration | Description |
|-----------|-------------|
| `create_resellers_table` | Creates `resellers` table with all columns, unique constraints on email/google_id/microsoft_id/referral_code |

### 4. HTTP Layer

#### Reseller Portal Endpoints

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/reseller/auth/google` | Google OAuth login for resellers | None |
| POST | `/api/v1/reseller/auth/microsoft` | Microsoft OAuth login for resellers | None |
| GET | `/api/v1/reseller/me` | Get current reseller profile | Reseller JWT |
| PUT | `/api/v1/reseller/profile` | Update own company_name and tax_id | Reseller JWT |
| GET | `/api/v1/reseller/dashboard` | Get dashboard data (placeholders in F1) | Reseller JWT |

**Files:**
- `adapters/http/api/reseller/routers.py` — Router with prefix `/api/v1/reseller`
- `adapters/http/api/reseller/dependencies.py` — `get_current_reseller()`, `get_reseller_repo()`, factory functions
- `adapters/http/api/reseller/schemas.py` — Request/Response schemas
- `adapters/http/api/reseller/mappers.py` — ResellerMapper (dto_to_response, dto_to_dashboard_response)

**`get_current_reseller()` dependency:**
1. Extract Bearer token
2. Decode JWT via `JWTService`
3. Check `payload["type"] == "reseller"` — reject if not
4. Load reseller by `payload["sub"]`
5. Check `status != deactivated` (suspended can read, checked at route level for writes)
6. Return `Reseller` entity

**`require_active_reseller()` dependency:**
- Wraps `get_current_reseller()`, raises 403 if status is `suspended`

#### Super Admin Reseller Endpoints

| Method | Route | Description | Auth |
|--------|-------|-------------|------|
| POST | `/api/v1/admin/resellers` | Create a new reseller | Super Admin |
| GET | `/api/v1/admin/resellers` | List all resellers | Super Admin |
| GET | `/api/v1/admin/resellers/:id` | Get reseller details | Super Admin |
| PATCH | `/api/v1/admin/resellers/:id` | Update reseller settings | Super Admin |

**Files:**
- `adapters/http/api/admin/reseller_routers.py` — Router with prefix `/api/v1/admin/resellers`

### 5. Collateral Changes

#### Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `core/jwt.py` | Modify | Add optional `type` param to `create_token()` (default `"user"` for backward compat) |
| `adapters/http/api/auth/dependencies.py` | Modify | Add `type` check in `get_current_user()` — reject tokens with `type != "user"` (or missing type, treated as `"user"`) |
| `app.py` | Modify | Register two new routers: `reseller_router` and `admin_reseller_router` |

#### Breaking Changes

| Change | Impact | Migration |
|--------|--------|-----------|
| JWT `type` claim | None — existing tokens without `type` treated as `"user"` | Backward compatible |

## Database Schema

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

CREATE INDEX ix_resellers_email ON resellers (email);
CREATE INDEX ix_resellers_google_id ON resellers (google_id);
CREATE INDEX ix_resellers_microsoft_id ON resellers (microsoft_id);
CREATE INDEX ix_resellers_referral_code ON resellers (referral_code);
```

## State Machine

```
                 create()
                    │
                    ▼
              ┌──────────┐
              │  ACTIVE   │◄──────────────────┐
              └─────┬─────┘                   │
                    │                         │
         suspend()  │          activate()     │
                    ▼                         │
              ┌──────────┐                    │
              │ SUSPENDED │────────────────────┘
              └─────┬─────┘
                    │
       deactivate() │   (can also deactivate from ACTIVE)
                    ▼
              ┌──────────────┐
              │ DEACTIVATED  │  (terminal — no reactivation)
              └──────────────┘
```

**Behavior by status:**
- `ACTIVE`: Full access — login, read, write
- `SUSPENDED`: Login + read allowed, write operations return 403
- `DEACTIVATED`: Login returns 401, cannot access any endpoint

## Dependencies

| Dependency | Type | Description |
|------------|------|-------------|
| GoogleTokenVerifier | Import (auth_bc) | Reuse for verifying Google ID tokens |
| MicrosoftTokenVerifier | Import (auth_bc) | Reuse for verifying Microsoft ID tokens |
| JWTService | Import (core) | Token creation and validation |
| OAuthSettings | Import (core/config) | Google/Microsoft client IDs |
| ULIDMixin, TimestampMixin | Import (core/mixins) | Model base mixins |
| Base | Import (core/database) | SQLAlchemy declarative base |

## Testing Strategy

| Test Type | Scope | File Path | Priority |
|-----------|-------|-----------|----------|
| Unit | Reseller entity (create, update_profile, update_settings, status transitions) | `tests/unit/reseller_bc/reseller/domain/test_entities.py` | High |
| Unit | CreateResellerCommandHandler | `tests/unit/reseller_bc/reseller/application/commands/test_create_reseller.py` | High |
| Unit | UpdateResellerCommandHandler | `tests/unit/reseller_bc/reseller/application/commands/test_update_reseller.py` | High |
| Unit | UpdateResellerProfileCommandHandler | `tests/unit/reseller_bc/reseller/application/commands/test_update_reseller_profile.py` | Medium |
| Unit | ResellerOAuthLoginService | `tests/unit/reseller_bc/reseller/application/services/test_reseller_oauth_login.py` | High |
| Unit | GetResellerDashboardQueryHandler | `tests/unit/reseller_bc/reseller/application/queries/test_get_reseller_dashboard.py` | Low |
| Integration | Reseller OAuth login endpoints | `tests/integration/test_reseller_auth_endpoints.py` | High |
| Integration | Reseller profile endpoints | `tests/integration/test_reseller_profile_endpoints.py` | Medium |
| Integration | Admin reseller CRUD endpoints | `tests/integration/test_admin_reseller_endpoints.py` | High |
| Integration | JWT type isolation (reseller token cannot access user endpoints and vice versa) | `tests/integration/test_jwt_type_isolation.py` | High |

## Implementation Order

1. [ ] Domain: `ResellerStatus` enum
2. [ ] Domain: Domain exceptions
3. [ ] Domain: `Reseller` entity with factory method and business methods
4. [ ] Domain: `ResellerRepositoryInterface`
5. [ ] Infrastructure: Alembic migration for `resellers` table
6. [ ] Infrastructure: `ResellerModel`
7. [ ] Infrastructure: `ResellerRepository`
8. [ ] Collateral: Modify `JWTService.create_token()` to accept `type` param
9. [ ] Collateral: Add `type` check in `get_current_user()` dependency
10. [ ] Application: `ResellerDto`, `ResellerDashboardDto`, `ResellerListDto`
11. [ ] Application: `CreateResellerCommand` + Handler
12. [ ] Application: `UpdateResellerCommand` + Handler
13. [ ] Application: `UpdateResellerProfileCommand` + Handler
14. [ ] Application: `GetResellerByIdQuery` + Handler
15. [ ] Application: `ListResellersQuery` + Handler
16. [ ] Application: `GetResellerDashboardQuery` + Handler
17. [ ] Application: `ResellerOAuthLoginService`
18. [ ] Application: `ResellerGoogleOAuthService`
19. [ ] Application: `ResellerMicrosoftOAuthService`
20. [ ] HTTP: `adapters/http/api/reseller/schemas.py`
21. [ ] HTTP: `adapters/http/api/reseller/mappers.py`
22. [ ] HTTP: `adapters/http/api/reseller/dependencies.py` (`get_current_reseller()`, factories)
23. [ ] HTTP: `adapters/http/api/reseller/routers.py` (auth + profile + dashboard)
24. [ ] HTTP: `adapters/http/api/admin/reseller_routers.py` (CRUD)
25. [ ] Collateral: Register routers in `app.py`
26. [ ] Tests: Unit tests for entity, commands, queries, services
27. [ ] Tests: Integration tests for all endpoints + JWT isolation
28. [ ] Frontend: `ResellerAuthContext.tsx`, login page, dashboard, profile (separate task)

## Open Technical Questions

None — all questions resolved during requirement validation.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Referral code collision on generation | Low | Low | Retry loop (max 3 attempts) with increasing length fallback |
| Existing tokens without `type` claim break after JWT change | Medium | High | Default `type` to `"user"` when missing — fully backward compatible |
| Shared OAuth client IDs cause confusion (user vs reseller) | Low | Low | Different callback paths and state params distinguish flows |
