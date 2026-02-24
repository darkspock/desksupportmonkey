# Feature 0: Audit Foundation

**Parent Epic:** [../../requirements.md](../../requirements.md)
**Feature #:** 0
**Dependencies:** None
**Complexity:** M

## Scope

### Included

- New bounded context: `audit_bc` with `audit/domain`, `audit/application`, `audit/infrastructure` layers
- AuditEntry domain entity (immutable, with per-entry SHA-256 hash)
- AuditEntry infrastructure model + SQLAlchemy table (`audit_entries`)
- Audit repository (abstract + SQLAlchemy implementation)
- FastAPI middleware for automatic HTTP audit capture (POST/PUT/PATCH/DELETE)
- Explicit MCP tool call audit capture in MCP handler/dispatcher layer
- Alembic migration: `audit_entries` table with composite indexes
- Request body sanitization (redact sensitive fields)
- `ContextVar` mechanism for handlers to pass `changes` (before/after diff) to middleware
- Unit tests: AuditEntry entity, hash computation, middleware logic
- Integration tests: middleware captures HTTP requests, MCP capture

### Excluded (in other features)

- Audit log UI pages (F1)
- Audit log export (F1)
- Compliance tagging (F1)
- Compliance control catalog (F1)
- GDPR export/anonymization (F2)
- Retention policy and purge (F3)
- Integrity verification (F3)
- Feature gating/402 responses (F1 — capture runs for all plans)

## User Value

All write operations across the platform are automatically captured in a centralized, tamper-evident audit log. Even though there is no UI yet, audit data starts accumulating immediately — so when Enterprise features are activated, historical data is available from day one.

## User Stories Covered

- UC-001: Automatic Audit Capture (HTTP Middleware)
- UC-002: Automatic Audit Capture (MCP Tools)

## Acceptance Criteria

- [ ] All POST/PUT/PATCH/DELETE HTTP requests automatically generate an AuditEntry via middleware
- [ ] All MCP write tool calls automatically generate an AuditEntry via explicit capture
- [ ] AuditEntry includes: actor_id, actor_email, action, resource_type, resource_id, http_method, http_path, ip_address, user_agent, request_data (sanitized), response_status, changes (if available), hash, created_at
- [ ] Per-entry SHA-256 hash is computed from: `company_id + actor_id + action + resource_type + resource_id + created_at`
- [ ] AuditEntry is truly immutable — no UPDATE operations after creation
- [ ] Audit write uses a separate DB transaction (best-effort: if audit fails, business operation is not rolled back)
- [ ] Sensitive fields in request body are sanitized: `password`, `password_hash`, `token`, `magic_link`, `secret`, `stripe_secret_key`, `credentials`
- [ ] Unauthenticated requests (e.g., registration) create an entry with `actor_id = null`
- [ ] Failed requests (4xx/5xx) are still audited (records failed attempts)
- [ ] Middleware adds < 5ms overhead per request
- [ ] DB indexes created: `(company_id, created_at)`, `(company_id, actor_id, created_at)`, `(company_id, resource_type, resource_id)`

## Technical Scope

### Entities (owned by this feature)

- **AuditEntry** — Immutable audit log record with per-entry hash

### Key Components

#### Domain Layer (`src/audit_bc/audit/domain/`)

- `entities.py` — `AuditEntry` dataclass with `create()` classmethod + `compute_hash()` static method
- `repository.py` — `AuditRepositoryInterface` abstract class with methods: `save(entry)`, `find_by_id(id, company_id)`, `find_by_company(company_id, filters, pagination)`, `count_by_company(company_id, filters)`
- `enums.py` — Action constants (if needed), sanitized field list

#### Application Layer (`src/audit_bc/audit/application/`)

- `services/audit_service.py` — Service that creates AuditEntry from request metadata, computes hash, and persists via repository in a separate transaction
- `context.py` — `ContextVar` definitions for `audit_changes` (before/after diff) that handlers can set

#### Infrastructure Layer (`src/audit_bc/audit/infrastructure/`)

- `models.py` — `AuditEntryModel` SQLAlchemy model
- `repository.py` — `AuditRepository` SQLAlchemy implementation

#### HTTP Layer (`adapters/http/api/audit/`)

- `middleware.py` — `AuditMiddleware` that intercepts non-GET requests, extracts metadata, and calls `AuditService`

#### MCP Layer

- Explicit audit capture in MCP tool dispatcher/handler (location TBD based on MCP architecture)

#### Migration

- `alembic/versions/xxxx_create_audit_entries.py` — Create `audit_entries` table with all columns and composite indexes

## Notes

- The middleware approach uses `BaseHTTPMiddleware`. MCP mounted sub-apps may bypass this, which is why explicit MCP capture is also included.
- The `ContextVar` for `changes` allows command handlers to optionally provide before/after diffs without coupling to the audit system. The middleware checks the ContextVar after the handler completes.
- Hash computation is synchronous (inline, not deferred) to ensure integrity at write time.
- No `previous_hash` field — per-entry hash only. Chain linking is a future enhancement.
