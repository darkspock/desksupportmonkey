# Feature: Dashboard, Report & My Tools

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F4
**Dependencies:** F1 (MCP Server Core)
**Complexity:** M

---

## Scope

### Included

18 MCP tools across three tool modules that expose dashboard analytics, report generation, and personal data operations to AI assistants.

**Dashboard Tools** (`adapters/mcp/tools/dashboard.py`) -- 7 tools, minimum role: Admin

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `dashboard_request_summary` | `GET /api/v1/dashboard/requests/summary` | *(none)* |
| `dashboard_resolution_time` | `GET /api/v1/dashboard/requests/resolution-time` | from_date?, to_date? |
| `dashboard_request_trend` | `GET /api/v1/dashboard/requests/trend` | bucket? (day/week/month), from_date?, to_date? |
| `dashboard_asset_summary` | `GET /api/v1/dashboard/assets/summary` | *(none)* |
| `dashboard_warranty_alerts` | `GET /api/v1/dashboard/alerts/warranty` | days? |
| `dashboard_aging_alerts` | `GET /api/v1/dashboard/alerts/aging` | years? |
| `dashboard_sla_alerts` | `GET /api/v1/dashboard/alerts/sla` | *(none)* |

**Report Tools** (`adapters/mcp/tools/reports.py`) -- 4 tools, minimum role: Admin

| Tool | Existing Endpoint | Parameters |
|------|------------------|------------|
| `request_report` | `POST /api/v1/reports` | type (asset_inventory, request_summary, technician_performance), from_date?, to_date? |
| `list_reports` | `GET /api/v1/reports` | page?, page_size? |
| `get_report` | `GET /api/v1/reports/{report_id}` | report_id |
| `download_report` | `GET /api/v1/reports/{report_id}/download` | report_id |

- `download_report` returns a signed URL string, not binary content. This is critical for MCP since tool results must be serializable text.

**My Tools** (`adapters/mcp/tools/my.py`) -- 7 tools, minimum role: varies

| Tool | Min Role | Existing Endpoint | Parameters |
|------|----------|------------------|------------|
| `my_equipment` | Employee | `GET /api/v1/my/equipment` | *(none)* |
| `my_requests` | Employee | `GET /api/v1/my/requests` | page?, page_size?, status? |
| `my_notifications` | Employee | `GET /api/v1/my/notifications` | page?, page_size?, is_read? |
| `mark_notification_read` | Employee | `PATCH /api/v1/my/notifications/{id}/read` | notification_id |
| `mark_all_notifications_read` | Employee | `PATCH /api/v1/my/notifications/read-all` | *(none)* |
| `get_my_company_settings` | Admin | `GET /api/v1/my/company-settings` | *(none)* |
| `update_my_company_settings` | Admin | `PUT /api/v1/my/company-settings` | email_domains |

Each tool reuses the existing application-layer command/query handlers. No new business logic is created.

### Excluded

- All other tool groups (assets, requests, users, departments, companies, auth)
- MCP server core setup (F1)
- SSE transport (F6)
- Any modifications to existing domain, application, or infrastructure layers

---

## User Value

An AI assistant connected via MCP can:
- Query dashboard metrics to understand current IT workload, SLA compliance, and asset health without navigating the web UI.
- Generate and download PDF reports on demand, enabling automated reporting workflows.
- Access the authenticated user's personal data (equipment, requests, notifications) for self-service automation.
- Mark notifications as read, reducing notification noise for users who interact primarily through AI.

These 18 tools complete the read-heavy, analytics-oriented portion of the MCP tool catalog.

---

## Acceptance Criteria

### Dashboard Tools (7)
- [ ] All 7 dashboard tools are callable via MCP and return data matching their HTTP endpoint equivalents
- [ ] Dashboard tools require minimum Admin role; Employee and Technician users do not see these tools in `tools/list`
- [ ] `dashboard_request_summary` returns counts by status, type, priority, total_open, and total_resolved
- [ ] `dashboard_resolution_time` accepts optional from_date/to_date and returns resolution time data
- [ ] `dashboard_request_trend` accepts optional bucket (day/week/month) and date range
- [ ] `dashboard_warranty_alerts` accepts optional days parameter
- [ ] `dashboard_aging_alerts` accepts optional years parameter
- [ ] `dashboard_sla_alerts` returns SLA violation data
- [ ] All dashboard tools are scoped to the authenticated user's company_id (multi-tenant isolation)

