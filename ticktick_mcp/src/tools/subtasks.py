"""Subtask tools for TickTick MCP."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.formatters import format_task_dict
from ticktick_mcp.src.models import VALID_PRIORITIES

from ._deps import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def create_subtask(
        subtask_title: str,
        parent_task_id: str,
        project_id: str,
        content: str | None = None,
        priority: int = 0,
    ) -> str:
        """Create a subtask for a parent task.

        Args:
            subtask_title: Title of the subtask
            parent_task_id: ID of the parent task
            project_id: ID of the project (must be same as parent)
            content: Optional description
            priority: Priority level (0: None, 1: Low, 3: Medium, 5: High)
        """
        if priority not in VALID_PRIORITIES:
            raise ValidationError(
                f"Invalid priority {priority}. Must be one of: {sorted(VALID_PRIORITIES)}"
            )

        client = get_client()
        subtask = await client.create_task(
            title=subtask_title,
            project_id=project_id,
            content=content,
            priority=priority,
            parent_id=parent_task_id,
        )
        return f"Subtask created successfully:\n\n{format_task_dict(subtask)}"

    @mcp.tool()
    async def list_subtasks(project_id: str, parent_task_id: str) -> str:
        """List all subtasks of a parent task.

        Args:
            project_id: ID of the project
            parent_task_id: ID of the parent task
        """
        client = get_client()
        task = await client.get_task(project_id, parent_task_id)
        items = task.get("items", [])

        if not items:
            return f"No subtasks found for task '{task.get('title', parent_task_id)}'."

        lines = [f"Subtasks for '{task.get('title', parent_task_id)}' ({len(items)}):"]
        for i, item in enumerate(items, 1):
            mark = "v" if item.get("status") == 1 else " "
            item_title = item.get("title", "No title")
            item_id = item.get("id", "")
            lines.append(f"  {i}. [{mark}] {item_title} (ID: {item_id})")
        return "\n".join(lines)

    @mcp.tool()
    async def update_subtask(
        task_id: str,
        project_id: str,
        subtask_id: str,
        title: str | None = None,
        status: int | None = None,
    ) -> str:
        """Update a subtask's title or status.

        Args:
            task_id: ID of the parent task
            project_id: ID of the project
            subtask_id: ID of the subtask/checklist item to update
            title: New title (optional)
            status: New status: 0=incomplete, 1=complete (optional)
        """
        client = get_client()
        task = await client.get_task(project_id, task_id)
        items = list(task.get("items", []))

        updated = False
        for item in items:
            if item.get("id") == subtask_id:
                if title is not None:
                    item["title"] = title
                if status is not None:
                    item["status"] = status
                updated = True
                break

        if not updated:
            raise ValidationError(f"Subtask '{subtask_id}' not found in task '{task_id}'.")

        result = await client.update_task(
            task_id=task_id,
            project_id=project_id,
            items=items,
        )
        return f"Subtask updated successfully:\n\n{format_task_dict(result)}"

    @mcp.tool()
    async def complete_subtask(
        task_id: str,
        project_id: str,
        subtask_id: str,
    ) -> str:
        """Mark a subtask as complete.

        Args:
            task_id: ID of the parent task
            project_id: ID of the project
            subtask_id: ID of the subtask to complete
        """
        client = get_client()
        task = await client.get_task(project_id, task_id)
        items = list(task.get("items", []))

        found = False
        for item in items:
            if item.get("id") == subtask_id:
                item["status"] = 1
                found = True
                break

        if not found:
            raise ValidationError(f"Subtask '{subtask_id}' not found in task '{task_id}'.")

        await client.update_task(task_id=task_id, project_id=project_id, items=items)
        return f"Subtask '{subtask_id}' marked as complete."

    @mcp.tool()
    async def delete_subtask(
        task_id: str,
        project_id: str,
        subtask_id: str,
    ) -> str:
        """Remove a subtask from a task.

        Args:
            task_id: ID of the parent task
            project_id: ID of the project
            subtask_id: ID of the subtask to delete
        """
        client = get_client()
        task = await client.get_task(project_id, task_id)
        items = [i for i in task.get("items", []) if i.get("id") != subtask_id]

        if len(items) == len(task.get("items", [])):
            raise ValidationError(f"Subtask '{subtask_id}' not found in task '{task_id}'.")

        await client.update_task(task_id=task_id, project_id=project_id, items=items)
        return f"Subtask '{subtask_id}' deleted successfully."
