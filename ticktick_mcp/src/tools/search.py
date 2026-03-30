"""Search and date-filter tools for TickTick MCP."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from mcp.server.fastmcp import FastMCP

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.formatters import format_project_dict, format_task_dict

from ._deps import get_client


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_all_tasks() -> str:
        """Get all tasks from TickTick. Ignores closed projects."""
        return await _filter_tasks_across_projects(lambda _: True, "all")

    @mcp.tool()
    async def get_tasks_by_priority(priority_id: int) -> str:
        """Get all tasks by priority. Ignores closed projects.

        Args:
            priority_id: Priority of tasks {0: None, 1: Low, 3: Medium, 5: High}
        """
        from ticktick_mcp.src.models import PRIORITY_MAP

        if priority_id not in PRIORITY_MAP:
            raise ValidationError(f"Invalid priority. Valid: {list(PRIORITY_MAP.keys())}")

        label = PRIORITY_MAP[priority_id]
        return await _filter_tasks_across_projects(
            lambda t: t.get("priority", 0) == priority_id,
            f"priority '{label}'",
        )

    @mcp.tool()
    async def search_tasks(search_term: str) -> str:
        """Search for tasks by title, content, or subtask titles. Case-insensitive.

        Args:
            search_term: Text to search for
        """
        if not search_term.strip():
            raise ValidationError("Search term cannot be empty.")

        return await _filter_tasks_across_projects(
            lambda t: _task_matches_search(t, search_term),
            f"matching '{search_term}'",
        )

    @mcp.tool()
    async def get_tasks_due_today() -> str:
        """Get all tasks due today. Ignores closed projects."""
        return await _filter_tasks_across_projects(_is_due_today, "due today")

    @mcp.tool()
    async def get_tasks_due_tomorrow() -> str:
        """Get all tasks due tomorrow. Ignores closed projects."""
        return await _filter_tasks_across_projects(
            lambda t: _is_due_in_days(t, 1), "due tomorrow"
        )

    @mcp.tool()
    async def get_tasks_due_in_days(days: int) -> str:
        """Get all tasks due in exactly N days. Ignores closed projects.

        Args:
            days: Number of days from today (0 = today, 1 = tomorrow, etc.)
        """
        if days < 0:
            raise ValidationError("Days must be a non-negative integer.")

        desc = "today" if days == 0 else f"in {days} day{'s' if days != 1 else ''}"
        return await _filter_tasks_across_projects(
            lambda t: _is_due_in_days(t, days), f"due {desc}"
        )

    @mcp.tool()
    async def get_tasks_due_this_week() -> str:
        """Get all tasks due within the next 7 days. Ignores closed projects."""
        return await _filter_tasks_across_projects(_is_due_this_week, "due this week")

    @mcp.tool()
    async def get_overdue_tasks() -> str:
        """Get all overdue tasks. Ignores closed projects."""
        return await _filter_tasks_across_projects(_is_overdue, "overdue")

    @mcp.tool()
    async def get_tasks_by_date_range(start: str, end: str) -> str:
        """Get all tasks due within a date range. Ignores closed projects.

        Args:
            start: Start date in ISO format (YYYY-MM-DD)
            end: End date in ISO format (YYYY-MM-DD)
        """
        try:
            start_date = datetime.fromisoformat(start).date()
            end_date = datetime.fromisoformat(end).date()
        except ValueError as e:
            raise ValidationError("Dates must be in ISO format: YYYY-MM-DD") from e

        if start_date > end_date:
            raise ValidationError("Start date must be before or equal to end date.")

        def in_range(task: dict[str, Any]) -> bool:
            due = _parse_due_date(task)
            return due is not None and start_date <= due <= end_date

        return await _filter_tasks_across_projects(
            in_range, f"due between {start} and {end}"
        )


# ── Helpers ────────────────────────────────────────────────

def _parse_due_date(task: dict[str, Any]) -> datetime | None:
    """Parse dueDate field, returning date or None."""
    raw = task.get("dueDate")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%f%z").date()
    except (ValueError, TypeError):
        return None


def _is_due_today(task: dict[str, Any]) -> bool:
    due = _parse_due_date(task)
    return due is not None and due == datetime.now(timezone.utc).date()


def _is_overdue(task: dict[str, Any]) -> bool:
    raw = task.get("dueDate")
    if not raw:
        return False
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S.%f%z") < datetime.now(timezone.utc)
    except (ValueError, TypeError):
        return False


def _is_due_in_days(task: dict[str, Any], days: int) -> bool:
    due = _parse_due_date(task)
    target = (datetime.now(timezone.utc) + timedelta(days=days)).date()
    return due is not None and due == target


def _is_due_this_week(task: dict[str, Any]) -> bool:
    due = _parse_due_date(task)
    if due is None:
        return False
    today = datetime.now(timezone.utc).date()
    return today <= due <= today + timedelta(days=7)


def _task_matches_search(task: dict[str, Any], term: str) -> bool:
    term_lower = term.lower()
    if term_lower in task.get("title", "").lower():
        return True
    if term_lower in task.get("content", "").lower():
        return True
    return any(term_lower in item.get("title", "").lower() for item in task.get("items", []))


async def _filter_tasks_across_projects(
    filter_func: Callable[[dict[str, Any]], bool],
    filter_name: str,
) -> str:
    """Fetch all projects in parallel, apply filter to tasks."""
    client = get_client()
    projects = await client.get_projects()
    if not projects:
        return "No projects found."

    all_data = await client.get_all_project_data(projects)

    lines = [f"Found {len(all_data)} active projects:\n"]
    for project_data in all_data:
        project = project_data.get("project", {})
        tasks = project_data.get("tasks", [])
        filtered = [t for t in tasks if filter_func(t)]

        lines.append(f"Project:\n{format_project_dict(project)}")
        lines.append(f"{len(filtered)} tasks {filter_name}:")
        for i, task in enumerate(filtered, 1):
            lines.append(f"  Task {i}:\n{format_task_dict(task)}")
        lines.append("")

    return "\n".join(lines)
