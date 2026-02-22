from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from src.company_bc.employee_role.infrastructure.repository import EmployeeRoleRepository


def get_employee_role_repo(db: Session = Depends(get_db)) -> EmployeeRoleRepository:
    return EmployeeRoleRepository(db)
