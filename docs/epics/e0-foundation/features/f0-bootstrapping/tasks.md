# Implementation Tasks: F0 - Bootstrapping

**Requirement:** [../requirements.md](../requirements.md)
**Solution Design:** [design.md](design.md)
**Created:** 2026-02-15
**Total Tasks:** 11
**Estimated Complexity:** M

---

## Summary

| Phase | Tasks | Complexity |
|---|---|---|
| 1. Domain | 1 | S |
| 2. Infrastructure | 2 | M |
| 3. Application | 0 | N/A |
| 4. HTTP | 4 | M |
| 5. Tests | 3 | M |
| 6. Configuration | 1 | S |

---

## Phase 1: Domain Layer

### TASK-F0-001: Create Base Model Mixins

**Phase:** Domain
**Complexity:** S
**Dependencies:** None

**Description:**
Create reusable mixins for model identity and timestamps. ULIDMixin provides unique identifiers using ULID format (sortable, timestamp-based). TimestampMixin tracks record creation and modification times with automatic updates.

**File:** `src/core/mixins.py`

**Acceptance Criteria:**
- [ ] ULIDMixin class implemented with `id` as primary key (String(26))
- [ ] ULID generation uses `ulid.new().str` as default factory
- [ ] TimestampMixin class implemented with `created_at` and `updated_at` fields
- [ ] Both fields use `func.now()` with timezone awareness
- [ ] `updated_at` has `onupdate=func.now()` for automatic updates
- [ ] Both mixins inherit from proper SQLAlchemy declarative base
- [ ] Type hints included for all fields

---

## Phase 2: Infrastructure Layer

### TASK-F0-002: Create SQLAlchemy Models

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-F0-001

**Description:**
Implement three core domain models: CompanyModel for tenant isolation, UserModel for authentication and authorization, and MagicLinkModel for passwordless authentication. All models use the ULIDMixin and TimestampMixin for consistency.

**Files:**
- `src/company_bc/company/infrastructure/models.py`
- `src/auth_bc/user/infrastructure/models.py`
- `src/auth_bc/magic_link/infrastructure/models.py`

**Acceptance Criteria:**
- [ ] CompanyModel created with fields: name (String(255), not null), subdomain (String(63), unique, not null), is_active (Boolean, default True)
- [ ] CompanyModel uses ULIDMixin and TimestampMixin
- [ ] UserModel created with fields: company_id (FK to companies.id), email (String(255), not null), full_name (String(255), not null), role (Enum: OWNER/ADMIN/AGENT), is_active (Boolean, default True)
- [ ] UserModel uses ULIDMixin and TimestampMixin
- [ ] UserModel has relationship to CompanyModel (back_populates)
- [ ] MagicLinkModel created with fields: user_id (FK to users.id), token (String(64), unique, not null), expires_at (DateTime(timezone=True), not null), used_at (DateTime(timezone=True), nullable)
- [ ] MagicLinkModel uses ULIDMixin and TimestampMixin
- [ ] MagicLinkModel has relationship to UserModel
- [ ] All foreign keys have proper CASCADE constraints
- [ ] All models have __tablename__ defined
- [ ] Type hints included for all fields and relationships

### TASK-F0-003: Create Initial Database Migration

**Phase:** Infrastructure
**Complexity:** M
**Dependencies:** TASK-F0-002

**Description:**
Generate Alembic migration for all three tables with proper indexes and foreign key constraints. Includes performance indexes for common query patterns and unique constraints for business rules.

**File:** `src/infrastructure/database/migrations/versions/001_initial_schema.py`

**Acceptance Criteria:**
- [ ] Migration creates `companies` table with all fields from CompanyModel
- [ ] Unique index on companies.subdomain
- [ ] Migration creates `users` table with all fields from UserModel
- [ ] Foreign key from users.company_id to companies.id with CASCADE on delete
- [ ] Composite unique index on (company_id, email) in users table
- [ ] Index on users.email for login lookups
- [ ] Migration creates `magic_links` table with all fields from MagicLinkModel
- [ ] Foreign key from magic_links.user_id to users.id with CASCADE on delete
- [ ] Unique index on magic_links.token
- [ ] Index on (token, expires_at) for validation queries
- [ ] Index on (user_id, used_at) for audit queries
- [ ] Migration includes proper downgrade() function to drop all tables and indexes
- [ ] Migration tested with upgrade and downgrade commands

---

## Phase 4: HTTP Layer

### TASK-F0-004: Create Response Schemas

**Phase:** HTTP
**Complexity:** S
**Dependencies:** None

**Description:**
Define standard Pydantic response schemas for API consistency. Includes success responses, paginated lists, and error responses with proper RFC 9457 Problem Details format.

**File:** `src/adapters/http/schemas/responses.py`

**Acceptance Criteria:**
- [ ] SuccessResponse[T] generic schema with data field
- [ ] PaginationMeta schema with total, page, per_page, total_pages fields
- [ ] ListResponse[T] generic schema with data (list) and meta (PaginationMeta) fields
- [ ] ErrorDetail schema with field (optional) and message fields
- [ ] ErrorResponse schema with type, title, status, detail, errors (list of ErrorDetail, optional)
- [ ] All schemas use Pydantic v2 ConfigDict with from_attributes=True
- [ ] Type hints use proper Generic typing
- [ ] Schemas are JSON-serializable

### TASK-F0-005: Create Error Handler Middleware

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-F0-004

**Description:**
Implement FastAPI middleware to catch exceptions and transform them into standardized error responses. Handles validation errors, not found errors, and unexpected exceptions with proper logging.

**File:** `src/adapters/http/middleware/error_handler.py`

