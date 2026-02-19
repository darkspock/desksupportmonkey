from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProcurementConfigUpdateRequest(BaseModel):
    enforcement_mode: str = Field(
        pattern="^(warn|strict)$",
    )
    approval_threshold_cents: int = Field(ge=0)
    po_number_prefix: str = Field(
        min_length=1, max_length=10,
    )
    fiscal_year_start_month: int = Field(ge=1, le=12)
    currency: str = Field(
        min_length=3, max_length=3,
    )
    auto_create_assets: bool = False


class ProcurementConfigResponse(BaseModel):
    id: Optional[str] = None
    company_id: str
    enforcement_mode: str
    approval_threshold_cents: int
    po_number_prefix: str
    fiscal_year_start_month: int
    currency: str
    auto_create_assets: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
