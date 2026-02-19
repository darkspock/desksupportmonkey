# Feature: API Key Management

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F0
**Dependencies:** None
**Complexity:** M

---

## Scope

### Included

- New `mcp_bc` bounded context with `server` subdomain
- `api_keys` table via Alembic migration with columns: `id` (ULID PK), `user_id` (FK to users), `key_hash` (bcrypt, 128 chars), `name` (human label, max 100 chars), `created_at`, `last_used_at`, `is_active` (default true)
- Indexes on `user_id` for the `api_keys` table
- `ApiKey` domain entity in `src/mcp_bc/server/domain/entities.py`
- `ApiKeyRepositoryInterface` in `src/mcp_bc/server/domain/repository.py`
- `ApiKeyRepository` (SQLAlchemy) in `src/mcp_bc/server/infrastructure/repository.py`
- `ApiKeyModel` (SQLAlchemy ORM) in `src/mcp_bc/server/infrastructure/models.py`
- Command handler: `CreateApiKey` -- generates key with `dsm_` prefix + 40 random hex chars, stores bcrypt hash, returns raw key once
- Query handler: `ListApiKeys` -- returns user's keys (name, created_at, last_used_at, is_active) without raw key
- Command handler: `RevokeApiKey` -- sets `is_active = False`, revoked keys cannot be reactivated
- 3 HTTP endpoints on `/api/v1/auth/api-keys`:
  - `POST /api/v1/auth/api-keys` -- create API key (returns raw key once)
  - `GET /api/v1/auth/api-keys` -- list user's API keys (no raw key in response)
  - `DELETE /api/v1/auth/api-keys/{key_id}` -- revoke an API key
- Maximum 10 active API keys per user enforced at the command handler level
- Key format: `dsm_` + 40 random hex characters (44 chars total)
- Unit tests for all command/query handlers
- Integration tests for all 3 HTTP endpoints

### Excluded

- MCP server setup (F1)
- MCP tools (F2-F5)
- Frontend API keys page (F7)
- SSE transport (F6)
- JWT passthrough authentication for MCP

---

## User Value

Users can create, list, and revoke API keys that will be used to authenticate MCP client connections. This is the foundational prerequisite for all MCP functionality -- without API keys, the MCP server has no authentication mechanism. Showing the raw key only once at creation follows security best practices (same pattern as GitHub, AWS, etc.).

---

## Acceptance Criteria

1. **Migration:** Running `make db-upgrade` creates the `api_keys` table with all columns and constraints
2. **Create key:** `POST /api/v1/auth/api-keys` with `{ "name": "My Key" }` returns the raw API key (format `dsm_` + 40 hex chars) and key metadata; the raw key is only returned in this response
3. **List keys:** `GET /api/v1/auth/api-keys` returns all of the authenticated user's API keys with `name`, `created_at`, `last_used_at`, and `is_active` -- but never the raw key or hash
4. **Revoke key:** `DELETE /api/v1/auth/api-keys/{key_id}` sets the key's `is_active` to false; subsequent authentication attempts with the revoked key are rejected
5. **Max 10 keys:** Attempting to create an 11th active API key returns an error
6. **Tenant isolation:** Users can only list and revoke their own API keys; attempting to revoke another user's key returns 404
7. **Authentication required:** All 3 endpoints require a valid JWT (existing auth middleware)
8. **Unit tests pass:** All command/query handlers have unit tests covering happy path and edge cases (max keys, revoke nonexistent, revoke already revoked)
9. **Integration tests pass:** All 3 endpoints tested end-to-end against a real database
10. **`make test` and `make lint` pass** with no regressions

---

## Technical Scope

### Entities (owned)

- `ApiKey` -- domain entity in `src/mcp_bc/server/domain/entities.py`

### Entities (used)

- `User` -- from `auth_bc`, referenced via `user_id` foreign key

### Key Components

| Component | Path | Description |
|-----------|------|-------------|
| Migration | `alembic/versions/xxx_create_api_keys_table.py` | Creates `api_keys` table |
| Domain entity | `src/mcp_bc/server/domain/entities.py` | `ApiKey` dataclass |
| Domain repository | `src/mcp_bc/server/domain/repository.py` | `ApiKeyRepositoryInterface` (ABC) |
| ORM model | `src/mcp_bc/server/infrastructure/models.py` | `ApiKeyModel` (SQLAlchemy `Mapped` style) |
| Repository | `src/mcp_bc/server/infrastructure/repository.py` | `ApiKeyRepository` implementation |
| CreateApiKey | `src/mcp_bc/server/application/commands/create_api_key.py` | Command + handler |
| RevokeApiKey | `src/mcp_bc/server/application/commands/revoke_api_key.py` | Command + handler |
| ListApiKeys | `src/mcp_bc/server/application/queries/list_api_keys.py` | Query + handler |
| HTTP router | `adapters/http/api/auth/api_keys_router.py` | 3 endpoints under `/api/v1/auth/api-keys` |
| Unit tests | `tests/unit/mcp_bc/server/application/` | Tests for all handlers |
| Integration tests | `tests/integration/test_api_keys_endpoints.py` | Tests for all endpoints |

---

## Notes

- The key format (`dsm_` + 40 hex) makes it easy for secret scanners to detect leaked keys.
- Bcrypt is used for hashing because it is already a project dependency (used for password hashing in `auth_bc`).
- Revoked keys cannot be reactivated -- the user must create a new key. This simplifies the state model and audit trail.
- The `last_used_at` field is updated by the MCP auth middleware (F1), not by this feature. It will remain null until F1 is implemented.
- All handlers must inherit from the framework base classes (`Command`, `CommandHandler`, `Query`, `QueryHandler`) in `src/framework/`.
