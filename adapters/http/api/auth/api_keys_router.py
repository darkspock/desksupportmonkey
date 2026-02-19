import ulid
from fastapi import APIRouter, Depends, HTTPException, status

from adapters.http.api.auth.api_keys_dependencies import get_api_key_repo
from adapters.http.api.auth.api_keys_schemas import (
    ApiKeyResponse,
    CreateApiKeyRequest,
    CreateApiKeyResponse,
)
from adapters.http.api.auth.dependencies import require_role
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.mcp_bc.server.application.commands.create_api_key import (
    CreateApiKeyCommand,
    CreateApiKeyCommandHandler,
    MaxApiKeysReachedError,
    generate_api_key,
)
from src.mcp_bc.server.application.commands.revoke_api_key import (
    ApiKeyNotFoundError,
    RevokeApiKeyCommand,
    RevokeApiKeyCommandHandler,
)
from src.mcp_bc.server.application.queries.list_api_keys import (
    ListApiKeysQuery,
    ListApiKeysQueryHandler,
)
from src.mcp_bc.server.domain.entities import ApiKeyAlreadyRevokedError
from src.mcp_bc.server.infrastructure.repository import ApiKeyRepository

router = APIRouter(prefix="/api/v1/auth/api-keys", tags=["API Keys"])

employee_dep = require_role(UserRole.EMPLOYEE)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_api_key(
    body: CreateApiKeyRequest,
    current_user: User = Depends(employee_dep),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo),
):
    raw_key, key_hash = generate_api_key()
    key_id = str(ulid.new())

    handler = CreateApiKeyCommandHandler(api_key_repo=api_key_repo)
    try:
        handler.handle(
            CreateApiKeyCommand(
                user_id=current_user.id,
                name=body.name,
                key_hash=key_hash,
                id=key_id,
            )
        )
    except MaxApiKeysReachedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    api_key = api_key_repo.find_by_id(key_id, current_user.id)
    return {
        "data": CreateApiKeyResponse(
            id=api_key.id,
            name=api_key.name,
            raw_key=raw_key,
            created_at=api_key.created_at,
            is_active=api_key.is_active,
        ).model_dump(mode="json")
    }


@router.get("")
def list_api_keys(
    current_user: User = Depends(employee_dep),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo),
):
    handler = ListApiKeysQueryHandler(api_key_repo=api_key_repo)
    keys = handler.handle(ListApiKeysQuery(user_id=current_user.id))
    return {
        "data": [
            ApiKeyResponse(
                id=k.id,
                name=k.name,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                is_active=k.is_active,
            ).model_dump(mode="json")
            for k in keys
        ]
    }


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    current_user: User = Depends(employee_dep),
    api_key_repo: ApiKeyRepository = Depends(get_api_key_repo),
):
    handler = RevokeApiKeyCommandHandler(api_key_repo=api_key_repo)
    try:
        handler.handle(
            RevokeApiKeyCommand(key_id=key_id, user_id=current_user.id)
        )
    except ApiKeyNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )
    except ApiKeyAlreadyRevokedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="API key is already revoked"
        )
