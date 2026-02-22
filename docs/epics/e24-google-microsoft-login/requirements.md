# Epic E24: Google & Microsoft Login

**Type:** Epic
**Status:** Validated
**Created:** 2026-02-22
**Priority:** High
**Depends on:** E0 (Foundation)

---

## Business Alignment

**Objective:** Allow users to log in with their corporate Google or Microsoft accounts, in addition to existing magic link and password authentication.

Many organizations use Google Workspace or Microsoft 365 as their corporate identity provider. Supporting OAuth2 login with these providers reduces friction for employees who already have active sessions, eliminates the need to check email for magic links, and aligns with corporate security policies that mandate centralized identity management.

---

## Problem Statement

### Current Situation
E0 delivered two authentication methods:
- Magic link (passwordless email-based login)
- Password login (user sets a password after first magic link login)

Both methods work but have limitations:
- Users must check email or remember a password for every login
- No integration with corporate identity providers
- Organizations using Google Workspace or Microsoft 365 cannot leverage existing SSO sessions
- No way to enforce corporate authentication policies from the IdP side

### What E24 Delivers
OAuth2 login for Google and Microsoft as additional authentication methods:
- "Sign in with Google" and "Sign in with Microsoft" buttons on the login page
- Backend token verification endpoints that validate OAuth tokens server-side
- Automatic account linking when the OAuth email matches an existing user
- New user auto-creation when the OAuth email domain matches a registered company
- `google_id` and `microsoft_id` fields on the User entity for persistent account linking

### What E24 Does NOT Deliver (deferred to E42)
- SAML/OIDC enterprise SSO configuration
- LDAP/Active Directory synchronization
- User provisioning/deprovisioning from directory
- Group/role mapping from identity provider
- OAuth account unlinking (removing a linked Google/Microsoft ID from a user)

---

## Proposed Solution

### US-E24-001: Google OAuth2 Login
**As a** user with a Google Workspace account
**I want** to log in by clicking "Sign in with Google"
**So that** I can access the platform without a magic link or password

**Acceptance Criteria:**
- [ ] Login page displays a "Sign in with Google" button
- [ ] Clicking the button initiates the Google OAuth2 flow (Google Identity Services)
- [ ] Backend endpoint `POST /api/v1/auth/oauth/google` receives the Google ID token
- [ ] Backend verifies the Google ID token using Google's public keys (no client secret exchange needed)
- [ ] If the token is valid and the email matches an existing user, the user is logged in and receives a JWT
- [ ] If the token is valid and the email does not match any user, but the email domain matches a registered company, a new user is created with `employee` role and logged in
- [ ] If the email domain does not match any registered company, returns 403 "Only corporate email addresses are allowed"
- [ ] If the matched company is suspended or deactivated, returns 403 "Company access is currently restricted"
- [ ] If the matched user is deactivated, returns 403 "User account is deactivated"
- [ ] The user's `google_id` (Google subject identifier) is stored on successful login
- [ ] The user's `name` field is always updated from the Google profile `name` claim on every login
- [ ] Subsequent Google logins match by `google_id` first, then by email as fallback
- [ ] Google login works alongside existing magic link and password authentication

### US-E24-002: Microsoft OAuth2 Login
**As a** user with a Microsoft 365 account
**I want** to log in by clicking "Sign in with Microsoft"
**So that** I can access the platform without a magic link or password

**Acceptance Criteria:**
- [ ] Login page displays a "Sign in with Microsoft" button
- [ ] Clicking the button initiates the Microsoft OAuth2 flow (Microsoft Identity Platform)
- [ ] Backend endpoint `POST /api/v1/auth/oauth/microsoft` receives the Microsoft ID token
- [ ] Backend verifies the Microsoft ID token using Microsoft's OIDC discovery endpoint and public keys
- [ ] If the token is valid and the email matches an existing user, the user is logged in and receives a JWT
- [ ] If the token is valid and the email does not match any user, but the email domain matches a registered company, a new user is created with `employee` role and logged in
- [ ] If the email domain does not match any registered company, returns 403 "Only corporate email addresses are allowed"
- [ ] If the matched company is suspended or deactivated, returns 403 "Company access is currently restricted"
- [ ] If the matched user is deactivated, returns 403 "User account is deactivated"
- [ ] The user's `microsoft_id` (Microsoft object identifier) is stored on successful login
- [ ] The user's `name` field is always updated from the Microsoft profile `name` claim on every login
- [ ] Subsequent Microsoft logins match by `microsoft_id` first, then by email as fallback
- [ ] Microsoft login works alongside existing magic link and password authentication

### US-E24-003: OAuth Account Linking
**As a** user who already has an account (created via magic link)
**I want** my Google or Microsoft login to automatically link to my existing account
**So that** I don't end up with duplicate accounts

