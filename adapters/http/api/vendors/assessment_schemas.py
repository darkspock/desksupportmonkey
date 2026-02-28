from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateAssessmentRequest(BaseModel):
    assessment_date: date
    next_review_date: Optional[date] = None
    data_handling_score: int = Field(ge=1, le=5)
    security_certs_score: int = Field(ge=1, le=5)
    incident_response_score: int = Field(ge=1, le=5)
    business_continuity_score: int = Field(ge=1, le=5)
    subcontractor_score: int = Field(ge=1, le=5)
    justification: Optional[str] = None


class AssessmentResponse(BaseModel):
    id: str
    vendor_id: str
    company_id: str
    assessed_by: str
    assessment_date: date
    next_review_date: Optional[date] = None
    data_handling_score: int
    security_certs_score: int
    incident_response_score: int
    business_continuity_score: int
    subcontractor_score: int
    overall_risk_level: str
    justification: Optional[str] = None
    created_at: Optional[str] = None
