import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.departments.schemas import (
    CreateDepartmentRequest,
    DepartmentDetailResponse,
    DepartmentResponse,
    UpdateDepartmentRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.department.application.commands.create_department import (
    CreateDepartmentCommand,
    CreateDepartmentCommandHandler,
    DepartmentNameExistsError,
)
from src.company_bc.department.application.commands.update_department import (
    DepartmentNotFoundError as UpdateDeptNotFoundError,
    DepartmentNameExistsError as UpdateNameExistsError,
    UpdateDepartmentCommand,
    UpdateDepartmentCommandHandler,
)
from src.company_bc.department.application.commands.delete_department import (
    DeleteDepartmentCommand,
    DeleteDepartmentCommandHandler,
    DepartmentHasUsersError,
    DepartmentNotFoundError as DeleteDeptNotFoundError,
)
from src.company_bc.department.application.queries.list_departments import (
    ListDepartmentsQuery,
    ListDepartmentsQueryHandler,
)
from src.company_bc.department.application.queries.get_department import (
    DepartmentNotFoundError as GetDeptNotFoundError,
    GetDepartmentQuery,
    GetDepartmentQueryHandler,
)
from src.company_bc.department.domain.entities import Department
from src.company_bc.department.infrastructure.repository import DepartmentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])


def _to_response(dept: Department) -> DepartmentResponse:
    return DepartmentResponse(
        id=dept.id,
        company_id=dept.company_id,
        name=dept.name,
        is_active=dept.is_active,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_department(
    body: CreateDepartmentRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    handler = CreateDepartmentCommandHandler(department_repo=DepartmentRepository(db))
    try:
        department = handler.handle(
            CreateDepartmentCommand(company_id=current_user.company_id, name=body.name)
        )
    except DepartmentNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name already exists",
        )
    return {"data": _to_response(department).model_dump(mode="json")}


@router.get("")
def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    handler = ListDepartmentsQueryHandler(department_repo=DepartmentRepository(db))
    departments, total = handler.handle(
        ListDepartmentsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )
    )
    return {
        "data": [_to_response(d).model_dump(mode="json") for d in departments],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{department_id}")
def get_department(
    department_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    handler = GetDepartmentQueryHandler(department_repo=DepartmentRepository(db))
    try:
        detail = handler.handle(
            GetDepartmentQuery(department_id=department_id, company_id=current_user.company_id)
        )
    except GetDeptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return {
        "data": DepartmentDetailResponse(
            id=detail.department.id,
            company_id=detail.department.company_id,
            name=detail.department.name,
            is_active=detail.department.is_active,
            created_at=detail.department.created_at,
            updated_at=detail.department.updated_at,
            user_count=detail.user_count,
        ).model_dump(mode="json")
    }


@router.put("/{department_id}")
def update_department(
    department_id: str,
    body: UpdateDepartmentRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    handler = UpdateDepartmentCommandHandler(department_repo=DepartmentRepository(db))
    try:
        department = handler.handle(
            UpdateDepartmentCommand(
                department_id=department_id, company_id=current_user.company_id, name=body.name
            )
        )
    except UpdateDeptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    except UpdateNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name already exists",
        )
    return {"data": _to_response(department).model_dump(mode="json")}


@router.delete("/{department_id}")
def delete_department(
    department_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    handler = DeleteDepartmentCommandHandler(department_repo=DepartmentRepository(db))
    try:
        department = handler.handle(
            DeleteDepartmentCommand(department_id=department_id, company_id=current_user.company_id)
        )
    except DeleteDeptNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    except DepartmentHasUsersError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return {"data": _to_response(department).model_dump(mode="json")}
