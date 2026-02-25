"""MCP tools for request management (10 tools)."""
import json
from typing import Any, cast

from mcp.types import TextContent

from adapters.mcp.registry import tool_registry
from core.database import SessionLocal
from core.tenant import TenantContext, get_tenant
from src.auth_bc.user.domain.enums import UserRole
from src.auth_bc.user.infrastructure.repository import (
    UserRepository,
)
from src.custom_field_bc.definition.application.services.enrichment_service import (
    CustomFieldEnrichmentService,
)
from src.custom_field_bc.definition.infrastructure.repository import (
    CustomFieldDefinitionRepository,
)
from src.request_bc.request.application.ports import (
    UserLookup,
)
from src.request_bc.request.application.commands.add_comment import (
    AddCommentCommand,
    AddCommentCommandHandler,
    RequestNotFoundError as CommentNotFoundError,
)
from src.request_bc.request.application.commands.add_note import (
    AddNoteCommand,
    AddNoteCommandHandler,
    RequestNotFoundError as NoteNotFoundError,
)
from src.request_bc.request.application.commands.assign_request import (
    AssignRequestCommand,
    AssignRequestCommandHandler,
    RequestNotFoundError as AssignNotFoundError,
    UserInactiveError,
    UserNotFoundError,
)
from src.request_bc.request.application.commands.change_request_priority import (  # noqa: E501
    ChangeRequestPriorityCommand,
    ChangeRequestPriorityCommandHandler,
    RequestNotFoundError as PriorityNotFoundError,
)
from src.request_bc.request.application.commands.change_request_status import (  # noqa: E501
    ChangeRequestStatusCommand,
    ChangeRequestStatusCommandHandler,
    RequestNotFoundError as StatusNotFoundError,
)
from src.request_bc.request.application.commands.create_request import (
    CreateRequestCommand,
    CreateRequestCommandHandler,
)
from src.request_bc.request.application.queries.get_request import (
    GetRequestQuery,
    GetRequestQueryHandler,
    RequestNotFoundError,
)
from src.request_bc.request.application.queries.list_comments import (
    ListCommentsQuery,
    ListCommentsQueryHandler,
    RequestNotFoundError as CommentsListNotFoundError,
)
from src.request_bc.request.application.queries.list_notes import (
    ListNotesQuery,
    ListNotesQueryHandler,
    RequestNotFoundError as NotesListNotFoundError,
)
from src.request_bc.request.application.queries.list_requests import (
    ListRequestsQuery,
    ListRequestsQueryHandler,
)
from src.request_bc.request.domain.entities import ServiceRequest
from src.request_bc.request.domain.enums import (
    InvalidStatusTransitionError,
)
from src.request_bc.request.infrastructure.repository import (
    RequestRepository,
)

# Each module defines its own RequestNotFoundError
_NOT_FOUND = (
    RequestNotFoundError,
    CommentNotFoundError,
    NoteNotFoundError,
    AssignNotFoundError,
    PriorityNotFoundError,
    StatusNotFoundError,
    CommentsListNotFoundError,
    NotesListNotFoundError,
)
_ASSIGN_ERRORS = _NOT_FOUND + (
    UserNotFoundError,
    UserInactiveError,
)


