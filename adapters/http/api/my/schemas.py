from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class MyEquipmentResponse(BaseModel):
    id: str
    type: str
    brand: str
    model: str
    serial_number: str
    created_at: Optional[datetime] = None


class MyRequestResponse(BaseModel):
    id: str
    type: str
    subtype: Optional[str] = None
    title: str
    status: str
    priority: str
    assigned_to: Optional[str] = None
    assigned_to_email: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class NotificationResponse(BaseModel):
    id: str
    event_type: str
    title: str
    body: str
    data: Optional[dict[str, Any]] = None
    is_read: bool
    created_at: Optional[datetime] = None


class NotificationListMeta(BaseModel):
    page: int
    page_size: int
    total: int
    unread_count: int


class MyCompanySettingsResponse(BaseModel):
    id: str
    name: str
    email_domains: list[str]


class UpdateMyCompanySettingsRequest(BaseModel):
    email_domains: list[str] = Field(min_length=1)


class UpdateMyProfileRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class MyProfileResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class ReportIncidentRequest(BaseModel):
    """Simplified form for employees."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    incident_type: str


class MyIncidentResponse(BaseModel):
    id: str
    title: str
    incident_type: str
    severity: str
    status: str
    created_at: Optional[datetime] = None


class MyMaintenanceResponse(BaseModel):
    id: str
    asset_id: str
    status: str
    priority: str
    title: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
