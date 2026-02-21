import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, status

from adapters.http.api.auth.dependencies import require_role
from adapters.http.api.users.dependencies import (
    get_company_repo,
    get_department_repo,
    get_magic_link_repo,
    get_user_repo,
)
from adapters.http.api.users.schemas import (
    AssignDepartmentRequest,
    ChangeRoleRequest,
    ImportConfirmResponse,
    ImportDepartmentResponse,
    ImportPreviewResponse,
    ImportRowErrorResponse,
    InviteUserRequest,
    QuickCreateEmployeeRequest,
    QuickCreateEmployeeResponse,
    UpdateUserRequest,
    UserDetailResponse,
)
from adapters.http.schemas.responses import PaginationMeta
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from core.email import get_email_service
from src.auth_bc.company_lookup.infrastructure.service import CompanyLookupService
from src.auth_bc.magic_link.application.commands.create_magic_link import (
    CompanyRestrictedError,
    CreateMagicLinkCommand,
    CreateMagicLinkCommandHandler,
    InvalidEmailDomainError,
    RateLimitExceededError,
)
from src.auth_bc.magic_link.infrastructure.repository import MagicLinkRepository
from src.auth_bc.user.application.commands.import_users import (
    ImportUsersService,
    InvalidCSVError,
)
from src.auth_bc.user.application.commands.change_user_role import (
    CannotAssignSuperAdminError,
    CannotChangeSelfError,
    ChangeUserRoleCommand,
    ChangeUserRoleCommandHandler,
    LastAdminError,
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
from src.company_bc.company.infrastructure.repository import CompanyRepository

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


def _get_user_response(user_repo: UserRepository, user_id: str, company_id: str) -> dict:
    query_handler = GetUserDetailQueryHandler(user_repo=user_repo)
    user = query_handler.handle(GetUserDetailQuery(user_id=user_id, company_id=company_id))
    return {"data": _to_response(user).model_dump(mode="json")}


@router.get("")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    department_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id = current_user.company_id
    handler = ListUsersQueryHandler(user_repo=user_repo)
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


def _validate_invite_email(email: str, company_id: str, company_repo: CompanyRepository) -> None:
    company = company_repo.find_by_id(company_id)
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
    domain = email.split("@", 1)[-1]
    if domain not in [d.lower() for d in company.email_domains]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email domain is not allowed for this company")


def _ensure_user_for_invite(
    email: str, company_id: str, user_repo: UserRepository,
    role: UserRole = UserRole.EMPLOYEE, name: Optional[str] = None,
) -> None:
    existing_user = user_repo.find_by_email(email)
    if existing_user:
        if existing_user.company_id != company_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")
        if not existing_user.is_active:
            existing_user.activate()
        existing_user.role = role
        if name is not None:
            existing_user.name = name
        user_repo.save(existing_user)
    else:
        user_repo.save(User.create(email=email, role=role, company_id=company_id, name=name))


def _send_invite_link(
    email: str, magic_link_repo: MagicLinkRepository, company_repo: CompanyRepository, user_repo: UserRepository,
) -> None:
    handler = CreateMagicLinkCommandHandler(
        magic_link_repo=magic_link_repo, company_lookup=CompanyLookupService(company_repo.session),
        email_service=get_email_service(), user_repo=user_repo,
    )
    try:
        handler.handle(CreateMagicLinkCommand(email=email))
    except InvalidEmailDomainError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email domain is not allowed for this company")
    except CompanyRestrictedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Company access is currently restricted")
    except RateLimitExceededError:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many requests. Please wait before requesting another invite.")


@router.post("/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    body: InviteUserRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
):
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid company context")
    email = body.email.lower().strip()
    invite_role = UserRole.EMPLOYEE
    if body.role:
        try:
            invite_role = UserRole(body.role)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role: {body.role}")
        if invite_role == UserRole.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot invite super admins")
    invite_name = body.name.strip() if body.name else None
    _validate_invite_email(email, company_id, company_repo)
    _ensure_user_for_invite(email, company_id, user_repo, role=invite_role, name=invite_name)
    _send_invite_link(email, magic_link_repo, company_repo, user_repo)
    return {"data": {"message": "Invitation sent"}}


def _parse_csv_upload(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be UTF-8 encoded",
        )


@router.post("/import/preview", status_code=status.HTTP_200_OK)
async def import_users_preview(
    file: UploadFile,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
    department_repo: DepartmentRepository = Depends(get_department_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid company context")
    if file.size and file.size > 1_048_576:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds 1MB limit")
    csv_content = _parse_csv_upload(await file.read())
    try:
        result = ImportUsersService(
            user_repo=user_repo, department_repo=department_repo, company_repo=company_repo,
        ).preview(csv_content=csv_content, company_id=company_id)
    except InvalidCSVError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {
        "data": ImportPreviewResponse(
            total_rows=result.total_rows,
            valid_rows=result.valid_rows,
            errors=[ImportRowErrorResponse(row=e.row, error=e.error) for e in result.errors],
            unknown_departments=result.unknown_departments,
            existing_departments=[
                ImportDepartmentResponse(id=d.id, name=d.name) for d in result.existing_departments
            ],
        ).model_dump()
    }


@router.post("/import/confirm", status_code=status.HTTP_200_OK)
async def import_users_confirm(
    file: UploadFile,
    department_mapping: str = Form("{}"),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
    department_repo: DepartmentRepository = Depends(get_department_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
    magic_link_repo: MagicLinkRepository = Depends(get_magic_link_repo),
):
    company_id = current_user.company_id
    if not company_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid company context")
    if file.size and file.size > 1_048_576:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds 1MB limit")

    try:
        mapping = json.loads(department_mapping)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid department_mapping JSON")

    csv_content = _parse_csv_upload(await file.read())

    def send_magic_link(email: str) -> None:
        handler = CreateMagicLinkCommandHandler(
            magic_link_repo=magic_link_repo,
            company_lookup=CompanyLookupService(company_repo.session),
            email_service=get_email_service(),
            user_repo=user_repo,
        )
        handler.handle(CreateMagicLinkCommand(email=email))

    try:
        result = ImportUsersService(
            user_repo=user_repo, department_repo=department_repo, company_repo=company_repo,
        ).confirm(
            csv_content=csv_content,
            company_id=company_id,
            performed_by=current_user.id,
            department_mapping=mapping,
            magic_link_sender=send_magic_link,
        )
    except InvalidCSVError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    return {
        "data": ImportConfirmResponse(
            total=result.total,
            successful=result.successful,
            failed=[ImportRowErrorResponse(row=e.row, error=e.error) for e in result.failed],
            departments_created=result.departments_created,
            invitations_sent=result.invitations_sent,
        ).model_dump()
    }


@router.post("/quick-create", status_code=status.HTTP_201_CREATED)
def quick_create_employee(
    body: QuickCreateEmployeeRequest,
    current_user: User = Depends(require_role(UserRole.TECHNICIAN)),
    user_repo: UserRepository = Depends(get_user_repo),
    company_repo: CompanyRepository = Depends(get_company_repo),
):
    email = body.email.lower().strip()
    _validate_invite_email(email, current_user.company_id, company_repo)
    existing = user_repo.find_by_email(email)
    if existing:
        if existing.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists in another company",
            )
        return {
            "data": QuickCreateEmployeeResponse(
                id=existing.id, email=existing.email, name=existing.name,
            ).model_dump()
        }
    new_user = User.create(
        email=email,
        role=UserRole.EMPLOYEE,
        company_id=current_user.company_id,
        name=body.name.strip() if body.name else None,
    )
    new_user.is_active = False
    user_repo.save(new_user)
    return {
        "data": QuickCreateEmployeeResponse(
            id=new_user.id, email=new_user.email, name=new_user.name,
        ).model_dump()
    }


@router.get("/{user_id}")
def get_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id = current_user.company_id
    handler = GetUserDetailQueryHandler(user_repo=user_repo)
    try:
        user = handler.handle(GetUserDetailQuery(user_id=user_id, company_id=company_id))
    except GetUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"data": _to_response(user).model_dump(mode="json")}


def _handle_change_role_errors(func):  # type: ignore[no-untyped-def]
    """Map change-role domain errors to HTTP exceptions."""
    try:
        func()
    except RoleUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except CannotChangeSelfError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot change your own role")
    except CannotAssignSuperAdminError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot assign super_admin role")
    except LastAdminError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="At least one admin must remain in the company")
    except ValueError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid role value")


@router.patch("/{user_id}", status_code=status.HTTP_200_OK)
def update_user(
    user_id: str,
    body: UpdateUserRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
    department_repo: DepartmentRepository = Depends(get_department_repo),
):
    company_id = current_user.company_id
    provided = body.model_fields_set

    if "name" in provided:
        user = user_repo.find_by_id_and_company(user_id, company_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.name = body.name.strip() if body.name else None
        user_repo.save(user)

    if "role" in provided and body.role:
        target = user_repo.find_by_id_and_company(user_id, company_id)
        if target and target.role.value != body.role:
            handler = ChangeUserRoleCommandHandler(user_repo=user_repo, email_service=get_email_service())
            _handle_change_role_errors(lambda: handler.handle(
                ChangeUserRoleCommand(user_id=user_id, company_id=company_id, current_user_id=current_user.id, new_role=body.role)
            ))

    if "department_id" in provided:
        dept_handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=department_repo)
        try:
            dept_handler.handle(AssignDepartmentCommand(user_id=user_id, company_id=company_id, department_id=body.department_id))
        except AssignUserNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        except DepartmentNotFoundError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
        except DepartmentInactiveError:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot assign user to inactive department")

    return _get_user_response(user_repo, user_id, company_id)


@router.patch("/{user_id}/role")
def change_role(
    user_id: str,
    body: ChangeRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id = current_user.company_id
    handler = ChangeUserRoleCommandHandler(user_repo=user_repo, email_service=get_email_service())
    _handle_change_role_errors(lambda: handler.handle(
        ChangeUserRoleCommand(user_id=user_id, company_id=company_id, current_user_id=current_user.id, new_role=body.role)
    ))
    return _get_user_response(user_repo, user_id, company_id)


@router.patch("/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id = current_user.company_id
    handler = DeactivateUserCommandHandler(user_repo=user_repo)
    try:
        handler.handle(
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
    return _get_user_response(user_repo, user_id, company_id)


@router.patch("/{user_id}/activate")
def activate_user(
    user_id: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
):
    company_id = current_user.company_id
    handler = ActivateUserCommandHandler(user_repo=user_repo)
    try:
        handler.handle(
            ActivateUserCommand(user_id=user_id, company_id=company_id)
        )
    except ActivateUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return _get_user_response(user_repo, user_id, company_id)


@router.patch("/{user_id}/department")
def assign_department(
    user_id: str,
    body: AssignDepartmentRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
    department_repo: DepartmentRepository = Depends(get_department_repo),
):
    company_id = current_user.company_id
    handler = AssignDepartmentCommandHandler(user_repo=user_repo, department_repo=department_repo)
    try:
        handler.handle(AssignDepartmentCommand(user_id=user_id, company_id=company_id, department_id=body.department_id))
    except AssignUserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except DepartmentNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    except DepartmentInactiveError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot assign user to inactive department")
    return _get_user_response(user_repo, user_id, company_id)
