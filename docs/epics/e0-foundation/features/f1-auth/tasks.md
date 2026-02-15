# Implementation Tasks: Authentication & Authorization (F1)

**Requirement:** [requirements.md](./requirements.md)
**Solution Design:** [design.md](./design.md)
**Created:** 2026-02-15
**Total Tasks:** 28
**Estimated Complexity:** L

---

## Summary

| Phase | Tasks | Complexity |
|---|---|---|
| 1. Domain | 7 | M |
| 2. Infrastructure | 5 | M |
| 3. Application | 5 | M |
| 4. HTTP | 5 | M |
| 5. Tests | 4 | L |
| 6. Configuration | 2 | S |

---

## Phase 1: Domain Layer

### TASK-F1-001: Create UserRole Enum

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create the UserRole enumeration with hierarchical role definitions for the system. This enum will be used throughout the authentication and authorization system to define user permissions.

**File:** `src/auth_bc/user/domain/enums.py`

**Acceptance Criteria:**
- [ ] Enum contains SUPER_ADMIN, ADMIN, TECHNICIAN, EMPLOYEE values
- [ ] Each enum value has appropriate string representation
- [ ] Enum is importable and usable in other modules
- [ ] Documentation includes role hierarchy description

---

### TASK-F1-002: Create User Entity

**Phase:** Domain
**Complexity:** M
**Dependencies:** TASK-F1-001

**Description:**
Implement the User domain entity with all required attributes and business methods. The entity should enforce domain rules and provide factory methods for creation.

**File:** `src/auth_bc/user/domain/entities.py`

**Acceptance Criteria:**
- [ ] Entity has id, email, name, role, company_id, is_active, created_at, updated_at attributes
- [ ] Factory method create() validates email format and sets defaults
- [ ] Method deactivate() sets is_active to False
- [ ] Method change_role() updates role with validation
- [ ] Entity is immutable except through defined methods
- [ ] All business rules are enforced at entity level

---

### TASK-F1-003: Create MagicLink Entity

**Phase:** Domain
**Complexity:** M
**Dependencies:** None

**Description:**
Implement the MagicLink domain entity for passwordless authentication. Include token generation, expiration logic, and usage tracking.

**File:** `src/auth_bc/magic_link/domain/entities.py`

**Acceptance Criteria:**
- [ ] Entity has id, email, token, expires_at, used_at, created_at attributes
- [ ] Factory method create() generates secure random token
- [ ] Factory method sets expiration to 15 minutes from creation
- [ ] Method mark_used() sets used_at timestamp
- [ ] Method is_expired() checks current time against expires_at
- [ ] Method is_used() checks if used_at is set
- [ ] Token generation uses cryptographically secure random

---

### TASK-F1-004: Create UserRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-F1-002

**Description:**
Define the repository interface for User entity persistence operations. This interface will be implemented by the infrastructure layer.

**File:** `src/auth_bc/user/domain/repository.py`

**Acceptance Criteria:**
- [ ] Abstract save(user: User) -> User method defined
- [ ] Abstract find_by_id(user_id: str) -> Optional[User] method defined
- [ ] Abstract find_by_email(email: str) -> Optional[User] method defined
- [ ] Interface uses proper type hints
- [ ] Documentation describes expected behavior for each method

---

### TASK-F1-005: Create MagicLinkRepositoryInterface

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-F1-003

**Description:**
Define the repository interface for MagicLink entity persistence operations including cleanup methods for expired links.

**File:** `src/auth_bc/magic_link/domain/repository.py`

**Acceptance Criteria:**
- [ ] Abstract save(magic_link: MagicLink) -> MagicLink method defined
- [ ] Abstract find_by_token(token: str) -> Optional[MagicLink] method defined
- [ ] Abstract count_recent_by_email(email: str, minutes: int) -> int method defined
- [ ] Abstract delete_older_than(minutes: int) -> int method defined
- [ ] Interface uses proper type hints
- [ ] Documentation describes rate limiting and cleanup behavior

