from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BillingOverviewResponse(BaseModel):
    plan: str
    billing_status: str
    complimentary: bool
    user_count: int
    user_limit: Optional[int]
    asset_count: int
    asset_limit: Optional[int]
    grace_days_remaining: Optional[int]
    current_period_end: Optional[datetime]
    pending_downgrade_plan: Optional[str]


class CheckoutRequest(BaseModel):
    target_plan: str


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str
