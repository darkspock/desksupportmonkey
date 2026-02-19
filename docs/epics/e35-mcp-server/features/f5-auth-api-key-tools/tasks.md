# Tasks: F5 — Auth & API Key MCP Tools (5 Tools)

## Implementation Tasks

### 1. Auth Tools (`adapters/mcp/tools/auth.py`)
- [x] Create `auth.py` with 5 tools, all EMPLOYEE minimum role
- [x] `get_current_user` — return user profile (id, email, name, role, company_id, department_id, is_active)
- [x] `set_password` — set password for admin user, return success message
- [x] `create_api_key` — create API key, return raw key once
- [x] `list_api_keys` — list user's API keys (metadata only, no raw keys)
- [x] `revoke_api_key` — revoke an API key by key_id

### 2. Module Registration
- [x] Update `adapters/mcp/tools/__init__.py` to import auth module

### 3. Unit Tests
- [x] `tests/unit/mcp/tools/test_auth.py` (11 tests)
  - get_current_user: success, not_found
  - set_password: success, not_admin, weak_password
  - create_api_key: success, max_keys_reached
  - list_api_keys: success
  - revoke_api_key: success, not_found, already_revoked

### 4. Verification
- [x] Lint passes
- [x] New tool tests pass (11/11)
- [x] Full unit suite passes (`make test` — 588 passed)

### 5. Progress Tracking
- [x] Mark all tasks done
- [x] Update `slicing.md` — F5 status to Done
