"""Task CRUD tools for TickTick MCP."""

from __future__ import annotations

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.formatters import format_task_dict
from ticktick_mcp.src.models import VALID_PRIORITIES

from ._deps import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_task(project_id: str, task_id: str) -> str:
        """Get details about a specific task.

        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        client = get_client()
        task = await client.get_task(project_id, task_id)
        return format_task_dict(task)

    @mcp.tool()
    async def get_project_tasks(project_id: str) -> str:
        """Get all tasks in a specific project.

        Args:
            project_id: ID of the project
        """
        client = get_client()
        project_data = await client.get_project_with_data(project_id)
        tasks = project_data.get("tasks", [])
        if not tasks:
            name = project_data.get("project", {}).get("name", project_id)
            return f"No tasks found in project '{name}'."

        name = project_data.get("project", {}).get("name", project_id)
        lines = [f"Found {len(tasks)} tasks in project '{name}':\n"]
        for i, task in enumerate(tasks, 1):
            lines.append(f"Task {i}:\n{format_task_dict(task)}\n")
        return "\n".join(lines)

    @mcp.tool()
    async def create_task(
        title: str,
        project_id: str,
        content: str | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        priority: int = 0,
    ) -> str:
        """Create a new task in TickTick.

        Args:
            title: Task title
            project_id: ID of the project to add the task to
            content: Task description/content (optional)
            start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High)
        """
        _validate_priority(priority)
        _validate_date(start_date, "start_date")
        _validate_date(due_date, "due_date")

        client = get_client()
        task = await client.create_task(
            title=title,
            project_id=project_id,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority,
        )
        return f"Task created successfully:\n\n{format_task_dict(task)}"

    @mcp.tool()
    async def update_task(
        task_id: str,
        project_id: str,
        title: str | None = None,
        content: str | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        priority: int | None = None,
    ) -> str:
        """Update an existing task in TickTick.

        Args:
            task_id: ID of the task to update
            project_id: ID of the project the task belongs to
            title: New task title (optional)
            content: New task description/content (optional)
            start_date: New start date in ISO format (optional)
            due_date: New due date in ISO format (optional)
            priority: New priority level (0: None, 1: Low, 3: Medium, 5: High) (optional)
        """
        if priority is not None:
            _validate_priority(priority)
        _validate_date(start_date, "start_date")
        _validate_date(due_date, "due_date")

        client = get_client()
        task = await client.update_task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority,
        )
        return f"Task updated successfully:\n\n{format_task_dict(task)}"

    @mcp.tool()
    async def complete_task(project_id: str, task_id: str) -> str:
        """Mark a task as complete.

        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        client = get_client()
        await client.complete_task(project_id, task_id)
        return f"Task {task_id} marked as complete."

    @mcp.tool()
    async def delete_task(project_id: str, task_id: str) -> str:
        """Delete a task.

        Args:
            project_id: ID of the project
            task_id: ID of the task
        """
        client = get_client()
        await client.delete_task(project_id, task_id)
        return f"Task {task_id} deleted successfully."

    @mcp.tool()
    async def move_task(task_id: str, from_project_id: str, to_project_id: str) -> str:
        """Move a task to a different project.

        Args:
            task_id: ID of the task to move
            from_project_id: ID of the current project
            to_project_id: ID of the destination project
        """
        client = get_client()
        task = await client.move_task(task_id, from_project_id, to_project_id)
        return f"Task moved successfully:\n\n{format_task_dict(task)}"


def _validate_priority(priority: int) -> None:
    if priority not in VALID_PRIORITIES:
        raise ValidationError(
            f"Invalid priority {priority}. Must be one of: {sorted(VALID_PRIORITIES)}"
        )


def _validate_date(date_str: str | None, field_name: str) -> None:
    if date_str is None:
        return
    try:
        datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValidationError(
            f"Invalid {field_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
        ) from e
