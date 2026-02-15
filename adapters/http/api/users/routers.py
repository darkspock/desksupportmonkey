import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.users.schemas import (
    AssignDepartmentRequest,
    ChangeRoleRequest,
    UserDetailResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from core.database import get_db
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.application.commands.change_user_role import (
    CannotAssignSuperAdminError,
    CannotChangeSelfError,
    ChangeUserRoleCommand,
    ChangeUserRoleCommandHandler,
    UserNotFoundError as RoleUserNotFoundError,
)
from src.auth_bc.user.application.commands.deactivate_user import (
    CannotDeactivateSelfError,
    DeactivateUserCommand,
    DeactivateUserCommandHandler,
    UserNotFoundError as DeactivateUserNotFoundError,
)
from src.auth_bc.user.application.commands.activate_user import (
    ActivateUserCommand,
    ActivateUserCommandHandler,
    UserNotFoundError as ActivateUserNotFoundError,
)
from src.auth_bc.user.application.commands.assign_department import (
    AssignDepartmentCommand,
    AssignDepartmentCommandHandler,
    DepartmentInactiveError,
    DepartmentNotFoundError,
    UserNotFoundError as AssignUserNotFoundError,
)
from src.auth_bc.user.application.queries.list_users import (
    ListUsersQuery,
    ListUsersQueryHandler,
)
from src.auth_bc.user.application.queries.get_user_detail import (
    GetUserDetailQuery,
    GetUserDetailQueryHandler,
    UserNotFoundError as GetUserNotFoundError,
)
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.department.infrastructure.repository import DepartmentRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _to_response(user: User) -> UserDetailResponse:
    return UserDetailResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        company_id=user.company_id,
        department_id=user.department_id,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    department_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = ListUsersQueryHandler(user_repo=UserRepository(db))
    users, total = handler.handle(
        ListUsersQuery(
            company_id=company_id,
            page=page,
            page_size=page_size,
            role=role,
            is_active=is_active,
            department_id=department_id,
            search=search,
        )
    )
    return {
        "data": [_to_response(u).model_dump(mode="json") for u in users],
        "meta": PaginationMeta(page=page, page_size=page_size, total=total).model_dump(),
    }


@router.get("/{user_id}")
def get_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = GetUserDetailQueryHandler(user_repo=UserRepository(db))
    try:
        user = handler.handle(GetUserDetailQuery(user_id=user_id, company_id=company_id))
    except GetUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"data": _to_response(user).model_dump(mode="json")}


@router.patch("/{user_id}/role")
def change_role(
    user_id: str,
    body: ChangeRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = ChangeUserRoleCommandHandler(user_repo=UserRepository(db))
    try:
        user = handler.handle(
            ChangeUserRoleCommand(
                user_id=user_id,
                company_id=company_id,
                current_user_id=current_user.id,
                new_role=body.role,
            )
        )
    except RoleUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except CannotChangeSelfError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot change your own role"
        )
    except CannotAssignSuperAdminError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign super_admin role"
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role value",
        )
    return {"data": _to_response(user).model_dump(mode="json")}


@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = DeactivateUserCommandHandler(user_repo=UserRepository(db))
    try:
        user = handler.handle(
            DeactivateUserCommand(
                user_id=user_id,
                company_id=company_id,
                current_user_id=current_user.id,
            )
        )
    except DeactivateUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except CannotDeactivateSelfError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Cannot deactivate your own account"
        )
    return {"data": _to_response(user).model_dump(mode="json")}


@router.patch("/{user_id}/activate")
def activate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = ActivateUserCommandHandler(user_repo=UserRepository(db))
    try:
        user = handler.handle(
            ActivateUserCommand(user_id=user_id, company_id=company_id)
        )
    except ActivateUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"data": _to_response(user).model_dump(mode="json")}


@router.patch("/{user_id}/department")
def assign_department(
    user_id: str,
    body: AssignDepartmentRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    company_id = current_user.company_id
    handler = AssignDepartmentCommandHandler(
        user_repo=UserRepository(db),
        department_repo=DepartmentRepository(db),
    )
    try:
        user = handler.handle(
            AssignDepartmentCommand(
                user_id=user_id,
                company_id=company_id,
                department_id=body.department_id,
            )
        )
    except AssignUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except DepartmentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found"
        )
    except DepartmentInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot assign user to inactive department",
        )
    return {"data": _to_response(user).model_dump(mode="json")}
