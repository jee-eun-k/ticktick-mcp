"""Domain models for TickTick MCP server."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PRIORITY_MAP: dict[int, str] = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
VALID_PRIORITIES: frozenset[int] = frozenset(PRIORITY_MAP.keys())
VALID_VIEW_MODES: frozenset[str] = frozenset({"list", "kanban", "timeline"})


@dataclass(frozen=True)
class ChecklistItem:
    """A subtask / checklist item within a task."""

    id: str
    title: str
    status: int = 0  # 0 = incomplete, 1 = complete

    @property
    def is_complete(self) -> bool:
        return self.status == 1

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> ChecklistItem:
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            status=data.get("status", 0),
        )


@dataclass(frozen=True)
class Task:
    """Represents a TickTick task."""

    id: str
    title: str
    project_id: str
    status: int = 0  # 0 = active, 2 = completed
    priority: int = 0
    content: str = ""
    start_date: str | None = None
    due_date: str | None = None
    parent_id: str | None = None
    items: tuple[ChecklistItem, ...] = field(default_factory=tuple)

    @property
    def is_complete(self) -> bool:
        return self.status == 2

    @property
    def priority_label(self) -> str:
        return PRIORITY_MAP.get(self.priority, str(self.priority))

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Task:
        items = tuple(
            ChecklistItem.from_api(item) for item in data.get("items", [])
        )
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            project_id=data.get("projectId", ""),
            status=data.get("status", 0),
            priority=data.get("priority", 0),
            content=data.get("content", ""),
            start_date=data.get("startDate"),
            due_date=data.get("dueDate"),
            parent_id=data.get("parentId"),
            items=items,
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "title": self.title,
            "project_id": self.project_id,
            "status": "completed" if self.is_complete else "active",
            "priority": self.priority_label,
        }
        if self.content:
            result["content"] = self.content
        if self.start_date:
            result["start_date"] = self.start_date
        if self.due_date:
            result["due_date"] = self.due_date
        if self.parent_id:
            result["parent_id"] = self.parent_id
        if self.items:
            result["subtasks"] = [
                {"title": item.title, "complete": item.is_complete}
                for item in self.items
            ]
        return result


@dataclass(frozen=True)
class Project:
    """Represents a TickTick project."""

    id: str
    name: str
    color: str = ""
    view_mode: str = ""
    closed: bool = False
    kind: str = ""

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Project:
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            color=data.get("color", ""),
            view_mode=data.get("viewMode", ""),
            closed=data.get("closed", False),
            kind=data.get("kind", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
        }
        if self.color:
            result["color"] = self.color
        if self.view_mode:
            result["view_mode"] = self.view_mode
        if self.closed:
            result["closed"] = True
        if self.kind:
            result["kind"] = self.kind
        return result


@dataclass(frozen=True)
class BatchResult:
    """Result of a batch operation."""

    succeeded: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    failed: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def success_count(self) -> int:
        return len(self.succeeded)

    @property
    def failure_count(self) -> int:
        return len(self.failed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "succeeded": list(self.succeeded),
            "failed": list(self.failed),
        }
