from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ChangeRoleRequest(BaseModel):
    role: str


class AssignDepartmentRequest(BaseModel):
    department_id: Optional[str] = None


class InviteUserRequest(BaseModel):
    email: EmailStr


class UserDetailResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str
    company_id: Optional[str] = None
    department_id: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
