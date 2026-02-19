# Feature: Auth & API Key MCP Tools

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F5
**Dependencies:** F1 (MCP Server Core), F0 (API Key Management)
**Complexity:** S

---

## Scope

### Included

5 MCP tools for authentication information and API key self-management, enabling AI assistants to manage their own credentials.

**Auth Tools** (`adapters/mcp/tools/auth.py`) -- 5 tools, minimum role: Employee

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `get_current_user` | `GET /api/v1/auth/me` | *(none)* |
| `set_password` | `POST /api/v1/auth/set-password` | password |
| `create_api_key` | `POST /api/v1/auth/api-keys` | name |
| `list_api_keys` | `GET /api/v1/auth/api-keys` | *(none)* |
| `revoke_api_key` | `DELETE /api/v1/auth/api-keys/{key_id}` | key_id |

Each tool reuses the existing application-layer command/query handlers from `auth_bc` and `mcp_bc`. No new business logic is created.

### Excluded

- All other tool groups (assets, requests, users, departments, companies, dashboard, reports, my)
- API key entity, repository, migration, and HTTP endpoints (F0)
- MCP server core setup (F1)
- SSE transport (F6)
- Any modifications to existing domain, application, or infrastructure layers

---

## User Value

An AI assistant connected via MCP can:
- Inspect the authenticated user's identity and role via `get_current_user`, enabling context-aware behavior.
- Set or update the user's password via `set_password`.
- Create new API keys for itself or other MCP clients via `create_api_key`, supporting self-provisioning workflows.
- List existing API keys to audit active credentials via `list_api_keys`.
- Revoke compromised or unused API keys via `revoke_api_key`, enabling security hygiene automation.

These tools allow the AI assistant to bootstrap and manage its own authentication lifecycle without requiring the user to visit the web UI.

---

## Acceptance Criteria

### get_current_user
- [ ] Returns the authenticated user's profile (id, email, name, role, company_id, department_id, is_active)
- [ ] Requires minimum Employee role
- [ ] Works with both API key and JWT authentication

### set_password
- [ ] Accepts a password string and updates the authenticated user's password
- [ ] Requires minimum Employee role
- [ ] Returns confirmation of success (not the password)
- [ ] Validates password requirements (if any exist in the handler)

### create_api_key
- [ ] Accepts a name parameter (human label, e.g., "Claude Desktop", "Cursor")
- [ ] Returns the raw API key exactly once in the tool result (format: `dsm_` prefix + 40 hex chars)
- [ ] Subsequent calls to `list_api_keys` do not expose the raw key (only metadata)
- [ ] Enforces the 10 active API key limit per user
- [ ] Requires minimum Employee role

### list_api_keys
- [ ] Returns list of the authenticated user's API keys with metadata: id, name, created_at, last_used_at, is_active
- [ ] Does not return key hashes or raw keys
- [ ] Requires minimum Employee role

### revoke_api_key
- [ ] Accepts key_id parameter
- [ ] Deactivates the specified API key (sets is_active to false)
- [ ] Returns 404 if key_id not found or belongs to another user
- [ ] Revoked keys cannot be reactivated (create a new key instead)
- [ ] Requires minimum Employee role

### General
- [ ] All 5 tools appear in `tools/list` for any authenticated user (Employee, Technician, Admin, Super Admin)
- [ ] Domain errors (NotFound, Conflict, Forbidden, ValidationError) are mapped to MCP error responses with clear messages
- [ ] Multi-tenant isolation: users can only see/manage their own API keys
- [ ] Unit tests cover all 5 tools (parameter handling, handler delegation, error mapping)
- [ ] Integration tests verify end-to-end tool calls including the create-list-revoke lifecycle

---

## Technical Scope

### Entities (owned)

None. This feature creates no new entities (ApiKey entity is created in F0).

### Entities (used)

- `User` (auth_bc) -- for get_current_user and set_password
- `ApiKey` (mcp_bc) -- for create_api_key, list_api_keys, revoke_api_key

### Key Components

| Component | Action | Description |
|-----------|--------|-------------|
| `adapters/mcp/tools/auth.py` | Create | 5 auth/API key tool definitions, delegating to existing handlers |
| `adapters/mcp/registry.py` | Modify | Register auth tools with the tool registry |
| `tests/unit/mcp/tools/test_auth_tools.py` | Create | Unit tests for all 5 tools |
| `tests/integration/test_mcp_auth_tools.py` | Create | Integration tests for create-list-revoke API key lifecycle via MCP |

---

## Notes

- The `create_api_key` tool result must clearly present the raw key to the AI assistant, since this is the only time the key is available. The tool description should emphasize that the key cannot be retrieved later.
- An AI assistant using an API key to authenticate could use `create_api_key` to create a new key for a different client, or `revoke_api_key` to revoke its own key (effectively logging itself out). Both are valid use cases.
- The `set_password` tool is included in auth tools because it modifies the user's own authentication credentials, consistent with the HTTP endpoint grouping under `/api/v1/auth/`.
- All 5 tools use Employee as the minimum role, meaning every authenticated user can manage their own auth and keys. This is intentional -- API key management is a self-service operation, not an admin-only one.
