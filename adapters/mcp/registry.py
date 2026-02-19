"""Tool registry with role-based filtering."""
from dataclasses import dataclass
from typing import Any, Callable

from src.auth_bc.user.domain.enums import UserRole


@dataclass
class ToolDefinition:
    """MCP tool definition with role requirement."""

    name: str
    description: str
    input_schema: dict[str, Any]
    min_role: UserRole
    handler: Callable[..., Any]


class ToolRegistry:
    """Registry of MCP tools with role-based filtering."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        min_role: UserRole,
        handler: Callable[..., Any],
    ) -> None:
        """Register a tool with minimum role requirement."""
        self._tools[name] = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            min_role=min_role,
            handler=handler,
        )

    def list_tools(self, user_role: UserRole) -> list[ToolDefinition]:
        """Return tools the user's role can access (role hierarchy)."""
        return [
            tool for tool in self._tools.values()
            if user_role.has_access(tool.min_role)
        ]

    def get_tool(self, name: str) -> ToolDefinition | None:
        """Get a specific tool by name."""
        return self._tools.get(name)

    def tool_count(self) -> int:
        """Return total number of registered tools."""
        return len(self._tools)


# Global registry instance — tool modules (F2-F5) register here
tool_registry = ToolRegistry()