**Acceptance Criteria:**
- [ ] When a user logs in via Google/Microsoft and the OAuth email matches an existing user, the `google_id`/`microsoft_id` is saved to that user record
- [ ] Once linked, the user can log in with either magic link, password, or the linked OAuth provider
- [ ] A user can have both `google_id` and `microsoft_id` linked simultaneously
- [ ] If an OAuth provider ID is already linked to a different user (email mismatch), returns 409 "This Google/Microsoft account is already linked to another user"
- [ ] Account linking is transparent to the user — no separate linking step required

### US-E24-004: OAuth Configuration
**As a** platform operator
**I want** to configure Google and Microsoft OAuth credentials via environment variables
**So that** OAuth login can be enabled or disabled per deployment

**Acceptance Criteria:**
- [ ] Google OAuth requires `GOOGLE_CLIENT_ID` environment variable
- [ ] Microsoft OAuth requires `MICROSOFT_CLIENT_ID` and `MICROSOFT_TENANT_ID` environment variables
- [ ] If `GOOGLE_CLIENT_ID` is not set, the Google login button is hidden and the endpoint returns 501 "Google login is not configured"
- [ ] If `MICROSOFT_CLIENT_ID` is not set, the Microsoft login button is hidden and the endpoint returns 501 "Microsoft login is not configured"
- [ ] A `GET /api/v1/auth/oauth/providers` endpoint returns which providers are enabled (for frontend to show/hide buttons)
- [ ] Configuration is documented in `.env.example`
- [ ] OAuth endpoints have rate limiting applied (consistent with existing auth endpoints)

---

## Entities

| Entity | Description | New in E24? |
|---|---|---|
| `User` | Extend with `google_id` and `microsoft_id` fields | Extend |

### User Entity (extended)

| Field | Type | Notes |
|---|---|---|
| `google_id` | string(255) | Google subject identifier (`sub` claim). Nullable, unique, indexed |
| `microsoft_id` | string(255) | Microsoft object identifier (`oid` claim). Nullable, unique, indexed |

All other User fields remain unchanged.

---

## Use Cases

### UC-E24-001: Google OAuth Login (Existing User)
**Actor:** User with Google account
**Preconditions:** User already has an account (created via magic link or password)

**Main Flow:**
1. User clicks "Sign in with Google" on the login page
2. Google Identity Services shows the Google account picker
3. User selects their Google account and consents
4. Frontend receives a Google ID token
5. Frontend sends `POST /api/v1/auth/oauth/google` with the ID token
6. Backend verifies the ID token with Google's public keys
7. Backend extracts email and Google subject ID from the token
8. Backend finds user by `google_id` or by email
9. Backend saves `google_id` to user if not already set
10. Backend returns JWT access token and refresh token
11. Frontend stores tokens and redirects to dashboard

**Alternative Flows:**
- A1: ID token invalid or expired -> 401 "Invalid Google token"
- A2: Email domain not in any company -> 403 "Only corporate email addresses are allowed"
- A3: Company suspended/deactivated -> 403 "Company access is currently restricted"
- A4: User deactivated -> 403 "User account is deactivated"
- A5: Google ID already linked to different user -> 409 "This Google account is already linked to another user"

### UC-E24-002: Google OAuth Login (New User Auto-Creation)
**Actor:** User with Google account whose email domain matches a registered company
**Preconditions:** No user account exists for this email

**Main Flow:**
1. Steps 1-7 from UC-E24-001
2. Backend finds no user by `google_id` or email
3. Backend extracts domain from email and looks up CompanyEmailDomain
4. Backend finds a matching active company
5. Backend creates a new User with `employee` role in the matched company, sets `google_id`
6. Backend returns JWT access token and refresh token
7. Frontend stores tokens and redirects to dashboard

**Alternative Flows:**
- Same as UC-E24-001 A1-A3

### UC-E24-003: Microsoft OAuth Login (Existing User)
**Actor:** User with Microsoft account
**Preconditions:** User already has an account

**Main Flow:**
1. User clicks "Sign in with Microsoft" on the login page
2. Microsoft Identity Platform shows the Microsoft account picker
3. User selects their Microsoft account and consents
4. Frontend receives a Microsoft ID token
5. Frontend sends `POST /api/v1/auth/oauth/microsoft` with the ID token
6. Backend verifies the ID token with Microsoft's OIDC public keys
7. Backend extracts email and Microsoft object ID from the token
8. Backend finds user by `microsoft_id` or by email
9. Backend saves `microsoft_id` to user if not already set
10. Backend returns JWT access token and refresh token
11. Frontend stores tokens and redirects to dashboard

