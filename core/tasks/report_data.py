"""Data collectors for report generation.

Each function gathers data from repositories and returns a dict
suitable for passing to a Jinja2 template.
"""

from typing import Any, Optional

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
