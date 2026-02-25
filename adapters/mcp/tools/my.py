"""MCP tools for personal data and settings (7 tools)."""
import json
from typing import Any

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.asset_bc.asset.application.queries.my_equipment import (
    MyEquipmentQuery,
    MyEquipmentQueryHandler,
)
from src.asset_bc.asset.domain.entities import Asset
from src.asset_bc.asset.infrastructure.repository import (
    AssetRepository,
)
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.company.application.commands.update_company import (  # noqa: E501
    CompanyNotFoundError as UpdateCompanyNotFoundError,
    DomainAlreadyTakenError,
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.application.queries.get_company import (  # noqa: E501
    CompanyNotFoundError as GetCompanyNotFoundError,
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.infrastructure.repository import (
    CompanyRepository,
)
from src.notification_bc.notification.application.commands.mark_all_read import (  # noqa: E501
    MarkAllReadCommand,
    MarkAllReadCommandHandler,
)
from src.notification_bc.notification.application.commands.mark_read import (  # noqa: E501
    MarkReadCommand,
    MarkReadCommandHandler,
    NotificationNotFoundError,
)
from src.notification_bc.notification.application.queries.list_notifications import (  # noqa: E501
    ListNotificationsQuery,
    ListNotificationsQueryHandler,
)
from src.notification_bc.notification.infrastructure.repository import (  # noqa: E501
    NotificationRepository,
)
from src.request_bc.request.application.queries.my_requests import (
    MyRequestsQuery,
    MyRequestsQueryHandler,
)
from src.request_bc.request.domain.entities import (
    ServiceRequest,
)
from src.request_bc.request.infrastructure.repository import (
    RequestRepository,
)


def _text(data: Any) -> list[TextContent]:
    return [TextContent(
        type="text", text=json.dumps(data),
    )]


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
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated"
    return _AuthenticatedTenant(tenant)


def _serialize_asset(asset: Asset) -> dict[str, Any]:
    return {
        "id": asset.id,
        "type": asset.type,
        "brand": asset.brand,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "status": asset.status.value,
        "created_at": (
            asset.created_at.isoformat()
            if asset.created_at else None
        ),
    }


def _serialize_request(
    req: ServiceRequest,
) -> dict[str, Any]:
    return {
        "id": req.id,
        "type": req.type,
        "title": req.title,
        "status": req.status.value,
        "priority": req.priority.value,
        "assigned_to": req.assigned_to,
        "created_at": (
            req.created_at.isoformat()
            if req.created_at else None
        ),
        "updated_at": (
            req.updated_at.isoformat()
            if req.updated_at else None
        ),
    }


# --- Tool handlers ---


async def handle_my_equipment(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        asset_repo = AssetRepository(db)

        handler = MyEquipmentQueryHandler(
            asset_repo=asset_repo,
        )
        assets = handler.handle(
            MyEquipmentQuery(
                user_id=tenant.user_id,
                company_id=tenant.company_id,
            )
        )

        return _text([
            _serialize_asset(a) for a in assets
        ])
    finally:
        db.close()


async def handle_my_requests(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        handler = MyRequestsQueryHandler(
            request_repo=request_repo,
        )
        requests, total = handler.handle(
            MyRequestsQuery(
                user_id=tenant.user_id,
                company_id=tenant.company_id,
                page=arguments.get("page", 1),
                page_size=arguments.get(
                    "page_size", 20,
                ),
                status=arguments.get("status"),
            )
        )

        return _text({
            "items": [
                _serialize_request(r)
                for r in requests
            ],
            "total": total,
            "page": arguments.get("page", 1),
            "page_size": arguments.get(
                "page_size", 20,
            ),
        })
    finally:
        db.close()


async def handle_my_notifications(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        notif_repo = NotificationRepository(db)

        handler = ListNotificationsQueryHandler(
            notification_repo=notif_repo,
        )
        result = handler.handle(
            ListNotificationsQuery(
                user_id=tenant.user_id,
                page=arguments.get("page", 1),
                page_size=arguments.get(
                    "page_size", 20,
                ),
                is_read=arguments.get("is_read"),
            )
        )
        notifications, total, unread_count = result

        return _text({
            "items": [
                {
                    "id": n.id,
                    "event_type": n.event_type,
                    "title": n.title,
                    "body": n.body,
                    "data": n.data,
                    "is_read": n.is_read,
                    "created_at": (
                        n.created_at.isoformat()
                        if n.created_at else None
                    ),
                }
                for n in notifications
            ],
            "total": total,
            "page": arguments.get("page", 1),
            "page_size": arguments.get(
                "page_size", 20,
            ),
            "unread_count": unread_count,
        })
    finally:
        db.close()


async def handle_mark_notification_read(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        notif_repo = NotificationRepository(db)

        handler = MarkReadCommandHandler(
            notification_repo=notif_repo,
        )
        handler.handle(
            MarkReadCommand(
                notification_id=arguments[
                    "notification_id"
                ],
                user_id=tenant.user_id,
            )
        )
        db.commit()

        return _text({
            "id": arguments["notification_id"],
            "is_read": True,
        })
    except NotificationNotFoundError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_mark_all_notifications_read(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        notif_repo = NotificationRepository(db)

        handler = MarkAllReadCommandHandler(
            notification_repo=notif_repo,
        )
        handler.handle(
            MarkAllReadCommand(
                user_id=tenant.user_id,
            )
        )
        db.commit()

        return _text({"success": True})
    finally:
        db.close()


async def handle_get_my_company_settings(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        company_repo = CompanyRepository(db)

        handler = GetCompanyQueryHandler(
            company_repo=company_repo,
        )
        detail = handler.handle(
            GetCompanyQuery(
                company_id=tenant.company_id,
            )
        )

        return _text({
            "id": detail.company.id,
            "name": detail.company.name,
            "email_domains": (
                detail.company.email_domains
            ),
        })
    except GetCompanyNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_update_my_company_settings(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        company_repo = CompanyRepository(db)

        handler = UpdateCompanyCommandHandler(
            company_repo=company_repo,
        )
        handler.handle(
            UpdateCompanyCommand(
                company_id=tenant.company_id,
                email_domains=arguments.get(
                    "email_domains",
                ),
            )
        )
        db.commit()

        # Re-fetch updated settings
        query_handler = GetCompanyQueryHandler(
            company_repo=company_repo,
        )
        detail = query_handler.handle(
            GetCompanyQuery(
                company_id=tenant.company_id,
            )
        )

        return _text({
            "id": detail.company.id,
            "name": detail.company.name,
            "email_domains": (
                detail.company.email_domains
            ),
        })
    except UpdateCompanyNotFoundError as e:
        db.rollback()
        return _error(str(e))
    except DomainAlreadyTakenError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="my_equipment",
    description=(
        "List assets assigned to the current user."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_my_equipment,
)

tool_registry.register(
    name="my_requests",
    description=(
        "List service requests created by the "
        "current user with optional status filter."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": (
                    "Page number (default 1)"
                ),
            },
            "page_size": {
                "type": "integer",
                "description": (
                    "Items per page (default 20)"
                ),
            },
            "status": {
                "type": "string",
                "description": (
                    "Filter by status: submitted, "
                    "in_review, in_progress, "
                    "resolved, closed, cancelled"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_my_requests,
)

tool_registry.register(
    name="my_notifications",
    description=(
        "List notifications for the current user "
        "with unread count."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": (
                    "Page number (default 1)"
                ),
            },
            "page_size": {
                "type": "integer",
                "description": (
                    "Items per page (default 20)"
                ),
            },
            "is_read": {
                "type": "boolean",
                "description": (
                    "Filter by read status"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_my_notifications,
)

tool_registry.register(
    name="mark_notification_read",
    description=(
        "Mark a specific notification as read."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "notification_id": {
                "type": "string",
                "description": (
                    "The notification ID"
                ),
            },
        },
        "required": ["notification_id"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_mark_notification_read,
)

tool_registry.register(
    name="mark_all_notifications_read",
    description=(
        "Mark all notifications as read for the "
        "current user."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_mark_all_notifications_read,
)

tool_registry.register(
    name="get_my_company_settings",
    description=(
        "Get the current user's company settings "
        "(name, email domains). Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_get_my_company_settings,
)

tool_registry.register(
    name="update_my_company_settings",
    description=(
        "Update the current user's company "
        "settings (email domains). Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "email_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of allowed email domains"
                ),
            },
        },
        "required": ["email_domains"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_update_my_company_settings,
)
