from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- Requests ---


class CreateRiskRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    category: str
    owner_id: Optional[str] = None


class UpdateRiskRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = None
    owner_id: Optional[str] = None
    review_cadence: Optional[str] = None


class AssessRiskRequest(BaseModel):
    likelihood: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)


class SetTreatmentRequest(BaseModel):
    treatment: str


class ChangeStatusRequest(BaseModel):
    status: str


class AddMitigationRequest(BaseModel):
    description: str = Field(min_length=1)
    owner_id: Optional[str] = None
    target_date: Optional[date] = None


class UpdateMitigationRequest(BaseModel):
    description: Optional[str] = Field(None, min_length=1)
    status: Optional[str] = None
    owner_id: Optional[str] = None
    target_date: Optional[date] = None


class AddLinkRequest(BaseModel):
    link_type: str
    link_id: str


# --- Responses ---


class RiskListItemResponse(BaseModel):
    id: str
    title: str
    category: str
    status: str
    risk_level: Optional[str] = None
    likelihood: Optional[int] = None
    impact: Optional[int] = None
    treatment: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MitigationResponse(BaseModel):
    id: str
    description: str
    status: str
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    target_date: Optional[date] = None
    created_at: Optional[datetime] = None


class RiskLinkResponse(BaseModel):
    id: str
    link_type: str
    link_id: str
    link_name: Optional[str] = None


class RiskHistoryResponse(BaseModel):
    id: str
    event_type: str
    description: str
    actor_id: str
    actor_name: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class RiskDashboardResponse(BaseModel):
    total_risks: int
    open_risks: int
    mitigated_risks: int
    accepted_risks: int
    by_level: dict[str, int]
    by_category: dict[str, int]
    heat_map: list[dict]
    overdue_reviews: int
    recent_risks: list[dict]


class RiskDetailResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: str
    likelihood: Optional[int] = None
    impact: Optional[int] = None
    risk_level: Optional[str] = None
    treatment: Optional[str] = None
    review_cadence: Optional[str] = None
    next_review_at: Optional[datetime] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    created_by: str
    created_by_name: Optional[str] = None
    mitigations: list[MitigationResponse] = []
    links: list[RiskLinkResponse] = []
    history: list[RiskHistoryResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
