from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Request schemas ---


class CreateChangeRequestSchema(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    change_type: str = "standard"
    planned_date: Optional[datetime] = None
    rollback_plan: Optional[str] = None


class UpdateChangeRequestSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    change_type: Optional[str] = None
    business_justification: Optional[str] = None
    risk_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None
    planned_date: Optional[datetime] = None


class ApproveChangeRequestSchema(BaseModel):
    notes: Optional[str] = None


class RejectChangeRequestSchema(BaseModel):
    reason: str = Field(min_length=1)


class ImplementChangeSchema(BaseModel):
    notes: Optional[str] = None


class RollbackChangeSchema(BaseModel):
    reason: str = Field(min_length=1)


class AssignChangeSchema(BaseModel):
    assigned_to: str


class LinkAssetsRequest(BaseModel):
    asset_ids: list[str] = Field(min_length=1)


class CreatePIRRequest(BaseModel):
    outcome: str = Field(description="successful, partial, or failed")
    issues_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    follow_up_actions: Optional[str] = None


# --- Response schemas ---


class ChangeRequestListItemResponse(BaseModel):
    id: str
    title: str
    change_type: str
    status: str
    planned_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    requested_by: str
    requested_by_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ChangeEventResponse(BaseModel):
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class ChangeAssetResponse(BaseModel):
    id: str
    asset_id: str
    asset_name: Optional[str] = None
    asset_tag: Optional[str] = None
    asset_brand: Optional[str] = None
    asset_model: Optional[str] = None
    created_at: Optional[datetime] = None


class PIRResponse(BaseModel):
    id: str
    outcome: str
    issues_found: Optional[str] = None
    lessons_learned: Optional[str] = None
    follow_up_actions: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class ChangeRequestDetailResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: Optional[str] = None
    change_type: str
    status: str
    business_justification: Optional[str] = None
    risk_assessment: Optional[str] = None
    rollback_plan: Optional[str] = None
    planned_date: Optional[datetime] = None
    requested_by: str
    requested_by_name: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    approved_by: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejected_by: Optional[str] = None
    rejected_by_name: Optional[str] = None
    rejected_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    implementation_notes: Optional[str] = None
    rolled_back_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    timeline: list[ChangeEventResponse] = []
    affected_assets: list[ChangeAssetResponse] = []
    pir: Optional[PIRResponse] = None


# --- Dashboard schemas ---


class UpcomingChangeResponse(BaseModel):
    id: str
    title: str
    change_type: str
    planned_date: Optional[datetime] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None


class RecentImplementedResponse(BaseModel):
    id: str
    title: str
    change_type: str
    implemented_at: Optional[datetime] = None
    pir_outcome: Optional[str] = None


class ChangeDashboardResponse(BaseModel):
    total_open: int
    pending_approval: int
    in_progress: int
    implemented: int
    scheduled_this_week: int
    status_counts: dict[str, int]
    type_counts: dict[str, int]
    upcoming_scheduled: list[UpcomingChangeResponse] = []
    recently_implemented: list[RecentImplementedResponse] = []
    rolled_back_90_days: int = 0
