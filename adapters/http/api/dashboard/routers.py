from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.database import get_db

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.dashboard.dependencies import (
    get_asset_repo,
    get_budget_checker,
    get_budget_repo,
    get_maintenance_record_repo,
    get_po_repo,
    get_request_repo,
    get_shipment_repo,
)
from adapters.http.api.dashboard.schemas import (
    AgingAlertItem,
    AssetStatusCounts,
    AssetSummaryResponse,
    AtRiskDepartmentItem,
    BudgetHealthResponse,
    RecentPOItem,
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
from src.asset_bc.asset.infrastructure.repository import AssetRepository
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.department.infrastructure.repository import DepartmentRepository
from src.procurement_bc.budget.application.queries.get_budget_health import (
    GetBudgetHealthQuery,
    GetBudgetHealthQueryHandler,
)
from src.procurement_bc.budget.application.services.budget_checker import (
    BudgetChecker,
)
from src.procurement_bc.budget.infrastructure.repository import (
    DepartmentBudgetRepository,
)
from src.procurement_bc.purchase_order.application.queries.get_recent_pos import (
    GetRecentPurchaseOrdersQuery,
    GetRecentPurchaseOrdersQueryHandler,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (
    PurchaseOrderRepository,
)
from src.request_bc.request.infrastructure.repository import RequestRepository
from src.shipping_bc.shipment.application.queries.shipment_dashboard import (
    ShipmentDashboardQuery,
    ShipmentDashboardQueryHandler,
)
from src.shipping_bc.shipment.infrastructure.repository import (
    ShipmentRepository,
)
from src.maintenance_bc.maintenance_record.application.queries.maintenance_dashboard import (
    MaintenanceDashboardQuery,
    MaintenanceDashboardQueryHandler,
)
from src.maintenance_bc.maintenance_record.infrastructure.repository import (
    MaintenanceRecordRepository,
)

from src.request_bc.request.domain.constants import SLA_THRESHOLDS_HOURS

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

admin_dep = require_role(UserRole.ADMIN)
tech_dep = require_role(UserRole.TECHNICIAN)


@router.get("/requests/queue-counts")
def request_queue_counts(
    current_user: User = Depends(tech_dep),
    repo: RequestRepository = Depends(get_request_repo),
):
    counts = repo.queue_counts(current_user.company_id)
    return {"data": counts}


@router.get("/my-tasks/counts")
def my_task_counts(
    current_user: User = Depends(tech_dep),
    db: Session = Depends(get_db),
):
    from src.request_bc.request.infrastructure.models import ServiceRequestModel
    from src.appointment_bc.appointment.infrastructure.models import AppointmentModel
    from src.maintenance_bc.maintenance_record.infrastructure.models import MaintenanceRecordModel

    open_statuses = ["submitted", "in_review", "in_progress"]
    base_req = select(func.count()).where(
        ServiceRequestModel.company_id == current_user.company_id,
        ServiceRequestModel.assigned_to == current_user.id,
        ServiceRequestModel.status.in_(open_statuses),
    )

    requests = db.scalar(base_req) or 0

    requests_urgent = db.scalar(
        base_req.where(ServiceRequestModel.priority == "urgent")
    ) or 0

    appointments = db.scalar(
        select(func.count()).where(
            AppointmentModel.company_id == current_user.company_id,
            AppointmentModel.technician_id == current_user.id,
            AppointmentModel.status.in_(["PENDING", "CONFIRMED"]),
        )
    ) or 0

    maintenance = db.scalar(
        select(func.count()).where(
            MaintenanceRecordModel.company_id == current_user.company_id,
            MaintenanceRecordModel.technician_id == current_user.id,
            MaintenanceRecordModel.status.in_(["scheduled", "in_progress"]),
        )
    ) or 0

    total = requests + appointments + maintenance
    return {"data": {
        "requests": requests,
        "requests_urgent": requests_urgent,
        "appointments": appointments,
        "maintenance": maintenance,
        "total": total,
        "has_urgent": requests_urgent > 0,
    }}


@router.get("/requests/summary")
def request_summary(
    current_user: User = Depends(admin_dep),
    repo: RequestRepository = Depends(get_request_repo),
):
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
    repo: RequestRepository = Depends(get_request_repo),
):
    avg_hours = repo.avg_resolution_time(current_user.company_id, from_date, to_date)
    by_tech = repo.avg_resolution_time_by_technician(current_user.company_id, from_date, to_date)

    return {
        "data": ResolutionTimeResponse(
            avg_hours=avg_hours,
            by_technician=[TechnicianResolutionTime(**t) for t in by_tech],
        ).model_dump()
    }


def _aggregate_trend_buckets(raw: list[dict]) -> list[TrendBucket]:
    buckets: dict[str, dict[str, int]] = {}
    for row in raw:
        period = row["period"]
        if period not in buckets:
            buckets[period] = {"incident": 0, "new_equipment": 0, "onboarding": 0}
        buckets[period][row["type"]] = row["count"]
    return [
        TrendBucket(period=p, total=sum(tc.values()), by_type=TrendBucketTypeCounts(**tc))
        for p, tc in sorted(buckets.items())
    ]


@router.get("/requests/trend")
def request_trend(
    bucket: str = Query("day", pattern="^(day|week|month)$"),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(admin_dep),
    repo: RequestRepository = Depends(get_request_repo),
):
    effective_to = to_date or date.today()
    effective_from = from_date or (effective_to - timedelta(days=30))
    raw = repo.count_by_period(current_user.company_id, bucket, effective_from, effective_to)
    return {
        "data": RequestTrendResponse(
            bucket=bucket,
            from_date=effective_from.isoformat(),
            to_date=effective_to.isoformat(),
            data=_aggregate_trend_buckets(raw),
        ).model_dump()
    }


@router.get("/assets/summary")
def asset_summary(
    current_user: User = Depends(admin_dep),
    repo: AssetRepository = Depends(get_asset_repo),
):
    by_status = repo.count_by_status(current_user.company_id)
    by_type = repo.count_by_type(current_user.company_id)
    total = sum(by_status.values())

    return {
        "data": AssetSummaryResponse(
            by_status=AssetStatusCounts(**by_status),
            by_type=by_type,
            total=total,
        ).model_dump()
    }


@router.get("/alerts/warranty")
def warranty_alerts(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(admin_dep),
    repo: AssetRepository = Depends(get_asset_repo),
):
    items = repo.find_expiring_warranties(current_user.company_id, days)
    return {
        "data": [WarrantyAlertItem(**item).model_dump(mode="json") for item in items]
    }


@router.get("/alerts/aging")
def aging_alerts(
    years: int = Query(3, ge=1, le=10),
    current_user: User = Depends(admin_dep),
    repo: AssetRepository = Depends(get_asset_repo),
):
    items = repo.find_aging_assets(current_user.company_id, years)
    return {
        "data": [AgingAlertItem(**item).model_dump(mode="json") for item in items]
    }


@router.get("/alerts/sla")
def sla_alerts(
    current_user: User = Depends(admin_dep),
    repo: RequestRepository = Depends(get_request_repo),
):
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


@router.get("/budget-health")
def budget_health(
    current_user: User = Depends(admin_dep),
    budget_repo: DepartmentBudgetRepository = Depends(get_budget_repo),
    budget_checker: BudgetChecker = Depends(get_budget_checker),
    db: Session = Depends(get_db),
):
    handler = GetBudgetHealthQueryHandler(
        budget_repo=budget_repo,
        budget_checker=budget_checker,
    )
    result = handler.handle(
        GetBudgetHealthQuery(company_id=current_user.company_id)
    )

    dept_repo = DepartmentRepository(db)
    dept_name_map: dict[str, str] = {}
    for dept_at_risk in result.departments_at_risk:
        if dept_at_risk.department_id not in dept_name_map:
            dept = dept_repo.find_by_id(dept_at_risk.department_id, current_user.company_id)
            dept_name_map[dept_at_risk.department_id] = dept.name if dept else dept_at_risk.department_id

    return {
        "data": BudgetHealthResponse(
            total_allocated_cents=result.total_allocated_cents,
            total_spent_cents=result.total_spent_cents,
            departments_at_risk=[
                AtRiskDepartmentItem(
                    department_id=d.department_id,
                    department_name=dept_name_map.get(d.department_id, d.department_id),
                    utilization_pct=d.utilization_pct,
                    remaining_cents=d.remaining_cents,
                )
                for d in result.departments_at_risk
            ],
        ).model_dump()
    }


tech_dep = require_role(UserRole.TECHNICIAN)


@router.get("/recent-purchase-orders")
def recent_purchase_orders(
    current_user: User = Depends(tech_dep),
    po_repo: PurchaseOrderRepository = Depends(get_po_repo),
):
    handler = GetRecentPurchaseOrdersQueryHandler(po_repo=po_repo)
    pos = handler.handle(
        GetRecentPurchaseOrdersQuery(company_id=current_user.company_id)
    )

    return {
        "data": [
            RecentPOItem(
                id=po.id,
                po_number=po.po_number,
                vendor_name=po.vendor_name,
                status=po.status.value,
                total_amount_cents=po.total_amount_cents,
                created_at=po.created_at,
            ).model_dump(mode="json")
            for po in pos
        ]
    }


@router.get("/shipments/summary")
def shipment_summary(
    current_user: User = Depends(admin_dep),
    shipment_repo: ShipmentRepository = Depends(
        get_shipment_repo,
    ),
):
    handler = ShipmentDashboardQueryHandler(
        shipment_repo=shipment_repo,
    )
    result = handler.handle(
        ShipmentDashboardQuery(
            company_id=current_user.company_id,
        )
    )

    return {
        "data": {
            "active_by_status": result.active_by_status,
            "recent_deliveries": [
                {
                    "id": s.id,
                    "direction": s.direction.value,
                    "destination_type": s.destination_type.value,
                    "status": s.status.value,
                    "carrier": s.carrier,
                    "service_level": s.service_level,
                    "tracking_number": s.tracking_number,
                    "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
                    "item_count": len(s.items),
                }
                for s in result.recent_deliveries
            ],
            "failed_count": result.failed_count,
        }
    }


@router.get("/maintenance")
def maintenance_summary(
    current_user: User = Depends(admin_dep),
    record_repo: MaintenanceRecordRepository = Depends(
        get_maintenance_record_repo,
    ),
):
    handler = MaintenanceDashboardQueryHandler(
        record_repo=record_repo,
    )
    result = handler.handle(
        MaintenanceDashboardQuery(
            company_id=current_user.company_id,
        )
    )
    return {
        "data": {
            "scheduled": result.scheduled,
            "overdue": result.overdue,
            "in_progress": result.in_progress,
            "completed_30d": result.completed_30d,
        }
    }
