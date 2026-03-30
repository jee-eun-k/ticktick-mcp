"""Tool registration for TickTick MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import batch, gtd, projects, search, subtasks, tasks


def register_all_tools(mcp: FastMCP) -> None:
    """Register all tool modules with the MCP server."""
    tasks.register(mcp)
    projects.register(mcp)
    search.register(mcp)
    batch.register(mcp)
    subtasks.register(mcp)
    gtd.register(mcp)
