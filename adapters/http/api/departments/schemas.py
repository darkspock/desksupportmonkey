from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UpdateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class DepartmentResponse(BaseModel):
    id: str
    company_id: str
    name: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DepartmentDetailResponse(DepartmentResponse):
    user_count: int
