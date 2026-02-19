from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChecklistItemRequest(BaseModel):
    title: str
    description: Optional[str] = None
    is_required: bool = True


class CreateMaintenanceTemplateRequest(BaseModel):
    name: str
    default_priority: str = "MEDIUM"
    description: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: int = Field(default=1, ge=1)
    asset_type_filter: Optional[str] = None
    checklist_items: list[ChecklistItemRequest] = Field(
        default_factory=list,
    )


class UpdateMaintenanceTemplateRequest(BaseModel):
    name: Optional[str] = None
    default_priority: Optional[str] = None
    description: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: Optional[int] = Field(default=None, ge=1)
    asset_type_filter: Optional[str] = None
    checklist_items: Optional[list[ChecklistItemRequest]] = None


class ApplyTemplateRequest(BaseModel):
    asset_ids: Optional[list[str]] = None
    first_due_at: Optional[datetime] = None


class ChecklistItemResponse(BaseModel):
    title: str
    description: Optional[str] = None
    is_required: bool


class MaintenanceTemplateResponse(BaseModel):
    id: str
    company_id: str
    name: str
    default_priority: str
    description: Optional[str] = None
    recurrence_frequency: Optional[str] = None
    recurrence_interval: int
    asset_type_filter: Optional[str] = None
    checklist_items: list[ChecklistItemResponse]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MaintenancePlanResponse(BaseModel):
    id: str
    company_id: str
    template_id: str
    asset_id: str
    is_active: bool
    next_due_at: datetime
    last_generated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
