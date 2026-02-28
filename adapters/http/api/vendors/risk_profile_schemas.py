from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class LatestAssessmentResponse(BaseModel):
    id: str
    assessment_date: date
    next_review_date: Optional[date] = None
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    overall_risk_level: str
    justification: Optional[str] = None


class VendorIncidentSummaryResponse(BaseModel):
    id: str
    title: str
    severity: str
    status: str
    created_at: Optional[datetime] = None


class VendorRiskSummaryResponse(BaseModel):
    id: str
    title: str
    risk_level: Optional[str] = None
    status: str


class VendorRiskProfileResponse(BaseModel):
    id: str
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    category: Optional[str] = None
    is_critical_ict: bool
    risk_level: Optional[str] = None
    is_active: bool
    latest_assessment: Optional[LatestAssessmentResponse] = None
    active_contracts_count: int
    total_contracts_count: int
    dependency_count: int
    critical_dependency_count: int
    incident_count: int
    risk_count: int
    incidents: list[VendorIncidentSummaryResponse]
    risks: list[VendorRiskSummaryResponse]
