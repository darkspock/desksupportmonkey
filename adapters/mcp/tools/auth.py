"""MCP tools for auth and API key management (5 tools)."""
import json
from typing import Any

import ulid
from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.password import PasswordService
from core.tenant import TenantContext, get_tenant
from src.auth_bc.user.application.commands.set_password import (
    NotAdminError,
    SetPasswordCommand,
    SetPasswordCommandHandler,
    WeakPasswordError,
)
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import (
    UserRepository,
)
from src.mcp_bc.server.application.commands.create_api_key import (  # noqa: E501
    CreateApiKeyCommand,
    CreateApiKeyCommandHandler,
    MaxApiKeysReachedError,
    generate_api_key,
)
from src.mcp_bc.server.application.commands.revoke_api_key import (  # noqa: E501
    ApiKeyNotFoundError,
    RevokeApiKeyCommand,
    RevokeApiKeyCommandHandler,
)
from src.mcp_bc.server.application.queries.list_api_keys import (  # noqa: E501
    ListApiKeysQuery,
    ListApiKeysQueryHandler,
)
from src.mcp_bc.server.domain.entities import (
    ApiKeyAlreadyRevokedError,
)
from src.mcp_bc.server.infrastructure.repository import (
    ApiKeyRepository,
)


def _text(data: Any) -> list[TextContent]:
    return [TextContent(
        type="text", text=json.dumps(data),
    )]


def _error(message: str) -> list[TextContent]:
    return _text({"error": message})


class _AuthenticatedTenant:
    """Typed wrapper ensuring company_id is non-None."""

    __slots__ = ("company_id", "user_id", "role")

    def __init__(self, ctx: TenantContext) -> None:
        assert ctx.company_id is not None
        self.company_id: str = ctx.company_id
        self.user_id: str = ctx.user_id
        self.role: str = ctx.role


def _require_tenant() -> _AuthenticatedTenant:
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated"
    return _AuthenticatedTenant(tenant)


# --- Tool handlers ---


async def handle_get_current_user(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        user = user_repo.find_by_id(tenant.user_id)
        if not user:
            return _error("User not found")

        return _text({
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role.value,
            "company_id": user.company_id,
            "department_id": user.department_id,
            "is_active": user.is_active,
        })
    finally:
        db.close()


async def handle_set_password(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        handler = SetPasswordCommandHandler(
            user_repo=user_repo,
            password_service=PasswordService(),
        )
        handler.handle(
            SetPasswordCommand(
                user_id=tenant.user_id,
                password=arguments["password"],
            )
        )
        db.commit()

        return _text({
            "message": "Password set successfully",
        })
    except NotAdminError as e:
        db.rollback()
        return _error(str(e))
    except WeakPasswordError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_create_api_key(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        api_key_repo = ApiKeyRepository(db)

        raw_key, key_hash = generate_api_key()
        key_id = str(ulid.new())

        handler = CreateApiKeyCommandHandler(
            api_key_repo=api_key_repo,
        )
        handler.handle(
            CreateApiKeyCommand(
                user_id=tenant.user_id,
                name=arguments["name"],
                key_hash=key_hash,
                id=key_id,
            )
        )
        db.commit()

        api_key = api_key_repo.find_by_id(
            key_id, tenant.user_id,
        )
        return _text({
            "id": api_key.id,
            "name": api_key.name,
            "raw_key": raw_key,
            "created_at": (
                api_key.created_at.isoformat()
                if api_key.created_at else None
            ),
            "is_active": api_key.is_active,
        })
    except MaxApiKeysReachedError as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_api_keys(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        api_key_repo = ApiKeyRepository(db)

        handler = ListApiKeysQueryHandler(
            api_key_repo=api_key_repo,
        )
        keys = handler.handle(
            ListApiKeysQuery(user_id=tenant.user_id)
        )

        return _text([
            {
                "id": k.id,
                "name": k.name,
                "created_at": (
                    k.created_at.isoformat()
                    if k.created_at else None
                ),
                "last_used_at": (
                    k.last_used_at.isoformat()
                    if k.last_used_at else None
                ),
                "is_active": k.is_active,
            }
            for k in keys
        ])
    finally:
        db.close()


async def handle_revoke_api_key(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        api_key_repo = ApiKeyRepository(db)

        handler = RevokeApiKeyCommandHandler(
            api_key_repo=api_key_repo,
        )
        handler.handle(
            RevokeApiKeyCommand(
                key_id=arguments["key_id"],
                user_id=tenant.user_id,
            )
        )
        db.commit()

        return _text({"success": True})
    except ApiKeyNotFoundError as e:
        db.rollback()
        return _error(str(e))
    except ApiKeyAlreadyRevokedError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="get_current_user",
    description=(
        "Get the authenticated user's profile "
        "(id, email, name, role, company, "
        "department, active status)."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_get_current_user,
)

tool_registry.register(
    name="set_password",
    description=(
        "Set or update the current user's password. "
        "Only admin/super_admin accounts can set "
        "passwords. Minimum 8 characters."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "password": {
                "type": "string",
                "description": (
                    "New password (min 8 chars)"
                ),
            },
        },
        "required": ["password"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_set_password,
)

tool_registry.register(
    name="create_api_key",
    description=(
        "Create a new API key. Returns the raw key "
        "ONCE — it cannot be retrieved later. "
        "Max 10 active keys per user."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": (
                    "Human label for this key "
                    "(e.g. 'Claude Desktop')"
                ),
            },
        },
        "required": ["name"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_create_api_key,
)

tool_registry.register(
    name="list_api_keys",
    description=(
        "List all API keys for the current user. "
        "Shows metadata only (no raw keys)."
    ),
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_list_api_keys,
)

tool_registry.register(
    name="revoke_api_key",
    description=(
        "Revoke an API key. Revoked keys cannot "
        "be reactivated."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "key_id": {
                "type": "string",
                "description": (
                    "The API key ID to revoke"
                ),
            },
        },
        "required": ["key_id"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_revoke_api_key,
)
