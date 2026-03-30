"""Formatting helpers for TickTick API responses.

Converts domain models to human-readable strings for MCP tool output.
"""

from __future__ import annotations

import json
from typing import Any

from .models import BatchResult, Project, Task


def format_task(task: Task) -> str:
    """Format a Task model into a human-readable string."""
    lines = [
        f"ID: {task.id}",
        f"Title: {task.title}",
        f"Project ID: {task.project_id}",
    ]

    if task.start_date:
        lines.append(f"Start Date: {task.start_date}")
    if task.due_date:
        lines.append(f"Due Date: {task.due_date}")

    lines.append(f"Priority: {task.priority_label}")
    lines.append(f"Status: {'Completed' if task.is_complete else 'Active'}")

    if task.content:
        lines.append(f"\nContent:\n{task.content}")

    if task.items:
        lines.append(f"\nSubtasks ({len(task.items)}):")
        for i, item in enumerate(task.items, 1):
            mark = "v" if item.is_complete else " "
            lines.append(f"{i}. [{mark}] {item.title}")

    return "\n".join(lines)


def format_task_dict(data: dict[str, Any]) -> str:
    """Format a raw task dict (from API) into a human-readable string."""
    return format_task(Task.from_api(data))


def format_project(project: Project) -> str:
    """Format a Project model into a human-readable string."""
    lines = [
        f"Name: {project.name}",
        f"ID: {project.id}",
    ]

    if project.color:
        lines.append(f"Color: {project.color}")
    if project.view_mode:
        lines.append(f"View Mode: {project.view_mode}")
    if project.closed:
        lines.append("Closed: Yes")
    if project.kind:
        lines.append(f"Kind: {project.kind}")

    return "\n".join(lines)


def format_project_dict(data: dict[str, Any]) -> str:
    """Format a raw project dict (from API) into a human-readable string."""
    return format_project(Project.from_api(data))


def format_batch_result(result: BatchResult, operation: str) -> str:
    """Format a BatchResult into a human-readable summary."""
    lines = [
        f"Batch {operation} completed.",
        f"Succeeded: {result.success_count}",
        f"Failed: {result.failure_count}",
    ]

    if result.succeeded:
        lines.append(f"\nSuccessful ({result.success_count}):")
        for item in result.succeeded:
            title = item.get("title", item.get("id", "unknown"))
            task_id = item.get("id", "")
            lines.append(f"  - {title} (ID: {task_id})")

    if result.failed:
        lines.append(f"\nFailed ({result.failure_count}):")
        for item in result.failed:
            title = item.get("title", "unknown")
            error = item.get("error", "unknown error")
            lines.append(f"  - {title}: {error}")

    return "\n".join(lines)


def format_as_json(data: Any) -> str:
    """Format data as indented JSON string."""
    return json.dumps(data, indent=2, default=str)