---

### TASK-F1-006: Create CompanyDomainLookup Service

**Phase:** Domain
**Complexity:** M
**Dependencies:** None

**Description:**
Implement domain service to determine company_id based on email domain. This service provides cross-aggregate logic for user-company association.

**File:** `src/auth_bc/company_lookup/domain/service.py`

**Acceptance Criteria:**
- [ ] Method get_company_id_by_email_domain(email: str) -> Optional[str] implemented
- [ ] Service queries company repository for domain match
- [ ] Returns None if no company found for domain
- [ ] Email domain extraction handles edge cases
- [ ] Service is stateless and injectable

---

### TASK-F1-007: Create Domain Module __init__ Files

**Phase:** Domain
**Complexity:** S
**Dependencies:** TASK-F1-001 through TASK-F1-006

**Description:**
Create proper Python package structure with __init__.py files for all domain modules to enable clean imports.

**Files:**
- `src/auth_bc/__init__.py`
- `src/auth_bc/user/__init__.py`
- `src/auth_bc/user/domain/__init__.py`
- `src/auth_bc/magic_link/__init__.py`
- `src/auth_bc/magic_link/domain/__init__.py`
- `src/auth_bc/company_lookup/__init__.py`
- `src/auth_bc/company_lookup/domain/__init__.py`

**Acceptance Criteria:**
- [ ] All directories have __init__.py files
- [ ] Key exports are defined in __init__.py where appropriate
- [ ] Import paths work correctly from other modules
- [ ] No circular import issues

---

## Phase 2: Infrastructure Layer

### TASK-F1-008: Implement UserRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-F1-004

**Description:**
Implement the concrete UserRepository using SQLAlchemy and PostgreSQL. Include proper error handling and transaction management.

**File:** `src/auth_bc/user/infrastructure/repository.py`

**Acceptance Criteria:**
- [ ] Implements UserRepositoryInterface
- [ ] save() method handles both insert and update operations
- [ ] find_by_id() returns None if user not found
- [ ] find_by_email() is case-insensitive
- [ ] Proper exception handling for database errors
- [ ] Uses tenant-aware queries (extends TenantBaseRepository)
- [ ] Database session management is correct

---

### TASK-F1-009: Implement MagicLinkRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-F1-005

**Description:**
Implement the concrete MagicLinkRepository with efficient queries for token validation and rate limiting checks.

**File:** `src/auth_bc/magic_link/infrastructure/repository.py`

**Acceptance Criteria:**
- [ ] Implements MagicLinkRepositoryInterface
- [ ] save() persists magic link with all attributes
- [ ] find_by_token() uses indexed query for performance
- [ ] count_recent_by_email() filters by time window correctly
- [ ] delete_older_than() uses bulk delete for expired links
- [ ] Proper exception handling and logging
- [ ] Database session management is correct

---

### TASK-F1-010: Implement EmailService Interface and SMTP Implementation

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** None

**Description:**
Create email service abstraction and SMTP implementation for sending magic link emails. Support both development and production configurations.

**File:** `core/email.py`

**Acceptance Criteria:**
- [ ] EmailService abstract interface defined with send_email() method
- [ ] SMTPEmailService implements interface using smtplib
- [ ] send_magic_link_email() method with proper HTML template
- [ ] Configuration from environment variables (SMTP_HOST, SMTP_PORT, etc.)
- [ ] Development mode prints to console instead of sending
- [ ] Proper error handling for SMTP failures
- [ ] Email content includes magic link with proper formatting
- [ ] Configurable sender address and display name

---

### TASK-F1-011: Implement JWTService

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** None

**Description:**
Implement JWT token creation and validation service using HS256 algorithm. Include proper expiration handling and claim validation.

**File:** `core/jwt.py`

