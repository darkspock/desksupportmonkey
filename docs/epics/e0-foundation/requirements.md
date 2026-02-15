# Epic E0: Foundation

**Type:** Epic
**Status:** Validated
**Created:** 2026-02-15
**Priority:** Critical
**Depends on:** None (this is the root epic)

---

## Business Alignment

**Objective:** Enable all subsequent development by establishing the core platform infrastructure.

This is a technical foundation epic. No direct user-facing value, but nothing else can be built without it. Every other epic (E1-E8) depends on E0.

---

## Problem Statement

### Current Situation
The project has a folder structure, framework code (CQRS bus), and configuration files, but no runnable application. There is no database, no authentication, no API, and no way to serve requests.

### What E0 Delivers
A running FastAPI application with authentication, multi-tenancy, role-based access, and the base infrastructure needed to build business features on top.

---

## Proposed Solution

### US-001: Project Bootstrapping
**As a** developer
**I want** to run `make start` and have a working API
**So that** I can start building features immediately

**Acceptance Criteria:**
- [ ] `make start` launches PostgreSQL, Redis, Mailpit, MinIO via Docker Compose
- [ ] FastAPI app starts on port 8000
- [ ] `GET /health` returns `{"status": "healthy"}`
- [ ] `GET /docs` shows Swagger UI
- [ ] Alembic migrations run successfully with `make db-upgrade`
- [ ] If `SUPER_ADMIN_EMAIL` env var is set, a super admin user is auto-created on app startup (idempotent - skips if already exists)

### US-002: Magic Link Authentication
**As a** user with a corporate email
**I want** to receive a login link via email
**So that** I can access the platform without a password

**Acceptance Criteria:**
- [ ] `POST /api/v1/auth/magic-link` with `{"email": "user@company.com"}` sends an email with a login link
- [ ] If the email domain is not associated with any company, returns 403 with message "Only corporate email addresses are allowed"
- [ ] The magic link contains a JWT token valid for 24 hours
- [ ] The magic link is single-use (invalidated after first verification)
- [ ] `POST /api/v1/auth/verify` with the token returns an access JWT
- [ ] In development mode (Mailpit), the link appears in the Mailpit UI at localhost:8027
- [ ] Rate limited: max 5 magic link requests per email per hour

### US-003: JWT Session Management
**As an** authenticated user
**I want** my session to persist via JWT
**So that** I don't have to re-authenticate on every request

**Acceptance Criteria:**
- [ ] `POST /api/v1/auth/verify` returns `{"access_token": "...", "token_type": "bearer"}`
- [ ] JWT payload contains: `user_id`, `company_id`, `role`, `exp`
- [ ] Access token expires after 24 hours
- [ ] All protected endpoints require `Authorization: Bearer <token>` header
- [ ] Invalid/expired tokens return 401
- [ ] `GET /api/v1/auth/me` returns current user profile (id, email, name, role, company_id)
- [ ] No refresh token mechanism - when JWT expires, user requests a new magic link
- [ ] Concurrent sessions allowed - multiple valid JWTs can coexist for the same user

### US-004: Role-Based Access Control (RBAC)
**As the** platform
**I want** to enforce role-based permissions on every endpoint
**So that** users can only access what their role allows

**Acceptance Criteria:**
- [ ] Four roles enforced: `super_admin`, `admin`, `technician`, `employee`
- [ ] Role hierarchy: super_admin > admin > technician > employee
- [ ] FastAPI dependency `require_role(role)` that can be applied to any endpoint
- [ ] Super admin endpoints return 403 for non-super-admin users
- [ ] Admin endpoints return 403 for technician/employee users
- [ ] Role is embedded in JWT and validated on each request
- [ ] Company-scoped roles: admin/technician/employee are scoped to their company

### US-005: Multi-Tenancy Base
**As the** platform
**I want** all data to be isolated by company
**So that** companies cannot see each other's data

