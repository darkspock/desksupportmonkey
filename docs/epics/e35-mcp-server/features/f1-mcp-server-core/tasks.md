# Tasks: F1 — MCP Server Core

**Feature:** [requirements.md](requirements.md)
**Status:** Done

## Implementation Tasks

### 1. Add MCP SDK dependency
- [x] Add `mcp>=1.26.0,<2.0.0` to `pyproject.toml`
- [x] Install with `uv add`

### 2. Add MCP configuration
- [x] Create `MCPSettings` class in `core/config.py` with `MCP_ENABLED` (bool) and `MCP_TRANSPORT` (str)
- [x] Add `mcp` property to `Settings` class

### 3. Create API key authentication middleware
- [x] Create `adapters/mcp/auth.py`
- [x] Implement `authenticate_api_key(raw_key, db) -> User`
- [x] Validate key format (dsm_ + 40 hex chars)
- [x] Iterate active keys and verify with bcrypt
- [x] Resolve user and check active status
- [x] Check company status (active)
- [x] Set tenant context via `set_tenant()`
- [x] Update `last_used_at`

### 4. Create tool registry with role-based filtering
- [x] Create `adapters/mcp/registry.py`
- [x] Implement `ToolDefinition` dataclass with name, description, input_schema, min_role, handler
- [x] Implement `ToolRegistry` with `register()`, `list_tools(role)`, `get_tool(name)`
- [x] Role filtering uses `UserRole.has_access()` hierarchy

### 5. Create MCP server
- [x] Create `adapters/mcp/server.py`
- [x] Create MCP server using `mcp.server.Server`
- [x] Implement `list_tools` handler with role-based filtering from registry
- [x] Implement `call_tool` handler with permission verification
- [x] Implement `run_stdio_server()` with API key auth from `DSM_API_KEY` env var

### 6. Create CLI entry point
- [x] Create `adapters/mcp/__main__.py`
- [x] Support `--transport stdio` argument
- [x] Check `MCP_ENABLED` before starting
- [x] Log to stderr (stdout reserved for MCP protocol)

### 7. Create package structure
- [x] Create `adapters/mcp/__init__.py`
- [x] Create `adapters/mcp/tools/__init__.py` (placeholder for F2-F5)

### 8. Add `find_all_active()` to ApiKeyRepository
- [x] Add method to `ApiKeyRepositoryInterface`
- [x] Implement in `ApiKeyRepository`

### 9. Unit tests
- [x] Create `tests/unit/mcp/__init__.py`
- [x] Create `tests/unit/mcp/test_auth.py` (8 tests)
  - [x] Valid key authenticates and returns user
  - [x] Invalid format (no prefix) rejected
  - [x] Invalid format (wrong length) rejected
  - [x] Wrong key rejected
  - [x] No active keys rejected
  - [x] Inactive user rejected
  - [x] Restricted company rejected
  - [x] Tenant context set correctly
- [x] Create `tests/unit/mcp/test_registry.py` (10 tests)
  - [x] Register tool
  - [x] Filter by Employee role
  - [x] Filter by Technician role
  - [x] Filter by Admin role
  - [x] Filter by Super Admin role
  - [x] Empty registry returns empty list
  - [x] Get tool found
  - [x] Get tool not found
  - [x] Employee cannot access Technician tools
  - [x] Technician can access Employee tools

### 10. Verification
- [x] `make test` passes (477 tests, 18 new)
- [x] `mypy adapters/mcp/` passes (0 errors)
- [x] `flake8 adapters/mcp/ tests/unit/mcp/` passes (0 errors)

## Acceptance Criteria Checklist

- [x] AC1: Server boots via `python -m adapters.mcp --transport stdio`
- [x] AC2: API key authentication resolves user and sets tenant context
- [x] AC3: Invalid/revoked API keys are rejected
- [x] AC4: `last_used_at` updated after successful auth
- [x] AC5: `tools/list` returns empty list (no tools registered yet)
- [x] AC6: Role filtering works when tools are registered (tested in unit tests)
- [x] AC7: Tenant isolation via `set_tenant()`
- [x] AC8: Connection events logged
- [x] AC9: `mcp` SDK dependency added to `pyproject.toml`
- [x] AC10: Config flags `MCP_ENABLED` and `MCP_TRANSPORT` in `core/config.py`
- [x] AC11: Unit tests pass for auth middleware and registry
- [x] AC12: `make test` and `make lint` pass with no regressions
