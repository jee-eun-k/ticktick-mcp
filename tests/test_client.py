"""Tests for async TickTick client."""

import pytest
from pytest_httpx import HTTPXMock

from ticktick_mcp.src.client import TickTickClient
from ticktick_mcp.src.config import TickTickConfig
from ticktick_mcp.src.errors import APIError, RateLimitError, TokenRefreshError

BASE_URL = "https://api.ticktick.com/open/v1"
TOKEN_URL = "https://ticktick.com/oauth/token"


def make_config(**overrides) -> TickTickConfig:
    defaults = {
        "client_id": "test_id",
        "client_secret": "test_secret",
        "access_token": "test_token",
        "refresh_token": "test_refresh",
        "base_url": BASE_URL,
        "auth_url": "https://ticktick.com/oauth/authorize",
        "token_url": TOKEN_URL,
    }
    defaults.update(overrides)
    return TickTickConfig(**defaults)


class FakeTokenStore:
    def __init__(self):
        self.saved: dict[str, str] = {}

    def load_tokens(self) -> dict[str, str]:
        return self.saved

    def save_tokens(self, tokens: dict[str, str]) -> None:
        self.saved.update(tokens)


@pytest.fixture
def token_store():
    return FakeTokenStore()


@pytest.fixture
async def client(token_store):
    config = make_config()
    c = TickTickClient(config=config, token_store=token_store)
    yield c
    await c.close()


class TestGetProjects:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            json=[{"id": "p1", "name": "Work"}],
        )
        projects = await client.get_projects()
        assert len(projects) == 1
        assert projects[0]["name"] == "Work"

    async def test_empty(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=f"{BASE_URL}/project", json=[])
        projects = await client.get_projects()
        assert projects == []


class TestGetTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1/task/t1",
            json={"id": "t1", "title": "Test", "projectId": "p1"},
        )
        task = await client.get_task("p1", "t1")
        assert task["id"] == "t1"


class TestCreateTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/task",
            json={"id": "t_new", "title": "New task", "projectId": "p1"},
        )
        task = await client.create_task("New task", "p1", priority=5)
        assert task["id"] == "t_new"

    async def test_with_parent(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/task",
            json={"id": "sub1", "title": "Sub", "projectId": "p1", "parentId": "t1"},
        )
        task = await client.create_task("Sub", "p1", parent_id="t1")
        assert task["parentId"] == "t1"


class TestUpdateTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/task/t1",
            json={"id": "t1", "title": "Updated", "projectId": "p1"},
        )
        task = await client.update_task("t1", "p1", title="Updated")
        assert task["title"] == "Updated"


class TestCompleteTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1/task/t1/complete",
            status_code=204,
        )
        result = await client.complete_task("p1", "t1")
        assert result == {}


class TestDeleteTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1/task/t1",
            status_code=204,
        )
        result = await client.delete_task("p1", "t1")
        assert result == {}


class TestProjectCRUD:
    async def test_create_project(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            json={"id": "p_new", "name": "New Project"},
        )
        project = await client.create_project("New Project")
        assert project["id"] == "p_new"

    async def test_update_project(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1",
            json={"id": "p1", "name": "Renamed"},
        )
        project = await client.update_project("p1", name="Renamed")
        assert project["name"] == "Renamed"

    async def test_delete_project(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1",
            status_code=204,
        )
        result = await client.delete_project("p1")
        assert result == {}


class TestMoveTask:
    async def test_success(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/task/t1",
            json={"id": "t1", "projectId": "p2"},
        )
        result = await client.move_task("t1", "p1", "p2")
        assert result["projectId"] == "p2"


class TestTokenRefresh:
    async def test_auto_refresh_on_401(
        self, token_store: FakeTokenStore, httpx_mock: HTTPXMock
    ):
        config = make_config()
        client = TickTickClient(config=config, token_store=token_store)

        # First request returns 401
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            status_code=401,
        )
        # Token refresh succeeds
        httpx_mock.add_response(
            url=TOKEN_URL,
            json={"access_token": "new_token", "refresh_token": "new_refresh"},
        )
        # Retry succeeds
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            json=[{"id": "p1", "name": "Work"}],
        )

        projects = await client.get_projects()
        assert len(projects) == 1
        assert token_store.saved["TICKTICK_ACCESS_TOKEN"] == "new_token"
        await client.close()

    async def test_refresh_failure(
        self, token_store: FakeTokenStore, httpx_mock: HTTPXMock
    ):
        config = make_config()
        client = TickTickClient(config=config, token_store=token_store)

        httpx_mock.add_response(url=f"{BASE_URL}/project", status_code=401)
        httpx_mock.add_response(url=TOKEN_URL, status_code=400)

        with pytest.raises(TokenRefreshError):
            await client.get_projects()
        await client.close()

    async def test_refresh_without_credentials(
        self, token_store: FakeTokenStore, httpx_mock: HTTPXMock
    ):
        config = make_config(client_id="", client_secret="")
        client = TickTickClient(config=config, token_store=token_store)

        httpx_mock.add_response(url=f"{BASE_URL}/project", status_code=401)

        with pytest.raises(TokenRefreshError, match="Missing client credentials"):
            await client.get_projects()
        await client.close()


class TestErrorHandling:
    async def test_api_error_4xx(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/bad",
            status_code=404,
            text="Not Found",
        )
        with pytest.raises(APIError) as exc_info:
            await client.get_project("bad")
        assert exc_info.value.status_code == 404
        assert exc_info.value.retryable is False

    async def test_api_error_5xx(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            status_code=500,
            text="Internal Server Error",
        )
        with pytest.raises(APIError) as exc_info:
            await client.get_projects()
        assert exc_info.value.retryable is True

    async def test_rate_limit(self, client: TickTickClient, httpx_mock: HTTPXMock):
        httpx_mock.add_response(
            url=f"{BASE_URL}/project",
            status_code=429,
            headers={"Retry-After": "60"},
        )
        with pytest.raises(RateLimitError) as exc_info:
            await client.get_projects()
        assert exc_info.value.retry_after == 60


class TestBulkFetch:
    async def test_get_all_project_data(
        self, client: TickTickClient, httpx_mock: HTTPXMock
    ):
        projects = [
            {"id": "p1", "name": "Work", "closed": False},
            {"id": "p2", "name": "Archived", "closed": True},
            {"id": "p3", "name": "Personal", "closed": False},
        ]

        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p1/data",
            json={"project": {"id": "p1"}, "tasks": [{"id": "t1"}]},
        )
        httpx_mock.add_response(
            url=f"{BASE_URL}/project/p3/data",
            json={"project": {"id": "p3"}, "tasks": [{"id": "t2"}]},
        )

        results = await client.get_all_project_data(projects)
        assert len(results) == 2  # p2 skipped (closed)
