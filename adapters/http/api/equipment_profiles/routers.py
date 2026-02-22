import logging

import ulid
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    status,
)

from adapters.http.api.auth.dependencies import (
    get_current_user,
)
from adapters.http.api.equipment_profiles.dependencies import (
    get_dept_repo,
    get_profile_repo,
    require_department_access,
)
from adapters.http.api.equipment_profiles.schemas import (
    CreateProfileRequest,
    ProfileItemResponse,
    ProfileResponse,
    UpdateProfileRequest,
)
from adapters.http.schemas.responses import PaginationMeta
from src.asset_bc.asset.domain.enums import AssetType
from src.auth_bc.user.domain.entities import User
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)
from src.company_bc.equipment_profile.application.commands.activate_profile import (  # noqa: E501
    ActivateEquipmentProfileCommand,
    ActivateEquipmentProfileCommandHandler,
    ProfileNotFoundError as ActivateNotFoundError,
)
from src.company_bc.equipment_profile.application.commands.create_profile import (  # noqa: E501
    ActiveProfileExistsError,
    CreateEquipmentProfileCommand,
    CreateEquipmentProfileCommandHandler,
    ProfileItemInput,
)
from src.company_bc.equipment_profile.application.commands.deactivate_profile import (  # noqa: E501
    DeactivateEquipmentProfileCommand,
    DeactivateEquipmentProfileCommandHandler,
    ProfileNotFoundError as DeactivateNotFoundError,
)
from src.company_bc.equipment_profile.application.commands.delete_profile import (  # noqa: E501
    DeleteEquipmentProfileCommand,
    DeleteEquipmentProfileCommandHandler,
    ProfileNotFoundError as DeleteNotFoundError,
)
from src.company_bc.equipment_profile.application.commands.update_profile import (  # noqa: E501
    ProfileItemInput as UpdateItemInput,
    ProfileNotFoundError as UpdateNotFoundError,
    UpdateEquipmentProfileCommand,
    UpdateEquipmentProfileCommandHandler,
)
from src.company_bc.equipment_profile.application.queries.get_profile import (  # noqa: E501
    GetEquipmentProfileQuery,
    GetEquipmentProfileQueryHandler,
    ProfileNotFoundError as GetNotFoundError,
)
from src.company_bc.equipment_profile.application.queries.get_my_budget import (  # noqa: E501
    GetMyBudgetQuery,
    GetMyBudgetQueryHandler,
)
from src.company_bc.equipment_profile.application.queries.list_profiles import (  # noqa: E501
    ListEquipmentProfilesQuery,
    ListEquipmentProfilesQueryHandler,
)
from src.company_bc.equipment_profile.domain.entities import (
    EquipmentProfile,
)
from src.company_bc.equipment_profile.infrastructure.repository import (  # noqa: E501
    EquipmentProfileRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/equipment-profiles",
    tags=["equipment-profiles"],
)


def _to_response(
    profile: EquipmentProfile,
) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        company_id=profile.company_id,
        department_id=profile.department_id,
        employee_role_id=profile.employee_role_id,
        is_active=profile.is_active,
        items=[
            ProfileItemResponse(
                id=item.id,
                asset_type=item.asset_type.value,
                quantity=item.quantity,
                preferred_brand=item.preferred_brand,
                preferred_model=item.preferred_model,
                min_ram_gb=item.min_ram_gb,
                min_storage_gb=item.min_storage_gb,
                budget_cents=item.budget_cents,
            )
            for item in profile.items
        ],
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )


def _validate_items(items):
    """Validate asset_type values."""
    for item in items:
        try:
            AssetType(item.asset_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid asset type: {item.asset_type}",
            )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_profile(
    body: CreateProfileRequest,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_dept_repo,
    ),
):
    assert current_user.company_id is not None
    require_department_access(
        current_user, body.department_id, dept_repo,
    )
    _validate_items(body.items)

    profile_id = str(ulid.new())
    handler = CreateEquipmentProfileCommandHandler(
        profile_repo=profile_repo,
    )
    try:
        handler.handle(
            CreateEquipmentProfileCommand(
                id=profile_id,
                company_id=current_user.company_id,
                department_id=body.department_id,
                employee_role_id=body.employee_role_id,
                items=[
                    ProfileItemInput(
                        asset_type=AssetType(i.asset_type),
                        quantity=i.quantity,
                        preferred_brand=i.preferred_brand,
                        preferred_model=i.preferred_model,
                        min_ram_gb=i.min_ram_gb,
                        min_storage_gb=i.min_storage_gb,
                        budget_cents=i.budget_cents,
                    )
                    for i in body.items
                ],
                performed_by=current_user.id,
            )
        )
    except ActiveProfileExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active profile already exists "
            "for this department and employee role",
        )

    query_handler = GetEquipmentProfileQueryHandler(
        profile_repo=profile_repo,
    )
    profile = query_handler.handle(
        GetEquipmentProfileQuery(
            profile_id=profile_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(profile).model_dump(
            mode="json",
        ),
    }


@router.get("")
def list_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    department_id: str = Query(None),
    employee_role_id: str = Query(None),
    is_active: bool = Query(None),
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
):
    # Any authenticated user with a company can list
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No company context",
        )
    handler = ListEquipmentProfilesQueryHandler(
        profile_repo=profile_repo,
    )
    profiles, total = handler.handle(
        ListEquipmentProfilesQuery(
            company_id=current_user.company_id,
            page=page,
            page_size=page_size,
            department_id=department_id,
            employee_role_id=employee_role_id,
            is_active=is_active,
        )
    )
    return {
        "data": [
            _to_response(p).model_dump(mode="json")
            for p in profiles
        ],
        "meta": PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
        ).model_dump(),
    }


