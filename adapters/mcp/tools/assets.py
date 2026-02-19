"""MCP tools for asset management (10 tools)."""
import json
from datetime import date
from typing import Any, Optional, cast

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.asset_bc.asset.application.commands.assign_asset import (
    AssignAssetCommand,
    AssignAssetCommandHandler,
    UserInactiveError,
    UserNotFoundError,
)
from src.asset_bc.asset.application.commands.change_asset_status import (
    ChangeAssetStatusCommand,
    ChangeAssetStatusCommandHandler,
)
from src.asset_bc.asset.application.commands.create_asset import (
    CreateAssetCommand,
    CreateAssetCommandHandler,
    SerialNumberExistsError,
)
from src.asset_bc.asset.application.commands.import_assets import (
    ImportAssetsRequest,
    ImportAssetsService,
    InvalidCSVError,
)
from src.asset_bc.asset.application.commands.unassign_asset import (
    UnassignAssetCommand,
    UnassignAssetCommandHandler,
)
from src.asset_bc.asset.application.commands.update_asset import (
    UpdateAssetCommand,
    UpdateAssetCommandHandler,
)
from src.asset_bc.asset.application.ports import UserLookup
from src.asset_bc.asset.application.queries.get_asset import (
    AssetNotFoundError,
    GetAssetQuery,
    GetAssetQueryHandler,
)
from src.asset_bc.asset.application.queries.get_asset_history import (
    GetAssetHistoryQuery,
    GetAssetHistoryQueryHandler,
)
from src.asset_bc.asset.application.queries.list_assets import (
    ListAssetsQuery,
    ListAssetsQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset, InvalidAssignmentError
from src.asset_bc.asset.domain.enums import InvalidStatusTransitionError
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository


def _serialize_asset(asset: Asset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "company_id": asset.company_id,
        "type": asset.type.value,
        "brand": asset.brand,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "status": asset.status.value,
        "assigned_to": asset.assigned_to,
        "department_id": asset.department_id,
        "purchase_date": (
            str(asset.purchase_date)
            if asset.purchase_date else None
        ),
        "warranty_expiration": (
            str(asset.warranty_expiration)
            if asset.warranty_expiration else None
        ),
        "notes": asset.notes,
        "created_at": (
            asset.created_at.isoformat()
            if asset.created_at else None
        ),
        "updated_at": (
            asset.updated_at.isoformat()
            if asset.updated_at else None
        ),
    }


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data))]


