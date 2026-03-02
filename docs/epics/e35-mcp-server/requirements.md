# Epic E35: MCP Server

**Type:** Epic
**Status:** Pending
**Created:** 2026-02-17
**Priority:** High
**Depends on:** E0 (Foundation), E1-E6 (All backend APIs)

---

## Business Alignment

**Objective:** Expose DeskSupportMonkey as a Model Context Protocol (MCP) server so AI assistants (Claude, Cursor, VS Code Copilot, custom agents) can manage assets, requests, users, reports, and dashboard data via tool calls — turning every existing API endpoint into an AI-callable tool without modifying the existing codebase.

**Why MCP:**
- MCP is the open standard for connecting AI assistants to external systems. Shipping an MCP server means any MCP-compatible client can manage DSM without building custom integrations.
- AI-assisted IT operations (AIOps) is a growing category. An MCP server enables AI agents to triage tickets, assign assets, generate reports, and monitor SLA compliance autonomously.
- The entire REST API already exists (57 endpoints). The MCP server is a thin adapter layer that reuses existing handlers — no new business logic required.

**KPIs:**
- All 57 public API endpoints exposed as MCP tools
- Multi-tenant isolation verified (tool calls scoped to authenticated user's company)
- Role-based tool filtering (tools invisible to unauthorized roles)
- Response latency within 2x of direct HTTP call
- Zero changes to existing domain, application, or infrastructure layers

---

## Context & Problem Statement

DeskSupportMonkey has a complete REST API covering assets, requests, users, companies, departments, reports, dashboard, and notifications. However, AI assistants cannot natively interact with REST APIs — they need structured tool definitions with typed parameters and descriptions.

MCP (Model Context Protocol) bridges this gap. An MCP server advertises tools (with JSON Schema parameter definitions), handles tool calls by delegating to the existing application layer, and returns structured results. The AI assistant sees a catalog of tools like `create_asset`, `list_requests`, `assign_request` and calls them directly.

**Current state:** AI assistants must use generic HTTP tools or custom API wrappers to interact with DSM.
**Target state:** Any MCP client connects to a DSM MCP server and immediately has typed access to all platform operations, scoped to their role and company.

---

## Proposed Solution

### Architecture

```
MCP Client (Claude, Cursor, etc.)
    │
    │  SSE / stdio transport
    │
    ▼
MCP Server (Python, `mcp` SDK)
    │
    ├── Auth middleware (API key → user context)
    ├── Tool registry (auto-generated from endpoint catalog)
    ├── Role filter (hide tools below user's role)
    │
    ▼
Existing Application Layer
    │
    ├── Command Handlers (write operations)
    ├── Query Handlers (read operations)
    └── Repositories (database access)
```

The MCP server is a **new adapter** alongside the existing HTTP adapter. It imports the same command/query handlers and repositories — no duplication of business logic.

### Transport

Two transport modes:
1. **SSE (Server-Sent Events)** — Primary. Runs as an HTTP endpoint (e.g., `/mcp/sse`). Integrates into the existing FastAPI app or runs standalone.
2. **stdio** — For local development. AI assistants can launch the MCP server as a subprocess.

### Authentication

- **API key per user** — New `api_keys` table: `id`, `user_id`, `key_hash`, `name`, `created_at`, `last_used_at`, `is_active`. The API key resolves to a user, which provides `company_id`, `role`, and tenant context.
- **JWT passthrough** — Optionally accept existing JWT tokens for clients that already have them.
- All tool calls execute within the authenticated user's tenant context (same `set_tenant()` pattern as HTTP layer).

### Role-Based Tool Filtering

Each tool declares its minimum required role. When a client connects, the tool list is filtered based on the authenticated user's role:

| Role | Visible Tools |
|------|--------------|
| **Employee** | My equipment, my requests, notifications, company settings (read) |
| **Technician** | Employee tools + assets CRUD, request management, assignable users |
| **Admin** | Technician tools + users, departments, dashboard, reports, company settings (write) |
| **Super Admin** | Admin tools + company management |

Tools the user cannot access are not advertised — they don't appear in `tools/list`.

---

## Tool Catalog

### Asset Tools (10 tools, minimum role: Technician)

| Tool | Method | Existing Endpoint | Parameters |
|------|--------|------------------|------------|
| `create_asset` | POST | `/api/v1/assets` | type, brand, model, serial_number, purchase_date?, warranty_expiration?, notes? |
| `list_assets` | GET | `/api/v1/assets` | page?, page_size?, search?, type?, status?, department_id?, assigned_to?, sort_by?, sort_order? |
| `get_asset` | GET | `/api/v1/assets/{asset_id}` | asset_id |
| `update_asset` | PUT | `/api/v1/assets/{asset_id}` | asset_id, brand?, model?, notes?, purchase_date?, warranty_expiration? |
| `change_asset_status` | PATCH | `/api/v1/assets/{asset_id}/status` | asset_id, status |
| `assign_asset` | PATCH | `/api/v1/assets/{asset_id}/assign` | asset_id, user_id |
| `unassign_asset` | PATCH | `/api/v1/assets/{asset_id}/unassign` | asset_id |
| `get_asset_history` | GET | `/api/v1/assets/{asset_id}/history` | asset_id |
| `import_assets` | POST | `/api/v1/assets/import` | csv_content (string) |
| `list_assignable_users` | GET | `/api/v1/assets/assignable-users` | *(none)* |

### Request Tools (10 tools, minimum role: varies)

| Tool | Min Role | Existing Endpoint | Parameters |
|------|----------|------------------|------------|
| `create_request` | Employee | `/api/v1/requests` | type, title, description, priority? |
| `list_requests` | Technician | `/api/v1/requests` | page?, page_size?, status?, type?, priority?, assigned_to?, search?, sort_by?, sort_order? |
| `get_request` | Employee | `/api/v1/requests/{request_id}` | request_id |
| `change_request_status` | Technician | `/api/v1/requests/{request_id}/status` | request_id, status |
| `change_request_priority` | Technician | `/api/v1/requests/{request_id}/priority` | request_id, priority |
| `assign_request` | Technician | `/api/v1/requests/{request_id}/assign` | request_id, assigned_to |
| `add_comment` | Employee | `/api/v1/requests/{request_id}/comments` | request_id, content |
| `list_comments` | Employee | `/api/v1/requests/{request_id}/comments` | request_id |
| `add_note` | Technician | `/api/v1/requests/{request_id}/notes` | request_id, content |
| `list_notes` | Technician | `/api/v1/requests/{request_id}/notes` | request_id |

### User Tools (7 tools, minimum role: Admin)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `list_users` | `/api/v1/users` | page?, page_size?, role?, is_active?, department_id?, search? |
| `invite_user` | `/api/v1/users/invite` | email |
| `get_user` | `/api/v1/users/{user_id}` | user_id |
| `change_user_role` | `/api/v1/users/{user_id}/role` | user_id, role |
| `activate_user` | `/api/v1/users/{user_id}/activate` | user_id |
| `deactivate_user` | `/api/v1/users/{user_id}/deactivate` | user_id |
| `assign_user_department` | `/api/v1/users/{user_id}/department` | user_id, department_id |

### Company Tools (5 tools, minimum role: Super Admin)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `create_company` | `/api/v1/companies` | name, email_domains |
| `list_companies` | `/api/v1/companies` | page?, page_size?, search?, status? |
| `get_company` | `/api/v1/companies/{company_id}` | company_id |
| `update_company` | `/api/v1/companies/{company_id}` | company_id, name?, email_domains? |
| `change_company_status` | `/api/v1/companies/{company_id}/status` | company_id, status |

### Department Tools (5 tools, minimum role: Admin)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `create_department` | `/api/v1/departments` | name |
| `list_departments` | `/api/v1/departments` | page?, page_size?, is_active? |
| `get_department` | `/api/v1/departments/{department_id}` | department_id |
| `update_department` | `/api/v1/departments/{department_id}` | department_id, name |
| `delete_department` | `/api/v1/departments/{department_id}` | department_id |

### Report Tools (4 tools, minimum role: Admin)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `request_report` | `/api/v1/reports` | type (asset_inventory, request_summary, technician_performance), from_date?, to_date? |
| `list_reports` | `/api/v1/reports` | page?, page_size? |
| `get_report` | `/api/v1/reports/{report_id}` | report_id |
| `download_report` | `/api/v1/reports/{report_id}/download` | report_id — returns signed URL string (not binary) |

### Dashboard Tools (7 tools, minimum role: Admin)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `dashboard_request_summary` | `/api/v1/dashboard/requests/summary` | *(none)* |
| `dashboard_resolution_time` | `/api/v1/dashboard/requests/resolution-time` | from_date?, to_date? |
| `dashboard_request_trend` | `/api/v1/dashboard/requests/trend` | bucket? (day/week/month), from_date?, to_date? |
| `dashboard_asset_summary` | `/api/v1/dashboard/assets/summary` | *(none)* |
| `dashboard_warranty_alerts` | `/api/v1/dashboard/alerts/warranty` | days? |
| `dashboard_aging_alerts` | `/api/v1/dashboard/alerts/aging` | years? |
| `dashboard_sla_alerts` | `/api/v1/dashboard/alerts/sla` | *(none)* |

### My Tools (7 tools, minimum role: varies)

| Tool | Min Role | Existing Endpoint | Parameters |
|------|----------|------------------|------------|
| `my_equipment` | Employee | `/api/v1/my/equipment` | *(none)* |
| `my_requests` | Employee | `/api/v1/my/requests` | page?, page_size?, status? |
| `my_notifications` | Employee | `/api/v1/my/notifications` | page?, page_size?, is_read? |
| `mark_notification_read` | Employee | `/api/v1/my/notifications/{id}/read` | notification_id |
| `mark_all_notifications_read` | Employee | `/api/v1/my/notifications/read-all` | *(none)* |
| `get_my_company_settings` | Admin | `/api/v1/my/company-settings` | *(none)* |
| `update_my_company_settings` | Admin | `/api/v1/my/company-settings` | email_domains |

### Auth Tools (2 tools, minimum role: Employee)

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `get_current_user` | `/api/v1/auth/me` | *(none)* |
| `set_password` | `/api/v1/auth/set-password` | password |

**Total: 57 tools** mirroring 57 API endpoints.

---

## Data Model Changes

### New Table: `api_keys`

| Column | Type | Constraints |
|--------|------|------------|
| `id` | `String(26)` ULID | PK |
| `user_id` | `String(26)` | FK → users, NOT NULL |
| `key_hash` | `String(128)` | NOT NULL, bcrypt hash |
| `name` | `String(100)` | NOT NULL, human label ("Claude Desktop", "Cursor") |
| `created_at` | `DateTime(tz)` | NOT NULL |
| `last_used_at` | `DateTime(tz)` | NULL |
| `is_active` | `Boolean` | NOT NULL, default True |

- One user can have up to **10 active API keys**.
- The raw key is shown once at creation, then only the hash is stored.
- Key format: `dsm_` prefix + 40 random hex chars (e.g., `dsm_a1b2c3d4...`).
- Revoked keys cannot be reactivated — create a new key instead.

### New Endpoints for Key Management (Admin self-service)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/api-keys` | POST | Create API key (returns raw key once) |
| `/api/v1/auth/api-keys` | GET | List user's API keys (name, created, last_used, active) |
| `/api/v1/auth/api-keys/{key_id}` | DELETE | Revoke an API key |

These are also exposed as MCP tools: `create_api_key`, `list_api_keys`, `revoke_api_key`.

---

## Technical Design

### Project Structure

```
src/
└── mcp_bc/                          # New bounded context
    └── server/
        ├── domain/
        │   ├── entities.py          # ApiKey entity
        │   ├── enums.py             # (if needed)
        │   └── repository.py        # ApiKeyRepositoryInterface
        ├── application/
        │   ├── commands/
        │   │   ├── create_api_key.py
        │   │   └── revoke_api_key.py
        │   └── queries/
        │       └── list_api_keys.py
        └── infrastructure/
            ├── models.py            # SQLAlchemy ApiKeyModel
            └── repository.py        # ApiKeyRepository

adapters/
└── mcp/                             # New MCP adapter (parallel to http/)
    ├── server.py                    # MCP server setup, tool registration
    ├── auth.py                      # API key → user resolution
    ├── tools/                       # Tool definitions grouped by domain
    │   ├── assets.py
    │   ├── requests.py
    │   ├── users.py
    │   ├── companies.py
    │   ├── departments.py
    │   ├── reports.py
    │   ├── dashboard.py
    │   ├── my.py
    │   └── auth.py
    └── registry.py                  # Auto-registration and role filtering
```

### Tool Definition Pattern

Each tool module defines tools using the `mcp` Python SDK:

```python
from mcp.server import Server
from mcp.types import Tool

def register_asset_tools(server: Server, min_role: str = "technician"):
    @server.tool(
        name="list_assets",
        description="List IT assets in the company inventory with optional filters",
    )
    async def list_assets(
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        type: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        # Reuse existing query handler
        handler = ListAssetsQueryHandler(asset_repo=asset_repo)
        assets, total = handler.handle(ListAssetsQuery(...))
        return {"data": [...], "meta": {"page": page, "total": total}}
```

### Entry Point

```bash
# SSE mode (production, integrates with FastAPI)
uvicorn app:app  # MCP SSE endpoint at /mcp/sse

# stdio mode (local dev, AI assistant launches as subprocess)
python -m adapters.mcp.server --transport stdio
```

### Configuration

```env
# .env additions
MCP_ENABLED=true                    # Enable/disable MCP server
MCP_TRANSPORT=sse                   # sse or stdio
MCP_SSE_PATH=/mcp/sse              # SSE endpoint path
```

---

## Non-Functional Requirements

- **No business logic duplication** — MCP tools call the same handlers as HTTP routers
- **Multi-tenant isolation** — Every tool call scoped to authenticated user's company_id
- **Role enforcement** — Tools filtered by role at connection time AND validated per call
- **Latency** — Tool call response within 2x of equivalent HTTP endpoint
- **Error handling** — Domain errors (NotFound, Conflict, Forbidden) mapped to MCP error responses with clear messages
- **Idempotency** — Same tool call behavior as HTTP (no double-create risks)
- **Logging** — Tool calls logged with user_id, tool_name, duration (same pattern as HTTP access logs)
- **No breaking changes** — Existing HTTP API, frontend, and tests unaffected

---

## Collateral Impact

| Component | Impact | Action Required |
|-----------|--------|----------------|
| `alembic/` | New migration for `api_keys` table | Create migration |
| `adapters/http/api/auth/` | New API key management endpoints | Add 3 endpoints |
| `adapters/mcp/` | Entire new adapter layer | Create from scratch |
| `src/mcp_bc/` | New bounded context for API keys | Create from scratch |
| `app.py` | Mount MCP SSE endpoint if enabled | Small addition |
| `pyproject.toml` | Add `mcp` SDK dependency | Add package |
| `tests/` | New unit + integration tests for MCP tools | Create test suite |
| `.env.example` | Add MCP config vars | Update |
| `web/app/src/` | New API Keys management page for admins | Create page + API client |
| Existing code | **Zero changes** to domain, application, or infrastructure layers | None |

---

## Testing Requirements

### Unit Tests
- API key creation, listing, revocation
- Role-based tool filtering (employee sees 7 tools, admin sees 50+)
- Tool parameter validation (required vs optional)
- Error mapping (domain errors → MCP errors)

### Integration Tests
- Full MCP connection → authenticate → list tools → call tool → verify response
- Multi-tenant isolation: user A cannot see user B's company data via tools
- Role enforcement: employee cannot call admin-only tools
- API key lifecycle: create, use, revoke, verify revoked key is rejected

### Compatibility Tests
- Verify MCP server works with Claude Desktop
- Verify MCP server works with Cursor
- Verify stdio and SSE transports both function

---

## Definition of Done

- [x] `mcp` Python SDK added to dependencies
- [x] `api_keys` table created via Alembic migration
- [x] API key CRUD endpoints implemented and tested
- [x] MCP server boots in both SSE and stdio modes
- [x] All 57 existing endpoints exposed as MCP tools (+ 3 API key tools = 60 total)
- [x] Role-based tool filtering verified for all 4 roles
- [x] Multi-tenant isolation verified (company_id scoping)
- [x] Authentication via API key works end-to-end
- [x] Error handling maps domain exceptions to MCP error responses
- [x] Unit tests for API key BC and tool registration
- [x] Integration tests for end-to-end MCP tool calls
- [x] Tested with at least one MCP client (Claude Desktop or Cursor)
- [x] `make test` and `make lint` pass
- [x] Frontend API Keys page for admin users (create, list, revoke)
- [x] Documentation updated (README, .env.example)
- [x] Zero changes to existing HTTP adapter, domain, or application code
