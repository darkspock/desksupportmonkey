"""MCP tools for report management (4 tools)."""
import json
from typing import Any, Optional

import ulid
from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.config import settings
from core.database import SessionLocal
from core.storage import S3StorageService
from core.tenant import TenantContext, get_tenant
from src.auth_bc.user.domain.enums import UserRole
from src.report_bc.report.application.commands.request_report import (
    RequestReportCommand,
    RequestReportCommandHandler,
)
from src.report_bc.report.application.queries.get_report import (
    GetReportQuery,
    GetReportQueryHandler,
    ReportNotFoundError,
)
from src.report_bc.report.application.queries.list_reports import (
    ListReportsQuery,
    ListReportsQueryHandler,
)
from src.report_bc.report.domain.entities import Report
from src.report_bc.report.domain.enums import ReportStatus
from src.report_bc.report.infrastructure.repository import ReportRepository


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
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated tool call"
    return _AuthenticatedTenant(tenant)


def _serialize_report(report: Report) -> dict[str, Any]:
    return {
        "id": report.id,
        "type": report.type.value,
        "status": report.status.value,
        "parameters": report.parameters,
        "created_at": (
            report.created_at.isoformat()
            if report.created_at else None
        ),
        "completed_at": (
            report.completed_at.isoformat()
            if report.completed_at else None
        ),
        "error_message": report.error_message,
    }


# --- Tool handlers ---


async def handle_request_report(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        report_repo = ReportRepository(db)

        report_id = str(ulid.new())
        parameters: Optional[dict] = None
        from_date = arguments.get("from_date")
        to_date = arguments.get("to_date")
        if from_date or to_date:
            parameters = {}
            if from_date:
                parameters["from_date"] = from_date
            if to_date:
                parameters["to_date"] = to_date

        handler = RequestReportCommandHandler(
            report_repo=report_repo,
        )
        handler.handle(
            RequestReportCommand(
                company_id=tenant.company_id,
                requested_by=tenant.user_id,
                type=arguments["type"],
                parameters=parameters,
                id=report_id,
            )
        )
        db.commit()

        query_handler = GetReportQueryHandler(
            report_repo=report_repo,
        )
        report = query_handler.handle(
            GetReportQuery(
                report_id=report_id,
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_report(report))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_reports(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        report_repo = ReportRepository(db)

        query = ListReportsQuery(
            company_id=tenant.company_id,
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
        )

        handler = ListReportsQueryHandler(
            report_repo=report_repo,
        )
        reports, total = handler.handle(query)

        return _text({
            "items": [
                _serialize_report(r) for r in reports
            ],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_get_report(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        report_repo = ReportRepository(db)

        handler = GetReportQueryHandler(
            report_repo=report_repo,
        )
        report = handler.handle(
            GetReportQuery(
                report_id=arguments["report_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_report(report))
    except ReportNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_download_report(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        report_repo = ReportRepository(db)

        report = report_repo.find_by_id(
            arguments["report_id"], tenant.company_id,
        )
        if not report:
            return _error("Report not found")

        if report.status != ReportStatus.COMPLETED:
            return _error(
                f"Report is {report.status.value}"
            )

        storage = S3StorageService()
        url = storage.get_signed_url(
            report.storage_key,
            settings.s3.S3_SIGNED_URL_EXPIRY,
        )
        return _text({"download_url": url})
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="request_report",
    description=(
        "Request generation of a report. Returns "
        "immediately with status 'pending'. The report "
        "is generated asynchronously. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": (
                    "Report type: asset_inventory, "
                    "request_summary, or "
                    "technician_performance"
                ),
            },
            "from_date": {
                "type": "string",
                "description": (
                    "Optional start date (YYYY-MM-DD)"
                ),
            },
            "to_date": {
                "type": "string",
                "description": (
                    "Optional end date (YYYY-MM-DD)"
                ),
            },
        },
        "required": ["type"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_request_report,
)

tool_registry.register(
    name="list_reports",
    description=(
        "List reports with pagination. Admin only."
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
                "description": (
                    "Items per page (default 20)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_list_reports,
)

tool_registry.register(
    name="get_report",
    description=(
        "Get detailed information about a specific "
        "report. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {
                "type": "string",
                "description": "The report ID",
            },
        },
        "required": ["report_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_get_report,
)

tool_registry.register(
    name="download_report",
    description=(
        "Get a download URL for a completed report. "
        "Report must have status 'completed'. "
        "Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "report_id": {
                "type": "string",
                "description": "The report ID to download",
            },
        },
        "required": ["report_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_download_report,
)
