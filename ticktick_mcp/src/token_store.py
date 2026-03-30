"""Token persistence for TickTick OAuth tokens."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class TokenStore(Protocol):
    """Protocol for token persistence backends."""

    def load_tokens(self) -> dict[str, str]: ...
    def save_tokens(self, tokens: dict[str, str]) -> None: ...


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class FileTokenStore:
    """Persists tokens to a .env file."""

    def __init__(self, env_path: str | Path | None = None) -> None:
        self._path = Path(env_path) if env_path else _PROJECT_ROOT / ".env"

    def load_tokens(self) -> dict[str, str]:
        """Load tokens from the .env file."""
        result: dict[str, str] = {}
        if not self._path.exists():
            return result

        for line in self._path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def save_tokens(self, tokens: dict[str, str]) -> None:
        """Save tokens to the .env file, preserving other entries."""
        existing = self.load_tokens()
        existing.update(tokens)

        lines = [f"{key}={value}" for key, value in existing.items()]
        self._path.write_text("\n".join(lines) + "\n")
        logger.debug("Tokens saved to %s", self._path)