**Acceptance Criteria:**
- [ ] All tenant-scoped tables have a `company_id` column (indexed)
- [ ] `BaseRepository` automatically filters by `company_id` from the JWT context
- [ ] A user from Company A cannot access data from Company B (even by guessing IDs)
- [ ] Super admin endpoints can query across companies
- [ ] `company_id` is extracted from JWT and injected into the request context

### US-006: API Response Standards
**As a** frontend developer
**I want** consistent API response formats
**So that** I can build a predictable client

**Acceptance Criteria:**
- [ ] Success responses: `{"data": {...}, "meta": {...}}`
- [ ] List responses include pagination: `{"data": [...], "meta": {"page": 1, "page_size": 20, "total": 100}}`
- [ ] Error responses: `{"error": {"code": "ERROR_CODE", "message": "Human readable message"}}`
- [ ] 400 validation errors include field-level details
- [ ] 401 for unauthenticated, 403 for unauthorized, 404 for not found
- [ ] CORS configured for frontend URL

### US-007: Database Foundation
**As a** developer
**I want** a solid database setup with migrations
**So that** schema changes are versioned and reproducible

**Acceptance Criteria:**
- [ ] SQLAlchemy models use ULID as primary keys
- [ ] All models include: `id`, `created_at`, `updated_at`
- [ ] `Base` declarative base shared across all models
- [ ] Alembic configured for autogenerate migrations
- [ ] `make db-migrate msg="description"` creates a new migration
- [ ] `make db-upgrade` applies all pending migrations
- [ ] Connection pooling configured (pool_size=20, max_overflow=30)

### US-008: Celery + Redis Base
**As a** developer
**I want** Celery configured and connected to Redis
**So that** async tasks (reports) can be added later

**Acceptance Criteria:**
- [ ] Celery app configured with Redis broker
- [ ] `make queue` starts a Celery worker
- [ ] Task routes configured for `reports` queue
- [ ] Task serialization: JSON
- [ ] Task time limit: 5 minutes
- [ ] A test task can be enqueued and executed successfully
- [ ] Periodic task configured: cleanup expired/used magic links older than 7 days

### US-009: MinIO (S3) Base
**As a** developer
**I want** S3 client configured and connected to MinIO
**So that** file storage (reports) can be added later

**Acceptance Criteria:**
- [ ] boto3 S3 client configured with MinIO endpoint
- [ ] `dsm-reports` bucket created on startup (or via setup script)
- [ ] Upload, download, and signed URL generation work against local MinIO
- [ ] MinIO Console accessible at localhost:9001

---

## Entities

| Entity | Description | Owned by E0? |
|---|---|---|
| `User` | Platform user (email, name, role, company_id) | Yes |
| `MagicLink` | Login token (token, email, expires_at, used_at) | Yes |
| `Company` | Minimal: id and name only (full CRUD in E1) | Partial (schema only, no API) |

### User Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | Primary key |
| `email` | string | Unique, indexed |
| `name` | string | Nullable (set on first login or by admin) |
| `role` | enum | `super_admin`, `admin`, `technician`, `employee` |
| `company_id` | ULID | FK to Company, nullable for super_admin |
| `is_active` | boolean | Default true |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

### MagicLink Entity

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | Primary key |
| `email` | string | Indexed |
| `token` | string | Unique, indexed (JWT or random) |
| `expires_at` | datetime | created_at + 24 hours |
| `used_at` | datetime | Nullable, set on verification |
| `created_at` | datetime | Auto |

### Company Entity (minimal for E0)

| Field | Type | Notes |
|---|---|---|
| `id` | ULID | Primary key |
| `name` | string | Company name |
| `is_active` | boolean | Default true |
| `created_at` | datetime | Auto |
| `updated_at` | datetime | Auto |

Note: Company email domains, contact person, departments, and full CRUD will be added in E1.

---

## Use Cases

### UC-001: Request Magic Link
**Actor:** Anonymous user
**Preconditions:** User knows their corporate email

