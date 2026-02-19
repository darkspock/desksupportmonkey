"""MCP tools for user management (7 tools)."""
import json
from typing import Any, cast

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.email import get_email_service
from core.tenant import TenantContext, get_tenant
from src.auth_bc.company_lookup.infrastructure.service import (
    CompanyLookupService,
)
from src.auth_bc.magic_link.application.commands.create_magic_link import (
    CompanyRestrictedError,
    CreateMagicLinkCommand,
    CreateMagicLinkCommandHandler,
    InvalidEmailDomainError,
    RateLimitExceededError,
)
from src.auth_bc.magic_link.infrastructure.repository import (
    MagicLinkRepository,
)
from src.auth_bc.user.application.commands.activate_user import (
    ActivateUserCommand,
    ActivateUserCommandHandler,
    UserNotFoundError as ActivateNotFoundError,
)
from src.auth_bc.user.application.commands.assign_department import (
    AssignDepartmentCommand,
    AssignDepartmentCommandHandler,
    DepartmentInactiveError,
    DepartmentNotFoundError,
    UserNotFoundError as AssignNotFoundError,
)
from src.auth_bc.user.application.commands.change_user_role import (
    CannotAssignSuperAdminError,
    CannotChangeSelfError,
    ChangeUserRoleCommand,
    ChangeUserRoleCommandHandler,
    LastAdminError,
    UserNotFoundError as RoleNotFoundError,
)
from src.auth_bc.user.application.commands.deactivate_user import (
    CannotDeactivateSelfError,
    DeactivateUserCommand,
    DeactivateUserCommandHandler,
    UserNotFoundError as DeactivateNotFoundError,
)
from src.auth_bc.user.application.ports import DepartmentLookup
from src.auth_bc.user.application.queries.get_user_detail import (
    GetUserDetailQuery,
    GetUserDetailQueryHandler,
    UserNotFoundError as GetNotFoundError,
)
from src.auth_bc.user.application.queries.list_users import (
    ListUsersQuery,
    ListUsersQueryHandler,
)
from src.auth_bc.user.domain.entities import User
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.infrastructure.repository import (
    CompanyRepository,
)
from src.company_bc.department.infrastructure.repository import (
    DepartmentRepository,
)


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role.value,
        "company_id": user.company_id,
        "department_id": user.department_id,
        "is_active": user.is_active,
        "created_at": (
            user.created_at.isoformat()
            if user.created_at else None
        ),
        "updated_at": (
            user.updated_at.isoformat()
            if user.updated_at else None
        ),
    }


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data))]


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
    """Get tenant context, raising if not authenticated."""
    tenant = get_tenant()
    assert tenant is not None, "Unauthenticated tool call"
    return _AuthenticatedTenant(tenant)


# --- Tool handlers ---


