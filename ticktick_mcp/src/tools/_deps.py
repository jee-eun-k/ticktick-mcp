"""Shared dependency injection for tool modules."""

from __future__ import annotations

from ticktick_mcp.src.client import TickTickClient

# Module-level client reference, set during server startup.
_client: TickTickClient | None = None


def set_client(client: TickTickClient) -> None:
    global _client
    _client = client


def get_client() -> TickTickClient:
    if _client is None:
        from ticktick_mcp.src.errors import ClientNotInitializedError

        raise ClientNotInitializedError()
    return _client