**Acceptance Criteria:**
- [ ] create_token(user_id: str, email: str, role: str, company_id: str) -> str method
- [ ] decode_token(token: str) -> dict method with validation
- [ ] Uses JWT_SECRET from environment variables
- [ ] Default token expiration of 24 hours (configurable)
- [ ] Tokens include sub, email, role, company_id claims
- [ ] Proper exception handling for invalid/expired tokens
- [ ] Uses PyJWT library with HS256 algorithm

---

### TASK-F1-012: Implement TenantContext and TenantBaseRepository

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** None

**Description:**
Create multi-tenancy support with context management and base repository class that automatically filters queries by company_id.

**File:** `core/tenant.py`

**Acceptance Criteria:**
- [ ] TenantContext class stores current company_id in context var
- [ ] set_tenant(company_id: str) method to set context
- [ ] get_tenant() -> Optional[str] method to retrieve context
- [ ] clear_tenant() method to reset context
- [ ] TenantBaseRepository base class for tenant-aware repositories
- [ ] Auto-filtering of queries by company_id when context is set
- [ ] Super admin bypass (no filtering when role is SUPER_ADMIN)
- [ ] Thread-safe context variable implementation

---

## Phase 3: Application Layer (CQRS)

### TASK-F1-013: Implement CreateMagicLinkCommand and Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-F1-003, TASK-F1-005, TASK-F1-006, TASK-F1-010

**Description:**
Implement CQRS command to create and send magic link for authentication. Include rate limiting and user validation logic.

**File:** `src/auth_bc/magic_link/application/commands/create_magic_link.py`

**Acceptance Criteria:**
- [ ] CreateMagicLinkCommand dataclass with email field
- [ ] CreateMagicLinkCommandHandler class with handle() method
- [ ] Rate limiting: max 3 links per 15 minutes per email
- [ ] User validation: check user exists and is active
- [ ] Company lookup by email domain
- [ ] Create magic link entity with 15-minute expiration
- [ ] Save to repository and send email via EmailService
- [ ] Return success/failure result with appropriate error messages
- [ ] Proper logging of command execution

---

### TASK-F1-014: Implement VerifyMagicLinkCommand and Handler

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-F1-003, TASK-F1-005, TASK-F1-011

**Description:**
Implement CQRS command to verify magic link token and generate JWT access token. Handle all validation and security checks.

**File:** `src/auth_bc/magic_link/application/commands/verify_magic_link.py`

**Acceptance Criteria:**
- [ ] VerifyMagicLinkCommand dataclass with token field
- [ ] VerifyMagicLinkCommandHandler class with handle() method
- [ ] Validate token exists in database
- [ ] Check token is not expired using is_expired()
- [ ] Check token is not already used using is_used()
- [ ] Mark token as used via mark_used()
- [ ] Load user by email and validate is_active
- [ ] Generate JWT using JWTService with user claims
- [ ] Return JWT token or validation error
- [ ] Proper logging and error handling

---

### TASK-F1-015: Implement GetCurrentUserQuery and Handler

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-F1-004

**Description:**
Implement CQRS query to retrieve current user information from database using user_id from JWT token.

**File:** `src/auth_bc/user/application/queries/get_current_user.py`

**Acceptance Criteria:**
- [ ] GetCurrentUserQuery dataclass with user_id field
- [ ] GetCurrentUserQueryHandler class with handle() method
- [ ] Find user by ID using UserRepository
- [ ] Return user entity or None if not found
- [ ] Validate user is_active
- [ ] Proper error handling for database errors
- [ ] Query is read-only (no mutations)

---

### TASK-F1-016: Create Application Layer __init__ Files

**Phase:** Application
**Complexity:** S
**Dependencies:** TASK-F1-013 through TASK-F1-015

**Description:**
Create proper Python package structure for application layer with clean exports of commands and queries.

**Files:**
- `src/auth_bc/user/application/__init__.py`
- `src/auth_bc/user/application/queries/__init__.py`
- `src/auth_bc/magic_link/application/__init__.py`
- `src/auth_bc/magic_link/application/commands/__init__.py`

