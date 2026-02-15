from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import ulid

from src.auth_bc.user.domain.enums import UserRole


@dataclass
class User:
    id: str
    email: str
    role: UserRole
    company_id: Optional[str] = None
    name: Optional[str] = None
    department_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        email: str,
        role: UserRole,
        company_id: Optional[str] = None,
        name: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> "User":
        if not email or "@" not in email:
            raise ValueError("Invalid email format")
        return cls(
            id=str(ulid.new()),
            email=email.lower().strip(),
            role=role,
            company_id=company_id,
            name=name,
            department_id=department_id,
            is_active=True,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def change_role(self, new_role: UserRole) -> None:
        if not isinstance(new_role, UserRole):
            raise ValueError(f"Invalid role: {new_role}")
        self.role = new_role

    def assign_department(self, department_id: Optional[str]) -> None:
        self.department_id = department_id