@router.get("/my-budget")
def my_budget(
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
):
    """Return budget items from the current user's active
    equipment profile. Used for informational budget
    indicators on the new-equipment request form."""
    budget = GetMyBudgetQueryHandler(
        profile_repo=profile_repo,
    ).handle(
        GetMyBudgetQuery(
            company_id=current_user.company_id,
            department_id=current_user.department_id,
            employee_role_id=current_user.employee_role_id,
        ),
    )

    return {
        "data": {
            "items": [
                {
                    "asset_type": item.asset_type,
                    "budget_cents": item.budget_cents,
                }
                for item in budget.items
            ],
        },
    }


@router.get("/{profile_id}")
def get_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
):
    assert current_user.company_id is not None
    handler = GetEquipmentProfileQueryHandler(
        profile_repo=profile_repo,
    )
    try:
        profile = handler.handle(
            GetEquipmentProfileQuery(
                profile_id=profile_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )
    return {
        "data": _to_response(profile).model_dump(
            mode="json",
        ),
    }


@router.put("/{profile_id}")
def update_profile(
    profile_id: str,
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_dept_repo,
    ),
):
    assert current_user.company_id is not None
    # Look up profile to get department_id for auth
    try:
        profile = GetEquipmentProfileQueryHandler(
            profile_repo=profile_repo,
        ).handle(
            GetEquipmentProfileQuery(
                profile_id=profile_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    require_department_access(
        current_user, profile.department_id, dept_repo,
    )
    _validate_items(body.items)

    handler = UpdateEquipmentProfileCommandHandler(
        profile_repo=profile_repo,
    )
    try:
        handler.handle(
            UpdateEquipmentProfileCommand(
                profile_id=profile_id,
                company_id=current_user.company_id,
                items=[
                    UpdateItemInput(
                        asset_type=AssetType(i.asset_type),
                        quantity=i.quantity,
                        preferred_brand=i.preferred_brand,
                        preferred_model=i.preferred_model,
                        min_ram_gb=i.min_ram_gb,
                        min_storage_gb=i.min_storage_gb,
                        budget_cents=i.budget_cents,
                    )
                    for i in body.items
                ],
                performed_by=current_user.id,
            )
        )
    except UpdateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    updated = GetEquipmentProfileQueryHandler(
        profile_repo=profile_repo,
    ).handle(
        GetEquipmentProfileQuery(
            profile_id=profile_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(updated).model_dump(
            mode="json",
        ),
    }


@router.post("/{profile_id}/activate")
def activate_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_dept_repo,
    ),
):
    assert current_user.company_id is not None
    try:
        profile = GetEquipmentProfileQueryHandler(
            profile_repo=profile_repo,
        ).handle(
            GetEquipmentProfileQuery(
                profile_id=profile_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    require_department_access(
        current_user, profile.department_id, dept_repo,
    )

    handler = ActivateEquipmentProfileCommandHandler(
        profile_repo=profile_repo,
    )
    try:
        handler.handle(
            ActivateEquipmentProfileCommand(
                profile_id=profile_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except ActivateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    updated = GetEquipmentProfileQueryHandler(
        profile_repo=profile_repo,
    ).handle(
        GetEquipmentProfileQuery(
            profile_id=profile_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(updated).model_dump(
            mode="json",
        ),
    }


@router.post("/{profile_id}/deactivate")
def deactivate_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_dept_repo,
    ),
):
    assert current_user.company_id is not None
    try:
        profile = GetEquipmentProfileQueryHandler(
            profile_repo=profile_repo,
        ).handle(
            GetEquipmentProfileQuery(
                profile_id=profile_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    require_department_access(
        current_user, profile.department_id, dept_repo,
    )

    handler = DeactivateEquipmentProfileCommandHandler(
        profile_repo=profile_repo,
    )
    try:
        handler.handle(
            DeactivateEquipmentProfileCommand(
                profile_id=profile_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except DeactivateNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    updated = GetEquipmentProfileQueryHandler(
        profile_repo=profile_repo,
    ).handle(
        GetEquipmentProfileQuery(
            profile_id=profile_id,
            company_id=current_user.company_id,
        )
    )
    return {
        "data": _to_response(updated).model_dump(
            mode="json",
        ),
    }


@router.delete(
    "/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    profile_repo: EquipmentProfileRepository = Depends(
        get_profile_repo,
    ),
    dept_repo: DepartmentRepository = Depends(
        get_dept_repo,
    ),
):
    assert current_user.company_id is not None
    try:
        profile = GetEquipmentProfileQueryHandler(
            profile_repo=profile_repo,
        ).handle(
            GetEquipmentProfileQuery(
                profile_id=profile_id,
                company_id=current_user.company_id,
            )
        )
    except GetNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )

    require_department_access(
        current_user, profile.department_id, dept_repo,
    )

    handler = DeleteEquipmentProfileCommandHandler(
        profile_repo=profile_repo,
    )
    try:
        handler.handle(
            DeleteEquipmentProfileCommand(
                profile_id=profile_id,
                company_id=current_user.company_id,
                performed_by=current_user.id,
            )
        )
    except DeleteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment profile not found",
        )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
