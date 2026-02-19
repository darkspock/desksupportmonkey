"""Entry point for MCP server: python -m adapters.mcp --transport stdio"""
import asyncio
import logging
import sys
from argparse import ArgumentParser

from core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = ArgumentParser(description="DeskSupportMonkey MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default=settings.mcp.MCP_TRANSPORT,
        help="Transport protocol (default: stdio)",
    )
    args = parser.parse_args()

    if not settings.mcp.MCP_ENABLED:
        logger.error(
            "MCP server is disabled. Set MCP_ENABLED=true in .env to enable."
        )
        sys.exit(1)

    logger.info("Starting MCP server with transport: %s", args.transport)

    if args.transport == "stdio":
        from adapters.mcp.server import run_stdio_server
        asyncio.run(run_stdio_server())
    elif args.transport == "sse":
        logger.error("SSE transport not yet implemented (see F6)")
        sys.exit(1)


if __name__ == "__main__":
    main()
