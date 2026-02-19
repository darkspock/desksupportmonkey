# Tasks: F2 — Asset & Request Tools (20 MCP Tools)

**Feature:** [requirements.md](requirements.md)
**Date:** 2026-02-17
**Status:** Done

## Tasks

### 1. Asset Tools (`adapters/mcp/tools/assets.py`)

- [x] `create_asset` — Create a new asset in the inventory
- [x] `list_assets` — List assets with filtering, search, and pagination
- [x] `get_asset` — Get detailed information about a specific asset
- [x] `update_asset` — Update asset details (brand, model, notes, dates)
- [x] `change_asset_status` — Change an asset's status with valid transition enforcement
- [x] `assign_asset` — Assign an asset to a user (must be in_stock)
- [x] `unassign_asset` — Unassign an asset from its current user
- [x] `get_asset_history` — Get audit history (creation, assignments, status changes)
- [x] `import_assets` — Import assets from CSV content
- [x] `list_assignable_users` — List active users who can be assigned assets

### 2. Request Tools (`adapters/mcp/tools/requests.py`)

- [x] `create_request` — Create a new support request (employee+)
- [x] `list_requests` — List support requests with filtering and pagination
- [x] `get_request` — Get request detail (employees only see their own)
- [x] `change_request_status` — Change a request's status with transition enforcement
- [x] `change_request_priority` — Change a request's priority level
- [x] `assign_request` — Assign a request to a technician/admin
- [x] `add_comment` — Add a public comment to a request (employee+)
- [x] `list_comments` — List all comments on a request (employee+)
- [x] `add_note` — Add an internal note (technician+)
- [x] `list_notes` — List internal notes (technician+)

### 3. Registration & Wiring

- [x] `adapters/mcp/tools/__init__.py` — Import asset/request modules to trigger registration
- [x] `adapters/mcp/server.py` — Import tools module at server creation

### 4. Unit Tests

- [x] `tests/unit/mcp/tools/test_assets.py` — 19 tests (success + error for each tool)
- [x] `tests/unit/mcp/tools/test_requests.py` — 21 tests (success + error + employee access control)
- [x] All 40 new tests pass
- [x] Full test suite passes (517 tests)

### 5. Code Quality

- [x] Flake8 passes on all new files (0 errors)
- [x] Mypy passes on all MCP module files (0 errors)
- [x] Consistent error handling pattern (domain exceptions → JSON error response)
- [x] Entity serialization helpers (`_serialize_asset`, `_serialize_request`)
- [x] Role-based tool registration (EMPLOYEE vs TECHNICIAN minimum roles)
- [x] Type-safe tenant context with `_AuthenticatedTenant` wrapper
- [x] Proper `UserLookup` port casting for command handlers
