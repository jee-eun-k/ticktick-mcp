"""Tests for domain models."""

import pytest

from ticktick_mcp.src.models import (
    PRIORITY_MAP,
    VALID_PRIORITIES,
    BatchResult,
    ChecklistItem,
    Project,
    Task,
)


class TestChecklistItem:
    def test_from_api_complete(self):
        data = {"id": "ci1", "title": "Buy milk", "status": 1}
        item = ChecklistItem.from_api(data)
        assert item.id == "ci1"
        assert item.title == "Buy milk"
        assert item.is_complete is True

    def test_from_api_incomplete(self):
        data = {"id": "ci2", "title": "Buy eggs", "status": 0}
        item = ChecklistItem.from_api(data)
        assert item.is_complete is False

    def test_from_api_defaults(self):
        item = ChecklistItem.from_api({})
        assert item.id == ""
        assert item.title == ""
        assert item.status == 0

    def test_immutability(self):
        item = ChecklistItem(id="x", title="y", status=0)
        with pytest.raises(AttributeError):
            item.title = "z"  # type: ignore[misc]


class TestTask:
    SAMPLE_API_DATA = {
        "id": "t1",
        "title": "Write tests",
        "projectId": "p1",
        "status": 0,
        "priority": 5,
        "content": "Unit tests for models",
        "startDate": "2026-03-16T09:00:00.000+0000",
        "dueDate": "2026-03-17T09:00:00.000+0000",
        "parentId": None,
        "items": [
            {"id": "ci1", "title": "Test models", "status": 1},
            {"id": "ci2", "title": "Test formatters", "status": 0},
        ],
    }

    def test_from_api(self):
        task = Task.from_api(self.SAMPLE_API_DATA)
        assert task.id == "t1"
        assert task.title == "Write tests"
        assert task.project_id == "p1"
        assert task.priority == 5
        assert task.priority_label == "High"
        assert task.is_complete is False
        assert len(task.items) == 2
        assert task.items[0].is_complete is True

    def test_from_api_defaults(self):
        task = Task.from_api({})
        assert task.id == ""
        assert task.priority == 0
        assert task.priority_label == "None"
        assert task.items == ()

    def test_to_dict_minimal(self):
        task = Task.from_api({"id": "t2", "title": "Simple", "projectId": "p1"})
        d = task.to_dict()
        assert d["id"] == "t2"
        assert d["status"] == "active"
        assert d["priority"] == "None"
        assert "content" not in d
        assert "subtasks" not in d

    def test_to_dict_full(self):
        task = Task.from_api(self.SAMPLE_API_DATA)
        d = task.to_dict()
        assert d["priority"] == "High"
        assert d["content"] == "Unit tests for models"
        assert len(d["subtasks"]) == 2
        assert d["subtasks"][0]["complete"] is True

    def test_completed_task(self):
        task = Task.from_api({"id": "t3", "title": "Done", "projectId": "p1", "status": 2})
        assert task.is_complete is True
        assert task.to_dict()["status"] == "completed"

    def test_immutability(self):
        task = Task(id="x", title="y", project_id="p")
        with pytest.raises(AttributeError):
            task.title = "z"  # type: ignore[misc]


class TestProject:
    def test_from_api(self):
        data = {
            "id": "p1",
            "name": "Work",
            "color": "#FF0000",
            "viewMode": "kanban",
            "closed": False,
            "kind": "TASK",
        }
        project = Project.from_api(data)
        assert project.id == "p1"
        assert project.name == "Work"
        assert project.color == "#FF0000"
        assert project.closed is False

    def test_from_api_defaults(self):
        project = Project.from_api({})
        assert project.id == ""
        assert project.name == ""
        assert project.closed is False

    def test_to_dict_minimal(self):
        project = Project.from_api({"id": "p2", "name": "Personal"})
        d = project.to_dict()
        assert d == {"id": "p2", "name": "Personal"}

    def test_to_dict_full(self):
        project = Project.from_api({
            "id": "p1",
            "name": "Work",
            "color": "#FF0000",
            "viewMode": "kanban",
            "closed": True,
            "kind": "TASK",
        })
        d = project.to_dict()
        assert d["color"] == "#FF0000"
        assert d["closed"] is True
        assert d["kind"] == "TASK"


class TestBatchResult:
    def test_empty(self):
        result = BatchResult()
        assert result.total == 0
        assert result.success_count == 0
        assert result.failure_count == 0

    def test_with_data(self):
        result = BatchResult(
            succeeded=({"id": "t1", "title": "A"},),
            failed=({"title": "B", "error": "bad request"},),
        )
        assert result.total == 2
        assert result.success_count == 1
        assert result.failure_count == 1
        d = result.to_dict()
        assert len(d["succeeded"]) == 1
        assert len(d["failed"]) == 1


class TestConstants:
    def test_priority_map_values(self):
        assert PRIORITY_MAP[0] == "None"
        assert PRIORITY_MAP[5] == "High"

    def test_valid_priorities(self):
        assert frozenset({0, 1, 3, 5}) == VALID_PRIORITIES
