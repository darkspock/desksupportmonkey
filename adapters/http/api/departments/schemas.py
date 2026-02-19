from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class UpdateDepartmentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    priority_weight: Optional[int] = Field(None, ge=-1, le=2)


class AssignManagerRequest(BaseModel):
    user_id: str = Field(min_length=1)


class DepartmentResponse(BaseModel):
    id: str
    company_id: str
    name: str
    is_active: bool
    manager_user_id: Optional[str] = None
    manager_email: Optional[str] = None
    manager_name: Optional[str] = None
    priority_weight: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DepartmentDetailResponse(DepartmentResponse):
    user_count: int
