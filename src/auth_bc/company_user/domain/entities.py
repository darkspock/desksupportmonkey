from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import ulid

from src.auth_bc.user.domain.enums import UserRole


@dataclass
class CompanyUser:
    """Membership registry record — one per (user, company)."""

    id: str
    user_id: str
    company_id: str
    role: UserRole
    department_id: Optional[str] = None
    employee_role_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        user_id: str,
        company_id: str,
        role: UserRole = UserRole.EMPLOYEE,
        department_id: Optional[str] = None,
        employee_role_id: Optional[str] = None,
    ) -> "CompanyUser":
        return cls(
            id=str(ulid.new()),
            user_id=user_id,
            company_id=company_id,
            role=role,
            department_id=department_id,
            employee_role_id=employee_role_id,
            is_active=True,
        )

    def change_role(self, new_role: UserRole) -> None:
        self.role = new_role

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True

    def assign_department(self, department_id: Optional[str]) -> None:
        self.department_id = department_id

    def assign_employee_role(self, employee_role_id: Optional[str]) -> None:
        self.employee_role_id = employee_role_id


class MembershipNotFoundError(Exception):
    pass


class MembershipDeactivatedError(Exception):
    pass


class MembershipNotAllowedError(Exception):
    pass


class MultipleCompaniesError(Exception):
    """Email matches multiple companies — must use slug-scoped login."""

    def __init__(self, slugs: list[str]):
        self.slugs = slugs
        super().__init__(
            f"Multiple companies found. Use company login: {', '.join(slugs)}"
        )
