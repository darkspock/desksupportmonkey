# F3 — User, Department & Company Tools (17 MCP Tools)

## Tasks

### 1. User Tools (`adapters/mcp/tools/users.py`)
- [x] Create `_serialize_user()` helper
- [x] Implement `list_users` tool (ADMIN, ListUsersQueryHandler, paginated with filters)
- [x] Implement `invite_user` tool (ADMIN, validate domain + ensure user + send magic link)
- [x] Implement `get_user` tool (ADMIN, GetUserDetailQueryHandler)
- [x] Implement `change_user_role` tool (ADMIN, ChangeUserRoleCommandHandler)
- [x] Implement `activate_user` tool (ADMIN, ActivateUserCommandHandler)
- [x] Implement `deactivate_user` tool (ADMIN, DeactivateUserCommandHandler)
- [x] Implement `assign_user_department` tool (ADMIN, AssignDepartmentCommandHandler)
- [x] Register all 7 user tools with `tool_registry`

### 2. Department Tools (`adapters/mcp/tools/departments.py`)
- [x] Create `_serialize_department()` helper
- [x] Implement `create_department` tool (ADMIN, CreateDepartmentCommandHandler)
- [x] Implement `list_departments` tool (ADMIN, ListDepartmentsQueryHandler)
- [x] Implement `get_department` tool (ADMIN, GetDepartmentQueryHandler)
- [x] Implement `update_department` tool (ADMIN, UpdateDepartmentCommandHandler)
- [x] Implement `delete_department` tool (ADMIN, DeleteDepartmentCommandHandler)
- [x] Register all 5 department tools with `tool_registry`

### 3. Company Tools (`adapters/mcp/tools/companies.py`)
- [x] Create `_serialize_company()` helper
- [x] Implement `create_company` tool (SUPER_ADMIN, CreateCompanyCommandHandler)
- [x] Implement `list_companies` tool (SUPER_ADMIN, ListCompaniesQueryHandler)
- [x] Implement `get_company` tool (SUPER_ADMIN, GetCompanyQueryHandler)
- [x] Implement `update_company` tool (SUPER_ADMIN, UpdateCompanyCommandHandler)
- [x] Implement `change_company_status` tool (SUPER_ADMIN, UpdateCompanyStatusCommandHandler)
- [x] Register all 5 company tools with `tool_registry`

### 4. Module Registration (`adapters/mcp/tools/__init__.py`)
- [x] Add imports for users, departments, companies modules

### 5. Unit Tests
- [x] Create `tests/unit/mcp/tools/test_users.py` (14 tests)
- [x] Create `tests/unit/mcp/tools/test_departments.py` (9 tests)
- [x] Create `tests/unit/mcp/tools/test_companies.py` (9 tests)

### 6. Verification
- [x] All tests pass (`make test`) — 549 passed
- [x] Lint passes (`uv run flake8`)
- [x] Update progress tracking documents
