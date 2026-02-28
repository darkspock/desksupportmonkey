import os

import ulid
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile

from adapters.http.api.auth.dependencies import require_plan_feature, require_role
from adapters.http.api.custom_fields.dependencies import get_cf_definition_repo
from adapters.http.api.custom_fields.schemas import (
    CreateFieldDefinitionRequest,
    FieldDefinitionResponse,
    FileDownloadResponse,
    FileUploadResponse,
    ReorderRequest,
    UpdateFieldDefinitionRequest,
)
from core.storage import S3StorageService
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.custom_field_bc.definition.domain.file_constants import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    CF_FILES_PREFIX,
    MAX_FILE_SIZE_BYTES,
)
from src.custom_field_bc.definition.application.commands.activate_definition import (
    ActivateFieldDefinitionCommand,
    ActivateFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.commands.create_definition import (
    CreateFieldDefinitionCommand,
    CreateFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.commands.deactivate_definition import (
    DeactivateFieldDefinitionCommand,
    DeactivateFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.commands.delete_definition import (
    DeleteFieldDefinitionCommand,
    DeleteFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.commands.reorder_definitions import (
    ReorderFieldDefinitionsCommand,
    ReorderFieldDefinitionsCommandHandler,
)
from src.custom_field_bc.definition.application.commands.update_definition import (
    UpdateFieldDefinitionCommand,
    UpdateFieldDefinitionCommandHandler,
)
from src.custom_field_bc.definition.application.queries.get_definition import (
    GetFieldDefinitionQuery,
    GetFieldDefinitionQueryHandler,
)
from src.custom_field_bc.definition.application.queries.list_definitions import (
    ListFieldDefinitionsQuery,
    ListFieldDefinitionsQueryHandler,
)
from src.custom_field_bc.definition.domain.exceptions import (
    DuplicateFieldKeyError,
    FieldDefinitionNotFoundError,
    MaxFieldsExceededError,
    OptionsRequiredError,
)
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)

router = APIRouter(prefix="/api/v1/custom-fields", tags=["custom-fields"])


def _to_response(dto) -> dict:
    return FieldDefinitionResponse(
        id=dto.id,
        entity_type=dto.entity_type,
        field_key=dto.field_key,
        label=dto.label,
        description=dto.description,
        field_type=dto.field_type,
        options=dto.options,
        required=dto.required,
        sort_order=dto.sort_order,
        is_active=dto.is_active,
        visible_to_employees=dto.visible_to_employees,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
    ).model_dump(mode="json")


@router.get("/definitions")
def list_definitions(
    entity_type: str = Query(pattern=r"^(asset|request|incident)$"),
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = ListFieldDefinitionsQueryHandler(repo=repo)
    definitions = handler.handle(
        ListFieldDefinitionsQuery(
            company_id=current_user.company_id,
            entity_type=entity_type,
        )
    )
    return {"data": [_to_response(d) for d in definitions]}


@router.put("/definitions/reorder")
def reorder_definitions(
    body: ReorderRequest,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = ReorderFieldDefinitionsCommandHandler(repo=repo)
    handler.handle(
        ReorderFieldDefinitionsCommand(
            company_id=current_user.company_id,
            entity_type=body.entity_type,
            field_ids=body.field_ids,
        )
    )
    list_handler = ListFieldDefinitionsQueryHandler(repo=repo)
    definitions = list_handler.handle(
        ListFieldDefinitionsQuery(
            company_id=current_user.company_id,
            entity_type=body.entity_type,
        )
    )
    return {"data": [_to_response(d) for d in definitions]}


@router.get("/definitions/{definition_id}")
def get_definition(
    definition_id: str,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = GetFieldDefinitionQueryHandler(repo=repo)
    try:
        dto = handler.handle(
            GetFieldDefinitionQuery(
                definition_id=definition_id,
                company_id=current_user.company_id,
            )
        )
    except FieldDefinitionNotFoundError:
        raise HTTPException(status_code=404, detail="Definition not found")
    return {"data": _to_response(dto)}


@router.post("/definitions", status_code=201)
def create_definition(
    body: CreateFieldDefinitionRequest,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    definition_id = str(ulid.new())
    handler = CreateFieldDefinitionCommandHandler(repo=repo)
    try:
        handler.handle(
            CreateFieldDefinitionCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
                entity_type=body.entity_type,
                label=body.label,
                field_type=body.field_type,
                description=body.description,
                options=body.options,
                required=body.required,
                visible_to_employees=body.visible_to_employees,
            )
        )
    except MaxFieldsExceededError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DuplicateFieldKeyError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except OptionsRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))

    query_handler = GetFieldDefinitionQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetFieldDefinitionQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.put("/definitions/{definition_id}")
def update_definition(
    definition_id: str,
    body: UpdateFieldDefinitionRequest,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = UpdateFieldDefinitionCommandHandler(repo=repo)
    try:
        handler.handle(
            UpdateFieldDefinitionCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
                label=body.label,
                description=body.description,
                options=body.options,
                required=body.required,
                visible_to_employees=body.visible_to_employees,
            )
        )
    except FieldDefinitionNotFoundError:
        raise HTTPException(status_code=404, detail="Definition not found")
    except OptionsRequiredError as e:
        raise HTTPException(status_code=422, detail=str(e))

    query_handler = GetFieldDefinitionQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetFieldDefinitionQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.delete("/definitions/{definition_id}", status_code=204)
def delete_definition(
    definition_id: str,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = DeleteFieldDefinitionCommandHandler(repo=repo)
    try:
        handler.handle(
            DeleteFieldDefinitionCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
            )
        )
    except FieldDefinitionNotFoundError:
        raise HTTPException(status_code=404, detail="Definition not found")


@router.post("/definitions/{definition_id}/deactivate")
def deactivate_definition(
    definition_id: str,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = DeactivateFieldDefinitionCommandHandler(repo=repo)
    try:
        handler.handle(
            DeactivateFieldDefinitionCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
            )
        )
    except FieldDefinitionNotFoundError:
        raise HTTPException(status_code=404, detail="Definition not found")

    query_handler = GetFieldDefinitionQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetFieldDefinitionQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


@router.post("/definitions/{definition_id}/activate")
def activate_definition(
    definition_id: str,
    current_user: User = Depends(require_plan_feature("custom_fields")),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    repo: CustomFieldDefinitionRepository = Depends(get_cf_definition_repo),
):
    handler = ActivateFieldDefinitionCommandHandler(repo=repo)
    try:
        handler.handle(
            ActivateFieldDefinitionCommand(
                definition_id=definition_id,
                company_id=current_user.company_id,
            )
        )
    except FieldDefinitionNotFoundError:
        raise HTTPException(status_code=404, detail="Definition not found")

    query_handler = GetFieldDefinitionQueryHandler(repo=repo)
    dto = query_handler.handle(
        GetFieldDefinitionQuery(
            definition_id=definition_id,
            company_id=current_user.company_id,
        )
    )
    return {"data": _to_response(dto)}


# ── File upload / download ───────────────────────────────────────────


@router.post("/files/upload", status_code=201)
async def upload_file(
    file: UploadFile,
    entity_type: str = Query(pattern=r"^(asset|request|incident)$"),
    field_key: str = Query(min_length=1),
    current_user: User = Depends(require_plan_feature("custom_fields")),
):
    # Validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"File extension '{ext}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Validate MIME
    mime = file.content_type or "application/octet-stream"
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"MIME type '{mime}' is not allowed. "
            f"Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    # Read and validate size
    data = await file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=422,
            detail=f"File exceeds maximum size of "
            f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
        )

    file_id = str(ulid.new())
    key = (
        f"{CF_FILES_PREFIX}/{current_user.company_id}/"
        f"{entity_type}/{field_key}/{file_id}{ext}"
    )

    storage = S3StorageService()
    storage.upload(key, data, content_type=mime)

    return {
        "data": FileUploadResponse(
            id=file_id,
            name=file.filename or f"{file_id}{ext}",
            size=len(data),
            mime=mime,
            key=key,
        ).model_dump()
    }


@router.get("/files/{file_id}/download")
def download_file(
    file_id: str,
    key: str = Query(min_length=1),
    current_user: User = Depends(require_plan_feature("custom_fields")),
):
    # Verify the key belongs to the requesting company
    expected_prefix = f"{CF_FILES_PREFIX}/{current_user.company_id}/"
    if not key.startswith(expected_prefix):
        raise HTTPException(status_code=403, detail="Access denied")

    storage = S3StorageService()
    url = storage.get_signed_url(key, expiration=3600)
    return {"data": FileDownloadResponse(url=url).model_dump()}
