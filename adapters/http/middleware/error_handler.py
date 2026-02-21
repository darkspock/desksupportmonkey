import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Register exception handlers on the FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": _status_to_code(exc.status_code),
                    "message": exc.detail,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": _format_validation_message(errors),
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s\n%s", str(exc), traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred.",
                }
            },
        )


def _status_to_code(status_code: int) -> str:
    """Map HTTP status codes to error code strings."""
    codes = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "TOO_MANY_REQUESTS",
    }
    return codes.get(status_code, f"HTTP_{status_code}")


def _format_validation_message(errors: list[dict[str, Any]]) -> str:
    """Return a concise message from FastAPI/Pydantic validation errors."""
    if not errors:
        return "Validation error"

    first = errors[0]
    msg = first.get("msg")
    if not isinstance(msg, str) or not msg.strip():
        return "Validation error"

    loc = first.get("loc")
    if isinstance(loc, tuple):
        parts = [str(p) for p in loc if p not in ("body", "query", "path")]
        if parts:
            return f"{'.'.join(parts)}: {msg}"
    return msg
