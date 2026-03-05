from typing import Optional

from pydantic import BaseModel, Field


# Auth
class OAuthLoginRequest(BaseModel):
    id_token: str


class OAuthRegisterRequest(BaseModel):
    id_token: str
    company_name: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str


class ResellerRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")
    company_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class PasswordLoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class RejectResellerRequest(BaseModel):
    reason: Optional[str] = None


# Reseller profile
class ResellerResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    company_name: Optional[str]
    tax_id: Optional[str]
    commission_pct: int
    min_payout_cents: int
    referral_code: str
    status: str
    created_at: str
    updated_at: Optional[str]


class UpdateResellerProfileRequest(BaseModel):
    company_name: Optional[str] = None
    tax_id: Optional[str] = None


# Dashboard
class ResellerDashboardResponse(BaseModel):
    reseller_id: str
    name: str
    referral_code: str
    status: str
    client_count: int
    total_commissions_cents: int
    available_balance_cents: int
    pending_payout_cents: int


# Admin
class CreateResellerRequest(BaseModel):
    email: str
    name: str
    commission_pct: int
    min_payout_cents: int


class UpdateResellerSettingsRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None
    tax_id: Optional[str] = None
    referral_code: Optional[str] = None
    commission_pct: Optional[int] = None
    min_payout_cents: Optional[int] = None
    status: Optional[str] = None


class ResellerListResponse(BaseModel):
    items: list[ResellerResponse]
    total: int


# Client schemas
class CreateDemoAccountRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    admin_email: Optional[str] = Field(default=None, pattern=r"^[^@]+@[^@]+\.[^@]+$")


class CreateClientAccountRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=200)
    admin_email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")


class DemoAccountCreatedResponse(BaseModel):
    client_id: str
    company_id: str
    company_name: str
    admin_email: str
    admin_password: str


class ResellerClientResponse(BaseModel):
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    source: str
    is_demo: bool
    demo_expires_at: Optional[str]
    plan: str
    company_status: str
    created_at: Optional[str]


class ResellerClientListResponse(BaseModel):
    items: list[ResellerClientResponse]
    total: int


# Commission schemas
class CommissionResponse(BaseModel):
    id: str
    reseller_id: str
    company_id: str
    company_name: str
    payment_amount_cents: int
    commission_pct: int
    commission_amount_cents: int
    period_start: Optional[str]
    period_end: Optional[str]
    status: str
    created_at: Optional[str]


class CommissionListResponse(BaseModel):
    items: list[CommissionResponse]
    total: int


# Payout schemas
class PayoutResponse(BaseModel):
    id: str
    reseller_id: str
    reseller_name: str
    amount_cents: int
    status: str
    requested_at: Optional[str]
    processed_at: Optional[str]
    processed_by: Optional[str]
    payment_reference: Optional[str]
    notes: Optional[str]


class PayoutListResponse(BaseModel):
    items: list[PayoutResponse]
    total: int


class ProcessPayoutRequest(BaseModel):
    action: str = Field(pattern=r"^(approve|reject|mark_paid)$")
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


# Invitation schemas
class CreateInvitationRequest(BaseModel):
    email: str = Field(pattern=r"^[^@]+@[^@]+\.[^@]+$")


class InvitationResponse(BaseModel):
    id: str
    reseller_id: str
    email: str
    status: str
    expires_at: str
    created_at: Optional[str]


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    total: int
