from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AppointmentCreateRequest(BaseModel):
    request_id: str
    technician_id: str
    employee_id: str
    scheduled_start: datetime
    duration_minutes: int = Field(ge=30, le=90)
    location: Optional[str] = None


class CancelAppointmentRequest(BaseModel):
    reason: str


class CompleteAppointmentRequest(BaseModel):
    notes: Optional[str] = None


class RescheduleAppointmentRequest(BaseModel):
    new_start: datetime
    new_duration_minutes: int = Field(ge=30, le=90)
    reason: str
    location: Optional[str] = None


class AppointmentResponse(BaseModel):
    id: str
    company_id: str
    request_id: str
    technician_id: str
    employee_id: str
    status: str
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int
    location: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = None
    rescheduled_from_id: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_by: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    technician_email: Optional[str] = None
    employee_email: Optional[str] = None
