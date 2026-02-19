# Feature: MCP Server Core

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F1
**Dependencies:** F0 (API Key Management)
**Complexity:** L

---

## Scope

### Included

- MCP server setup using the `mcp` Python SDK in `adapters/mcp/server.py`
- API key authentication middleware in `adapters/mcp/auth.py` -- resolves API key to user, sets tenant context (`set_tenant()`), updates `last_used_at`
- Tool registry with role-based filtering in `adapters/mcp/registry.py` -- each tool declares a minimum role; `tools/list` only returns tools the authenticated user's role can access
- stdio transport (local development mode)
- `mcp` SDK dependency added to `pyproject.toml`
- MCP configuration in `core/config.py`: `MCP_ENABLED` (bool), `MCP_TRANSPORT` (str: "stdio" or "sse")
- Entry point: `python -m adapters.mcp.server --transport stdio`
- `adapters/mcp/__init__.py` and `adapters/mcp/__main__.py` for module execution
- Logging of connection events (connect, disconnect, auth success/failure)
- Unit tests for auth middleware (key resolution, invalid key rejection, tenant context)
- Unit tests for registry (role filtering, tool registration)

### Excluded

- Individual tool implementations (F2, F3, F4, F5) -- the server boots with an empty tool list
- SSE transport (F6)
- Frontend API keys page (F7)
- JWT passthrough authentication (future enhancement)

---

## User Value

After this feature, the MCP server can boot via stdio, authenticate an API key, resolve the user and company context, and return a (currently empty) filtered tool list. This is the infrastructure foundation that all tool features (F2-F5) plug into. Developers can verify the connection flow end-to-end before any tools are implemented.

---

## Acceptance Criteria

1. **Server boots:** Running `python -m adapters.mcp.server --transport stdio` starts the MCP server without errors
2. **API key authentication:** Connecting with a valid API key resolves the correct user and sets the tenant context (company_id)
3. **Invalid key rejected:** Connecting with an invalid or revoked API key returns an authentication error
4. **`last_used_at` updated:** After successful authentication, the API key's `last_used_at` timestamp is updated
5. **Tools list empty:** `tools/list` returns an empty list (no tools registered yet) -- confirms the registry works but has no tools
6. **Role filtering works:** When tools are registered (by tests or manually), the registry filters them based on the authenticated user's role; tools above the user's role are hidden
7. **Tenant isolation:** The tenant context (`set_tenant()`) is correctly set from the authenticated user's `company_id`, ensuring all downstream queries are scoped
8. **Logging:** Connection events (connect, auth success, auth failure, disconnect) are logged with user_id and timestamp
9. **Dependency added:** `mcp` SDK is pinned to an exact version in `pyproject.toml`
10. **Config flags:** `MCP_ENABLED` and `MCP_TRANSPORT` are available in `core/config.py` with sensible defaults (`MCP_ENABLED=false`, `MCP_TRANSPORT=stdio`)
11. **Unit tests pass:** Auth middleware and registry have full unit test coverage
12. **`make test` and `make lint` pass** with no regressions

---

## Technical Scope

### Entities (owned)

- None (this feature creates adapter infrastructure, not domain entities)

### Entities (used)

- `ApiKey` -- from `mcp_bc`, used for authentication lookup
- `User` -- from `auth_bc`, resolved from the API key to get role and company_id

### Key Components

| Component | Path | Description |
|-----------|------|-------------|
| MCP server | `adapters/mcp/server.py` | Server setup, tool registration orchestration, transport selection |
| Auth middleware | `adapters/mcp/auth.py` | API key lookup, bcrypt verify, user resolution, `set_tenant()`, `last_used_at` update |
| Tool registry | `adapters/mcp/registry.py` | Tool registration, role-based filtering for `tools/list` |
| Module entry | `adapters/mcp/__main__.py` | CLI entry point with `--transport` argument |
| Package init | `adapters/mcp/__init__.py` | Package marker |
| Config | `core/config.py` | `MCP_ENABLED`, `MCP_TRANSPORT` settings |
| Dependency | `pyproject.toml` | `mcp` SDK pinned version |
| Unit tests | `tests/unit/mcp/` | Tests for auth middleware, registry, role filtering |

---

## Notes

- The `mcp` Python SDK provides the `Server` class, transport handling, and JSON-RPC protocol. This feature configures the SDK -- it does not implement the MCP protocol from scratch.
- The auth middleware pattern mirrors the existing JWT middleware in the HTTP adapter: resolve credentials to a user, call `set_tenant()`, proceed.
- Role hierarchy for filtering: Employee < Technician < Admin < Super Admin. A tool with `min_role=Technician` is visible to Technicians, Admins, and Super Admins.
- The registry should support a simple decorator or registration function so tool modules (F2-F5) can register themselves without modifying `server.py`.
- stdio transport is sufficient for Claude Desktop and Cursor integration during development. SSE is deferred to F6 for production use.
- The MCP SDK is relatively new. Pin the exact version and document the tested client versions (Claude Desktop, Cursor) in the adapter module docstring.
