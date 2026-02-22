from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import CompanyRepository
from src.company_bc.department.infrastructure.repository import DepartmentRepository
from src.company_bc.employee_role.infrastructure.repository import EmployeeRoleRepository


def get_user_repo(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_company_repo(db: Session = Depends(get_db)) -> CompanyRepository:
    return CompanyRepository(db)


def get_magic_link_repo(db: Session = Depends(get_db)) -> MagicLinkRepository:
    return MagicLinkRepository(db)


def get_department_repo(db: Session = Depends(get_db)) -> DepartmentRepository:
    return DepartmentRepository(db)


def get_employee_role_repo(db: Session = Depends(get_db)) -> EmployeeRoleRepository:
    return EmployeeRoleRepository(db)