**Acceptance Criteria:**
- [ ] All application directories have __init__.py files
- [ ] Commands and queries are properly exported
- [ ] Import paths work from HTTP layer
- [ ] No circular import issues

---

### TASK-F1-017: Create Command/Query Bus (Optional)

**Phase:** Application
**Complexity:** M
**Dependencies:** TASK-F1-013 through TASK-F1-015

**Description:**
Optionally create a simple command/query bus for decoupled handler invocation. This can be skipped for direct handler instantiation.

**File:** `core/cqrs.py`

**Acceptance Criteria:**
- [ ] CommandBus class with register_handler() and dispatch() methods
- [ ] QueryBus class with register_handler() and dispatch() methods
- [ ] Type-safe handler registration and invocation
- [ ] Dependency injection support for handlers
- [ ] Thread-safe handler registry
- [ ] Or document direct handler instantiation pattern if bus not used

---

## Phase 4: HTTP Layer

### TASK-F1-018: Create Auth Schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-F1-002

**Description:**
Define Pydantic schemas for API request/response validation in authentication endpoints.

**File:** `adapters/http/api/auth/schemas.py`

**Acceptance Criteria:**
- [ ] MagicLinkRequest schema with email field and validation
- [ ] VerifyRequest schema with token field
- [ ] TokenResponse schema with access_token and token_type fields
- [ ] UserResponse schema with id, email, name, role, company_id fields
- [ ] Proper Pydantic validators for email format
- [ ] Schema examples for OpenAPI documentation
- [ ] Exclude sensitive fields from UserResponse

---

### TASK-F1-019: Create Auth Dependencies

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-F1-011, TASK-F1-015, TASK-F1-012

**Description:**
Implement FastAPI dependencies for authentication and authorization including JWT validation and role-based access control.

**File:** `adapters/http/api/auth/dependencies.py`

**Acceptance Criteria:**
- [ ] get_current_user() dependency extracts and validates JWT from Authorization header
- [ ] Dependency uses JWTService to decode token
- [ ] Dependency executes GetCurrentUserQuery to load user
- [ ] Dependency sets TenantContext with user's company_id
- [ ] require_role() dependency factory for role-based authorization
- [ ] Role hierarchy enforced: super_admin > admin > technician > employee
- [ ] Proper HTTP 401 for authentication failures
- [ ] Proper HTTP 403 for authorization failures
- [ ] Clear error messages in exceptions

---

### TASK-F1-020: Create Auth Router

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-F1-013, TASK-F1-014, TASK-F1-015, TASK-F1-018, TASK-F1-019

**Description:**
Implement FastAPI router with all authentication endpoints including magic link creation, verification, and current user retrieval.

**File:** `adapters/http/api/auth/routers.py`

**Acceptance Criteria:**
- [ ] POST /api/v1/auth/magic-link endpoint creates magic link
- [ ] POST /api/v1/auth/verify endpoint verifies token and returns JWT
- [ ] GET /api/v1/auth/me endpoint returns current user (requires auth)
- [ ] Proper request/response schema validation
- [ ] HTTP status codes: 200 for success, 400 for validation, 401 for auth failures
- [ ] OpenAPI documentation with descriptions and examples
- [ ] Proper error handling with structured error responses
- [ ] Instantiate and invoke command/query handlers
- [ ] Router integrated into main FastAPI app

---

### TASK-F1-021: Create Super Admin Auto-Creation

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-F1-002, TASK-F1-008

**Description:**
Implement startup logic to automatically create super admin user if SUPER_ADMIN_EMAIL environment variable is set and user doesn't exist.

**File:** `app.py` (or appropriate startup module)

