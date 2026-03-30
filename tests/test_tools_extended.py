"""Extended tool tests to cover remaining paths."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.tools._deps import set_client


@pytest.fixture
def mock_client():
    client = AsyncMock()
    set_client(client)
    yield client
    set_client(None)


def _make_mcp_and_register(module):
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("test")
    module.register(mcp)
    return mcp


async def _call(mcp, tool_name, **kwargs):
    for tool in mcp._tool_manager._tools.values():
        if tool.name == tool_name:
            return await tool.fn(**kwargs)
    raise ValueError(f"Tool '{tool_name}' not found")


# ── Tasks: happy paths ────────────────────────────────────


class TestTaskToolsExtended:
    async def test_get_task(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Hello", "projectId": "p1"
        }
        result = await _call(mcp, "get_task", project_id="p1", task_id="t1")
        assert "Hello" in result

    async def test_get_project_tasks(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_project_with_data.return_value = {
            "project": {"id": "p1", "name": "Work"},
            "tasks": [
                {"id": "t1", "title": "Task A", "projectId": "p1"},
                {"id": "t2", "title": "Task B", "projectId": "p1"},
            ],
        }
        result = await _call(mcp, "get_project_tasks", project_id="p1")
        assert "Found 2 tasks" in result
        assert "Task A" in result

    async def test_get_project_tasks_empty(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_project_with_data.return_value = {
            "project": {"id": "p1", "name": "Work"},
            "tasks": [],
        }
        result = await _call(mcp, "get_project_tasks", project_id="p1")
        assert "No tasks found" in result

    async def test_update_task(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.update_task.return_value = {
            "id": "t1", "title": "Updated", "projectId": "p1", "priority": 3
        }
        result = await _call(
            mcp, "update_task", task_id="t1", project_id="p1", title="Updated", priority=3
        )
        assert "Task updated successfully" in result

    async def test_delete_task(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.delete_task.return_value = {}
        result = await _call(mcp, "delete_task", project_id="p1", task_id="t1")
        assert "deleted successfully" in result

    async def test_create_task_invalid_date(self, mock_client):
        from ticktick_mcp.src.tools import tasks as mod

        mcp = _make_mcp_and_register(mod)
        with pytest.raises(ValidationError, match="Invalid due_date"):
            await _call(
                mcp, "create_task", title="X", project_id="p1", due_date="bad-date"
            )


# ── Projects: happy paths ─────────────────────────────────


class TestProjectToolsExtended:
    async def test_get_project(self, mock_client):
        from ticktick_mcp.src.tools import projects as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_project.return_value = {"id": "p1", "name": "Work"}
        result = await _call(mcp, "get_project", project_id="p1")
        assert "Work" in result

    async def test_create_project(self, mock_client):
        from ticktick_mcp.src.tools import projects as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.create_project.return_value = {"id": "p_new", "name": "New"}
        result = await _call(mcp, "create_project", name="New")
        assert "Project created" in result

    async def test_update_project(self, mock_client):
        from ticktick_mcp.src.tools import projects as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.update_project.return_value = {"id": "p1", "name": "Renamed"}
        result = await _call(mcp, "update_project", project_id="p1", name="Renamed")
        assert "Project updated" in result

    async def test_update_project_invalid_view_mode(self, mock_client):
        from ticktick_mcp.src.tools import projects as mod

        mcp = _make_mcp_and_register(mod)
        with pytest.raises(ValidationError, match="Invalid view_mode"):
            await _call(mcp, "update_project", project_id="p1", view_mode="bad")

    async def test_delete_project(self, mock_client):
        from ticktick_mcp.src.tools import projects as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.delete_project.return_value = {}
        result = await _call(mcp, "delete_project", project_id="p1")
        assert "deleted successfully" in result


# ── Search: happy paths ───────────────────────────────────


class TestSearchToolsExtended:
    async def test_get_all_tasks(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": [{"id": "t1", "title": "A", "projectId": "p1"}]}
        ]
        result = await _call(mcp, "get_all_tasks")
        assert "1 active projects" in result

    async def test_search_tasks(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {
                "project": {"id": "p1"},
                "tasks": [
                    {"id": "t1", "title": "Buy groceries", "projectId": "p1"},
                    {"id": "t2", "title": "Clean house", "projectId": "p1"},
                ],
            }
        ]
        result = await _call(mcp, "search_tasks", search_term="grocery")
        assert "matching" in result

    async def test_get_tasks_by_priority(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {
                "project": {"id": "p1"},
                "tasks": [{"id": "t1", "title": "A", "projectId": "p1", "priority": 5}],
            }
        ]
        result = await _call(mcp, "get_tasks_by_priority", priority_id=5)
        assert "priority" in result

    async def test_get_tasks_due_today(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(mcp, "get_tasks_due_today")
        assert "due today" in result

    async def test_get_tasks_due_tomorrow(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(mcp, "get_tasks_due_tomorrow")
        assert "due tomorrow" in result

    async def test_get_overdue_tasks(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(mcp, "get_overdue_tasks")
        assert "overdue" in result

    async def test_get_tasks_due_this_week(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(mcp, "get_tasks_due_this_week")
        assert "due this week" in result

    async def test_get_tasks_due_in_days(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(mcp, "get_tasks_due_in_days", days=3)
        assert "due in 3 days" in result

    async def test_get_tasks_by_date_range(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {"project": {"id": "p1"}, "tasks": []}
        ]
        result = await _call(
            mcp, "get_tasks_by_date_range", start="2026-03-16", end="2026-03-20"
        )
        assert "due between" in result

    async def test_no_projects(self, mock_client):
        from ticktick_mcp.src.tools import search as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = []
        result = await _call(mcp, "get_all_tasks")
        assert "No projects found" in result


# ── Batch: edge cases ─────────────────────────────────────


class TestBatchToolsExtended:
    async def test_batch_complete_missing_ids(self, mock_client):
        from ticktick_mcp.src.tools import batch as mod

        mcp = _make_mcp_and_register(mod)
        result = await _call(
            mcp, "batch_complete_tasks", tasks=[{"project_id": "p1"}]
        )  # missing task_id
        assert "Failed: 1" in result

    async def test_batch_create_with_failure(self, mock_client):
        from ticktick_mcp.src.tools import batch as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.create_task.side_effect = [
            {"id": "t1", "title": "OK"},
            Exception("API Error"),
        ]
        result = await _call(
            mcp,
            "batch_create_tasks",
            tasks=[
                {"title": "OK", "project_id": "p1"},
                {"title": "Fail", "project_id": "p1"},
            ],
        )
        assert "Succeeded: 1" in result
        assert "Failed: 1" in result

    async def test_batch_empty_raises(self, mock_client):
        from ticktick_mcp.src.tools import batch as mod

        mcp = _make_mcp_and_register(mod)
        with pytest.raises(ValidationError, match="No tasks"):
            await _call(mcp, "batch_complete_tasks", tasks=[])


# ── Subtasks: more paths ──────────────────────────────────


class TestSubtaskToolsExtended:
    async def test_update_subtask(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1",
            "items": [{"id": "ci1", "title": "Sub 1", "status": 0}],
        }
        mock_client.update_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1",
        }
        result = await _call(
            mcp, "update_subtask",
            task_id="t1", project_id="p1", subtask_id="ci1", title="New title"
        )
        assert "Subtask updated" in result
        # Verify items with modification are passed to update_task
        call_kwargs = mock_client.update_task.call_args
        assert call_kwargs.kwargs["items"] == [{"id": "ci1", "title": "New title", "status": 0}]

    async def test_update_subtask_not_found(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1", "items": [],
        }
        with pytest.raises(ValidationError, match="not found"):
            await _call(
                mcp, "update_subtask",
                task_id="t1", project_id="p1", subtask_id="bad"
            )

    async def test_complete_subtask(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1",
            "items": [{"id": "ci1", "title": "Sub", "status": 0}],
        }
        mock_client.update_task.return_value = {"id": "t1", "title": "Parent", "projectId": "p1"}
        result = await _call(
            mcp, "complete_subtask", task_id="t1", project_id="p1", subtask_id="ci1"
        )
        assert "marked as complete" in result
        # Verify items with status=1 are passed to update_task
        call_kwargs = mock_client.update_task.call_args
        assert call_kwargs.kwargs["items"] == [{"id": "ci1", "title": "Sub", "status": 1}]

    async def test_delete_subtask(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1",
            "items": [{"id": "ci1", "title": "Sub", "status": 0}],
        }
        mock_client.update_task.return_value = {"id": "t1", "title": "Parent", "projectId": "p1"}
        result = await _call(
            mcp, "delete_subtask", task_id="t1", project_id="p1", subtask_id="ci1"
        )
        assert "deleted successfully" in result
        # Verify empty items list is passed (subtask removed)
        call_kwargs = mock_client.update_task.call_args
        assert call_kwargs.kwargs["items"] == []

    async def test_delete_subtask_not_found(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_task.return_value = {
            "id": "t1", "title": "Parent", "projectId": "p1", "items": [],
        }
        with pytest.raises(ValidationError, match="not found"):
            await _call(
                mcp, "delete_subtask", task_id="t1", project_id="p1", subtask_id="bad"
            )

    async def test_create_subtask_invalid_priority(self, mock_client):
        from ticktick_mcp.src.tools import subtasks as mod

        mcp = _make_mcp_and_register(mod)
        with pytest.raises(ValidationError, match="Invalid priority"):
            await _call(
                mcp, "create_subtask",
                subtask_title="X", parent_task_id="t1", project_id="p1", priority=99
            )


# ── GTD: next tasks ───────────────────────────────────────


class TestGTDToolsExtended:
    async def test_get_next_tasks(self, mock_client):
        from ticktick_mcp.src.tools import gtd as mod

        mcp = _make_mcp_and_register(mod)
        mock_client.get_projects.return_value = [{"id": "p1", "name": "W", "closed": False}]
        mock_client.get_all_project_data.return_value = [
            {
                "project": {"id": "p1"},
                "tasks": [{"id": "t1", "title": "Medium", "projectId": "p1", "priority": 3}],
            }
        ]
        result = await _call(mcp, "get_next_tasks")
        assert "next" in result
