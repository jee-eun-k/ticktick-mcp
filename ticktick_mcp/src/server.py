"""TickTick MCP server — thin entry point."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import FastMCP

from .client import TickTickClient
from .config import TickTickConfig
from .errors import ClientNotInitializedError, TickTickError
from .tools import register_all_tools
from .tools._deps import set_client

logger = logging.getLogger(__name__)

mcp = FastMCP("ticktick")
register_all_tools(mcp)


async def _initialize_client() -> None:
    """Load config and initialize the async TickTick client."""
    config = TickTickConfig.from_env()
    if not config.is_authenticated:
        raise ClientNotInitializedError()

    client = TickTickClient(config=config)
    set_client(client)

    # Verify connectivity
    projects = await client.get_projects()
    logger.info("Connected to TickTick API with %d projects", len(projects))


def main() -> None:
    """Main entry point for the MCP server."""
    import asyncio

    async def _startup() -> None:
        await _initialize_client()

    try:
        asyncio.get_event_loop().run_until_complete(_startup())
    except TickTickError as e:
        logger.error("Failed to initialize: %s", e)
        return

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
