# Feature: Asset & Request Tools

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F2
**Dependencies:** F1 (MCP Server Core)
**Complexity:** L

---

## Scope

### Included

- `adapters/mcp/tools/assets.py` -- 10 MCP tools covering all asset endpoints:
  1. `create_asset` -- Create a new IT asset (type, brand, model, serial_number, purchase_date?, warranty_expiration?, notes?)
  2. `list_assets` -- List assets with filters (page?, page_size?, search?, type?, status?, department_id?, assigned_to?, sort_by?, sort_order?)
  3. `get_asset` -- Get asset details by ID (asset_id)
  4. `update_asset` -- Update asset fields (asset_id, brand?, model?, notes?, purchase_date?, warranty_expiration?)
  5. `change_asset_status` -- Change asset status (asset_id, status)
  6. `assign_asset` -- Assign asset to a user (asset_id, user_id)
  7. `unassign_asset` -- Remove asset assignment (asset_id)
  8. `get_asset_history` -- Get asset event history (asset_id)
  9. `import_assets` -- Import assets from CSV content (csv_content)
  10. `list_assignable_users` -- List users who can be assigned assets (no params)

- `adapters/mcp/tools/requests.py` -- 10 MCP tools covering all request endpoints:
  1. `create_request` -- Create a service request (type, title, description, priority?)
  2. `list_requests` -- List requests with filters (page?, page_size?, status?, type?, priority?, assigned_to?, search?, sort_by?, sort_order?)
  3. `get_request` -- Get request details by ID (request_id)
  4. `change_request_status` -- Change request status (request_id, status)
  5. `change_request_priority` -- Change request priority (request_id, priority)
  6. `assign_request` -- Assign request to a technician (request_id, assigned_to)
  7. `add_comment` -- Add a public comment to a request (request_id, content)
  8. `list_comments` -- List comments on a request (request_id)
  9. `add_note` -- Add an internal note to a request (request_id, content)
  10. `list_notes` -- List internal notes on a request (request_id)

- Each tool reuses existing command/query handlers from the application layer -- no new business logic
- Error mapping: domain exceptions (NotFound, Conflict, Forbidden, ValidationError) mapped to MCP error responses with clear messages
- Tool descriptions include parameter documentation for AI assistants
- Tools register with the registry (F1) with their minimum role declarations

### Excluded

- User, department, and company tools (F3)
- Dashboard, report, and my tools (F4)
- Auth and API key MCP tools (F5)
- Any new business logic or domain changes
- Frontend changes

---

## User Value

This is the highest-value tool group. With 20 tools covering assets and service requests, an AI assistant can manage the two core business domains of DeskSupportMonkey: IT asset inventory and service request lifecycle. An AI agent can create assets, assign them to users, create and triage support tickets, assign technicians, add comments, and track request status -- all via MCP tool calls.

---

## Acceptance Criteria

### Asset Tools

1. **`create_asset`:** Creates an asset with required fields (type, brand, model, serial_number) and optional fields; returns created asset data
2. **`list_assets`:** Returns paginated asset list with all filter parameters working correctly; default page_size=20
3. **`get_asset`:** Returns full asset details for a valid asset_id; returns error for nonexistent asset
4. **`update_asset`:** Updates specified fields; returns error for nonexistent asset
5. **`change_asset_status`:** Changes status following the status state machine; returns error for invalid transitions
6. **`assign_asset`:** Assigns asset to a user; validates user exists in same company and asset is in `in_stock` status
7. **`unassign_asset`:** Removes assignment; validates asset is in `assigned` status
8. **`get_asset_history`:** Returns chronological event history for the asset
9. **`import_assets`:** Accepts CSV content string and imports assets; returns import results (created, errors)
10. **`list_assignable_users`:** Returns list of active users in the company who can receive asset assignments

### Request Tools

11. **`create_request`:** Creates a service request with auto-assigned priority based on type; Employee+ can call
12. **`list_requests`:** Returns paginated request list with all filter parameters; Technician+ only
13. **`get_request`:** Returns request details; Employees can only see their own requests, Technicians see all
14. **`change_request_status`:** Changes status following the state machine; Technician+ only
15. **`change_request_priority`:** Changes priority; Technician+ only
16. **`assign_request`:** Assigns request to a technician; Technician+ only
17. **`add_comment`:** Adds a public comment; Employee+ can call (on accessible requests)
18. **`list_comments`:** Lists comments; Employee+ can call (on accessible requests)
19. **`add_note`:** Adds an internal/technician note; Technician+ only
20. **`list_notes`:** Lists internal notes; Technician+ only

### Cross-Cutting

21. **Role enforcement:** Asset tools require minimum Technician role; Request tools enforce per-tool minimum roles as listed above
22. **Multi-tenant isolation:** All tools scope data to the authenticated user's `company_id` via tenant context
23. **Error mapping:** Domain exceptions are mapped to MCP error responses with descriptive messages (e.g., "Asset not found", "Invalid status transition from 'assigned' to 'decommissioned'")
24. **Unit tests:** Each tool module (`assets.py`, `requests.py`) has unit tests verifying parameter mapping, handler invocation, and error mapping
25. **Integration test:** At least one end-to-end test per module demonstrating: MCP client connects, authenticates, calls a tool, receives correct response
26. **`make test` and `make lint` pass** with no regressions

---

## Technical Scope

### Entities (owned)

- None (this feature creates adapter tools, not domain entities)

### Entities (used)

- `Asset` -- from `asset_bc`, all asset operations
- `AssetEvent` -- from `asset_bc`, asset history
- `ServiceRequest` -- from `request_bc`, all request operations
- `RequestComment` -- from `request_bc`, comment operations
- `RequestNote` -- from `request_bc`, note operations
- `RequestEvent` -- from `request_bc`, request events

### Key Components

| Component | Path | Description |
|-----------|------|-------------|
| Asset tools | `adapters/mcp/tools/assets.py` | 10 MCP tools for asset operations |
| Request tools | `adapters/mcp/tools/requests.py` | 10 MCP tools for request operations |
| Tools init | `adapters/mcp/tools/__init__.py` | Package marker, tool registration |
| Unit tests | `tests/unit/mcp/tools/test_assets.py` | Asset tool unit tests |
| Unit tests | `tests/unit/mcp/tools/test_requests.py` | Request tool unit tests |
| Integration tests | `tests/integration/test_mcp_asset_request_tools.py` | End-to-end MCP tool call tests |

---

## Notes

- Each tool function is a thin adapter: it receives MCP parameters, constructs a Command or Query dataclass, calls the existing handler, and maps the result (or error) to an MCP response.
- No new repositories, entities, or migrations are needed. All business logic lives in the existing application layer.
- Tool descriptions should be clear and concise for AI assistants. Include parameter descriptions, enum values (e.g., status options), and any constraints in the tool schema.
- The `import_assets` tool accepts `csv_content` as a string (not a file upload), since MCP tools communicate via JSON. The AI assistant would format CSV content inline.
- Request tools have mixed minimum roles (Employee for create/get/comments, Technician for status/priority/assign/notes). Each tool declares its own `min_role` in the registry.
- Employee access control for `get_request` mirrors the HTTP layer: employees can only see their own requests; attempting to access another user's request returns a "not found" error.
