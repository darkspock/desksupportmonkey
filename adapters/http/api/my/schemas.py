from datetime import datetime
from typing import Optional

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
