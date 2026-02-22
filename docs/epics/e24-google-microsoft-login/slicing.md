# Epic Slicing: E24 - Google & Microsoft Login

**Epic:** [requirements.md](requirements.md)
**Date:** 2026-02-22
**Total Features:** 3

---

## Slicing Rationale

E24 is sliced into 3 features following a dependency chain: first build the OAuth infrastructure on the backend (User entity fields, configuration, shared token verification logic), then implement Google login end-to-end (backend + frontend), then implement Microsoft login end-to-end (backend + frontend). F1 and F2 are independent of each other but both depend on F0.

---

## Dependency Graph

```
F0: Backend OAuth Infrastructure
 │
 ├── F1: Google Login (Backend + Frontend)
 │
 └── F2: Microsoft Login (Backend + Frontend)
```

F1 and F2 both depend on F0 but are independent of each other.

---

## Features Summary

| # | Feature | Dependencies | Value Delivered | Complexity | Status |
|---|---|---|---|---|---|
| F0 | Backend OAuth Infrastructure | E0 | User entity extended, OAuth config, provider availability endpoint, shared login logic | S | Pending |
| F1 | Google Login | F0 | Users can log in with Google, frontend button, token verification | M | Pending |
| F2 | Microsoft Login | F0 | Users can log in with Microsoft, frontend button, token verification | M | Pending |

---

## F0: Backend OAuth Infrastructure

**Scope:** Extend User entity with `google_id` and `microsoft_id` fields. Add OAuth configuration (env vars). Create the `GET /api/v1/auth/oauth/providers` endpoint. Establish shared logic for OAuth login flow (find-or-create user, account linking, JWT issuance).

**Why F0 first:** Both Google and Microsoft login share the same User fields, configuration pattern, and login flow (verify token -> find user by provider ID or email -> link account -> create if new -> issue JWT). Extracting this into F0 avoids duplication in F1 and F2.

**Depends on:** E0 (Foundation — auth infrastructure, User entity, JWT issuance)

**Includes:**

### Entities
- Extend `User` domain entity with `google_id: Optional[str]` and `microsoft_id: Optional[str]`
- Extend `UserModel` with `google_id` and `microsoft_id` columns (nullable, unique, indexed)
- Alembic migration for the new columns

### Repository
- Add `find_by_google_id(google_id: str) -> Optional[User]` to UserRepository interface and implementation
- Add `find_by_microsoft_id(microsoft_id: str) -> Optional[User]` to UserRepository interface and implementation

### Configuration
- Add `GOOGLE_CLIENT_ID`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_TENANT_ID` to settings
- Add these to `.env.example` with documentation comments

### Endpoints
| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/auth/oauth/providers` | Returns which OAuth providers are enabled |

### Shared Logic
- OAuth login service/helper: given a verified email, provider ID field name, and provider ID value — find user by provider ID, fallback to email, link account, create new user if domain matches, issue JWT. This shared logic is used by F1 and F2.

---

## F1: Google Login

**Scope:** Google OAuth2 token verification endpoint and frontend "Sign in with Google" button. Full end-to-end Google login flow.

**Why F1:** Google Workspace is the most common corporate identity provider. Delivering Google login first maximizes value.

**Depends on:** F0 (OAuth infrastructure, User entity fields, shared login logic)

**Includes:**

### Commands
- `GoogleOAuthLogin` command: receives Google ID token, verifies it, delegates to shared login logic with `google_id`

### Token Verification
- Google ID token verification using `google-auth` library (or `google-api-python-client`)
- Validates token audience matches `GOOGLE_CLIENT_ID`
- Extracts `sub` (Google subject ID), `email`, and `name` from token claims

### Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/oauth/google` | Verify Google ID token and return JWT |

### Frontend
- "Sign in with Google" button on the login page using Google Identity Services JavaScript API
- Button hidden when Google provider is not enabled (from `/api/v1/auth/oauth/providers`)
- On success, sends ID token to backend and handles JWT response
- i18n labels for button and error messages (EN/ES)

### Tests
- Unit test: Google token verification logic (mocked Google API)
- Unit test: Google login command handler (existing user, new user, deactivated user, invalid domain)
- Integration test: `POST /api/v1/auth/oauth/google` endpoint (mocked token verification)

---

## F2: Microsoft Login

**Scope:** Microsoft OAuth2 token verification endpoint and frontend "Sign in with Microsoft" button. Full end-to-end Microsoft login flow.

**Why F2:** Microsoft 365 is the second most common corporate identity provider. Completes the OAuth login story.

**Depends on:** F0 (OAuth infrastructure, User entity fields, shared login logic)

**Includes:**

### Commands
- `MicrosoftOAuthLogin` command: receives Microsoft ID token, verifies it, delegates to shared login logic with `microsoft_id`

### Token Verification
- Microsoft ID token verification using PyJWT with JWKS from Microsoft's OIDC discovery endpoint
- Validates token audience matches `MICROSOFT_CLIENT_ID`
- Validates token issuer matches `MICROSOFT_TENANT_ID` (or allows any tenant if set to `common`)
- Extracts `oid` (Microsoft object ID), `preferred_username` or `email`, and `name` from token claims

### Endpoints
| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/auth/oauth/microsoft` | Verify Microsoft ID token and return JWT |

### Frontend
- "Sign in with Microsoft" button on the login page using MSAL.js (Microsoft Authentication Library)
- Button hidden when Microsoft provider is not enabled (from `/api/v1/auth/oauth/providers`)
- On success, sends ID token to backend and handles JWT response
- i18n labels for button and error messages (EN/ES)

### Tests
- Unit test: Microsoft token verification logic (mocked JWKS endpoint)
- Unit test: Microsoft login command handler (existing user, new user, deactivated user, invalid domain)
- Integration test: `POST /api/v1/auth/oauth/microsoft` endpoint (mocked token verification)

---

## Recommended Order

1. **F0: Backend OAuth Infrastructure** — Must be first. Adds User fields and shared logic.
2. **F1: Google Login** — Google is the most common provider, delivers value fastest.
3. **F2: Microsoft Login** — Completes OAuth story. Follows same pattern as F1.

---

## Migration Strategy

**F0** includes a single Alembic migration that adds `google_id` and `microsoft_id` columns to the `users` table. Both columns are nullable so the migration is non-breaking and backward compatible. No data migration needed.

---

## Slicing Validation

- [x] No circular dependencies
- [x] Unidirectional dependency flow
- [x] Each feature independently deployable
- [x] Vertical slices (not horizontal layers)
- [x] Shared foundation identified (F0)
- [x] No overlapping scope
- [x] Each feature delivers minimum viable value
- [x] All epic scope covered

---

## Risk Notes

- F0 modifies the User entity which is used across the entire platform — requires regression tests on existing auth flows (magic link, password login).
- Google token verification relies on Google's public key infrastructure — needs graceful error handling for network failures during key fetching.
- Microsoft OIDC discovery endpoint URL varies by tenant configuration — test with both single-tenant and multi-tenant (`common`) setups.
- Frontend OAuth libraries (Google Identity Services, MSAL.js) add JavaScript dependencies — ensure they are loaded conditionally only when the provider is enabled.
