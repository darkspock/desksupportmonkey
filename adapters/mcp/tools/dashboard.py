"""MCP tools for dashboard analytics (7 tools)."""
import json
from datetime import date, timedelta
from typing import Any, Optional

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.domain.enums import UserRole
from src.request_bc.request.domain.constants import SLA_THRESHOLDS_HOURS
from src.request_bc.request.infrastructure.repository import RequestRepository


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data))]


def _error(message: str) -> list[TextContent]:
    return _text({"error": message})


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
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated tool call"
    return _AuthenticatedTenant(tenant)


def _aggregate_trend_buckets(raw: list[dict]) -> list[dict]:
    """Group raw period rows by period, sum type counts."""
    buckets: dict[str, dict[str, int]] = {}
    for row in raw:
        period = row["period"]
        if period not in buckets:
            buckets[period] = {
                "incident": 0,
                "new_equipment": 0,
                "onboarding": 0,
            }
        buckets[period][row["type"]] = row["count"]
    return [
        {
            "period": p,
            "total": sum(tc.values()),
            "by_type": tc,
        }
        for p, tc in sorted(buckets.items())
    ]


# --- Tool handlers ---


async def handle_dashboard_request_summary(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = RequestRepository(db)

        by_status = repo.count_by_status(tenant.company_id)
        by_type = repo.count_by_type(tenant.company_id)
        by_priority = repo.count_by_priority(tenant.company_id)

        total_open = (
            by_status.get("submitted", 0)
            + by_status.get("in_review", 0)
            + by_status.get("in_progress", 0)
        )
        total_resolved = by_status.get("resolved", 0)

        return _text({
            "by_status": by_status,
            "by_type": by_type,
            "by_priority": by_priority,
            "total_open": total_open,
            "total_resolved": total_resolved,
        })
    finally:
        db.close()


async def handle_dashboard_resolution_time(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = RequestRepository(db)

        from_date = _parse_date(arguments.get("from_date"))
        to_date = _parse_date(arguments.get("to_date"))

        avg_hours = repo.avg_resolution_time(
            tenant.company_id, from_date, to_date,
        )
        by_tech = repo.avg_resolution_time_by_technician(
            tenant.company_id, from_date, to_date,
        )

        return _text({
            "avg_hours": avg_hours,
            "by_technician": by_tech,
        })
    finally:
        db.close()


async def handle_dashboard_request_trend(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = RequestRepository(db)

        bucket = arguments.get("bucket", "day")
        to_dt = _parse_date(arguments.get("to_date")) or date.today()
        from_dt = (
            _parse_date(arguments.get("from_date"))
            or (to_dt - timedelta(days=30))
        )

        raw = repo.count_by_period(
            tenant.company_id, bucket, from_dt, to_dt,
        )

        return _text({
            "bucket": bucket,
            "from_date": from_dt.isoformat(),
            "to_date": to_dt.isoformat(),
            "data": _aggregate_trend_buckets(raw),
        })
    finally:
        db.close()


async def handle_dashboard_asset_summary(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = AssetRepository(db)

        by_status = repo.count_by_status(tenant.company_id)
        by_type = repo.count_by_type(tenant.company_id)
        total = sum(by_status.values())

        return _text({
            "by_status": by_status,
            "by_type": by_type,
            "total": total,
        })
    finally:
        db.close()


async def handle_dashboard_warranty_alerts(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = AssetRepository(db)

        days = arguments.get("days", 30)
        items = repo.find_expiring_warranties(
            tenant.company_id, days,
        )

        return _text(items)
    finally:
        db.close()


async def handle_dashboard_aging_alerts(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = AssetRepository(db)

        years = arguments.get("years", 3)
        items = repo.find_aging_assets(
            tenant.company_id, years,
        )

        return _text(items)
    finally:
        db.close()


async def handle_dashboard_sla_alerts(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        repo = RequestRepository(db)

        open_requests = repo.find_open_requests_with_age(
            tenant.company_id,
        )

        items = []
        for req in open_requests:
            threshold = SLA_THRESHOLDS_HOURS.get(
                req["priority"], 168,
            )
            items.append({
                "id": req["id"],
                "title": req["title"],
                "type": req["type"],
                "priority": req["priority"],
                "status": req["status"],
                "assigned_to": req["assigned_to"],
                "created_at": (
                    req["created_at"].isoformat()
                    if hasattr(req["created_at"], "isoformat")
                    else str(req["created_at"])
                ),
                "hours_open": req["hours_open"],
                "sla_threshold_hours": threshold,
                "breached": req["hours_open"] > threshold,
            })

        return _text(items)
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="dashboard_request_summary",
    description=(
        "Get request summary with counts by status, "
        "type, and priority. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_request_summary,
)

tool_registry.register(
    name="dashboard_resolution_time",
    description=(
        "Get average resolution time overall and by "
        "technician. Optionally filter by date range. "
        "Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "from_date": {
                "type": "string",
                "description": (
                    "Start date filter (YYYY-MM-DD)"
                ),
            },
            "to_date": {
                "type": "string",
                "description": (
                    "End date filter (YYYY-MM-DD)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_resolution_time,
)

tool_registry.register(
    name="dashboard_request_trend",
    description=(
        "Get request trend data grouped by time period. "
        "Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "bucket": {
                "type": "string",
                "description": (
                    "Time bucket: day, week, or month "
                    "(default day)"
                ),
            },
            "from_date": {
                "type": "string",
                "description": (
                    "Start date (YYYY-MM-DD, default "
                    "30 days ago)"
                ),
            },
            "to_date": {
                "type": "string",
                "description": (
                    "End date (YYYY-MM-DD, default today)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_request_trend,
)

tool_registry.register(
    name="dashboard_asset_summary",
    description=(
        "Get asset summary with counts by status and "
        "type. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_asset_summary,
)

tool_registry.register(
    name="dashboard_warranty_alerts",
    description=(
        "Get assets with warranties expiring soon. "
        "Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "days": {
                "type": "integer",
                "description": (
                    "Days until expiration threshold "
                    "(default 30)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_warranty_alerts,
)

tool_registry.register(
    name="dashboard_aging_alerts",
    description=(
        "Get assets older than a specified number of "
        "years. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "years": {
                "type": "integer",
                "description": (
                    "Age threshold in years (default 3)"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_aging_alerts,
)

tool_registry.register(
    name="dashboard_sla_alerts",
    description=(
        "Get open requests with SLA breach detection. "
        "Shows hours open vs SLA threshold. Admin only."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_dashboard_sla_alerts,
)
