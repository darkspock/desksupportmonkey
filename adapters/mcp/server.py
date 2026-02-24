"""MCP server setup using the mcp Python SDK (v1.26.0).

Tested with: Claude Desktop, Cursor.
Transport: stdio (local development). SSE deferred to F6.
"""
import logging
import os
from typing import Any, Optional, Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.auth_bc.user.domain.enums import UserRole

from adapters.mcp.auth import authenticate_api_key, AuthenticationError
from adapters.mcp.registry import tool_registry
import adapters.mcp.tools  # noqa: F401 — triggers tool registration

logger = logging.getLogger(__name__)

_WRITE_PREFIXES = (
    "create_", "update_", "delete_", "assign_", "unassign_",
    "dispatch_", "deliver_", "change_", "add_", "remove_", "move_",
)


def create_mcp_server() -> Server:
    """Create and configure the MCP server with tool handlers."""
    server = Server("desksupportmonkey")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """Return tools filtered by authenticated user's role."""
        tenant = get_tenant()
        if not tenant:
            logger.warning("No tenant context found during list_tools")
            return []

        user_role = UserRole(tenant.role)
        tools_for_user = tool_registry.list_tools(user_role)

        logger.info(
            "Returning %d tools for user_id=%s, role=%s",
            len(tools_for_user),
            tenant.user_id,
            tenant.role,
        )

        return [
            Tool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.input_schema,
            )
            for tool in tools_for_user
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any]
    ) -> Sequence[TextContent]:
        """Execute a tool by name with given arguments."""
        tenant = get_tenant()
        if not tenant:
            raise Exception("Unauthenticated tool call")

        user_role = UserRole(tenant.role)

        tool = tool_registry.get_tool(name)
        if not tool:
            raise Exception(f"Unknown tool: {name}")

        if not user_role.has_access(tool.min_role):
            raise Exception(f"Insufficient permissions for tool: {name}")

        logger.info("Calling tool '%s' for user_id=%s", name, tenant.user_id)

        result: Sequence[TextContent] = await tool.handler(arguments)

        # Audit capture for write tools
        try:
            _record_mcp_audit(tenant, name, arguments)
        except Exception:
            logger.exception("MCP audit recording failed for tool %s", name)

        return result

    logger.info(
        "MCP server created with %d registered tools",
        tool_registry.tool_count(),
    )

    return server


async def run_stdio_server() -> None:
    """Run the MCP server with stdio transport.

    Reads DSM_API_KEY from environment variable, authenticates once
    at startup (stdio is a 1:1 session), then runs the server.
    """
    raw_key = os.environ.get("DSM_API_KEY")
    if not raw_key:
        msg = "DSM_API_KEY environment variable is required"
        logger.error(msg)
        raise AuthenticationError(msg)

    # Authenticate API key
    db = SessionLocal()
    try:
        user = authenticate_api_key(raw_key, db)
        db.commit()
        logger.info(
            "MCP stdio session authenticated: user_id=%s, role=%s",
            user.id,
            user.role.value,
        )
    except AuthenticationError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    # Create and run server
    server = create_mcp_server()

    logger.info("Starting MCP server with stdio transport")

    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


# ------------------------------------------------------------------
# MCP audit helpers
# ------------------------------------------------------------------


def _record_mcp_audit(
    tenant: TenantContext, tool_name: str, arguments: dict[str, Any]
) -> None:
    """Record an audit entry for MCP write tool calls."""
    if not any(tool_name.startswith(p) for p in _WRITE_PREFIXES):
        return

    from src.audit_bc.audit.application.services.audit_service import (
        AuditService,
    )
    from src.audit_bc.audit.infrastructure.repository import AuditRepository

    resource_type = _extract_mcp_resource_type(tool_name)
    resource_id = _extract_mcp_resource_id(arguments)

    db = SessionLocal()
    try:
        repo = AuditRepository(db)
        service = AuditService(repo)
        service.record(
            company_id=tenant.company_id,
            actor_id=tenant.user_id,
            actor_email="",
            action=f"mcp.{tool_name}",
            resource_type=resource_type,
            resource_id=resource_id,
            http_method="MCP",
            http_path=tool_name,
            ip_address=None,
            user_agent=None,
            request_data=arguments,
            response_status=0,
            changes=None,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _extract_mcp_resource_type(tool_name: str) -> str:
    """Extract resource type from tool name (e.g. 'create_asset' -> 'asset')."""
    for prefix in _WRITE_PREFIXES:
        if tool_name.startswith(prefix):
            return tool_name[len(prefix):]
    return tool_name


def _extract_mcp_resource_id(
    arguments: dict[str, Any],
) -> Optional[str]:
    """Extract resource ID from tool arguments."""
    for key in ("id", "asset_id", "request_id", "user_id", "risk_id",
                "incident_id", "shipment_id", "article_id"):
        if key in arguments:
            return str(arguments[key])
    return None
