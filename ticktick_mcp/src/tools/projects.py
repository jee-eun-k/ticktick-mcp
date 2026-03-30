"""Project CRUD tools for TickTick MCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.formatters import format_project_dict
from ticktick_mcp.src.models import VALID_VIEW_MODES

from ._deps import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_projects() -> str:
        """Get all projects from TickTick."""
        client = get_client()
        projects = await client.get_projects()
        if not projects:
            return "No projects found."

        lines = [f"Found {len(projects)} projects:\n"]
        for i, project in enumerate(projects, 1):
            lines.append(f"Project {i}:\n{format_project_dict(project)}\n")
        return "\n".join(lines)

    @mcp.tool()
    async def get_project(project_id: str) -> str:
        """Get details about a specific project.

        Args:
            project_id: ID of the project
        """
        client = get_client()
        project = await client.get_project(project_id)
        return format_project_dict(project)

    @mcp.tool()
    async def create_project(
        name: str,
        color: str = "#F18181",
        view_mode: str = "list",
    ) -> str:
        """Create a new project in TickTick.

        Args:
            name: Project name
            color: Color code (hex format)
            view_mode: View mode - one of list, kanban, or timeline
        """
        if view_mode not in VALID_VIEW_MODES:
            raise ValidationError(
                f"Invalid view_mode '{view_mode}'. Must be one of: {sorted(VALID_VIEW_MODES)}"
            )

        client = get_client()
        project = await client.create_project(name=name, color=color, view_mode=view_mode)
        return f"Project created successfully:\n\n{format_project_dict(project)}"

    @mcp.tool()
    async def update_project(
        project_id: str,
        name: str | None = None,
        color: str | None = None,
        view_mode: str | None = None,
    ) -> str:
        """Update an existing project in TickTick.

        Args:
            project_id: ID of the project to update
            name: New project name (optional)
            color: New color code in hex format (optional)
            view_mode: New view mode - list, kanban, or timeline (optional)
        """
        if view_mode is not None and view_mode not in VALID_VIEW_MODES:
            raise ValidationError(
                f"Invalid view_mode '{view_mode}'. Must be one of: {sorted(VALID_VIEW_MODES)}"
            )

        client = get_client()
        project = await client.update_project(
            project_id, name=name, color=color, view_mode=view_mode
        )
        return f"Project updated successfully:\n\n{format_project_dict(project)}"

    @mcp.tool()
    async def delete_project(project_id: str) -> str:
        """Delete a project.

        Args:
            project_id: ID of the project
        """
        client = get_client()
        await client.delete_project(project_id)
        return f"Project {project_id} deleted successfully."
