import logging

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.employee_roles.dependencies import get_employee_role_repo
from adapters.http.api.employee_roles.schemas import (
    CreateEmployeeRoleRequest,
    EmployeeRoleResponse,
    UpdateEmployeeRoleRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.company_bc.employee_role.application.commands.create_employee_role import (
    CreateEmployeeRoleCommand,
    CreateEmployeeRoleCommandHandler,
    EmployeeRoleNameExistsError,
)
from src.company_bc.employee_role.application.commands.delete_employee_role import (
    DeleteEmployeeRoleCommand,
    DeleteEmployeeRoleCommandHandler,
    EmployeeRoleInUseError,
    EmployeeRoleNotFoundError as DeleteNotFoundError,
)
from src.company_bc.employee_role.application.commands.update_employee_role import (
    EmployeeRoleNameExistsError as UpdateNameExistsError,
    EmployeeRoleNotFoundError as UpdateNotFoundError,
    UpdateEmployeeRoleCommand,
    UpdateEmployeeRoleCommandHandler,
)
from src.company_bc.employee_role.application.queries.get_employee_role import (
    EmployeeRoleReadModel,
    EmployeeRoleNotFoundError as GetNotFoundError,
    GetEmployeeRoleQuery,
    GetEmployeeRoleQueryHandler,
)
from src.company_bc.employee_role.application.queries.list_employee_roles import (
    ListEmployeeRolesQuery,
    ListEmployeeRolesQueryHandler,
)
from src.company_bc.employee_role.infrastructure.repository import EmployeeRoleRepository

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/employee-roles", tags=["employee-roles"],
)


def _to_response(role: EmployeeRoleReadModel) -> EmployeeRoleResponse:
    return EmployeeRoleResponse(
        id=role.id,
        company_id=role.company_id,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_employee_role(
    body: CreateEmployeeRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    role_repo: EmployeeRoleRepository = Depends(get_employee_role_repo),
):
    assert current_user.company_id is not None
    role_id = str(ulid.new())
    handler = CreateEmployeeRoleCommandHandler(role_repo=role_repo)
    try:
        handler.handle(
            CreateEmployeeRoleCommand(
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
                id=role_id,
            )
        )
    except EmployeeRoleNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee role with this name already exists",
        )
    query_handler = GetEmployeeRoleQueryHandler(role_repo=role_repo)
    role = query_handler.handle(
        GetEmployeeRoleQuery(role_id=role_id, company_id=current_user.company_id)
    )
    return {"data": _to_response(role).model_dump(mode="json")}


@router.get("")
def list_employee_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    role_repo: EmployeeRoleRepository = Depends(get_employee_role_repo),
):
    assert current_user.company_id is not None
    handler = ListEmployeeRolesQueryHandler(role_repo=role_repo)
    roles, total = handler.handle(
        ListEmployeeRolesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )
    )
    return {
        "data": [_to_response(r).model_dump(mode="json") for r in roles],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{role_id}")
def get_employee_role(
    role_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    role_repo: EmployeeRoleRepository = Depends(get_employee_role_repo),
):
    assert current_user.company_id is not None
    handler = GetEmployeeRoleQueryHandler(role_repo=role_repo)
    try:
        role = handler.handle(
            GetEmployeeRoleQuery(role_id=role_id, company_id=current_user.company_id)
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee role not found",
        )
    return {"data": _to_response(role).model_dump(mode="json")}


@router.put("/{role_id}")
def update_employee_role(
    role_id: str,
    body: UpdateEmployeeRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    role_repo: EmployeeRoleRepository = Depends(get_employee_role_repo),
):
    assert current_user.company_id is not None
    handler = UpdateEmployeeRoleCommandHandler(role_repo=role_repo)
    try:
        handler.handle(
            UpdateEmployeeRoleCommand(
                role_id=role_id,
                company_id=current_user.company_id,
                name=body.name,
                description=body.description,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee role not found",
        )
    except UpdateNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee role with this name already exists",
        )
    query_handler = GetEmployeeRoleQueryHandler(role_repo=role_repo)
    role = query_handler.handle(
        GetEmployeeRoleQuery(role_id=role_id, company_id=current_user.company_id)
    )
    return {"data": _to_response(role).model_dump(mode="json")}


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_role(
    role_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    role_repo: EmployeeRoleRepository = Depends(get_employee_role_repo),
):
    assert current_user.company_id is not None
    handler = DeleteEmployeeRoleCommandHandler(role_repo=role_repo)
    try:
        handler.handle(
            DeleteEmployeeRoleCommand(
                role_id=role_id,
                company_id=current_user.company_id,
            )
        )
    except DeleteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee role not found",
        )
    except EmployeeRoleInUseError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
