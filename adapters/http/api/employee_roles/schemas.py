from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateEmployeeRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class UpdateEmployeeRoleRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=500)


class EmployeeRoleResponse(BaseModel):
    id: str
    company_id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
