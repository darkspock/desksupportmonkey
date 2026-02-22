from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ChangeRoleRequest(BaseModel):
    role: str


class AssignDepartmentRequest(BaseModel):
    department_id: Optional[str] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    department_id: Optional[str] = None
    employee_role_id: Optional[str] = None


class InviteUserRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: Optional[str] = None


class QuickCreateEmployeeRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None


class QuickCreateEmployeeResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None


class UserDetailResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    role: str
    company_id: Optional[str] = None
    department_id: Optional[str] = None
    employee_role_id: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# --- Import schemas ---


class ImportRowErrorResponse(BaseModel):
    row: int
    error: str


class ImportDepartmentResponse(BaseModel):
    id: str
    name: str


class ImportPreviewResponse(BaseModel):
    total_rows: int
    valid_rows: int
    errors: list[ImportRowErrorResponse]
    unknown_departments: list[str]
    existing_departments: list[ImportDepartmentResponse]


class ImportConfirmResponse(BaseModel):
    total: int
    successful: int
    failed: list[ImportRowErrorResponse]
    departments_created: list[str]
    invitations_sent: int
