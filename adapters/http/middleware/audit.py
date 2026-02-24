import logging
import re
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from core.database import SessionLocal
from core.jwt import JWTService
from src.audit_bc.audit.application.context import (
    audit_action_override,
    audit_changes,
)
from src.audit_bc.audit.application.services.audit_service import AuditService
from src.audit_bc.audit.infrastructure.repository import AuditRepository

logger = logging.getLogger(__name__)

_WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_EXCLUDED_PREFIXES = (
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/ws/",
    "/mcp/",
)

# Matches /api/v1/{resource} or /api/v1/{resource}/{id}/...
_PATH_RESOURCE_RE = re.compile(r"^/api/v1/([a-z_-]+)")
# Matches a ULID-shaped segment (26 alphanumeric chars)
_ULID_RE = re.compile(r"^[0-9A-Za-z]{26}$")

_METHOD_ACTION_MAP = {
    "POST": "created",
    "PUT": "updated",
    "PATCH": "updated",
    "DELETE": "deleted",
}

_jwt_service = JWTService()


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(  # type: ignore[override]
        self, request: Request, call_next
    ) -> Response:
        audit_changes.set(None)
        audit_action_override.set(None)

        response: Response = await call_next(request)

        if (
            request.method in _WRITE_METHODS
            and not self._is_excluded_path(request.url.path)
        ):
            try:
                self._record_audit(request, response)
            except Exception:
                logger.exception("Audit recording failed")

        return response

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _record_audit(self, request: Request, response: Response) -> None:
        path = request.url.path
        company_id, actor_id = self._extract_identity(request)

        action = self._derive_action(request)
        resource_type = self._extract_resource_type(path)
        resource_id = self._extract_resource_id(path)

        db = SessionLocal()
        try:
            actor_email = ""
            if actor_id:
                actor_email = self._resolve_email(db, actor_id)

            repo = AuditRepository(db)
            service = AuditService(repo)
            service.record(
                company_id=company_id,
                actor_id=actor_id,
                actor_email=actor_email,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                http_method=request.method,
                http_path=path,
                ip_address=(
                    request.client.host if request.client else None
                ),
                user_agent=request.headers.get("user-agent"),
                request_data=None,
                response_status=response.status_code,
                changes=audit_changes.get(),
            )
            db.commit()
        except Exception:
            db.rollback()
            logger.exception("Failed to save audit entry")
        finally:
            db.close()

    def _derive_action(self, request: Request) -> str:
        override = audit_action_override.get()
        if override:
            return override
        resource_type = self._extract_resource_type(request.url.path)
        method_suffix = _METHOD_ACTION_MAP.get(request.method, "action")
        # Check for sub-resource actions like /assets/{id}/move
        sub_action = self._extract_sub_action(request.url.path)
        if sub_action:
            return f"{resource_type}.{sub_action}"
        return f"{resource_type}.{method_suffix}"

    @staticmethod
    def _extract_resource_type(path: str) -> str:
        match = _PATH_RESOURCE_RE.match(path)
        if not match:
            return "unknown"
        raw = match.group(1)
        # Singularize common plurals
        if raw.endswith("ies"):
            return raw[:-3] + "y"
        if raw.endswith("ses"):
            return raw[:-2]
        if raw.endswith("s") and not raw.endswith("ss"):
            return raw[:-1]
        return raw

    @staticmethod
    def _extract_resource_id(path: str) -> Optional[str]:
        segments = path.strip("/").split("/")
        # Look for ULID-shaped segments after resource name
        for seg in segments[3:]:  # skip api/v1/resource
            if _ULID_RE.match(seg):
                return seg
        return None

    @staticmethod
    def _extract_sub_action(path: str) -> Optional[str]:
        """Extract trailing action segment like /move, /status, /assign."""
        segments = path.strip("/").split("/")
        if len(segments) >= 5:
            last = segments[-1]
            if not _ULID_RE.match(last) and last.isalpha():
                return last
        return None

    @staticmethod
    def _is_excluded_path(path: str) -> bool:
        return any(path.startswith(prefix) for prefix in _EXCLUDED_PREFIXES)

    @staticmethod
    def _extract_identity(
        request: Request,
    ) -> tuple[Optional[str], Optional[str]]:
        """Decode JWT from Authorization header to get company_id, user_id.

        This avoids relying on ContextVar (which is lost across threads
        in BaseHTTPMiddleware).
        """
        auth = request.headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None, None
        token = auth[7:]
        try:
            payload = _jwt_service.decode_token(token)
            user_id = payload.get("sub")
            company_id = payload.get("company_id")
            return company_id, user_id
        except Exception:
            return None, None

    @staticmethod
    def _resolve_email(db, user_id: str) -> str:  # type: ignore[no-untyped-def]
        from sqlalchemy import select
        from src.auth_bc.user.infrastructure.models import UserModel

        row = db.execute(
            select(UserModel.email).where(UserModel.id == user_id)
        ).scalar_one_or_none()
        return row or ""
