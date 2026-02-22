from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)
from src.company_bc.equipment_profile.infrastructure.repository import (
    EquipmentProfileRepository,
)


def get_profile_repo(
    db: Session = Depends(get_db),
) -> EquipmentProfileRepository:
    return EquipmentProfileRepository(db)


def get_dept_repo(
    db: Session = Depends(get_db),
) -> DepartmentRepository:
    return DepartmentRepository(db)


def can_manage_department(
    user: User,
    department_id: str,
    dept_repo: DepartmentRepository,
) -> bool:
    """Check if user is admin or manager of the dept."""
    if user.role.has_access(UserRole.ADMIN):
        return True
    assert user.company_id is not None
    dept = dept_repo.find_by_id(
        department_id, user.company_id,
    )
    if dept and dept.manager_user_id == user.id:
        return True
    return False


def require_department_access(
    user: User,
    department_id: str,
    dept_repo: DepartmentRepository,
) -> None:
    """Raise 403 if user cannot manage department."""
    if not can_manage_department(
        user, department_id, dept_repo,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this department",
        )
