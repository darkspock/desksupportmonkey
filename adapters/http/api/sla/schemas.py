from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateSlaPolicyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    priority: str = Field(pattern=r"^(urgent|high|medium|low)$")
    request_type: Optional[str] = None
    response_time_hours: float = Field(gt=0)
    resolution_time_hours: float = Field(gt=0)
    warning_threshold_pct: int = Field(default=75, ge=1, le=99)
    escalate_on_breach: bool = False


class UpdateSlaPolicyRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    response_time_hours: Optional[float] = Field(default=None, gt=0)
    resolution_time_hours: Optional[float] = Field(default=None, gt=0)
    warning_threshold_pct: Optional[int] = Field(default=None, ge=1, le=99)
    escalate_on_breach: Optional[bool] = None


class ComplianceByGroupResponse(BaseModel):
    group: str
    total: int
    met: int
    breached: int
    compliance_pct: float


class BreachTrendPointResponse(BaseModel):
    period: str
    count: int


class SlaDashboardResponse(BaseModel):
    total_resolved: int
    met: int
    breached: int
    compliance_pct: float
    by_priority: list[ComplianceByGroupResponse]
    by_type: list[ComplianceByGroupResponse]
    breach_trend: list[BreachTrendPointResponse]


class SlaPolicyResponse(BaseModel):
    id: str
    company_id: str
    name: str
    priority: str
    request_type: Optional[str]
    response_time_hours: float
    resolution_time_hours: float
    warning_threshold_pct: int
    escalate_on_breach: bool
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
