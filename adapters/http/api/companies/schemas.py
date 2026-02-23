from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from src.company_bc.company.domain.billing_enums import BillingStatus, PlanTier


class CreateCompanyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email_domains: list[str] = Field(min_length=1)
    admin_email: Optional[EmailStr] = None


class UpdateCompanyRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email_domains: Optional[list[str]] = Field(None, min_length=1)


class CompanyResponse(BaseModel):
    id: str
    name: str
    status: str
    email_domains: list[str]
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    plan: Optional[str] = None
    billing_status: Optional[str] = None
    user_count: Optional[int] = None
    asset_count: Optional[int] = None
    trial_days_remaining: Optional[int] = None


class CompanyDetailResponse(CompanyResponse):
    user_count: int
    department_count: int


class UpdateCompanyStatusRequest(BaseModel):
    status: str


class CompanyBillingResponse(BaseModel):
    company_id: str
    company_name: str
    plan: str
    billing_status: str
    complimentary: bool
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    current_period_end: Optional[datetime] = None
    pending_downgrade_plan: Optional[str] = None
    grace_period_started_at: Optional[datetime] = None
    trial_days_remaining: Optional[int] = None
    trial_ends_at: Optional[datetime] = None


class InvoiceResponse(BaseModel):
    invoice_id: str
    date: datetime
    period_start: datetime
    period_end: datetime
    amount_cents: int
    currency: str
    status: str
    invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None


class OverridePlanRequest(BaseModel):
    new_plan: str = Field(description="Plan tier: free, premium, enterprise, or open_source")


class GrantComplimentaryRequest(BaseModel):
    plan: str = Field(description="Plan tier: free, premium, enterprise, or open_source")
