"""Configuration loading for TickTick MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class TickTickConfig:
    """Immutable configuration loaded from env vars / .env file."""

    client_id: str
    client_secret: str
    access_token: str
    refresh_token: str
    base_url: str
    auth_url: str
    token_url: str

    @classmethod
    def from_env(cls, dotenv_path: str | None = None) -> TickTickConfig:
        """Load config from environment variables with .env fallback."""
        load_dotenv(dotenv_path)

        return cls(
            client_id=os.getenv("TICKTICK_CLIENT_ID", ""),
            client_secret=os.getenv("TICKTICK_CLIENT_SECRET", ""),
            access_token=os.getenv("TICKTICK_ACCESS_TOKEN", ""),
            refresh_token=os.getenv("TICKTICK_REFRESH_TOKEN", ""),
            base_url=os.getenv("TICKTICK_BASE_URL", "https://api.ticktick.com/open/v1"),
            auth_url=os.getenv("TICKTICK_AUTH_URL", "https://ticktick.com/oauth/authorize"),
            token_url=os.getenv("TICKTICK_TOKEN_URL", "https://ticktick.com/oauth/token"),
        )

    @property
    def is_authenticated(self) -> bool:
        return bool(self.access_token)

    @property
    def can_refresh(self) -> bool:
        return bool(self.refresh_token and self.client_id and self.client_secret)
