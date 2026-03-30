"""GTD (Getting Things Done) framework tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .search import _filter_tasks_across_projects, _is_due_in_days, _is_due_today, _is_overdue


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    async def get_engaged_tasks() -> str:
        """Get tasks that need immediate attention.

        Includes: high priority (5), due today, or overdue tasks.
        """

        def engaged_filter(task: dict[str, Any]) -> bool:
            return (
                task.get("priority", 0) == 5
                or _is_overdue(task)
                or _is_due_today(task)
            )

        return await _filter_tasks_across_projects(engaged_filter, "engaged")

    @mcp.tool()
    async def get_next_tasks() -> str:
        """Get tasks to work on next.

        Includes: medium priority (3) or due tomorrow.
        """

        def next_filter(task: dict[str, Any]) -> bool:
            return task.get("priority", 0) == 3 or _is_due_in_days(task, 1)

        return await _filter_tasks_across_projects(next_filter, "next")