**Alternative Flows:**
- A1: ID token invalid or expired -> 401 "Invalid Microsoft token"
- A2-A5: Same as UC-E24-001

### UC-E24-004: Microsoft OAuth Login (New User Auto-Creation)
**Actor:** User with Microsoft account whose email domain matches a registered company
**Preconditions:** No user account exists for this email

**Main Flow:**
1. Steps 1-7 from UC-E24-003
2. Backend finds no user by `microsoft_id` or email
3. Backend extracts domain from email and looks up CompanyEmailDomain
4. Backend finds a matching active company
5. Backend creates a new User with `employee` role in the matched company, sets `microsoft_id`
6. Backend returns JWT access token and refresh token
7. Frontend stores tokens and redirects to dashboard

**Alternative Flows:**
- Same as UC-E24-003 A1-A3

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| `UserModel` | Add `google_id` and `microsoft_id` columns | Alembic migration |
| `User` entity | Add `google_id` and `microsoft_id` fields | Update dataclass |
| `UserRepository` | Add `find_by_google_id` and `find_by_microsoft_id` methods | Extend repository |
| Auth router | Add OAuth endpoints | New endpoints in `auth/routers.py` |
| Login page (frontend) | Add Google and Microsoft login buttons | Update `LoginPage.tsx` |
| `.env.example` | Add OAuth configuration variables | Update file |
| `CompanyLookupService` | Used by OAuth flow to match email domain to company | Already exists from E1 |
| `core/config.py` | Add OAuth settings (`GOOGLE_CLIENT_ID`, `MICROSOFT_CLIENT_ID`, `MICROSOFT_TENANT_ID`) | New settings fields |
| `pyproject.toml` | Add `google-auth` library for Google token verification | New backend dependency |
| `package.json` (frontend) | Add `@react-oauth/google` and `@azure/msal-browser` for OAuth flows | New frontend dependencies |

---

## Bounded Context

This epic extends the `auth_bc` bounded context:

```
src/auth_bc/
├── user/
│   ├── domain/
│   │   ├── entities.py         # Add google_id, microsoft_id fields
│   │   └── repository.py       # Add find_by_google_id, find_by_microsoft_id
│   ├── application/
│   │   └── commands/
│   │       ├── google_oauth_login.py    # Verify Google token, login/create user
│   │       └── microsoft_oauth_login.py # Verify Microsoft token, login/create user
│   └── infrastructure/
│       ├── models.py           # Add google_id, microsoft_id columns
│       └── repository.py       # Implement new find methods

adapters/http/api/
├── auth/
│   ├── routers.py              # Add OAuth endpoints
│   └── schemas.py              # Add OAuth request/response schemas
```

---

## Definition of Done

- [ ] `POST /api/v1/auth/oauth/google` verifies Google ID token and returns JWT
- [ ] `POST /api/v1/auth/oauth/microsoft` verifies Microsoft ID token and returns JWT
- [ ] `GET /api/v1/auth/oauth/providers` returns enabled providers
- [ ] Existing users are automatically linked on first OAuth login (by email match)
- [ ] New users are auto-created when OAuth email domain matches a company
- [ ] `google_id` and `microsoft_id` fields added to User entity and model
- [ ] Login page shows Google and Microsoft buttons (conditionally based on provider availability)
- [ ] Buttons are hidden when provider is not configured
- [ ] OAuth login respects company status (suspended/deactivated blocks login)
- [ ] OAuth login respects user status (deactivated blocks login)
- [ ] Alembic migration adds `google_id` and `microsoft_id` columns
- [ ] Configuration via environment variables documented in `.env.example`
- [ ] Unit tests for OAuth token verification and login logic
- [ ] Integration tests for OAuth endpoints (mocked token verification)
- [ ] Frontend tests for OAuth button visibility and flow
- [ ] i18n: button labels and error messages in English and Spanish

---

## Time Constraints

**Deadline:** None
**Estimated complexity:** Medium (2 OAuth integrations, entity extension, frontend buttons)
**Note:** Google and Microsoft use different token verification approaches — Google uses its own library, Microsoft uses standard OIDC discovery. Keep the token verification logic isolated behind a clean interface for each provider.

---

## Resolved Questions

1. **Token verification approach:** Use `google-auth` library for Google (handles key rotation) and `PyJWT` with JWKS for Microsoft (standard OIDC approach).
2. **Name population:** Always overwrite the User `name` field from the OAuth profile `name` claim on every login, keeping it in sync with the identity provider.
3. **Profile picture:** Not in E24 scope, defer to a future UX epic.
4. **Multi-tenant Microsoft:** Support both — if `MICROSOFT_TENANT_ID` is set to `common`, any Microsoft account can log in (email domain still validated against companies); if set to a specific tenant ID, only accounts from that tenant are accepted.
