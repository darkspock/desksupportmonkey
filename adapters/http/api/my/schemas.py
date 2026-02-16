from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


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
