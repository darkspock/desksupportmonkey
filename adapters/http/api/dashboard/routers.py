from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.dashboard.schemas import (
    AgingAlertItem,
    AssetStatusCounts,
    AssetSummaryResponse,
    AssetTypeCounts,
    RequestPriorityCounts,
    RequestStatusCounts,
    RequestSummaryResponse,
    RequestTrendResponse,
    RequestTypeCounts,
    ResolutionTimeResponse,
    SlaAlertItem,
    TechnicianResolutionTime,
    TrendBucket,
    TrendBucketTypeCounts,
    WarrantyAlertItem,
)
from core.database import get_db
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.request_bc.request.infrastructure.repository import RequestRepository

from src.request_bc.request.domain.constants import SLA_THRESHOLDS_HOURS

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

admin_dep = require_role(UserRole.ADMIN)


@router.get("/requests/summary")
def request_summary(
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = RequestRepository(db)
    by_status = repo.count_by_status(current_user.company_id)
    by_type = repo.count_by_type(current_user.company_id)
    by_priority = repo.count_by_priority(current_user.company_id)

    total_open = by_status.get("submitted", 0) + by_status.get("in_review", 0) + by_status.get("in_progress", 0)
    total_resolved = by_status.get("resolved", 0)

    return {
        "data": RequestSummaryResponse(
            by_status=RequestStatusCounts(**by_status),
            by_type=RequestTypeCounts(**by_type),
            by_priority=RequestPriorityCounts(**by_priority),
            total_open=total_open,
            total_resolved=total_resolved,
        ).model_dump()
    }


@router.get("/requests/resolution-time")
def request_resolution_time(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = RequestRepository(db)
    avg_hours = repo.avg_resolution_time(current_user.company_id, from_date, to_date)
    by_tech = repo.avg_resolution_time_by_technician(current_user.company_id, from_date, to_date)

    return {
        "data": ResolutionTimeResponse(
            avg_hours=avg_hours,
            by_technician=[TechnicianResolutionTime(**t) for t in by_tech],
        ).model_dump()
    }


@router.get("/requests/trend")
def request_trend(
    bucket: str = Query("day", pattern="^(day|week|month)$"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = RequestRepository(db)
    effective_to = to_date or date.today()
    effective_from = from_date or (effective_to - timedelta(days=30))

    raw = repo.count_by_period(current_user.company_id, bucket, effective_from, effective_to)

    # Aggregate raw rows (period, type, count) into TrendBucket list
    buckets: dict[str, dict[str, int]] = {}
    for row in raw:
        period = row["period"]
        if period not in buckets:
            buckets[period] = {"incident": 0, "new_equipment": 0, "onboarding": 0}
        buckets[period][row["type"]] = row["count"]

    data = []
    for period, type_counts in sorted(buckets.items()):
        total = sum(type_counts.values())
        data.append(TrendBucket(
            period=period,
            total=total,
            by_type=TrendBucketTypeCounts(**type_counts),
        ))

    return {
        "data": RequestTrendResponse(
            bucket=bucket,
            from_date=effective_from.isoformat(),
            to_date=effective_to.isoformat(),
            data=data,
        ).model_dump()
    }


@router.get("/assets/summary")
def asset_summary(
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = AssetRepository(db)
    by_status = repo.count_by_status(current_user.company_id)
    by_type = repo.count_by_type(current_user.company_id)
    total = sum(by_status.values())

    return {
        "data": AssetSummaryResponse(
            by_status=AssetStatusCounts(**by_status),
            by_type=AssetTypeCounts(**by_type),
            total=total,
        ).model_dump()
    }


@router.get("/alerts/warranty")
def warranty_alerts(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = AssetRepository(db)
    items = repo.find_expiring_warranties(current_user.company_id, days)
    return {
        "data": [WarrantyAlertItem(**item).model_dump(mode="json") for item in items]
    }


@router.get("/alerts/aging")
def aging_alerts(
    years: int = Query(3, ge=1, le=10),
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = AssetRepository(db)
    items = repo.find_aging_assets(current_user.company_id, years)
    return {
        "data": [AgingAlertItem(**item).model_dump(mode="json") for item in items]
    }


@router.get("/alerts/sla")
def sla_alerts(
    current_user: User = Depends(admin_dep),
    db: Session = Depends(get_db),
):
    repo = RequestRepository(db)
    open_requests = repo.find_open_requests_with_age(current_user.company_id)

    items = []
    for req in open_requests:
        threshold = SLA_THRESHOLDS_HOURS.get(req["priority"], 168)
        items.append(SlaAlertItem(
            id=req["id"],
            title=req["title"],
            type=req["type"],
            priority=req["priority"],
            status=req["status"],
            assigned_to=req["assigned_to"],
            created_at=req["created_at"],
            hours_open=req["hours_open"],
            sla_threshold_hours=threshold,
            breached=req["hours_open"] > threshold,
        ))

    return {
        "data": [item.model_dump(mode="json") for item in items]
    }
