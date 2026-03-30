"""Tests for config module."""

import os

import pytest

from ticktick_mcp.src.config import TickTickConfig


class TestTickTickConfig:
    def test_from_env_defaults(self, monkeypatch):
        # Clear all TICKTICK env vars
        for key in list(os.environ):
            if key.startswith("TICKTICK_"):
                monkeypatch.delenv(key, raising=False)

        config = TickTickConfig.from_env(dotenv_path="/dev/null")
        assert config.base_url == "https://api.ticktick.com/open/v1"
        assert config.auth_url == "https://ticktick.com/oauth/authorize"
        assert config.token_url == "https://ticktick.com/oauth/token"
        assert config.is_authenticated is False
        assert config.can_refresh is False

    def test_from_env_with_values(self, monkeypatch):
        monkeypatch.setenv("TICKTICK_CLIENT_ID", "test_id")
        monkeypatch.setenv("TICKTICK_CLIENT_SECRET", "test_secret")
        monkeypatch.setenv("TICKTICK_ACCESS_TOKEN", "test_token")
        monkeypatch.setenv("TICKTICK_REFRESH_TOKEN", "test_refresh")

        config = TickTickConfig.from_env(dotenv_path="/dev/null")
        assert config.client_id == "test_id"
        assert config.is_authenticated is True
        assert config.can_refresh is True

    def test_immutability(self, monkeypatch):
        monkeypatch.setenv("TICKTICK_ACCESS_TOKEN", "tok")
        config = TickTickConfig.from_env(dotenv_path="/dev/null")
        with pytest.raises(AttributeError):
            config.access_token = "new"  # type: ignore[misc]
