from adapters.mcp.registry import ToolRegistry
from src.auth_bc.user.domain.enums import UserRole


def _noop_handler(args):
    return []


def _make_registry_with_tools() -> ToolRegistry:
    """Create a registry with one tool per role level."""
    registry = ToolRegistry()
    registry.register(
        name="view_my_requests",
        description="View my support requests",
        input_schema={"type": "object", "properties": {}},
        min_role=UserRole.EMPLOYEE,
        handler=_noop_handler,
    )
    registry.register(
        name="assign_request",
        description="Assign a request to a technician",
        input_schema={
            "type": "object",
            "properties": {"request_id": {"type": "string"}},
            "required": ["request_id"],
        },
        min_role=UserRole.TECHNICIAN,
        handler=_noop_handler,
    )
    registry.register(
        name="manage_users",
        description="Manage company users",
        input_schema={"type": "object", "properties": {}},
        min_role=UserRole.ADMIN,
        handler=_noop_handler,
    )
    registry.register(
        name="manage_companies",
        description="Manage all companies",
        input_schema={"type": "object", "properties": {}},
        min_role=UserRole.SUPER_ADMIN,
        handler=_noop_handler,
    )
    return registry


class TestToolRegistry:
    def test_register_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}},
            min_role=UserRole.EMPLOYEE,
            handler=_noop_handler,
        )

        assert registry.tool_count() == 1
        tool = registry.get_tool("test_tool")
        assert tool is not None
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.min_role == UserRole.EMPLOYEE

    def test_list_tools_filters_by_role_employee(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.EMPLOYEE)

        names = [t.name for t in tools]
        assert "view_my_requests" in names
        assert "assign_request" not in names
        assert "manage_users" not in names
        assert "manage_companies" not in names

    def test_list_tools_filters_by_role_technician(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.TECHNICIAN)

        names = [t.name for t in tools]
        assert "view_my_requests" in names
        assert "assign_request" in names
        assert "manage_users" not in names
        assert "manage_companies" not in names

    def test_list_tools_filters_by_role_admin(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.ADMIN)

        names = [t.name for t in tools]
        assert "view_my_requests" in names
        assert "assign_request" in names
        assert "manage_users" in names
        assert "manage_companies" not in names

    def test_list_tools_filters_by_role_super_admin(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.SUPER_ADMIN)

        names = [t.name for t in tools]
        assert len(names) == 4
        assert "manage_companies" in names

    def test_list_tools_empty_registry(self):
        registry = ToolRegistry()

        tools = registry.list_tools(UserRole.SUPER_ADMIN)

        assert tools == []

    def test_get_tool_found(self):
        registry = _make_registry_with_tools()

        tool = registry.get_tool("assign_request")

        assert tool is not None
        assert tool.name == "assign_request"
        assert tool.min_role == UserRole.TECHNICIAN

    def test_get_tool_not_found(self):
        registry = _make_registry_with_tools()

        tool = registry.get_tool("nonexistent")

        assert tool is None

    def test_role_hierarchy_employee_cannot_access_technician(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.EMPLOYEE)

        names = [t.name for t in tools]
        assert "assign_request" not in names

    def test_role_hierarchy_technician_can_access_employee(self):
        registry = _make_registry_with_tools()

        tools = registry.list_tools(UserRole.TECHNICIAN)

        names = [t.name for t in tools]
        assert "view_my_requests" in names