def _serialize_request(req: ServiceRequest) -> dict[str, Any]:
    resolved = (
        req.resolved_at.isoformat()
        if req.resolved_at else None
    )
    created = (
        req.created_at.isoformat()
        if req.created_at else None
    )
    updated = (
        req.updated_at.isoformat()
        if req.updated_at else None
    )
    return {
        "id": req.id,
        "company_id": req.company_id,
        "created_by": req.created_by,
        "type": req.type,
        "title": req.title,
        "description": req.description,
        "status": req.status.value,
        "priority": req.priority.value,
        "assigned_to": req.assigned_to,
        "resolved_at": resolved,
        "created_at": created,
        "updated_at": updated,
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


async def handle_create_request(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        command = CreateRequestCommand(
            company_id=tenant.company_id,
            created_by=tenant.user_id,
            type=arguments["type"],
            title=arguments["title"],
            description=arguments["description"],
            data=arguments.get("data"),
        )

        handler = CreateRequestCommandHandler(request_repo)
        handler.handle(command)
        db.commit()

        # Re-fetch most recent request to get timestamps
        requests, _ = request_repo.find_all(
            company_id=tenant.company_id,
            page=1,
            page_size=1,
        )
        if requests:
            return _text(_serialize_request(requests[0]))
        return _text({"success": True})
    except (ValueError, KeyError) as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_requests(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        query = ListRequestsQuery(
            company_id=tenant.company_id,
            page=arguments.get("page", 1),
            page_size=arguments.get("page_size", 20),
            search=arguments.get("search"),
            status=arguments.get("status"),
            type=arguments.get("type"),
            priority=arguments.get("priority"),
            assigned_to=arguments.get("assigned_to"),
        )

        handler = ListRequestsQueryHandler(request_repo)
        requests, total = handler.handle(query)

        cf_repo = CustomFieldDefinitionRepository(db)
        cf_enricher = CustomFieldEnrichmentService(cf_repo)
        enriched_batch = cf_enricher.enrich_batch(
            tenant.company_id,
            "request",
            [r.custom_fields_data or {} for r in requests],
        )

        items = []
        for req, enriched_cf in zip(requests, enriched_batch):
            item = _serialize_request(req)
            if enriched_cf:
                item["custom_fields"] = enriched_cf
            items.append(item)

        return _text({
            "items": items,
            "total": total,
            "page": query.page,
            "page_size": query.page_size,
        })
    finally:
        db.close()


async def handle_get_request(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        query = GetRequestQuery(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
        )

        handler = GetRequestQueryHandler(request_repo)
        detail = handler.handle(query)

        # Employees can only see their own requests
        user_role = UserRole(tenant.role)
        if (
            user_role == UserRole.EMPLOYEE
            and detail.request.created_by != tenant.user_id
        ):
            return _error("Request not found")

        result = _serialize_request(detail.request)
        result["comment_count"] = detail.comment_count

        cf_repo = CustomFieldDefinitionRepository(db)
        cf_enricher = CustomFieldEnrichmentService(cf_repo)
        custom_fields = cf_enricher.enrich(
            tenant.company_id,
            "request",
            detail.request.custom_fields_data or {},
        )
        if custom_fields:
            result["custom_fields"] = custom_fields

        return _text(result)
    except _NOT_FOUND as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_change_request_status(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        cmd = ChangeRequestStatusCommand(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
            new_status=arguments["new_status"],
            performed_by=tenant.user_id,
        )

        handler = ChangeRequestStatusCommandHandler(
            request_repo,
        )
        handler.handle(cmd)
        db.commit()

        get_handler = GetRequestQueryHandler(request_repo)
        detail = get_handler.handle(
            GetRequestQuery(
                request_id=arguments["request_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_request(detail.request))
    except _NOT_FOUND as e:
        db.rollback()
        return _error(str(e))
    except InvalidStatusTransitionError as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_change_request_priority(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        cmd = ChangeRequestPriorityCommand(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
            new_priority=arguments["new_priority"],
            performed_by=tenant.user_id,
        )

        handler = ChangeRequestPriorityCommandHandler(
            request_repo,
        )
        handler.handle(cmd)
        db.commit()

        get_handler = GetRequestQueryHandler(request_repo)
        detail = get_handler.handle(
            GetRequestQuery(
                request_id=arguments["request_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_request(detail.request))
    except _NOT_FOUND as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_assign_request(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)
        user_repo = UserRepository(db)

        command = AssignRequestCommand(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
            user_id=arguments["user_id"],
            performed_by=tenant.user_id,
        )

        handler = AssignRequestCommandHandler(
            request_repo, cast(UserLookup, user_repo),
        )
        handler.handle(command)
        db.commit()

        get_handler = GetRequestQueryHandler(request_repo)
        detail = get_handler.handle(
            GetRequestQuery(
                request_id=arguments["request_id"],
                company_id=tenant.company_id,
            )
        )
        return _text(_serialize_request(detail.request))
    except _ASSIGN_ERRORS as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_add_comment(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        command = AddCommentCommand(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
            author_id=tenant.user_id,
            body=arguments["body"],
        )

        handler = AddCommentCommandHandler(request_repo)
        handler.handle(command)
        db.commit()

        return _text({"success": True})
    except _NOT_FOUND as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_comments(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        query = ListCommentsQuery(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
        )

        handler = ListCommentsQueryHandler(request_repo)
        comments = handler.handle(query)

        return _text([
            {
                "id": c.id,
                "author_id": c.author_id,
                "body": c.body,
                "created_at": (
                    c.created_at.isoformat()
                    if c.created_at else None
                ),
            }
            for c in comments
        ])
    except _NOT_FOUND as e:
        return _error(str(e))
    finally:
        db.close()


async def handle_add_note(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        command = AddNoteCommand(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
            author_id=tenant.user_id,
            body=arguments["body"],
        )

        handler = AddNoteCommandHandler(request_repo)
        handler.handle(command)
        db.commit()

        return _text({"success": True})
    except _NOT_FOUND as e:
        db.rollback()
        return _error(str(e))
    except ValueError as e:
        db.rollback()
        return _error(str(e))
    finally:
        db.close()


async def handle_list_notes(
    arguments: dict,
) -> list[TextContent]:
    db = SessionLocal()
    try:
        tenant = _require_tenant()
        request_repo = RequestRepository(db)

        query = ListNotesQuery(
            request_id=arguments["request_id"],
            company_id=tenant.company_id,
        )

        handler = ListNotesQueryHandler(request_repo)
        notes = handler.handle(query)

        return _text([
            {
                "id": n.id,
                "author_id": n.author_id,
                "body": n.body,
                "created_at": (
                    n.created_at.isoformat()
                    if n.created_at else None
                ),
            }
            for n in notes
        ])
    except _NOT_FOUND as e:
        return _error(str(e))
    finally:
        db.close()


# --- Tool Registration ---

_CREATE_DESC = (
    "Create a new support request "
    "(incident, new_equipment, or onboarding)."
)

tool_registry.register(
    name="create_request",
    description=_CREATE_DESC,
    input_schema={
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": (
                    "Request type: incident, "
                    "new_equipment, or onboarding"
                ),
            },
            "title": {
                "type": "string",
                "description": "Request title",
            },
            "description": {
                "type": "string",
                "description": (
                    "Detailed description of the request"
                ),
            },
            "data": {
                "type": "object",
                "description": (
                    "Optional additional data"
                ),
            },
        },
        "required": ["type", "title", "description"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_create_request,
)

tool_registry.register(
    name="list_requests",
    description=(
        "List support requests with filtering "
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
                "description": (
                    "Search in title and description"
                ),
            },
            "status": {
                "type": "string",
                "description": (
                    "Filter by status: submitted, "
                    "in_review, in_progress, "
                    "resolved, rejected"
                ),
            },
            "type": {
                "type": "string",
                "description": (
                    "Filter by type: incident, "
                    "new_equipment, onboarding"
                ),
            },
            "priority": {
                "type": "string",
                "description": (
                    "Filter by priority: "
                    "low, medium, high, urgent"
                ),
            },
            "assigned_to": {
                "type": "string",
                "description": (
                    "Filter by assigned user ID"
                ),
            },
        },
        "required": [],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_list_requests,
)

tool_registry.register(
    name="get_request",
    description=(
        "Get detailed info about a request. "
        "Employees can only view their own."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
        },
        "required": ["request_id"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_get_request,
)

_STATUS_DESC = (
    "Change a request's status. Transitions: "
    "submitted->in_review, "
    "in_review->in_progress/rejected, "
    "in_progress->resolved/in_review."
)

tool_registry.register(
    name="change_request_status",
    description=_STATUS_DESC,
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
            "new_status": {
                "type": "string",
                "description": (
                    "Target status: submitted, "
                    "in_review, in_progress, "
                    "resolved, rejected"
                ),
            },
        },
        "required": ["request_id", "new_status"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_change_request_status,
)

tool_registry.register(
    name="change_request_priority",
    description="Change a request's priority level.",
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
            "new_priority": {
                "type": "string",
                "description": (
                    "New priority: "
                    "low, medium, high, urgent"
                ),
            },
        },
        "required": ["request_id", "new_priority"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_change_request_priority,
)

tool_registry.register(
    name="assign_request",
    description=(
        "Assign a request to a technician "
        "or admin user."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
            "user_id": {
                "type": "string",
                "description": (
                    "The user ID to assign to"
                ),
            },
        },
        "required": ["request_id", "user_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_assign_request,
)

tool_registry.register(
    name="add_comment",
    description=(
        "Add a public comment to a request "
        "(visible to all parties)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
            "body": {
                "type": "string",
                "description": "Comment text",
            },
        },
        "required": ["request_id", "body"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_add_comment,
)

tool_registry.register(
    name="list_comments",
    description="List all comments on a request.",
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
        },
        "required": ["request_id"],
    },
    min_role=UserRole.EMPLOYEE,
    handler=handle_list_comments,
)

_NOTE_DESC = (
    "Add an internal note to a request "
    "(only visible to technicians/admins)."
)

tool_registry.register(
    name="add_note",
    description=_NOTE_DESC,
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
            "body": {
                "type": "string",
                "description": "Note text",
            },
        },
        "required": ["request_id", "body"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_add_note,
)

tool_registry.register(
    name="list_notes",
    description=(
        "List internal notes on a request "
        "(technicians/admins only)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "request_id": {
                "type": "string",
                "description": "The request ID",
            },
        },
        "required": ["request_id"],
    },
    min_role=UserRole.TECHNICIAN,
    handler=handle_list_notes,
)
