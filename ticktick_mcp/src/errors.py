"""Custom exception hierarchy for TickTick MCP server."""

from __future__ import annotations


class TickTickError(Exception):
    """Base exception for all TickTick MCP errors."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


class AuthenticationError(TickTickError):
    """Raised when authentication fails (invalid/expired tokens)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, retryable=True)


class TokenRefreshError(TickTickError):
    """Raised when token refresh fails."""

    def __init__(self, message: str = "Token refresh failed") -> None:
        super().__init__(message, retryable=False)


class APIError(TickTickError):
    """Raised for TickTick API errors (4xx/5xx responses)."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 0,
        retryable: bool = False,
    ) -> None:
        super().__init__(message, retryable=retryable)
        self.status_code = status_code


class ValidationError(TickTickError):
    """Raised for input validation failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message, retryable=False)


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""

    def __init__(self, resource: str, resource_id: str) -> None:
        super().__init__(
            f"{resource} '{resource_id}' not found",
            status_code=404,
            retryable=False,
        )


class RateLimitError(APIError):
    """Raised when rate limited by TickTick API (429)."""

    def __init__(self, retry_after: int | None = None) -> None:
        msg = "Rate limited by TickTick API"
        if retry_after:
            msg += f" — retry after {retry_after}s"
        super().__init__(msg, status_code=429, retryable=True)
        self.retry_after = retry_after


class ClientNotInitializedError(TickTickError):
    """Raised when client is used before initialization."""

    def __init__(self) -> None:
        super().__init__(
            "TickTick client not initialized. Run 'uv run -m ticktick_mcp.cli auth' first.",
            retryable=False,
        )
