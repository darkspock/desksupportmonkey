from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


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


class CompanyDetailResponse(CompanyResponse):
    user_count: int
    department_count: int


class UpdateCompanyStatusRequest(BaseModel):
    status: str
