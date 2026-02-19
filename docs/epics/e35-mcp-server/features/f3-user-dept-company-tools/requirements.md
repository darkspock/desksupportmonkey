# Feature: User, Department & Company Tools

**Parent Epic:** [E35 - MCP Server](../../requirements.md)
**Feature #:** F3
**Dependencies:** F1 (MCP Server Core)
**Complexity:** M

---

## Scope

### Included

- `adapters/mcp/tools/users.py` -- 7 MCP tools for user management (minimum role: Admin):
  1. `list_users` -- List users with filters (page?, page_size?, role?, is_active?, department_id?, search?)
  2. `invite_user` -- Invite a new user by email (email)
  3. `get_user` -- Get user details by ID (user_id)
  4. `change_user_role` -- Change a user's role (user_id, role)
  5. `activate_user` -- Activate a deactivated user (user_id)
  6. `deactivate_user` -- Deactivate a user (user_id)
  7. `assign_user_department` -- Assign a user to a department (user_id, department_id)

- `adapters/mcp/tools/departments.py` -- 5 MCP tools for department management (minimum role: Admin):
  1. `create_department` -- Create a new department (name)
  2. `list_departments` -- List departments with filters (page?, page_size?, is_active?)
  3. `get_department` -- Get department details by ID (department_id)
  4. `update_department` -- Update department name (department_id, name)
  5. `delete_department` -- Delete a department (department_id)

- `adapters/mcp/tools/companies.py` -- 5 MCP tools for company management (minimum role: Super Admin):
  1. `create_company` -- Create a new company (name, email_domains)
  2. `list_companies` -- List companies with filters (page?, page_size?, search?, status?)
  3. `get_company` -- Get company details by ID (company_id)
  4. `update_company` -- Update company fields (company_id, name?, email_domains?)
  5. `change_company_status` -- Change company status (company_id, status)

- Each tool reuses existing command/query handlers from the application layer -- no new business logic
- Error mapping: domain exceptions mapped to MCP error responses with clear messages
- Tool descriptions include parameter documentation for AI assistants
- Tools register with the registry (F1) with their minimum role declarations

### Excluded

- Asset and request tools (F2)
- Dashboard, report, and my tools (F4)
- Auth and API key MCP tools (F5)
- Any new business logic or domain changes
- Frontend changes

---

## User Value

An AI assistant with Admin or Super Admin credentials can fully manage the organizational structure of DeskSupportMonkey: invite and manage users, create and organize departments, and (for Super Admins) manage company accounts. This enables AI-driven IT operations workflows such as automated onboarding (create department, invite users, assign departments) and organizational restructuring.

---

## Acceptance Criteria

### User Tools (minimum role: Admin)

1. **`list_users`:** Returns paginated user list with all filter parameters working (role, is_active, department_id, search)
2. **`invite_user`:** Sends an invitation to the provided email; returns error if email domain is not in company's allowed domains
3. **`get_user`:** Returns full user details for a valid user_id; returns error for nonexistent user
4. **`change_user_role`:** Changes the user's role; returns error for invalid role values
5. **`activate_user`:** Activates a deactivated user; returns error if user is already active
6. **`deactivate_user`:** Deactivates a user; returns error if user is already inactive
7. **`assign_user_department`:** Assigns user to a department; validates department exists in same company

### Department Tools (minimum role: Admin)

8. **`create_department`:** Creates a department with the given name; returns created department data
9. **`list_departments`:** Returns paginated department list with optional `is_active` filter
10. **`get_department`:** Returns department details for a valid department_id; returns error for nonexistent department
11. **`update_department`:** Updates department name; returns error for nonexistent department
12. **`delete_department`:** Deletes a department; returns error if department has assigned users (or handles per existing business rules)

### Company Tools (minimum role: Super Admin)

13. **`create_company`:** Creates a new company with name and email_domains; returns created company data
14. **`list_companies`:** Returns paginated company list with search and status filters
15. **`get_company`:** Returns full company details for a valid company_id
16. **`update_company`:** Updates company name and/or email_domains
17. **`change_company_status`:** Changes company status (e.g., active/suspended); returns error for invalid transitions

### Cross-Cutting

18. **Role enforcement:** User and department tools hidden from users below Admin role; company tools hidden from users below Super Admin role
19. **Multi-tenant isolation:** User and department tools scope data to the authenticated user's `company_id`; company tools are scoped to Super Admin access
20. **Error mapping:** Domain exceptions mapped to MCP error responses with descriptive messages
21. **Unit tests:** Each tool module (`users.py`, `departments.py`, `companies.py`) has unit tests verifying parameter mapping, handler invocation, and error mapping
22. **Integration test:** At least one end-to-end test per module demonstrating a complete MCP tool call flow
23. **`make test` and `make lint` pass** with no regressions

---

## Technical Scope

### Entities (owned)

- None (this feature creates adapter tools, not domain entities)

### Entities (used)

- `User` -- from `auth_bc`, all user management operations
- `Department` -- from `company_bc`, department operations
- `Company` -- from `company_bc`, company operations

### Key Components

| Component | Path | Description |
|-----------|------|-------------|
| User tools | `adapters/mcp/tools/users.py` | 7 MCP tools for user management |
| Department tools | `adapters/mcp/tools/departments.py` | 5 MCP tools for department management |
| Company tools | `adapters/mcp/tools/companies.py` | 5 MCP tools for company management |
| Unit tests | `tests/unit/mcp/tools/test_users.py` | User tool unit tests |
| Unit tests | `tests/unit/mcp/tools/test_departments.py` | Department tool unit tests |
| Unit tests | `tests/unit/mcp/tools/test_companies.py` | Company tool unit tests |
| Integration tests | `tests/integration/test_mcp_user_dept_company_tools.py` | End-to-end MCP tool call tests |

---

## Notes

- Each tool function is a thin adapter: it receives MCP parameters, constructs a Command or Query dataclass, calls the existing handler, and maps the result (or error) to an MCP response.
- No new repositories, entities, or migrations are needed. All business logic lives in the existing application layer.
- Company tools are the only tools that require Super Admin role. The registry must correctly distinguish between Admin and Super Admin minimum roles within this feature.
- The `invite_user` tool triggers the same magic link / invitation flow as the HTTP endpoint. The AI assistant provides the email; the system handles the rest.
- Department deletion behavior follows existing business rules in the `delete_department` command handler (may fail if users are assigned).
- The `email_domains` parameter for company tools is a list of strings (e.g., `["acme.com", "acme.org"]`). MCP tool parameters support array types via JSON Schema.
- This feature can be implemented in parallel with F2 and F4, since all tool groups are independent and only depend on F1 (MCP Server Core).
