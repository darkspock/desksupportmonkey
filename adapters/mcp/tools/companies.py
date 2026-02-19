"""MCP tools for company management (5 tools)."""
import json
from typing import Any, cast

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.email import get_email_service
from core.tenant import TenantContext, get_tenant
from src.auth_bc.magic_link.infrastructure.repository import (
    MagicLinkRepository,
)
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import UserRepository
from src.company_bc.company.application.commands.create_company import (
    CompanyNameExistsError as CreateNameExistsError,
    CreateCompanyCommand,
    CreateCompanyCommandHandler,
    DomainAlreadyTakenError as CreateDomainTakenError,
    UserAlreadyExistsError,
)
from src.company_bc.company.application.commands.update_company import (
    CompanyNameExistsError as UpdateNameExistsError,
    CompanyNotFoundError as UpdateNotFoundError,
    DomainAlreadyTakenError as UpdateDomainTakenError,
    UpdateCompanyCommand,
    UpdateCompanyCommandHandler,
)
from src.company_bc.company.application.commands.update_company_status import (  # noqa: E501
    CompanyNotFoundError as StatusNotFoundError,
    UpdateCompanyStatusCommand,
    UpdateCompanyStatusCommandHandler,
)
from src.company_bc.company.application.ports import (
    MagicLinkWriter,
    UserWriter,
)
from src.company_bc.company.application.queries.get_company import (
    CompanyNotFoundError as GetNotFoundError,
    GetCompanyQuery,
    GetCompanyQueryHandler,
)
from src.company_bc.company.application.queries.list_companies import (
    ListCompaniesQuery,
    ListCompaniesQueryHandler,
)
from src.company_bc.company.domain.entities import (
    Company,
    InvalidStatusTransitionError,
)
from src.company_bc.company.infrastructure.repository import (
    CompanyRepository,
)


def _serialize_company(company: Company) -> dict[str, Any]:
    return {
        "id": company.id,
        "name": company.name,
        "status": company.status.value,
        "email_domains": company.email_domains,
        "is_active": company.is_active,
        "created_at": (
            company.created_at.isoformat()
            if company.created_at else None
        ),
        "updated_at": (
            company.updated_at.isoformat()
            if company.updated_at else None
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


async def handle_create_company(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        _require_tenant()
        company_repo = CompanyRepository(db)
        user_repo = UserRepository(db)
        magic_link_repo = MagicLinkRepository(db)

        command = CreateCompanyCommand(
            name=arguments["name"],
            email_domains=arguments["email_domains"],
            admin_email=arguments.get("admin_email"),
        )

        handler = CreateCompanyCommandHandler(
            company_repo,
            cast(UserWriter, user_repo),
            cast(MagicLinkWriter, magic_link_repo),
            get_email_service(),
        )
        handler.handle(command)
        db.commit()

        # Re-fetch by name to get timestamps
        company = company_repo.find_by_name(command.name)
        assert company is not None
        return _text(_serialize_company(company))
    except (
        CreateNameExistsError,
        CreateDomainTakenError,
        UserAlreadyExistsError,
    ) as e:
        db.rollback()
        return _error(str(e))
    except (ValueError, KeyError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_companies(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        _require_tenant()
        company_repo = CompanyRepository(db)

        query = ListCompaniesQuery(
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
            search=arguments.get("search"),
        )

        handler = ListCompaniesQueryHandler(company_repo)
        companies, total = handler.handle(query)

        return _text({
            "items": [
                _serialize_company(c) for c in companies
            ],
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_get_company(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        _require_tenant()
        company_repo = CompanyRepository(db)

        query = GetCompanyQuery(
            company_id=arguments["company_id"],
        )

        handler = GetCompanyQueryHandler(company_repo)
        detail = handler.handle(query)

        result = _serialize_company(detail.company)
        result["user_count"] = detail.user_count
        result["department_count"] = detail.department_count
        return _text(result)
    except GetNotFoundError as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_update_company(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        _require_tenant()
        company_repo = CompanyRepository(db)

        command = UpdateCompanyCommand(
            company_id=arguments["company_id"],
            name=arguments.get("name"),
            email_domains=arguments.get("email_domains"),
        )

        handler = UpdateCompanyCommandHandler(company_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch updated company
        get_handler = GetCompanyQueryHandler(company_repo)
        detail = get_handler.handle(
            GetCompanyQuery(
                company_id=arguments["company_id"],
            )
        )
        return _text(_serialize_company(detail.company))
    except (
        UpdateNotFoundError,
        UpdateNameExistsError,
        UpdateDomainTakenError,
    ) as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_change_company_status(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        _require_tenant()
        company_repo = CompanyRepository(db)

        command = UpdateCompanyStatusCommand(
            company_id=arguments["company_id"],
            new_status=arguments["new_status"],
        )

        handler = UpdateCompanyStatusCommandHandler(
            company_repo,
        )
        handler.handle(command)
        db.commit()

        # Re-fetch updated company
        get_handler = GetCompanyQueryHandler(company_repo)
        detail = get_handler.handle(
            GetCompanyQuery(
                company_id=arguments["company_id"],
            )
        )
        return _text(_serialize_company(detail.company))
    except StatusNotFoundError as e:
        db.rollback()
        return _error(str(e))
    except (
        InvalidStatusTransitionError,
        ValueError,
    ) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

tool_registry.register(
    name="create_company",
    description=(
        "Create a new company with email domains. "
        "Optionally create an initial admin user."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Company name",
            },
            "email_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Allowed email domains "
                    "(e.g. ['acme.com'])"
                ),
            },
            "admin_email": {
                "type": "string",
                "description": (
                    "Optional initial admin email "
                    "(sends magic link invite)"
                ),
            },
        },
        "required": ["name", "email_domains"],
    },
    min_role=UserRole.SUPER_ADMIN,
    handler=handle_create_company,
)

tool_registry.register(
    name="list_companies",
    description=(
        "List all companies with optional search "
        "and pagination."
    ),
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
            "search": {
                "type": "string",
                "description": "Search by company name",
            },
        },
        "required": [],
    },
    min_role=UserRole.SUPER_ADMIN,
    handler=handle_list_companies,
)

tool_registry.register(
    name="get_company",
    description=(
        "Get company details including user and "
        "department counts."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "company_id": {
                "type": "string",
                "description": "The company ID",
            },
        },
        "required": ["company_id"],
    },
    min_role=UserRole.SUPER_ADMIN,
    handler=handle_get_company,
)

tool_registry.register(
    name="update_company",
    description=(
        "Update company name and/or email domains."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "company_id": {
                "type": "string",
                "description": "The company ID to update",
            },
            "name": {
                "type": "string",
                "description": "New company name",
            },
            "email_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "New list of allowed email domains"
                ),
            },
        },
        "required": ["company_id"],
    },
    min_role=UserRole.SUPER_ADMIN,
    handler=handle_update_company,
)

_STATUS_DESC = (
    "Change a company's status. Valid transitions: "
    "active->suspended/deactivated, "
    "suspended->active/deactivated, "
    "deactivated->active."
)

tool_registry.register(
    name="change_company_status",
    description=_STATUS_DESC,
    input_schema={
        "type": "object",
        "properties": {
            "company_id": {
                "type": "string",
                "description": "The company ID",
            },
            "new_status": {
                "type": "string",
                "description": (
                    "Target status: active, "
                    "suspended, deactivated"
                ),
            },
        },
        "required": ["company_id", "new_status"],
    },
    min_role=UserRole.SUPER_ADMIN,
    handler=handle_change_company_status,
)