**Acceptance Criteria:**
- [ ] Check for SUPER_ADMIN_EMAIL environment variable on startup
- [ ] Query UserRepository for existing user with that email
- [ ] If not exists, create User entity with SUPER_ADMIN role
- [ ] Set company_id to None for super admin (company-agnostic)
- [ ] Save user via UserRepository
- [ ] Log creation or skip if already exists
- [ ] Handle errors gracefully (log warning, don't crash app)
- [ ] Only run once during application startup

---

### TASK-F1-022: Create HTTP Layer __init__ Files

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-F1-018 through TASK-F1-020

**Description:**
Create proper Python package structure for HTTP/API layer.

**Files:**
- `adapters/__init__.py`
- `adapters/http/__init__.py`
- `adapters/http/api/__init__.py`
- `adapters/http/api/auth/__init__.py`

**Acceptance Criteria:**
- [ ] All adapter directories have __init__.py files
- [ ] Router is exported for easy import in main app
- [ ] Import paths work correctly
- [ ] No circular import issues

---

## Phase 5: Tests

### TASK-F1-023: Create Domain Layer Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-F1-001 through TASK-F1-006

**Description:**
Write comprehensive unit tests for all domain entities, value objects, and domain services.

**Files:**
- `tests/unit/auth_bc/user/domain/test_entities.py`
- `tests/unit/auth_bc/magic_link/domain/test_entities.py`
- `tests/unit/auth_bc/company_lookup/domain/test_service.py`

**Acceptance Criteria:**
- [ ] Test User entity factory method and business methods
- [ ] Test MagicLink entity token generation, expiration, and usage
- [ ] Test CompanyDomainLookup service with various email domains
- [ ] Test edge cases and validation errors
- [ ] Test immutability of entities
- [ ] 100% code coverage for domain layer
- [ ] Use pytest fixtures for test data
- [ ] Tests are fast and isolated (no database)

---

### TASK-F1-024: Create Infrastructure Layer Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-F1-008 through TASK-F1-012

**Description:**
Write integration tests for repositories, email service, JWT service, and tenant context using test database.

**Files:**
- `tests/integration/auth_bc/user/infrastructure/test_repository.py`
- `tests/integration/auth_bc/magic_link/infrastructure/test_repository.py`
- `tests/integration/core/test_email.py`
- `tests/integration/core/test_jwt.py`
- `tests/integration/core/test_tenant.py`

**Acceptance Criteria:**
- [ ] Test UserRepository CRUD operations with real database
- [ ] Test MagicLinkRepository queries and cleanup methods
- [ ] Test EmailService with mock SMTP server
- [ ] Test JWTService token creation and validation
- [ ] Test TenantContext isolation between requests
- [ ] Use pytest fixtures for database setup/teardown
- [ ] Use transaction rollback for test isolation
- [ ] Tests verify SQL queries are correct

---

### TASK-F1-025: Create Application Layer Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-F1-013 through TASK-F1-017

**Description:**
Write unit tests for command and query handlers using mocked dependencies.

**Files:**
- `tests/unit/auth_bc/magic_link/application/commands/test_create_magic_link.py`
- `tests/unit/auth_bc/magic_link/application/commands/test_verify_magic_link.py`
- `tests/unit/auth_bc/user/application/queries/test_get_current_user.py`

**Acceptance Criteria:**
- [ ] Test CreateMagicLinkCommand handler with rate limiting scenarios
- [ ] Test VerifyMagicLinkCommand handler with valid/expired/used tokens
- [ ] Test GetCurrentUserQuery handler with existing/missing users
- [ ] Mock all repository and service dependencies
- [ ] Test error handling and validation logic
- [ ] Test business rule enforcement
- [ ] Use pytest-mock for mocking
- [ ] Tests are fast and isolated

---

### TASK-F1-026: Create HTTP Layer Tests

**Phase:** Tests
**Complexity:** L
**Dependencies:** TASK-F1-018 through TASK-F1-021

**Description:**
Write end-to-end API tests for all authentication endpoints using TestClient.

**Files:**
- `tests/e2e/api/auth/test_auth_endpoints.py`
- `tests/e2e/api/auth/test_auth_flow.py`

**Acceptance Criteria:**
- [ ] Test POST /api/v1/auth/magic-link with valid/invalid emails
- [ ] Test POST /api/v1/auth/verify with valid/expired/used tokens
- [ ] Test GET /api/v1/auth/me with valid/invalid JWT
- [ ] Test complete auth flow: request link -> verify -> access protected endpoint
- [ ] Test authorization with different roles
- [ ] Test tenant isolation (user can't access other company data)
- [ ] Test rate limiting for magic link creation
- [ ] Use FastAPI TestClient with test database
- [ ] Tests verify HTTP status codes and response schemas
- [ ] Clean up test data after each test

---

## Phase 6: Configuration

### TASK-F1-027: Create Environment Configuration

**Phase:** Configuration
**Complexity:** S
**Dependencies:** None

**Description:**
Document all required environment variables and create .env.example file with sensible defaults.

**Files:**
- `.env.example`
- `docs/configuration.md`

**Acceptance Criteria:**
- [ ] JWT_SECRET with random default for development
- [ ] JWT_EXPIRATION_HOURS with default of 24
- [ ] SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
- [ ] SMTP_FROM_EMAIL and SMTP_FROM_NAME
- [ ] EMAIL_ENABLED (true/false for dev mode)
- [ ] SUPER_ADMIN_EMAIL for auto-creation
- [ ] DATABASE_URL for PostgreSQL connection
- [ ] Clear comments explaining each variable
- [ ] Sensitive values marked as "CHANGE_IN_PRODUCTION"
- [ ] Documentation includes setup instructions

---

### TASK-F1-028: Create Database Migrations

**Phase:** Configuration
**Complexity:** M
**Dependencies:** TASK-F1-002, TASK-F1-003

**Description:**
Create Alembic database migrations for users and magic_links tables with proper indexes and constraints.

**Files:**
- `migrations/versions/001_create_users_table.py`
- `migrations/versions/002_create_magic_links_table.py`

**Acceptance Criteria:**
- [ ] users table with all entity fields (id, email, name, role, company_id, is_active, created_at, updated_at)
- [ ] Unique constraint on email (case-insensitive)
- [ ] Index on company_id for tenant filtering
- [ ] magic_links table with all entity fields (id, email, token, expires_at, used_at, created_at)
- [ ] Unique index on token for fast lookup
- [ ] Index on email and created_at for rate limiting queries
- [ ] Proper foreign key constraints if needed
- [ ] Down migrations that cleanly remove tables
- [ ] Migrations are idempotent and reversible

---

## Notes

### Implementation Order
1. Start with Phase 1 (Domain) to establish core business logic
2. Move to Phase 2 (Infrastructure) to enable persistence
3. Implement Phase 3 (Application) for use cases
4. Build Phase 4 (HTTP) for external access
5. Complete Phase 5 (Tests) throughout development (TDD recommended)
6. Finalize Phase 6 (Configuration) for deployment

### Key Dependencies
- User entity must exist before UserRepository
- MagicLink entity must exist before MagicLinkRepository
- Repositories must exist before command handlers
- Command/query handlers must exist before HTTP endpoints
- All layers must exist before comprehensive tests

### Testing Strategy
- Unit tests for domain logic (no mocks needed)
- Integration tests for infrastructure (use test database)
- Unit tests for application layer (mock dependencies)
- E2E tests for HTTP layer (full stack with test database)
- Aim for >80% code coverage overall

### Security Considerations
- Never log tokens or passwords
- Use environment variables for all secrets
- Validate all inputs at schema level
- Rate limit magic link creation
- Expire magic links after 15 minutes
- Mark tokens as used after verification
- Use secure random token generation
- Implement proper CORS configuration
- Use HTTPS in production

### Performance Considerations
- Index email fields for fast user lookup
- Index token field for magic link verification
- Use connection pooling for database
- Cache JWT public keys if using asymmetric algorithms
- Implement cleanup job for expired magic links
- Consider Redis for rate limiting in production

### Multi-Tenancy Considerations
- Always filter by company_id in queries (except super admin)
- Set tenant context from JWT claims
- Validate user can only access their company data
- Super admin can access all companies
- Test tenant isolation thoroughly
