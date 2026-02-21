from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateMaintenanceRecordRequest(BaseModel):
    asset_id: str
    title: str
    priority: str = "MEDIUM"
    description: Optional[str] = None
    technician_id: Optional[str] = None
    template_id: Optional[str] = None
    plan_id: Optional[str] = None
    checklist_items: list[str] = Field(default_factory=list)
    scheduled_at: Optional[datetime] = None


class UpdateMaintenanceRecordRequest(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    checklist_items: Optional[list[str]] = None
    scheduled_at: Optional[datetime] = None


class AssignMaintenanceRequest(BaseModel):
    technician_id: str


class CompleteMaintenanceRequest(BaseModel):
    completion_notes: Optional[str] = None
    actual_findings: Optional[str] = None


class CancelMaintenanceRequest(BaseModel):
    reason: str


class SkipMaintenanceRequest(BaseModel):
    reason: str


class MaintenanceRecordResponse(BaseModel):
    id: str
    company_id: str
    asset_id: str
    status: str
    priority: str
    title: str
    description: Optional[str] = None
    technician_id: Optional[str] = None
    template_id: Optional[str] = None
    plan_id: Optional[str] = None
    checklist_items: list[str]
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None
    actual_findings: Optional[str] = None
    cancellation_reason: Optional[str] = None
    skip_reason: Optional[str] = None
    reminder_48h_sent: bool
    overdue_alert_sent: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