async def handle_list_users(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        query = ListUsersQuery(
            company_id=tenant.company_id,
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
            role=arguments.get("role"),
            is_active=arguments.get("is_active"),
            department_id=arguments.get("department_id"),
            search=arguments.get("search"),
        )

        handler = ListUsersQueryHandler(user_repo)
        users, total = handler.handle(query)

        return _text({
            "items": [_serialize_user(u) for u in users],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_invite_user(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)
        company_repo = CompanyRepository(db)
        magic_link_repo = MagicLinkRepository(db)

        email = arguments["email"].lower().strip()

        # 1. Validate email domain against company
        company = company_repo.find_by_id(tenant.company_id)
        if not company:
            return _error("Company not found")
        domain = email.split("@", 1)[-1]
        if domain not in [
            d.lower() for d in company.email_domains
        ]:
            return _error(
                "Email domain is not allowed for this company"
            )

        # 2. Create or reactivate user
        existing_user = user_repo.find_by_email(email)
        if existing_user:
            if (
                existing_user.company_id != tenant.company_id
                or existing_user.role != UserRole.EMPLOYEE
            ):
                return _error(
                    "User with this email already exists"
                )
            if not existing_user.is_active:
                existing_user.activate()
                user_repo.save(existing_user)
        else:
            user_repo.save(
                User.create(
                    email=email,
                    role=UserRole.EMPLOYEE,
                    company_id=tenant.company_id,
                )
            )

        # 3. Send magic link
        lookup = CompanyLookupService(db)
        ml_handler = CreateMagicLinkCommandHandler(
            magic_link_repo=magic_link_repo,
            company_lookup=lookup,
            email_service=get_email_service(),
            user_repo=user_repo,
        )
        ml_handler.handle(CreateMagicLinkCommand(email=email))
        db.commit()

        return _text({
            "success": True,
            "message": "Invitation sent",
        })
    except InvalidEmailDomainError:
        db.rollback()
        return _error(
            "Email domain is not allowed for this company"
        )
    except CompanyRestrictedError:
        db.rollback()
        return _error(
            "Company access is currently restricted"
        )
    except RateLimitExceededError:
        db.rollback()
        return _error(
            "Too many requests. Please wait before "
            "requesting another invite."
        )
    except (ValueError, KeyError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_get_user(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        query = GetUserDetailQuery(
            user_id=arguments["user_id"],
            company_id=tenant.company_id,
        )

        handler = GetUserDetailQueryHandler(user_repo)
        user = handler.handle(query)
        return _text(_serialize_user(user))
    except GetNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_change_user_role(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        command = ChangeUserRoleCommand(
            user_id=arguments["user_id"],
            company_id=tenant.company_id,
            current_user_id=tenant.user_id,
            new_role=arguments["new_role"],
        )

        handler = ChangeUserRoleCommandHandler(
            user_repo, email_service=get_email_service(),
        )
        handler.handle(command)
        db.commit()

        # Re-fetch updated user
        get_handler = GetUserDetailQueryHandler(user_repo)
        user = get_handler.handle(
            GetUserDetailQuery(
                user_id=arguments["user_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_user(user))
    except (
        RoleNotFoundError,
        CannotChangeSelfError,
        CannotAssignSuperAdminError,
        LastAdminError,
    ) as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_activate_user(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        command = ActivateUserCommand(
            user_id=arguments["user_id"],
            company_id=tenant.company_id,
        )

        handler = ActivateUserCommandHandler(user_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch
        get_handler = GetUserDetailQueryHandler(user_repo)
        user = get_handler.handle(
            GetUserDetailQuery(
                user_id=arguments["user_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_user(user))
    except ActivateNotFoundError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_deactivate_user(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)

        command = DeactivateUserCommand(
            user_id=arguments["user_id"],
            company_id=tenant.company_id,
            current_user_id=tenant.user_id,
        )

        handler = DeactivateUserCommandHandler(user_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch
        get_handler = GetUserDetailQueryHandler(user_repo)
        user = get_handler.handle(
            GetUserDetailQuery(
                user_id=arguments["user_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_user(user))
    except (
        DeactivateNotFoundError,
        CannotDeactivateSelfError,
    ) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_assign_user_department(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        user_repo = UserRepository(db)
        dept_repo = DepartmentRepository(db)

        command = AssignDepartmentCommand(
            user_id=arguments["user_id"],
            company_id=tenant.company_id,
            department_id=arguments.get("department_id"),
        )

        handler = AssignDepartmentCommandHandler(
            user_repo, cast(DepartmentLookup, dept_repo),
        )
        handler.handle(command)
        db.commit()

        # Re-fetch
        get_handler = GetUserDetailQueryHandler(user_repo)
        user = get_handler.handle(
            GetUserDetailQuery(
                user_id=arguments["user_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_user(user))
    except (
        AssignNotFoundError,
        DepartmentNotFoundError,
        DepartmentInactiveError,
    ) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="list_users",
    description="List users with filtering and pagination.",
    input_schema={
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": "Page number (default 1)",
            },
            "page_size": {
                "type": "integer",
                "description": "Items per page (default 20)",
            },
            "role": {
                "type": "string",
                "description": (
                    "Filter by role: employee, technician, "
                    "admin"
                ),
            },
            "is_active": {
                "type": "boolean",
                "description": (
                    "Filter by active status"
                ),
            },
            "department_id": {
                "type": "string",
                "description": "Filter by department ID",
            },
            "search": {
                "type": "string",
                "description": (
                    "Search by email or name"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.ADMIN,
    handler=handle_list_users,
)

tool_registry.register(
    name="invite_user",
    description=(
        "Invite a new user by email. Creates the user "
        "as employee and sends a magic link invitation."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": (
                    "Email address to invite "
                    "(must match company domain)"
                ),
            },
        },
        "required": ["email"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_invite_user,
)

tool_registry.register(
    name="get_user",
    description="Get detailed information about a user.",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user ID",
            },
        },
        "required": ["user_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_get_user,
)

tool_registry.register(
    name="change_user_role",
    description=(
        "Change a user's role. Cannot change own role "
        "or assign super_admin."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user ID",
            },
            "new_role": {
                "type": "string",
                "description": (
                    "New role: employee, technician, admin"
                ),
            },
        },
        "required": ["user_id", "new_role"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_change_user_role,
)

tool_registry.register(
    name="activate_user",
    description="Activate a deactivated user account.",
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user ID to activate",
            },
        },
        "required": ["user_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_activate_user,
)

tool_registry.register(
    name="deactivate_user",
    description=(
        "Deactivate a user account. "
        "Cannot deactivate yourself."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": (
                    "The user ID to deactivate"
                ),
            },
        },
        "required": ["user_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_deactivate_user,
)

tool_registry.register(
    name="assign_user_department",
    description=(
        "Assign a user to a department, "
        "or remove from department (null department_id)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "The user ID",
            },
            "department_id": {
                "type": "string",
                "description": (
                    "Department ID to assign, "
                    "or omit to remove from department"
                ),
            },
        },
        "required": ["user_id"],
    },
    min_role=UserRole.ADMIN,
    handler=handle_assign_user_department,
)
