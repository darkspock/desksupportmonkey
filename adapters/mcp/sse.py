"""MCP SSE transport for production HTTP access."""
import logging

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from adapters.mcp.auth import (
    AuthenticationError,
    authenticate_bearer_token,
)
from adapters.mcp.server import create_mcp_server
from core.database import SessionLocal

logger = logging.getLogger(__name__)


def create_sse_app() -> Starlette:
    """Create a Starlette app for MCP SSE transport.

    Routes:
      GET /sse       — SSE connection (auth required)
      POST /messages — Client messages for active sessions
    """
    sse_transport = SseServerTransport("/messages")

    async def handle_sse(request: Request) -> None:
        """Handle SSE connection with auth."""
        auth_header = request.headers.get(
            "authorization", "",
        )
        if not auth_header.lower().startswith("bearer "):
            response = Response(
                "Authorization header required",
                status_code=401,
            )
            await response(
                request.scope, request.receive,
                request._send,
            )
            return

        token = auth_header[7:]  # Strip "Bearer "

        db = SessionLocal()
        try:
            authenticate_bearer_token(token, db)
            db.commit()
        except AuthenticationError as e:
            db.rollback()
            response = Response(
                str(e), status_code=401,
            )
            await response(
                request.scope, request.receive,
                request._send,
            )
            return
        finally:
            db.close()

        server = create_mcp_server()
        init_options = (
            server.create_initialization_options()
        )

        async with sse_transport.connect_sse(
            request.scope, request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream,
                init_options,
            )

    async def handle_messages(
        request: Request,
    ) -> None:
        """Forward POST messages to SSE transport."""
        await sse_transport.handle_post_message(
            request.scope, request.receive,
            request._send,
        )

    return Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route(
                "/messages",
                endpoint=handle_messages,
                methods=["POST"],
            ),
        ],
    )
