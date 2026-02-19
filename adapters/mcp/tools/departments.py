"""MCP tools for department management (5 tools)."""
import json
from typing import Any

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.department.application.commands.create_department import (
    CreateDepartmentCommand,
    CreateDepartmentCommandHandler,
    DepartmentNameExistsError as CreateNameExistsError,
)
from src.company_bc.department.application.commands.delete_department import (
    DeleteDepartmentCommand,
    DeleteDepartmentCommandHandler,
    DepartmentHasUsersError,
    DepartmentNotFoundError as DeleteNotFoundError,
)
from src.company_bc.department.application.commands.update_department import (
    DepartmentNameExistsError as UpdateNameExistsError,
    DepartmentNotFoundError as UpdateNotFoundError,
    UpdateDepartmentCommand,
    UpdateDepartmentCommandHandler,
)
from src.company_bc.department.application.queries.get_department import (
    DepartmentNotFoundError as GetNotFoundError,
    GetDepartmentQuery,
    GetDepartmentQueryHandler,
)
from src.company_bc.department.application.queries.list_departments import (
    ListDepartmentsQuery,
    ListDepartmentsQueryHandler,
)
from src.company_bc.department.domain.entities import Department
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)


def _serialize_department(dept: Department) -> dict[str, Any]:
    return {
        "id": dept.id,
        "company_id": dept.company_id,
        "name": dept.name,
        "is_active": dept.is_active,
        "created_at": (
            dept.created_at.isoformat()
            if dept.created_at else None
        ),
        "updated_at": (
            dept.updated_at.isoformat()
            if dept.updated_at else None
        ),
    }


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data))]


def _error(message: str) -> list[TextContent]:
    return _text({"error": message})


class _AuthenticatedTenant:
    """Typed wrapper ensuring company_id is non-None."""

    __slots__ = ("company_id", "user_id", "role")

    def __init__(self, ctx: TenantContext) -> None:
        assert ctx.company_id is not None
        self.company_id: str = ctx.company_id
        self.user_id: str = ctx.user_id
        self.role: str = ctx.role


def _require_tenant() -> _AuthenticatedTenant:
    """Get tenant context, raising if not authenticated."""
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated tool call"
    return _AuthenticatedTenant(tenant)


# --- Tool handlers ---


async def handle_create_department(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        dept_repo = DepartmentRepository(db)

        command = CreateDepartmentCommand(
            company_id=tenant.company_id,
            name=arguments["name"],
        )

        handler = CreateDepartmentCommandHandler(dept_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch by name to get timestamps
        dept = dept_repo.find_by_name(
            arguments["name"], tenant.company_id,
        )
        assert dept is not None
        return _text(_serialize_department(dept))
    except CreateNameExistsError as e:
        db.rollback()
        return _error(str(e))
    except (ValueError, KeyError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_departments(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        dept_repo = DepartmentRepository(db)

        query = ListDepartmentsQuery(
            company_id=tenant.company_id,
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
            include_inactive=arguments.get(
                "include_inactive", False,
            ),
        )

        handler = ListDepartmentsQueryHandler(dept_repo)
        departments, total = handler.handle(query)

        return _text({
            "items": [
                _serialize_department(d) for d in departments
            ],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_get_department(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        dept_repo = DepartmentRepository(db)

        query = GetDepartmentQuery(
            department_id=arguments["department_id"],
            company_id=tenant.company_id,
        )

        handler = GetDepartmentQueryHandler(dept_repo)
        detail = handler.handle(query)

        result = _serialize_department(detail.department)
        result["user_count"] = detail.user_count
        return _text(result)
    except GetNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_update_department(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        dept_repo = DepartmentRepository(db)

        command = UpdateDepartmentCommand(
            department_id=arguments["department_id"],
            company_id=tenant.company_id,
            name=arguments["name"],
        )

        handler = UpdateDepartmentCommandHandler(dept_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch updated department
        get_handler = GetDepartmentQueryHandler(dept_repo)
        detail = get_handler.handle(
            GetDepartmentQuery(
                department_id=arguments["department_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(
            _serialize_department(detail.department)
        )
    except (
        UpdateNotFoundError,
        UpdateNameExistsError,
    ) as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_delete_department(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        dept_repo = DepartmentRepository(db)

        command = DeleteDepartmentCommand(
            department_id=arguments["department_id"],
            company_id=tenant.company_id,
        )

        handler = DeleteDepartmentCommandHandler(dept_repo)
        handler.handle(command)
        db.commit()

        return _text({"success": True})
    except (
        DeleteNotFoundError,
        DepartmentHasUsersError,
    ) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="create_department",
    description="Create a new department in the company.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Department name",
            },
        },
        "required": ["name"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_create_department,
)

tool_registry.register(
    name="list_departments",
    description=(
        "List departments with pagination. "
        "Optionally include inactive departments."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": "Page number (default 1)",
            },
            "page_size": {
                "type": "integer",
                "description": "Items per page (default 20)",
            },
            "include_inactive": {
                "type": "boolean",
                "description": (
                    "Include inactive/deleted departments "
                    "(default false)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_list_departments,
)

tool_registry.register(
    name="get_department",
    description=(
        "Get department details including user count."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "department_id": {
                "type": "string",
                "description": "The department ID",
            },
        },
        "required": ["department_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_get_department,
)

tool_registry.register(
    name="update_department",
    description="Update a department's name.",
    input_schema={
        "type": "object",
        "properties": {
            "department_id": {
                "type": "string",
                "description": "The department ID to update",
            },
            "name": {
                "type": "string",
                "description": "New department name",
            },
        },
        "required": ["department_id", "name"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_update_department,
)

tool_registry.register(
    name="delete_department",
    description=(
        "Delete (deactivate) a department. "
        "Fails if users are assigned."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "department_id": {
                "type": "string",
                "description": (
                    "The department ID to delete"
                ),
            },
        },
        "required": ["department_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_delete_department,
)
