"""Tests for formatters module."""

from ticktick_mcp.src.formatters import (
    format_batch_result,
    format_project,
    format_project_dict,
    format_task,
    format_task_dict,
)
from ticktick_mcp.src.models import BatchResult, ChecklistItem, Project, Task


class TestFormatTask:
    def test_minimal_task(self):
        task = Task(id="t1", title="Simple task", project_id="p1")
        result = format_task(task)
        assert "ID: t1" in result
        assert "Title: Simple task" in result
        assert "Priority: None" in result
        assert "Status: Active" in result
        assert "Subtasks" not in result

    def test_full_task(self):
        task = Task(
            id="t2",
            title="Full task",
            project_id="p1",
            priority=5,
            status=2,
            content="Some notes",
            start_date="2026-03-16T09:00:00.000+0000",
            due_date="2026-03-17T09:00:00.000+0000",
            items=(
                ChecklistItem(id="c1", title="Sub 1", status=1),
                ChecklistItem(id="c2", title="Sub 2", status=0),
            ),
        )
        result = format_task(task)
        assert "Priority: High" in result
        assert "Status: Completed" in result
        assert "Start Date:" in result
        assert "Due Date:" in result
        assert "Content:\nSome notes" in result
        assert "Subtasks (2):" in result
        assert "[v] Sub 1" in result
        assert "[ ] Sub 2" in result

    def test_format_task_dict(self):
        data = {"id": "t3", "title": "From dict", "projectId": "p1", "priority": 3}
        result = format_task_dict(data)
        assert "Title: From dict" in result
        assert "Priority: Medium" in result


class TestFormatProject:
    def test_minimal_project(self):
        project = Project(id="p1", name="Work")
        result = format_project(project)
        assert "Name: Work" in result
        assert "ID: p1" in result
        assert "Closed" not in result

    def test_full_project(self):
        project = Project(
            id="p2",
            name="Personal",
            color="#00FF00",
            view_mode="kanban",
            closed=True,
            kind="TASK",
        )
        result = format_project(project)
        assert "Color: #00FF00" in result
        assert "View Mode: kanban" in result
        assert "Closed: Yes" in result
        assert "Kind: TASK" in result

    def test_format_project_dict(self):
        data = {"id": "p3", "name": "From dict", "color": "#ABCDEF"}
        result = format_project_dict(data)
        assert "Name: From dict" in result
        assert "Color: #ABCDEF" in result


class TestFormatBatchResult:
    def test_empty_result(self):
        result = format_batch_result(BatchResult(), "create")
        assert "Batch create completed" in result
        assert "Succeeded: 0" in result
        assert "Failed: 0" in result

    def test_mixed_result(self):
        batch = BatchResult(
            succeeded=({"id": "t1", "title": "Task A"},),
            failed=({"title": "Task B", "error": "Invalid project"},),
        )
        result = format_batch_result(batch, "create")
        assert "Succeeded: 1" in result
        assert "Failed: 1" in result
        assert "Task A (ID: t1)" in result
        assert "Task B: Invalid project" in result
