"""Data collectors for report generation.

Each function gathers data from repositories and returns a dict
suitable for passing to a Jinja2 template.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.request_bc.request.domain.constants import SLA_THRESHOLDS_HOURS
from src.request_bc.request.infrastructure.repository import RequestRepository


def collect_asset_inventory(
    company_id: str, params: Optional[dict], session: Session
) -> dict[str, Any]:
    asset_repo = AssetRepository(session)
    company_repo = CompanyRepository(session)

    company = company_repo.find_by_id(company_id)
    assets = asset_repo.find_all_by_company(company_id)
    by_status = asset_repo.count_by_status(company_id)
    by_type = asset_repo.count_by_type(company_id)
    expiring = asset_repo.find_expiring_warranties(company_id, 90)

    return {
        "company_name": company.name if company else "Unknown",
        "total_assets": sum(by_status.values()),
        "by_status": by_status,
        "by_type": by_type,
        "assets": assets,
        "expiring_warranties": expiring,
    }


def collect_request_summary(
    company_id: str, params: Optional[dict], session: Session
) -> dict[str, Any]:
    request_repo = RequestRepository(session)
    company_repo = CompanyRepository(session)

    company = company_repo.find_by_id(company_id)

    from_date = params.get("from_date") if params else None
    to_date = params.get("to_date") if params else None

    by_status = request_repo.count_by_status(company_id)
    by_type = request_repo.count_by_type(company_id)
    by_priority = request_repo.count_by_priority(company_id)
    avg_time = request_repo.avg_resolution_time(company_id, from_date, to_date)
    open_requests = request_repo.find_open_requests_with_age(company_id)

    total_open = (
        by_status.get("submitted", 0)
        + by_status.get("in_review", 0)
        + by_status.get("in_progress", 0)
    )
    total_resolved = by_status.get("resolved", 0)

    # Build SLA breach summary
    sla_breaches = []
    sla_summary: dict[str, dict[str, int]] = {}
    for req in open_requests:
        priority = req["priority"]
        threshold = SLA_THRESHOLDS_HOURS.get(priority, 168)
        if priority not in sla_summary:
            sla_summary[priority] = {"breached": 0, "threshold": threshold}
        if req["hours_open"] > threshold:
            sla_breaches.append(req)
            sla_summary[priority]["breached"] += 1

    date_range = None
    if from_date or to_date:
        date_range = {"from_date": from_date or "start", "to_date": to_date or "now"}

    return {
        "company_name": company.name if company else "Unknown",
        "by_status": by_status,
        "by_type": by_type,
        "by_priority": by_priority,
        "total_open": total_open,
        "total_resolved": total_resolved,
        "avg_resolution_time": avg_time,
        "sla_breaches": sla_breaches,
        "sla_summary": sla_summary,
        "date_range": date_range,
    }


def collect_technician_performance(
    company_id: str, params: Optional[dict], session: Session
) -> dict[str, Any]:
    request_repo = RequestRepository(session)
    company_repo = CompanyRepository(session)

    company = company_repo.find_by_id(company_id)

    from_date = params.get("from_date") if params else None
    to_date = params.get("to_date") if params else None

    by_technician = request_repo.avg_resolution_time_by_technician(
        company_id, from_date, to_date
    )

    date_range = None
    if from_date or to_date:
        date_range = {"from_date": from_date or "start", "to_date": to_date or "now"}

    return {
        "company_name": company.name if company else "Unknown",
        "by_technician": by_technician,
        "date_range": date_range,
    }


def _format_cents(cents: int, currency: str = "USD") -> str:
    return f"{currency} {cents / 100:,.2f}"


def collect_department_spending(
    company_id: str, params: Optional[dict], session: Session
) -> dict[str, Any]:
    from src.company_bc.department.infrastructure.repository import (
        DepartmentRepository,
    )
    from src.procurement_bc.budget.infrastructure.models import (
        DepartmentBudgetModel,
    )
    from src.procurement_bc.budget.infrastructure.repository import (
        CompanyProcurementConfigRepository,
        DepartmentBudgetRepository,
    )
    from src.procurement_bc.purchase_order.infrastructure.models import (
        PurchaseOrderItemModel,
        PurchaseOrderModel,
    )

    company_repo = CompanyRepository(session)
    dept_repo = DepartmentRepository(session)
    budget_repo = DepartmentBudgetRepository(session)
    config_repo = CompanyProcurementConfigRepository(session)

    company = company_repo.find_by_id(company_id)
    config = config_repo.find_by_company_id(company_id)
    fiscal_year = int(params.get("fiscal_year", datetime.now().year)) if params else datetime.now().year
    currency = config.currency if config else "USD"

    # Compute fiscal year date range
    fy_start_month = config.fiscal_year_start_month if config else 1
    now = datetime.now()
    if now.month >= fy_start_month:
        fy_start = datetime(now.year, fy_start_month, 1)
    else:
        fy_start = datetime(now.year - 1, fy_start_month, 1)
    fy_end_year = fy_start.year + 1
    fy_end = datetime(fy_end_year, fy_start_month, 1)

    budgets = budget_repo.find_all_by_company_year(company_id, fiscal_year)
    departments_data, _ = dept_repo.find_all(company_id=company_id, page=1, page_size=200)
    dept_name_map = {d.id: d.name for d in departments_data}

    # Countable PO statuses for budget
    countable_statuses = ["APPROVED", "ORDERED", "PARTIALLY_RECEIVED", "RECEIVED", "CLOSED"]

    # Compute spent per department via SQL
    spent_by_dept: dict[str, int] = {}
    stmt = (
        select(
            PurchaseOrderModel.department_id,
            func.coalesce(func.sum(PurchaseOrderModel.total_amount_cents), 0),
        )
        .where(
            PurchaseOrderModel.company_id == company_id,
            PurchaseOrderModel.status.in_(countable_statuses),
            PurchaseOrderModel.created_at >= fy_start,
            PurchaseOrderModel.created_at < fy_end,
        )
        .group_by(PurchaseOrderModel.department_id)
    )
    for row in session.execute(stmt).all():
        spent_by_dept[row[0]] = int(row[1])

    total_allocated_cents = 0
    total_spent_cents = 0
    dept_rows = []
    for budget in budgets:
        spent_cents = spent_by_dept.get(budget.department_id, 0)
        allocated = budget.allocated_amount_cents
        remaining = allocated - spent_cents
        utilization = round(spent_cents * 100 / allocated) if allocated > 0 else 0
        total_allocated_cents += allocated
        total_spent_cents += spent_cents
        dept_rows.append({
            "name": dept_name_map.get(budget.department_id, budget.department_id),
            "allocated": _format_cents(allocated, currency),
            "spent": _format_cents(spent_cents, currency),
            "remaining": _format_cents(remaining, currency),
            "utilization_pct": utilization,
        })

    overall_util = round(total_spent_cents * 100 / total_allocated_cents) if total_allocated_cents > 0 else 0

    # Top 5 vendors by spend
    vendor_stmt = (
        select(
            PurchaseOrderModel.vendor_name,
            func.sum(PurchaseOrderModel.total_amount_cents).label("total"),
            func.count(PurchaseOrderModel.id).label("cnt"),
        )
        .where(
            PurchaseOrderModel.company_id == company_id,
            PurchaseOrderModel.status.in_(countable_statuses),
            PurchaseOrderModel.created_at >= fy_start,
            PurchaseOrderModel.created_at < fy_end,
        )
        .group_by(PurchaseOrderModel.vendor_name)
        .order_by(func.sum(PurchaseOrderModel.total_amount_cents).desc())
        .limit(5)
    )
    top_vendors = []
    for row in session.execute(vendor_stmt).all():  # type: ignore[assignment]
        top_vendors.append({
            "name": row[0],
            "total_spend": _format_cents(int(row[1]), currency),
            "po_count": row[2],
        })

    # Top 5 asset types by spend
    asset_type_stmt = (
        select(
            PurchaseOrderItemModel.asset_type,
            func.sum(PurchaseOrderItemModel.total_cost_cents).label("total"),
            func.count(PurchaseOrderItemModel.id).label("cnt"),
        )
        .join(
            PurchaseOrderModel,
            PurchaseOrderItemModel.purchase_order_id == PurchaseOrderModel.id,
        )
        .where(
            PurchaseOrderModel.company_id == company_id,
            PurchaseOrderModel.status.in_(countable_statuses),
            PurchaseOrderModel.created_at >= fy_start,
            PurchaseOrderModel.created_at < fy_end,
            PurchaseOrderItemModel.asset_type.is_not(None),
        )
        .group_by(PurchaseOrderItemModel.asset_type)
        .order_by(func.sum(PurchaseOrderItemModel.total_cost_cents).desc())
        .limit(5)
    )
    top_asset_types = []
    for row in session.execute(asset_type_stmt).all():  # type: ignore[assignment]
        top_asset_types.append({
            "type": str(row[0]).replace("_", " ").title(),
            "total_spend": _format_cents(int(row[1]), currency),
            "item_count": row[2],
        })

    return {
        "company_name": company.name if company else "Unknown",
        "fiscal_year": fiscal_year,
        "total_allocated": _format_cents(total_allocated_cents, currency),
        "total_spent": _format_cents(total_spent_cents, currency),
        "total_remaining": _format_cents(total_allocated_cents - total_spent_cents, currency),
        "overall_utilization": overall_util,
        "departments": dept_rows,
        "top_vendors": top_vendors,
        "top_asset_types": top_asset_types,
    }
