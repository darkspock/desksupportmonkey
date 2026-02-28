from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class CreateContractRequest(BaseModel):
    contract_type: str = Field(
        pattern="^(service|supply|licensing|saas)$",
    )
    title: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: bool = False
    annual_value: Optional[Decimal] = Field(
        default=None, ge=0, decimal_places=2,
    )
    currency: Optional[str] = Field(
        default=None, max_length=3,
    )
    security_clauses: Optional[dict] = None
    notes: Optional[str] = None


class UpdateContractRequest(BaseModel):
    title: Optional[str] = Field(
        default=None, min_length=1, max_length=200,
    )
    contract_type: Optional[str] = Field(
        default=None,
        pattern="^(service|supply|licensing|saas)$",
    )
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: Optional[bool] = None
    annual_value: Optional[Decimal] = Field(
        default=None, ge=0, decimal_places=2,
    )
    currency: Optional[str] = Field(
        default=None, max_length=3,
    )
    security_clauses: Optional[dict] = None
    notes: Optional[str] = None


class ChangeContractStatusRequest(BaseModel):
    status: str = Field(
        pattern="^(draft|active|expired|terminated)$",
    )


class ContractResponse(BaseModel):
    id: str
    vendor_id: str
    company_id: str
    contract_type: str
    title: str
    start_date: date
    end_date: Optional[date] = None
    renewal_date: Optional[date] = None
    auto_renewal: bool
    annual_value: Optional[Decimal] = None
    currency: Optional[str] = None
    security_clauses: dict = {}
    notes: Optional[str] = None
    status: str
    document_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
