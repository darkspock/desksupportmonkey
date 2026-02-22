# Tasks: F0 - Backend OAuth Infrastructure

**Design:** [design.md](design.md)

---

## Domain Layer

- [x] **F0-1** Add `google_id: Optional[str]` and `microsoft_id: Optional[str]` to `User` dataclass (`src/auth_bc/user/domain/entities.py`)
- [x] **F0-2** Add `link_google(google_id: str)` and `link_microsoft(microsoft_id: str)` methods to `User`
- [x] **F0-3** Add `find_by_google_id` and `find_by_microsoft_id` abstract methods to `UserRepositoryInterface` (`src/auth_bc/user/domain/repository.py`)
- [x] **F0-4** Add `OAuthProviderAlreadyLinkedError` and `OAuthProviderNotConfiguredError` to `src/auth_bc/user/domain/exceptions.py`

## Infrastructure Layer

- [x] **F0-5** Add `google_id` and `microsoft_id` columns to `UserModel` (`src/auth_bc/user/infrastructure/models.py`) — nullable, unique, indexed
- [x] **F0-6** Update `_to_entity()` and `save()` in `UserRepository` to include `google_id` and `microsoft_id`
- [x] **F0-7** Implement `find_by_google_id` and `find_by_microsoft_id` in `UserRepository`
- [x] **F0-8** Alembic migration: add `google_id` and `microsoft_id` columns with unique constraints and indexes

## Application Layer

- [x] **F0-9** Create `OAuthUserInfo` dataclass and `OAuthLoginService` in `src/auth_bc/user/application/services/oauth_login_service.py`
- [x] **F0-10** Create `GetOAuthProvidersQuery` and handler in `src/auth_bc/user/application/queries/get_oauth_providers.py`

## Configuration

- [x] **F0-11** Add `OAuthSettings` class to `core/config.py` with `GOOGLE_CLIENT_ID`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_TENANT_ID`
- [x] **F0-12** Update `.env.example` with commented OAuth variables

## HTTP Layer

- [x] **F0-13** Add `OAuthLoginRequest` and `OAuthProvidersResponse` schemas to `adapters/http/api/auth/schemas.py`
- [x] **F0-14** Add `get_oauth_settings()` and `get_oauth_login_service()` to `adapters/http/api/auth/dependencies.py`
- [x] **F0-15** Add `GET /auth/oauth/providers` endpoint to `adapters/http/api/auth/routers.py`

## Tests

- [ ] **F0-T1** Unit: `User.link_google()` and `User.link_microsoft()`
- [ ] **F0-T2** Unit: `OAuthLoginService.login_or_create()` — existing user by provider ID, existing user by email, new user (valid domain), deactivated user, company restricted, provider already linked to different user, invalid domain
- [ ] **F0-T3** Unit: `GetOAuthProvidersHandler` — both enabled, both disabled, one enabled
- [ ] **F0-T4** Integration: `GET /api/v1/auth/oauth/providers` — correct booleans based on config
- [ ] **F0-T5** Integration: `UserRepository.find_by_google_id` and `find_by_microsoft_id`
