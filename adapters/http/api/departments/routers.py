import logging

import ulid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.departments.dependencies import (
    get_department_repo,
    get_po_repo,
    get_user_repo,
)
from adapters.http.api.departments.schemas import (
    AssignManagerRequest,
    CreateDepartmentRequest,
    DepartmentDetailResponse,
    DepartmentResponse,
    UpdateDepartmentRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.department.application.commands.assign_manager import (
    AssignDepartmentManagerCommand,
    AssignDepartmentManagerCommandHandler,
    CrossCompanyError,
    DepartmentNotFoundError as AssignDeptNotFoundError,
    UserInactiveError,
    UserNotFoundError as AssignUserNotFoundError,
)
from src.company_bc.department.application.commands.create_department import (
    CreateDepartmentCommand,
    CreateDepartmentCommandHandler,
    DepartmentNameExistsError,
)
from src.company_bc.department.application.commands.delete_department import (
    DeleteDepartmentCommand,
    DeleteDepartmentCommandHandler,
    DepartmentHasOpenPOsError,
    DepartmentHasUsersError,
    DepartmentNotFoundError as DeleteDeptNotFoundError,
)
from src.company_bc.department.application.commands.remove_manager import (
    DepartmentNotFoundError as RemoveDeptNotFoundError,
    RemoveDepartmentManagerCommand,
    RemoveDepartmentManagerCommandHandler,
)
from src.company_bc.department.application.commands.update_department import (
    DepartmentNameExistsError as UpdateNameExistsError,
    DepartmentNotFoundError as UpdateDeptNotFoundError,
    UpdateDepartmentCommand,
    UpdateDepartmentCommandHandler,
)
from src.company_bc.department.application.queries.get_department import (
    DepartmentNotFoundError as GetDeptNotFoundError,
    GetDepartmentQuery,
    GetDepartmentQueryHandler,
)
from src.company_bc.department.application.queries.list_departments import (
    ListDepartmentsQuery,
    ListDepartmentsQueryHandler,
)
from src.company_bc.department.domain.entities import Department
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)
from src.procurement_bc.purchase_order.infrastructure.repository import (
    PurchaseOrderRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/departments", tags=["departments"],
)


def _to_response(
    dept: Department,
    dept_repo: DepartmentRepository,
) -> DepartmentResponse:
    manager_email = None
    manager_name = None
    if dept.manager_user_id:
        info = dept_repo.find_manager_info(
            dept.manager_user_id,
        )
        if info:
            manager_email, manager_name = info
    return DepartmentResponse(
        id=dept.id,
        company_id=dept.company_id,
        name=dept.name,
        is_active=dept.is_active,
        manager_user_id=dept.manager_user_id,
        manager_email=manager_email,
        manager_name=manager_name,
        priority_weight=dept.priority_weight,
        budget_enforcement_enabled=dept.budget_enforcement_enabled,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_department(
    body: CreateDepartmentRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
):
    department_id = str(ulid.new())
    handler = CreateDepartmentCommandHandler(
        department_repo=dept_repo,
    )
    try:
        handler.handle(
            CreateDepartmentCommand(
                company_id=current_user.company_id,
                name=body.name,
                id=department_id,
            )
        )
    except DepartmentNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name already exists",
        )
    query_handler = GetDepartmentQueryHandler(
        department_repo=dept_repo,
    )
    detail = query_handler.handle(
        GetDepartmentQuery(
            department_id=department_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(
            detail.department, dept_repo,
        ).model_dump(mode="json"),
    }


@router.get("")
def list_departments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
):
    handler = ListDepartmentsQueryHandler(
        department_repo=dept_repo,
    )
    departments, total = handler.handle(
        ListDepartmentsQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            include_inactive=include_inactive,
        )
    )
    return {
        "data": [
            _to_response(d, dept_repo).model_dump(
                mode="json",
            )
            for d in departments
        ],
        "meta": PaginationMeta(
            page=page, page_size=page_size, total=total,
        ).model_dump(),
    }


