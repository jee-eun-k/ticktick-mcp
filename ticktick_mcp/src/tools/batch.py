"""Batch operation tools for TickTick MCP."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.formatters import format_batch_result
from ticktick_mcp.src.models import VALID_PRIORITIES, BatchResult

from ._deps import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def batch_create_tasks(tasks: list[dict[str, Any]]) -> str:
        """Create multiple tasks at once.

        Args:
            tasks: List of task dicts, each with:
                - title (required): Task name
                - project_id (required): Project ID
                - content (optional): Description
                - start_date (optional): ISO date
                - due_date (optional): ISO date
                - priority (optional): 0/1/3/5
        """
        if not tasks:
            raise ValidationError("No tasks provided.")

        _validate_batch_tasks(tasks)

        client = get_client()
        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for task_data in tasks:
            try:
                result = await client.create_task(
                    title=task_data["title"],
                    project_id=task_data["project_id"],
                    content=task_data.get("content"),
                    start_date=task_data.get("start_date"),
                    due_date=task_data.get("due_date"),
                    priority=task_data.get("priority", 0),
                )
                succeeded.append(result)
            except Exception as e:
                failed.append({"title": task_data.get("title", "?"), "error": str(e)})

        return format_batch_result(
            BatchResult(succeeded=tuple(succeeded), failed=tuple(failed)),
            "create",
        )

    @mcp.tool()
    async def batch_complete_tasks(
        tasks: list[dict[str, str]],
    ) -> str:
        """Complete multiple tasks at once.

        Args:
            tasks: List of dicts with project_id and task_id
        """
        if not tasks:
            raise ValidationError("No tasks provided.")

        client = get_client()
        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for item in tasks:
            pid = item.get("project_id", "")
            tid = item.get("task_id", "")
            if not pid or not tid:
                failed.append({"title": tid, "error": "Missing project_id or task_id"})
                continue
            try:
                await client.complete_task(pid, tid)
                succeeded.append({"id": tid, "title": f"task {tid}"})
            except Exception as e:
                failed.append({"title": tid, "error": str(e)})

        return format_batch_result(
            BatchResult(succeeded=tuple(succeeded), failed=tuple(failed)),
            "complete",
        )

    @mcp.tool()
    async def batch_delete_tasks(
        tasks: list[dict[str, str]],
    ) -> str:
        """Delete multiple tasks at once.

        Args:
            tasks: List of dicts with project_id and task_id
        """
        if not tasks:
            raise ValidationError("No tasks provided.")

        client = get_client()
        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for item in tasks:
            pid = item.get("project_id", "")
            tid = item.get("task_id", "")
            if not pid or not tid:
                failed.append({"title": tid, "error": "Missing project_id or task_id"})
                continue
            try:
                await client.delete_task(pid, tid)
                succeeded.append({"id": tid, "title": f"task {tid}"})
            except Exception as e:
                failed.append({"title": tid, "error": str(e)})

        return format_batch_result(
            BatchResult(succeeded=tuple(succeeded), failed=tuple(failed)),
            "delete",
        )

    @mcp.tool()
    async def batch_update_tasks(
        tasks: list[dict[str, Any]],
    ) -> str:
        """Update multiple tasks at once.

        Args:
            tasks: List of dicts with task_id, project_id, and optional fields:
                title, content, priority, start_date, due_date
        """
        if not tasks:
            raise ValidationError("No tasks provided.")

        client = get_client()
        succeeded: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []

        for item in tasks:
            tid = item.get("task_id", "")
            pid = item.get("project_id", "")
            if not tid or not pid:
                failed.append({"title": tid, "error": "Missing task_id or project_id"})
                continue
            try:
                result = await client.update_task(
                    task_id=tid,
                    project_id=pid,
                    title=item.get("title"),
                    content=item.get("content"),
                    priority=item.get("priority"),
                    start_date=item.get("start_date"),
                    due_date=item.get("due_date"),
                )
                succeeded.append(result)
            except Exception as e:
                failed.append({"title": tid, "error": str(e)})

        return format_batch_result(
            BatchResult(succeeded=tuple(succeeded), failed=tuple(failed)),
            "update",
        )


def _validate_batch_tasks(tasks: list[dict[str, Any]]) -> None:
    """Validate batch task data before processing."""
    errors: list[str] = []
    for i, task_data in enumerate(tasks):
        if not isinstance(task_data, dict):
            errors.append(f"Task {i + 1}: Must be a dictionary")
            continue
        if not task_data.get("title"):
            errors.append(f"Task {i + 1}: 'title' is required")
        if not task_data.get("project_id"):
            errors.append(f"Task {i + 1}: 'project_id' is required")
        priority = task_data.get("priority")
        if priority is not None and priority not in VALID_PRIORITIES:
            errors.append(f"Task {i + 1}: Invalid priority {priority}")

    if errors:
        raise ValidationError("Validation errors:\n" + "\n".join(errors))
