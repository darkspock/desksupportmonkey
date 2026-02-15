# Feature F1: Authentication & Authorization

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 1
**Dependencies:** F0 (Bootstrapping)
**Complexity:** L

---

## Scope

### Included
- `POST /api/v1/auth/magic-link` - Request magic link
- `POST /api/v1/auth/verify` - Verify token, return JWT
- `GET /api/v1/auth/me` - Current user profile
- Magic link email sending via SMTP (Mailpit in dev)
- JWT generation and validation
- Auto-create user on first login (employee role)
- Super admin auto-creation via `SUPER_ADMIN_EMAIL` env var
- Rate limiting: max 5 magic link requests per email per hour
- `require_role()` FastAPI dependency
- `get_current_user()` FastAPI dependency
- Multi-tenancy: `company_id` extraction from JWT into request context
- `TenantBaseRepository` that auto-filters by `company_id`
- `auth_bc` bounded context (domain, application, infrastructure layers)

### Excluded (in other features)
- User CRUD / management (E1)
- Company CRUD / management (E1)
- Celery tasks (F2)
- MinIO (F2)

---

## User Value

After F1:
- A user with a corporate email can request a magic link and log in
- The platform enforces who can access what based on roles
- Companies cannot see each other's data
- Super admin exists and can access platform-level endpoints

---

## Acceptance Criteria

### Magic Link Flow
- [ ] `POST /api/v1/auth/magic-link` with valid company email sends email via SMTP
- [ ] Email contains a link with format: `{FRONTEND_URL}/auth/verify?token={token}`
- [ ] Magic link token is valid for 24 hours
- [ ] Magic link is single-use (returns 401 if used again)
- [ ] Unknown email domain returns 403 "Only corporate email addresses are allowed"
- [ ] 6th request in 1 hour from same email returns 429

### Token Verification
- [ ] `POST /api/v1/auth/verify` with valid token returns `{"data": {"access_token": "...", "token_type": "bearer"}}`
- [ ] If user doesn't exist, creates user with `employee` role in the matching company
- [ ] If user exists, returns JWT for existing user
- [ ] Expired token returns 401 "Link expired"
- [ ] Used token returns 401 "Link already used"
- [ ] Invalid token returns 401 "Invalid link"

### JWT & Session
- [ ] JWT payload: `user_id`, `company_id`, `role`, `exp`
- [ ] JWT expires after 24 hours
- [ ] Multiple JWTs can coexist for the same user (concurrent sessions)
- [ ] `GET /api/v1/auth/me` returns user profile with standard response format

### RBAC
- [ ] `require_role("admin")` blocks employee and technician
- [ ] `require_role("technician")` blocks employee
- [ ] `require_role("employee")` allows all authenticated users
- [ ] `require_role("super_admin")` blocks all non-super-admin
- [ ] Missing/invalid Authorization header returns 401
- [ ] Insufficient role returns 403
- [ ] Deactivated user (is_active=false) returns 403

### Multi-Tenancy
- [ ] `company_id` extracted from JWT and available in request context
- [ ] `TenantBaseRepository` filters all queries by `company_id`
- [ ] Super admin can query without company filter
- [ ] User from Company A gets 404 when requesting Company B's resources

### Super Admin Bootstrap
- [ ] If `SUPER_ADMIN_EMAIL` is set in env, super admin user is created on app startup
- [ ] Idempotent: skips creation if user already exists
- [ ] Super admin has no `company_id` (platform-level)

---

## Technical Scope

### Entities (used from F0)
- User (add business logic, no schema changes)
- MagicLink (add business logic, no schema changes)
- Company (read-only, for domain matching)

### Key Components

```
src/auth_bc/
├── user/
│   ├── domain/
│   │   └── entities.py              # User domain entity
│   ├── application/
│   │   ├── commands/
│   │   │   └── create_user.py       # CreateUser + handler
│   │   └── queries/
│   │       └── get_user_by_email.py # GetUserByEmail + handler
│   └── infrastructure/
│       ├── models.py                # UserModel (from F0)
│       └── repository.py           # UserRepository
├── magic_link/
│   ├── domain/
│   │   └── entities.py              # MagicLink domain entity
│   ├── application/
│   │   ├── commands/
│   │   │   ├── create_magic_link.py # CreateMagicLink + handler (sends email)
│   │   │   └── verify_magic_link.py # VerifyMagicLink + handler (returns JWT)
│   │   └── queries/
│   └── infrastructure/
│       ├── models.py                # MagicLinkModel (from F0)
│       └── repository.py           # MagicLinkRepository

adapters/http/api/auth/
├── routers.py                       # POST magic-link, POST verify, GET me
├── dependencies.py                  # require_role(), get_current_user()
└── schemas.py                       # MagicLinkRequest, VerifyRequest, UserResponse

core/
├── email.py                         # SMTP email service
└── tenant.py                        # TenantBaseRepository, tenant context
```

---

## Notes

- This is the largest feature in E0. If it becomes unwieldy during implementation, the natural split point is: (a) magic link + JWT, (b) RBAC + multi-tenancy. But they share the same JWT dependency so keeping them together avoids duplication.
- The email service should be a simple abstraction (interface) so it can be swapped for production SMTP later.
