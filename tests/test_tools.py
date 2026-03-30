"""Tests for MCP tool modules using mock client."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from ticktick_mcp.src.errors import ValidationError
from ticktick_mcp.src.tools._deps import set_client


@pytest.fixture
def mock_client():
    """Create a mock TickTickClient and inject it."""
    client = AsyncMock()
    set_client(client)
    yield client
    set_client(None)


# ── Project tools ──────────────────────────────────────────


class TestProjectTools:
    async def test_get_projects(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import projects as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.get_projects.return_value = [
            {"id": "p1", "name": "Work"},
            {"id": "p2", "name": "Personal"},
        ]

        # Call the tool function directly through the registered tools
        result = await _call_tool(mcp, "get_projects")
        assert "Found 2 projects" in result
        assert "Work" in result

    async def test_get_projects_empty(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import projects as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.get_projects.return_value = []
        result = await _call_tool(mcp, "get_projects")
        assert "No projects found" in result

    async def test_create_project_invalid_view_mode(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import projects as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="Invalid view_mode"):
            await _call_tool(mcp, "create_project", name="X", color="#FFF", view_mode="grid")


# ── Task tools ─────────────────────────────────────────────


class TestTaskTools:
    async def test_create_task(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import tasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.create_task.return_value = {
            "id": "t1",
            "title": "Buy milk",
            "projectId": "p1",
            "priority": 0,
        }

        result = await _call_tool(
            mcp, "create_task", title="Buy milk", project_id="p1"
        )
        assert "Task created successfully" in result
        assert "Buy milk" in result

    async def test_create_task_invalid_priority(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import tasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="Invalid priority"):
            await _call_tool(
                mcp, "create_task", title="X", project_id="p1", priority=7
            )

    async def test_complete_task(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import tasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.complete_task.return_value = {}
        result = await _call_tool(mcp, "complete_task", project_id="p1", task_id="t1")
        assert "marked as complete" in result

    async def test_move_task(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import tasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.move_task.return_value = {
            "id": "t1",
            "title": "Moved",
            "projectId": "p2",
        }
        result = await _call_tool(
            mcp,
            "move_task",
            task_id="t1",
            from_project_id="p1",
            to_project_id="p2",
        )
        assert "Task moved successfully" in result


# ── Batch tools ────────────────────────────────────────────


class TestBatchTools:
    async def test_batch_create_tasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import batch as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.create_task.return_value = {
            "id": "t1",
            "title": "Task A",
        }

        result = await _call_tool(
            mcp,
            "batch_create_tasks",
            tasks=[
                {"title": "Task A", "project_id": "p1"},
                {"title": "Task B", "project_id": "p1"},
            ],
        )
        assert "Succeeded: 2" in result

    async def test_batch_create_validation_error(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import batch as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="title"):
            await _call_tool(
                mcp,
                "batch_create_tasks",
                tasks=[{"project_id": "p1"}],  # missing title
            )

    async def test_batch_complete_tasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import batch as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.complete_task.return_value = {}
        result = await _call_tool(
            mcp,
            "batch_complete_tasks",
            tasks=[
                {"project_id": "p1", "task_id": "t1"},
                {"project_id": "p1", "task_id": "t2"},
            ],
        )
        assert "Succeeded: 2" in result

    async def test_batch_delete_tasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import batch as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.delete_task.return_value = {}
        result = await _call_tool(
            mcp,
            "batch_delete_tasks",
            tasks=[{"project_id": "p1", "task_id": "t1"}],
        )
        assert "Succeeded: 1" in result

    async def test_batch_update_tasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import batch as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.update_task.return_value = {"id": "t1", "title": "Updated"}
        result = await _call_tool(
            mcp,
            "batch_update_tasks",
            tasks=[{"task_id": "t1", "project_id": "p1", "title": "Updated"}],
        )
        assert "Succeeded: 1" in result


# ── Search tools ───────────────────────────────────────────


class TestSearchTools:
    async def test_search_empty_term(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import search as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="empty"):
            await _call_tool(mcp, "search_tasks", search_term="  ")

    async def test_get_tasks_due_in_days_negative(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import search as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="non-negative"):
            await _call_tool(mcp, "get_tasks_due_in_days", days=-1)

    async def test_date_range_invalid_format(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import search as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="ISO format"):
            await _call_tool(
                mcp, "get_tasks_by_date_range", start="not-a-date", end="2026-03-20"
            )

    async def test_date_range_inverted(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import search as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        with pytest.raises(ValidationError, match="before or equal"):
            await _call_tool(
                mcp, "get_tasks_by_date_range", start="2026-03-20", end="2026-03-10"
            )


# ── Subtask tools ──────────────────────────────────────────


class TestSubtaskTools:
    async def test_create_subtask(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import subtasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.create_task.return_value = {
            "id": "sub1",
            "title": "Sub",
            "projectId": "p1",
            "parentId": "t1",
        }

        result = await _call_tool(
            mcp,
            "create_subtask",
            subtask_title="Sub",
            parent_task_id="t1",
            project_id="p1",
        )
        assert "Subtask created" in result

    async def test_list_subtasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import subtasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.get_task.return_value = {
            "id": "t1",
            "title": "Parent",
            "projectId": "p1",
            "items": [
                {"id": "ci1", "title": "Item A", "status": 0},
                {"id": "ci2", "title": "Item B", "status": 1},
            ],
        }

        result = await _call_tool(
            mcp, "list_subtasks", project_id="p1", parent_task_id="t1"
        )
        assert "Item A" in result
        assert "Item B" in result
        assert "[v]" in result  # completed item

    async def test_list_subtasks_empty(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import subtasks as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.get_task.return_value = {
            "id": "t1",
            "title": "Parent",
            "projectId": "p1",
            "items": [],
        }

        result = await _call_tool(
            mcp, "list_subtasks", project_id="p1", parent_task_id="t1"
        )
        assert "No subtasks found" in result


# ── GTD tools ──────────────────────────────────────────────


class TestGTDTools:
    async def test_get_engaged_tasks(self, mock_client):
        from mcp.server.fastmcp import FastMCP

        from ticktick_mcp.src.tools import gtd as mod

        mcp = FastMCP("test")
        mod.register(mcp)

        mock_client.get_projects.return_value = [
            {"id": "p1", "name": "Work", "closed": False}
        ]
        mock_client.get_all_project_data.return_value = [
            {
                "project": {"id": "p1", "name": "Work"},
                "tasks": [
                    {"id": "t1", "title": "Urgent", "projectId": "p1", "priority": 5},
                    {"id": "t2", "title": "Chill", "projectId": "p1", "priority": 0},
                ],
            }
        ]

        result = await _call_tool(mcp, "get_engaged_tasks")
        assert "Urgent" in result


# ── Helper ─────────────────────────────────────────────────


async def _call_tool(mcp, tool_name: str, **kwargs) -> str:
    """Call a registered MCP tool function directly (bypassing ToolError wrapper)."""
    for tool in mcp._tool_manager._tools.values():
        if tool.name == tool_name:
            # Call the underlying function directly to get real exceptions
            return await tool.fn(**kwargs)
    raise ValueError(f"Tool '{tool_name}' not found")