def _error(message: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": message}))]


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    return date.fromisoformat(value)


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


async def handle_create_asset(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        command = CreateAssetCommand(
            company_id=tenant.company_id,
            type=arguments["type"],
            brand=arguments["brand"],
            model=arguments["model"],
            serial_number=arguments["serial_number"],
            performed_by=tenant.user_id,
            purchase_date=_parse_date(
                arguments.get("purchase_date")
            ),
            warranty_expiration=_parse_date(
                arguments.get("warranty_expiration")
            ),
            notes=arguments.get("notes"),
        )

        handler = CreateAssetCommandHandler(asset_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch to get timestamps
        found = asset_repo.find_by_serial_number(
            command.serial_number, tenant.company_id
        )
        assert found is not None
        return _text(_serialize_asset(found))
    except SerialNumberExistsError as e:
        db.rollback()
        return _error(str(e))
    except (ValueError, KeyError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_assets(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        query = ListAssetsQuery(
            company_id=tenant.company_id,
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
            search=arguments.get("search"),
            type=arguments.get("type"),
            status=arguments.get("status"),
            department_id=arguments.get("department_id"),
            assigned_to=arguments.get("assigned_to"),
            sort_by=arguments.get("sort_by", "created_at"),
            sort_order=arguments.get("sort_order", "desc"),
        )

        handler = ListAssetsQueryHandler(asset_repo)
        assets, total = handler.handle(query)

        return _text({
            "items": [_serialize_asset(a) for a in assets],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_get_asset(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        query = GetAssetQuery(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
        )

        handler = GetAssetQueryHandler(asset_repo)
        asset = handler.handle(query)
        return _text(_serialize_asset(asset))
    except AssetNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_update_asset(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        command = UpdateAssetCommand(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
            performed_by=tenant.user_id,
            brand=arguments.get("brand"),
            model=arguments.get("model"),
            notes=arguments.get("notes"),
            purchase_date=_parse_date(
                arguments.get("purchase_date")
            ),
            warranty_expiration=_parse_date(
                arguments.get("warranty_expiration")
            ),
        )

        handler = UpdateAssetCommandHandler(asset_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch updated asset
        get_handler = GetAssetQueryHandler(asset_repo)
        asset = get_handler.handle(
            GetAssetQuery(
                asset_id=arguments["asset_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_asset(asset))
    except AssetNotFoundError as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_change_asset_status(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        command = ChangeAssetStatusCommand(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
            new_status=arguments["new_status"],
            performed_by=tenant.user_id,
        )

        handler = ChangeAssetStatusCommandHandler(asset_repo)
        handler.handle(command)
        db.commit()

        get_handler = GetAssetQueryHandler(asset_repo)
        asset = get_handler.handle(
            GetAssetQuery(
                asset_id=arguments["asset_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_asset(asset))
    except (AssetNotFoundError, InvalidStatusTransitionError) as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_assign_asset(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)
        user_repo = UserRepository(db)

        command = AssignAssetCommand(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
            user_id=arguments["user_id"],
            performed_by=tenant.user_id,
        )

        handler = AssignAssetCommandHandler(
            asset_repo, cast(UserLookup, user_repo),
        )
        handler.handle(command)
        db.commit()

        get_handler = GetAssetQueryHandler(asset_repo)
        asset = get_handler.handle(
            GetAssetQuery(
                asset_id=arguments["asset_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_asset(asset))
    except (
        AssetNotFoundError,
        UserNotFoundError,
        UserInactiveError,
        InvalidAssignmentError,
    ) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_unassign_asset(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        command = UnassignAssetCommand(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
            performed_by=tenant.user_id,
        )

        handler = UnassignAssetCommandHandler(asset_repo)
        handler.handle(command)
        db.commit()

        get_handler = GetAssetQueryHandler(asset_repo)
        asset = get_handler.handle(
            GetAssetQuery(
                asset_id=arguments["asset_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_asset(asset))
    except (AssetNotFoundError, InvalidAssignmentError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_get_asset_history(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        query = GetAssetHistoryQuery(
            asset_id=arguments["asset_id"],
            company_id=tenant.company_id,
        )

        handler = GetAssetHistoryQueryHandler(asset_repo)
        events = handler.handle(query)

        return _text([
            {
                "event_type": e.event_type,
                "data": e.data,
                "performed_by": e.performed_by,
                "created_at": (
                    e.created_at.isoformat()
                    if e.created_at else None
                ),
            }
            for e in events
        ])
    except AssetNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_import_assets(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        request = ImportAssetsRequest(
            company_id=tenant.company_id,
            performed_by=tenant.user_id,
            csv_content=arguments["csv_content"],
        )

        service = ImportAssetsService(asset_repo)
        result = service.handle(request)
        db.commit()

        return _text({
            "total": result.total,
            "successful": result.successful,
            "failed": [
                {"row": f.row, "error": f.error}
                for f in result.failed
            ],
        })
    except InvalidCSVError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_assignable_users(arguments: dict) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        users, _ = user_repo.find_all_by_company(
            company_id=tenant.company_id,
            page=1,
            page_size=1000,
            is_active=True,
        )

        return _text([
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
            }
            for u in users
        ])
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="create_asset",
    description="Create a new asset in the inventory.",
    input_schema={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": (
                    "Asset type. One of: laptop, monitor, keyboard, mouse, "
                    "headset, docking_station, other"
                ),
            },
            "brand": {"type": "string", "description": "Brand/manufacturer"},
            "model": {"type": "string", "description": "Model name"},
            "serial_number": {
                "type": "string",
                "description": "Unique serial number",
            },
            "purchase_date": {
                "type": "string",
                "description": "Purchase date (YYYY-MM-DD)",
            },
            "warranty_expiration": {
                "type": "string",
                "description": "Warranty expiration date (YYYY-MM-DD)",
            },
            "notes": {"type": "string", "description": "Optional notes"},
        },
        "required": ["type", "brand", "model", "serial_number"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_create_asset,
)

tool_registry.register(
    name="list_assets",
    description="List assets with filtering, search, and pagination.",
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
            "search": {
                "type": "string",
                "description": (
                    "Search by serial number, brand, or model"
                ),
            },
            "type": {
                "type": "string",
                "description": (
                    "Filter by type: laptop, monitor, keyboard, mouse, "
                    "headset, docking_station, other"
                ),
            },
            "status": {
                "type": "string",
                "description": (
                    "Filter by status: in_stock, assigned, "
                    "in_repair, decommissioned"
                ),
            },
            "department_id": {
                "type": "string",
                "description": "Filter by department ID",
            },
            "assigned_to": {
                "type": "string",
                "description": (
                    "Filter by assigned user ID, "
                    "or 'none' for unassigned"
                ),
            },
            "sort_by": {
                "type": "string",
                "description": (
                    "Sort field: created_at, "
                    "purchase_date, "
                    "warranty_expiration "
                    "(default created_at)"
                ),
            },
            "sort_order": {
                "type": "string",
                "description": "Sort order: asc or desc (default desc)",
            },
        },
        "required": [],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_list_assets,
)

tool_registry.register(
    name="get_asset",
    description="Get detailed information about a specific asset.",
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {"type": "string", "description": "The asset ID"},
        },
        "required": ["asset_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_get_asset,
)

tool_registry.register(
    name="update_asset",
    description="Update asset details (brand, model, notes, dates).",
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {
                "type": "string",
                "description": "The asset ID to update",
            },
            "brand": {"type": "string", "description": "New brand"},
            "model": {"type": "string", "description": "New model name"},
            "notes": {"type": "string", "description": "New notes"},
            "purchase_date": {
                "type": "string",
                "description": "New purchase date (YYYY-MM-DD)",
            },
            "warranty_expiration": {
                "type": "string",
                "description": (
                    "New warranty expiration date "
                    "(YYYY-MM-DD)"
                ),
            },
        },
        "required": ["asset_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_update_asset,
)

tool_registry.register(
    name="change_asset_status",
    description=(
        "Change an asset's status. Valid transitions: "
        "in_stock->in_repair/decommissioned, "
        "assigned->in_repair/decommissioned, "
        "in_repair->in_stock/decommissioned."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {"type": "string", "description": "The asset ID"},
            "new_status": {
                "type": "string",
                "description": (
                    "Target status: in_stock, assigned, "
                    "in_repair, decommissioned"
                ),
            },
        },
        "required": ["asset_id", "new_status"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_change_asset_status,
)

tool_registry.register(
    name="assign_asset",
    description="Assign an asset to a user. Asset must be in_stock.",
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {
                "type": "string",
                "description": "The asset ID to assign",
            },
            "user_id": {
                "type": "string",
                "description": (
                    "The user ID to assign the asset to"
                ),
            },
        },
        "required": ["asset_id", "user_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_assign_asset,
)

tool_registry.register(
    name="unassign_asset",
    description=(
        "Unassign an asset from its current user. "
        "Returns it to in_stock."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {
                "type": "string",
                "description": "The asset ID to unassign",
            },
        },
        "required": ["asset_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_unassign_asset,
)

tool_registry.register(
    name="get_asset_history",
    description=(
        "Get the audit history of an asset "
        "(creation, assignments, status changes)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {"type": "string", "description": "The asset ID"},
        },
        "required": ["asset_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_get_asset_history,
)

tool_registry.register(
    name="import_assets",
    description=(
        "Import assets from CSV content. "
        "Required columns: type, brand, "
        "model, serial_number. Optional: "
        "purchase_date, "
        "warranty_expiration, notes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "csv_content": {
                "type": "string",
                "description": "CSV content with headers as first row",
            },
        },
        "required": ["csv_content"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_import_assets,
)

tool_registry.register(
    name="list_assignable_users",
    description="List active users who can be assigned assets.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_list_assignable_users,
)
