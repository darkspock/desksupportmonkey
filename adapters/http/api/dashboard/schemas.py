from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# --- Request Summary ---

class RequestStatusCounts(BaseModel):
    submitted: int = 0
    in_review: int = 0
    in_progress: int = 0
    resolved: int = 0
    rejected: int = 0


class RequestTypeCounts(BaseModel):
    incident: int = 0
    new_equipment: int = 0
    onboarding: int = 0


class RequestPriorityCounts(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    urgent: int = 0


class RequestSummaryResponse(BaseModel):
    by_status: RequestStatusCounts
    by_type: RequestTypeCounts
    by_priority: RequestPriorityCounts
    total_open: int
    total_resolved: int


# --- Resolution Time ---

class TechnicianResolutionTime(BaseModel):
    technician_id: str
    avg_hours: float
    resolved_count: int


class ResolutionTimeResponse(BaseModel):
    avg_hours: Optional[float] = None
    by_technician: list[TechnicianResolutionTime]


# --- Request Trend ---

class TrendBucketTypeCounts(BaseModel):
    incident: int = 0
    new_equipment: int = 0
    onboarding: int = 0


class TrendBucket(BaseModel):
    period: str
    total: int
    by_type: TrendBucketTypeCounts


class RequestTrendResponse(BaseModel):
    bucket: str
    from_date: str
    to_date: str
    data: list[TrendBucket]


# --- Asset Summary ---

class AssetStatusCounts(BaseModel):
    in_stock: int = 0
    assigned: int = 0
    in_repair: int = 0
    decommissioned: int = 0


class AssetTypeCounts(BaseModel):
    laptop: int = 0
    monitor: int = 0
    keyboard: int = 0
    mouse: int = 0
    headset: int = 0
    docking_station: int = 0
    other: int = 0


class AssetSummaryResponse(BaseModel):
    by_status: AssetStatusCounts
    by_type: AssetTypeCounts
    total: int


# --- Warranty Alerts ---

class WarrantyAlertItem(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    warranty_expiration: date
    assigned_to: Optional[str] = None
    days_remaining: int


# --- Aging Alerts ---

class AgingAlertItem(BaseModel):
    id: str
    brand: str
    model: str
    serial_number: str
    purchase_date: date
    age_years: float
    assigned_to: Optional[str] = None


# --- SLA Alerts ---

class SlaAlertItem(BaseModel):
    id: str
    title: str
    type: str
    priority: str
    status: str
    assigned_to: Optional[str] = None
    created_at: datetime
    hours_open: float
    sla_threshold_hours: int
    breached: bool


# --- Budget Health ---

class AtRiskDepartmentItem(BaseModel):
    department_id: str
    department_name: str
    utilization_pct: float
    remaining_cents: int


class BudgetHealthResponse(BaseModel):
    total_allocated_cents: int
    total_spent_cents: int
    departments_at_risk: list[AtRiskDepartmentItem]


# --- Recent Purchase Orders ---

class RecentPOItem(BaseModel):
    id: str
    po_number: str
    vendor_name: str
    status: str
    total_amount_cents: int
    created_at: Optional[datetime] = None