**Acceptance Criteria:**
- [ ] Middleware function registered with FastAPI app
- [ ] Catches HTTPException and returns ErrorResponse with proper status code
- [ ] Catches RequestValidationError (422) and maps to ErrorResponse with field-level errors
- [ ] Catches generic Exception (500) and returns sanitized ErrorResponse
- [ ] Logs all 500 errors with full traceback
- [ ] Does not expose internal error details in production
- [ ] Returns proper content-type: application/json
- [ ] Uses RFC 9457 type URIs (e.g., about:blank for generic errors)

### TASK-F0-006: Create Health Check Endpoint

**Phase:** HTTP
**Complexity:** S
**Dependencies:** TASK-F0-004

**Description:**
Implement health check endpoint for monitoring and load balancer health checks. Verifies database connectivity and returns system status.

**File:** `src/adapters/http/api/health.py`

**Acceptance Criteria:**
- [ ] GET /health endpoint returns 200 with status, version, database status
- [ ] Database check executes simple SELECT 1 query
- [ ] Returns 503 if database is unreachable
- [ ] Response uses SuccessResponse schema
- [ ] Endpoint does not require authentication
- [ ] Response includes timestamp
- [ ] Version read from environment or hardcoded placeholder

### TASK-F0-007: Create FastAPI Application Factory

**Phase:** HTTP
**Complexity:** M
**Dependencies:** TASK-F0-005, TASK-F0-006

**Description:**
Implement app factory pattern for FastAPI application initialization. Configures CORS, registers middleware, includes routers, and verifies database connection on startup.

**File:** `src/app.py`

**Acceptance Criteria:**
- [ ] create_app() factory function returns configured FastAPI instance
- [ ] CORS middleware configured with allowed origins from environment
- [ ] Error handler middleware registered
- [ ] Health router included with /health prefix
- [ ] Startup event handler verifies database connection
- [ ] Startup handler logs successful initialization
- [ ] App metadata includes title, description, version
- [ ] Database session dependency configured
- [ ] Graceful error handling if database unavailable on startup

---

## Phase 5: Tests

### TASK-F0-008: Create Domain Layer Tests

**Phase:** Tests
**Complexity:** S
**Dependencies:** TASK-F0-001

**Description:**
Unit tests for mixins to ensure ULID generation and timestamp behavior work correctly.

**File:** `tests/unit/core/test_mixins.py`

**Acceptance Criteria:**
- [ ] Test ULIDMixin generates valid 26-character ULID
- [ ] Test ULIDMixin IDs are unique across instances
- [ ] Test TimestampMixin sets created_at on instantiation
- [ ] Test TimestampMixin sets updated_at on instantiation
- [ ] Test updated_at changes on record update (integration with SQLAlchemy)
- [ ] All tests use pytest fixtures for database session

### TASK-F0-009: Create Infrastructure Layer Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-F0-002, TASK-F0-003

**Description:**
Integration tests for SQLAlchemy models and database migration. Verifies relationships, constraints, and indexes work as expected.

**Files:**
- `tests/integration/infrastructure/test_models.py`
- `tests/integration/infrastructure/test_migrations.py`

**Acceptance Criteria:**
- [ ] Test CompanyModel CRUD operations
- [ ] Test UserModel CRUD with company relationship
- [ ] Test MagicLinkModel CRUD with user relationship
- [ ] Test unique constraint on companies.subdomain
- [ ] Test unique constraint on (company_id, email) in users
- [ ] Test cascade delete from company to users
- [ ] Test cascade delete from user to magic_links
- [ ] Test migration applies cleanly to empty database
- [ ] Test migration downgrades without errors
- [ ] All tests use pytest fixtures with transaction rollback

### TASK-F0-010: Create HTTP Layer Tests

**Phase:** Tests
**Complexity:** M
**Dependencies:** TASK-F0-004, TASK-F0-005, TASK-F0-006, TASK-F0-007

**Description:**
Integration tests for HTTP layer including response schemas, error handling, health check, and application initialization.

**Files:**
- `tests/integration/http/test_error_handler.py`
- `tests/integration/http/test_health.py`
- `tests/unit/http/test_response_schemas.py`

**Acceptance Criteria:**
- [ ] Test response schemas serialize correctly
- [ ] Test error handler returns 400 for bad requests
- [ ] Test error handler returns 404 for not found
- [ ] Test error handler returns 422 for validation errors with field details
- [ ] Test error handler returns 500 for unhandled exceptions
- [ ] Test error handler does not leak internal errors
- [ ] Test GET /health returns 200 with proper structure
- [ ] Test GET /health returns 503 when database unavailable
- [ ] Test FastAPI app initializes successfully
- [ ] Test CORS headers present in responses
- [ ] All tests use TestClient from FastAPI

---

## Phase 6: Configuration

### TASK-F0-011: Create Environment Configuration Template

**Phase:** Configuration
**Complexity:** S
**Dependencies:** None

**Description:**
Create .env.example file with all required environment variables for bootstrapping phase. Includes database connection, CORS settings, and application configuration.

**File:** `.env.example`

**Acceptance Criteria:**
- [ ] DATABASE_URL with PostgreSQL example
- [ ] CORS_ORIGINS with localhost examples
- [ ] APP_ENV (development/staging/production)
- [ ] APP_VERSION placeholder
- [ ] LOG_LEVEL configuration
- [ ] All variables have descriptive comments
- [ ] Sensitive values use placeholder format
- [ ] File includes setup instructions at top

---

## Notes

- All code must follow PEP 8 and project coding standards
- Use type hints consistently across all modules
- All database operations should use async/await pattern
- Error messages must be user-friendly and not expose internal details
- Tests must be isolated and use fixtures for database state
- Migration naming: `{sequence}_{description}.py`
- ULID format: 26 characters, timestamp + randomness, sortable
