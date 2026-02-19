from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel, Field


class AvailabilityWindowSchema(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time


class SetAvailabilityRequest(BaseModel):
    windows: List[AvailabilityWindowSchema]


class AvailabilityWindowResponse(BaseModel):
    id: str
    day_of_week: int
    start_time: time
    end_time: time


class OverrideCreateRequest(BaseModel):
    date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None


class OverrideResponse(BaseModel):
    id: str
    date: date
    is_available: bool
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SlotResponse(BaseModel):
    start: time
    end: time


class SlotsQueryResponse(BaseModel):
    date: date
    technician_id: str
    duration_minutes: int
    slots: List[SlotResponse]
