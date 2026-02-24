from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Request schemas ---


class CreateIncidentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    incident_type: str
    severity: str
    detected_at: datetime
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    custom_fields_data: Optional[dict[str, Any]] = None


class UpdateIncidentRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    custom_fields_data: Optional[dict[str, Any]] = None


class ChangeIncidentStatusRequest(BaseModel):
    status: str
    close_reason: Optional[str] = None


class ChangeIncidentSeverityRequest(BaseModel):
    severity: str


class AssignIncidentRequest(BaseModel):
    user_id: str = Field(min_length=1)


# --- Response schemas ---


class TimelineEntryResponse(BaseModel):
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    report_type: str
    status: str
    deadline_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    elapsed_percentage: Optional[float] = None


class IncidentListItemResponse(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    custom_fields: Optional[list[dict[str, Any]]] = None
    detected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class IncidentAssetResponse(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: Optional[str] = None
    impact_description: Optional[str] = None


class IncidentVendorResponse(BaseModel):
    vendor_id: str
    vendor_name: str
    involvement_description: Optional[str] = None


class LinkAssetRequest(BaseModel):
    asset_id: str = Field(min_length=1)
    impact_description: Optional[str] = None


class LinkVendorRequest(BaseModel):
    vendor_id: str = Field(min_length=1)
    involvement_description: Optional[str] = None


class CreatePostMortemRequest(BaseModel):
    root_cause: str = Field(min_length=1)
    lessons_learned: str = Field(min_length=1)
    corrective_actions: str = Field(min_length=1)


class UpdatePostMortemRequest(BaseModel):
    root_cause: Optional[str] = Field(None, min_length=1)
    lessons_learned: Optional[str] = Field(None, min_length=1)
    corrective_actions: Optional[str] = Field(None, min_length=1)


class PostMortemResponse(BaseModel):
    id: str
    root_cause: str
    lessons_learned: str
    corrective_actions: str
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UpcomingDeadlineResponse(BaseModel):
    incident_id: str
    incident_title: str
    report_type: str
    deadline_at: str
    time_remaining_seconds: int


class RecentIncidentResponse(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    detected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class DashboardResponse(BaseModel):
    total_active: int
    total_closed: int
    active_by_severity: dict[str, int]
    by_type: dict[str, int]
    mttc_hours: Optional[float] = None
    mttr_hours: Optional[float] = None
    upcoming_deadlines: list[UpcomingDeadlineResponse] = []
    recent_incidents: list[RecentIncidentResponse] = []


class IncidentDetailResponse(BaseModel):
    id: str
    title: str
    description: str
    incident_type: str
    severity: str
    status: str
    attack_vector: Optional[str] = None
    data_breach_scope: Optional[str] = None
    reported_by: str
    reported_by_name: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    detected_at: Optional[datetime] = None
    close_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    custom_fields: Optional[list[dict[str, Any]]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    timeline: list[TimelineEntryResponse] = []
    reports: list[ReportResponse] = []
    assets: list[IncidentAssetResponse] = []
    vendors: list[IncidentVendorResponse] = []
    postmortem: Optional[PostMortemResponse] = None