@router.get("/{department_id}")
def get_department(
    department_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
):
    handler = GetDepartmentQueryHandler(
        department_repo=dept_repo,
    )
    try:
        detail = handler.handle(
            GetDepartmentQuery(
                department_id=department_id,
                company_id=current_user.company_id,
            )
        )
    except GetDeptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    mgr_email = None
    mgr_name = None
    if detail.department.manager_user_id:
        info = dept_repo.find_manager_info(
            detail.department.manager_user_id,
        )
        if info:
            mgr_email, mgr_name = info
    return {
        "data": DepartmentDetailResponse(
            id=detail.department.id,
            company_id=detail.department.company_id,
            name=detail.department.name,
            is_active=detail.department.is_active,
            manager_user_id=(
                detail.department.manager_user_id
            ),
            manager_email=mgr_email,
            manager_name=mgr_name,
            priority_weight=detail.department.priority_weight,
            budget_enforcement_enabled=detail.department.budget_enforcement_enabled,
            created_at=detail.department.created_at,
            updated_at=detail.department.updated_at,
            user_count=detail.user_count,
        ).model_dump(mode="json"),
    }


@router.put("/{department_id}")
def update_department(
    department_id: str,
    body: UpdateDepartmentRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
):
    handler = UpdateDepartmentCommandHandler(
        department_repo=dept_repo,
    )
    try:
        handler.handle(
            UpdateDepartmentCommand(
                department_id=department_id,
                company_id=current_user.company_id,
                name=body.name,
                priority_weight=body.priority_weight,
                budget_enforcement_enabled=body.budget_enforcement_enabled,
            )
        )
    except UpdateDeptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    except UpdateNameExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department with this name already exists",
        )
    query_handler = GetDepartmentQueryHandler(
        department_repo=dept_repo,
    )
    detail = query_handler.handle(
        GetDepartmentQuery(
            department_id=department_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(
            detail.department, dept_repo,
        ).model_dump(mode="json"),
    }


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_department(
    department_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
    po_repo: PurchaseOrderRepository = Depends(
        get_po_repo,
    ),
):
    handler = DeleteDepartmentCommandHandler(
        department_repo=dept_repo,
        po_repo=po_repo,
    )
    try:
        handler.handle(
            DeleteDepartmentCommand(
                department_id=department_id,
                company_id=current_user.company_id,
            )
        )
    except DeleteDeptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    except DepartmentHasUsersError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except DepartmentHasOpenPOsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{department_id}/manager")
def assign_manager(
    department_id: str,
    body: AssignManagerRequest,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
    user_repo: UserRepository = Depends(get_user_repo),
):
    handler = AssignDepartmentManagerCommandHandler(
        department_repo=dept_repo,
        user_lookup=user_repo,
    )
    try:
        handler.handle(
            AssignDepartmentManagerCommand(
                department_id=department_id,
                company_id=current_user.company_id,
                manager_user_id=body.user_id,
                performed_by=current_user.id,
            )
        )
    except AssignDeptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    except AssignUserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    except UserInactiveError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is inactive",
        )
    except CrossCompanyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User does not belong to this company",
        )
    query_handler = GetDepartmentQueryHandler(
        department_repo=dept_repo,
    )
    detail = query_handler.handle(
        GetDepartmentQuery(
            department_id=department_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(
            detail.department, dept_repo,
        ).model_dump(mode="json"),
    }


@router.delete(
    "/{department_id}/manager",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_manager(
    department_id: str,
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
    dept_repo: DepartmentRepository = Depends(
        get_department_repo,
    ),
):
    handler = RemoveDepartmentManagerCommandHandler(
        department_repo=dept_repo,
    )
    try:
        handler.handle(
            RemoveDepartmentManagerCommand(
                department_id=department_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except RemoveDeptNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