### Report Tools (4)
- [ ] All 4 report tools are callable via MCP and return data matching their HTTP endpoint equivalents
- [ ] Report tools require minimum Admin role
- [ ] `request_report` accepts type enum (asset_inventory, request_summary, technician_performance) and optional date range
- [ ] `list_reports` returns paginated list of reports
- [ ] `get_report` returns report details including status
- [ ] `download_report` returns a signed URL string (not binary content)
- [ ] Report tools are scoped to the authenticated user's company_id

### My Tools (7)
- [ ] All 7 my tools are callable via MCP
- [ ] `my_equipment`, `my_requests`, `my_notifications`, `mark_notification_read`, `mark_all_notifications_read` require minimum Employee role
- [ ] `get_my_company_settings` and `update_my_company_settings` require minimum Admin role
- [ ] `my_equipment` returns the authenticated user's assigned assets
- [ ] `my_requests` returns the authenticated user's submitted requests with optional pagination and status filter
- [ ] `my_notifications` returns notifications with optional pagination and is_read filter
- [ ] `mark_notification_read` marks a single notification as read
- [ ] `mark_all_notifications_read` marks all user notifications as read
- [ ] `update_my_company_settings` accepts email_domains and updates company settings
- [ ] My tools are scoped to the authenticated user's data (user_id and company_id)

### General
- [ ] Domain errors (NotFound, Conflict, Forbidden) are mapped to MCP error responses with clear messages
- [ ] Invalid parameters return descriptive validation errors
- [ ] Unit tests cover all 18 tools (parameter handling, handler delegation, error mapping)
- [ ] Integration tests verify end-to-end tool calls for representative tools from each group

---

## Technical Scope

### Entities (owned)

None. This feature creates no new entities.

### Entities (used)

- `ServiceRequest` (request_bc) -- for dashboard and my_requests
- `Asset` (asset_bc) -- for dashboard and my_equipment
- `Report` (report_bc) -- for report tools
- `Notification` (notification_bc) -- for notification tools
- `Company` (company_bc) -- for company settings

### Key Components

| Component | Action | Description |
|-----------|--------|-------------|
| `adapters/mcp/tools/dashboard.py` | Create | 7 dashboard tool definitions, each delegating to existing dashboard query handlers |
| `adapters/mcp/tools/reports.py` | Create | 4 report tool definitions, delegating to existing report command/query handlers |
| `adapters/mcp/tools/my.py` | Create | 7 my tool definitions, delegating to existing my query/command handlers |
| `adapters/mcp/registry.py` | Modify | Register dashboard, report, and my tools with the tool registry |
| `tests/unit/mcp/tools/test_dashboard_tools.py` | Create | Unit tests for dashboard tool parameter handling and delegation |
| `tests/unit/mcp/tools/test_report_tools.py` | Create | Unit tests for report tools including download_report URL return |
| `tests/unit/mcp/tools/test_my_tools.py` | Create | Unit tests for my tools including role differentiation |
| `tests/integration/test_mcp_dashboard_report_my.py` | Create | Integration tests for end-to-end tool calls |

---

## Notes

- The `download_report` tool is a special case: the HTTP endpoint returns a redirect or signed URL. The MCP tool must return the signed URL as a plain string in the tool result, since MCP tool responses are text-based. The AI assistant can then present the URL to the user or use it for further processing.
- The My Tools group has mixed role requirements: 5 tools at Employee level, 2 at Admin level. The tool registry must handle per-tool role filtering, not just per-module filtering.
- Dashboard tools are read-only and stateless, making them safe for frequent AI polling without side effects.
- Report generation (`request_report`) triggers an async Celery task. The tool should return the report metadata (including status "pending") immediately, not wait for generation to complete. The AI can then poll `get_report` for status updates.
