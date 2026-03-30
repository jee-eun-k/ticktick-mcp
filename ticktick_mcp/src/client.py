"""Async TickTick API client using httpx."""

from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

import httpx

from .config import TickTickConfig
from .errors import APIError, RateLimitError, TokenRefreshError
from .token_store import FileTokenStore, TokenStore

logger = logging.getLogger(__name__)


class TickTickClient:
    """Async client for the TickTick Open API."""

    def __init__(
        self,
        config: TickTickConfig,
        token_store: TokenStore | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._config = config
        self._token_store = token_store or FileTokenStore()
        self._access_token = config.access_token
        self._refresh_token = config.refresh_token
        self._client = http_client or httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        await self._client.aclose()

    # ── HTTP core ──────────────────────────────────────────────

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: dict[str, Any] | None = None,
    ) -> Any:
        """Make an authenticated API request with auto-retry on 401."""
        url = f"{self._config.base_url}{endpoint}"

        response = await self._client.request(
            method, url, headers=self._headers(), json=json_data
        )

        if response.status_code == 401:
            logger.info("Access token expired, attempting refresh…")
            await self._refresh_access_token()
            response = await self._client.request(
                method, url, headers=self._headers(), json=json_data
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)

        if response.status_code >= 400:
            raise APIError(
                f"API error: {response.status_code} {response.text}",
                status_code=response.status_code,
                retryable=response.status_code >= 500,
            )

        if response.status_code == 204 or not response.text:
            return {}

        return response.json()

    async def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._config.can_refresh:
            raise TokenRefreshError("Missing client credentials or refresh token")

        auth_str = f"{self._config.client_id}:{self._config.client_secret}"
        auth_b64 = base64.b64encode(auth_str.encode("ascii")).decode("ascii")

        response = await self._client.post(
            self._config.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
            headers={
                "Authorization": f"Basic {auth_b64}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        if response.status_code != 200:
            raise TokenRefreshError(f"Token refresh failed: {response.status_code}")

        tokens = response.json()
        self._access_token = tokens["access_token"]
        if "refresh_token" in tokens:
            self._refresh_token = tokens["refresh_token"]

        self._token_store.save_tokens({
            "TICKTICK_ACCESS_TOKEN": self._access_token,
            "TICKTICK_REFRESH_TOKEN": self._refresh_token,
        })
        logger.info("Access token refreshed successfully")

    # ── Project operations ─────────────────────────────────────

    async def get_projects(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/project")

    async def get_project(self, project_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/project/{project_id}")

    async def get_project_with_data(self, project_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/project/{project_id}/data")

    async def create_project(
        self,
        name: str,
        color: str = "#F18181",
        view_mode: str = "list",
        kind: str = "TASK",
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/project",
            json_data={"name": name, "color": color, "viewMode": view_mode, "kind": kind},
        )

    async def update_project(
        self,
        project_id: str,
        *,
        name: str | None = None,
        color: str | None = None,
        view_mode: str | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if name is not None:
            data["name"] = name
        if color is not None:
            data["color"] = color
        if view_mode is not None:
            data["viewMode"] = view_mode
        return await self._request("POST", f"/project/{project_id}", json_data=data)

    async def delete_project(self, project_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/project/{project_id}")

    # ── Task operations ────────────────────────────────────────

    async def get_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        return await self._request("GET", f"/project/{project_id}/task/{task_id}")

    async def create_task(
        self,
        title: str,
        project_id: str,
        *,
        content: str | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        priority: int = 0,
        is_all_day: bool = False,
        parent_id: str | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"title": title, "projectId": project_id}
        if content:
            data["content"] = content
        if start_date:
            data["startDate"] = start_date
        if due_date:
            data["dueDate"] = due_date
        if priority:
            data["priority"] = priority
        if is_all_day:
            data["isAllDay"] = is_all_day
        if parent_id:
            data["parentId"] = parent_id
        return await self._request("POST", "/task", json_data=data)

    async def update_task(
        self,
        task_id: str,
        project_id: str,
        *,
        title: str | None = None,
        content: str | None = None,
        priority: int | None = None,
        start_date: str | None = None,
        due_date: str | None = None,
        items: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"id": task_id, "projectId": project_id}
        if title is not None:
            data["title"] = title
        if content is not None:
            data["content"] = content
        if priority is not None:
            data["priority"] = priority
        if start_date is not None:
            data["startDate"] = start_date
        if due_date is not None:
            data["dueDate"] = due_date
        if items is not None:
            data["items"] = items
        return await self._request("POST", f"/task/{task_id}", json_data=data)

    async def complete_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        return await self._request(
            "POST", f"/project/{project_id}/task/{task_id}/complete"
        )

    async def delete_task(self, project_id: str, task_id: str) -> dict[str, Any]:
        return await self._request("DELETE", f"/project/{project_id}/task/{task_id}")

    async def move_task(
        self, task_id: str, from_project_id: str, to_project_id: str
    ) -> dict[str, Any]:
        """Move a task to a different project by updating its projectId."""
        return await self._request(
            "POST",
            f"/task/{task_id}",
            json_data={"id": task_id, "projectId": to_project_id},
        )

    # ── Bulk operations (parallel fetch) ───────────────────────

    async def get_all_project_data(
        self, projects: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Fetch data for all projects in parallel (fixes N+1 problem)."""
        tasks = [
            self.get_project_with_data(p["id"])
            for p in projects
            if not p.get("closed", False)
        ]
        return list(await asyncio.gather(*tasks))
