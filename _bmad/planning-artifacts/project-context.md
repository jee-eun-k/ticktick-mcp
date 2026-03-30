# ticktick-mcp — Project Context

## What It Is

An MCP (Model Context Protocol) server that integrates TickTick/Dida365 task management with Claude and other MCP-compatible AI assistants. Fork of jacepark12/ticktick-mcp with major architectural improvements.

## Tech Stack

- **Language**: Python 3.10+
- **Async**: httpx (async HTTP), asyncio
- **MCP**: mcp[cli] >= 1.2.0 (FastMCP)
- **Packaging**: pyproject.toml + hatchling, uv
- **Testing**: pytest, pytest-asyncio, pytest-httpx, pytest-cov
- **Linting**: ruff

## Architecture

Modular domain-driven structure:

```
ticktick_mcp/
├── cli.py              # CLI entry (auth/run commands)
├── authenticate.py     # OAuth flow orchestration
└── src/
    ├── server.py       # Thin MCP entry point
    ├── client.py       # Async HTTP client (httpx)
    ├── config.py       # Env-based configuration
    ├── errors.py       # Exception hierarchy
    ├── formatters.py   # Human-readable output
    ├── models.py       # Frozen dataclasses (Task, Project, etc.)
    ├── token_store.py  # Token persistence
    └── tools/          # MCP tools by domain
        ├── tasks.py    # Task CRUD (7 tools)
        ├── projects.py # Project CRUD (6 tools)
        ├── search.py   # Search & date filtering (8 tools)
        ├── batch.py    # Batch operations (4 tools)
        ├── subtasks.py # Subtask management (5 tools)
        └── gtd.py      # GTD framework (2 tools)
```

**Key patterns**: Frozen dataclasses, dependency injection via module singleton, tool registration pattern, async throughout.

## Current State (2026-03-30)

- **Epic 1 (Modularization)**: DONE — monolith broken into modules, tests written, 80% coverage target
- **Epic 2 (Bug Fixes & Reliability)**: Subtask update/complete bugs, missing retry logic
- **Epic 3 (Feature Gaps)**: Recurring tasks, attachments, collaboration features not yet exposed

## How to Run

```bash
uv run -m ticktick_mcp.cli auth     # First-time OAuth setup
uv run -m ticktick_mcp.cli run      # Start MCP server
uv run pytest tests/ -v             # Run tests
```