**Main Flow:**
1. User enters email on login page
2. System checks if email domain matches any active company
3. System creates a MagicLink record
4. System sends email with login URL containing the token
5. System returns 200 with message "Check your email"

**Alternative Flows:**
- A1: Email domain not associated with any company -> 403 "Only corporate email addresses are allowed"
- A2: User already has 5 pending magic links in the last hour -> 429 "Too many requests"

**Error Scenarios:**
- E1: SMTP server unreachable -> 500, log error, do not create MagicLink record

### UC-002: Verify Magic Link
**Actor:** User clicking the link from email
**Preconditions:** Valid, unused, non-expired magic link token

**Main Flow:**
1. User clicks link, frontend calls `POST /api/v1/auth/verify` with token
2. System validates token exists, is unused, and not expired
3. System marks MagicLink as used (sets `used_at`)
4. If user does not exist: create User with `employee` role in the matching company
5. System generates JWT access token
6. System returns access token

**Alternative Flows:**
- A1: Token already used -> 401 "Link already used"
- A2: Token expired -> 401 "Link expired"
- A3: Token not found -> 401 "Invalid link"

### UC-003: Access Protected Endpoint
**Actor:** Authenticated user
**Preconditions:** Valid JWT in Authorization header

**Main Flow:**
1. Request hits a protected endpoint
2. RBAC dependency extracts and validates JWT
3. Dependency verifies role meets minimum required role
4. Dependency injects `company_id` into request context
5. Request proceeds to handler

**Alternative Flows:**
- A1: No Authorization header -> 401
- A2: Invalid/expired JWT -> 401
- A3: Role insufficient -> 403
- A4: User deactivated (is_active=false) -> 403

---

## Collateral Impact

| Component | Impact | Action Required |
|---|---|---|
| All future epics | Foundation for everything | Must be stable and well-tested |
| Docker Compose | Already exists, needs verification | Verify all services start correctly |
| Core config | Already adapted | Verify all settings load correctly |

---

## Bounded Context

This epic creates the `auth_bc` bounded context:

```
src/auth_bc/
├── user/
│   ├── domain/
│   │   └── entities.py         # User entity
│   ├── application/
│   │   ├── commands/
│   │   │   └── create_user.py  # CreateUser command + handler
│   │   └── queries/
│   │       └── get_user.py     # GetUser query + handler
│   └── infrastructure/
│       ├── models.py           # UserModel (SQLAlchemy)
│       └── repository.py       # UserRepository
├── magic_link/
│   ├── domain/
│   │   └── entities.py         # MagicLink entity
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_magic_link.py
│   │   │   └── verify_magic_link.py
│   │   └── queries/
│   └── infrastructure/
│       ├── models.py           # MagicLinkModel
│       └── repository.py       # MagicLinkRepository
```

HTTP layer:
```
adapters/http/api/auth/
├── routers.py        # Auth routes (magic-link, verify, me)
├── dependencies.py   # require_role(), get_current_user()
└── schemas.py        # Request/response Pydantic models
```

---

## Definition of Done

- [ ] `make start` boots all services without errors
- [ ] `make db-upgrade` creates all tables
- [ ] Magic link flow works end-to-end (request -> email in Mailpit -> verify -> JWT)
- [ ] RBAC blocks unauthorized access
- [ ] Multi-tenancy isolates data by company
- [ ] API responses follow standard format
- [ ] Celery worker starts and can execute a test task
- [ ] MinIO bucket exists and accepts uploads
- [ ] Health check returns 200
- [ ] All endpoints documented in Swagger
- [ ] Unit tests for auth flow (happy path + error cases)
- [ ] Integration tests for magic link verification

---

## Time Constraints

**Deadline:** None (foundation, must be right)
**Estimated complexity:** Medium
**Note:** Rushing this will create debt that slows every subsequent epic.

---

## Open Questions

None - all decisions already captured in functional and technical requirements.
