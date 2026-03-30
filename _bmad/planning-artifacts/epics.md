---
stepsCompleted: [1, 2]
workflowType: 'epics'
project_name: 'ticktick-mcp'
user_name: 'Alexa'
date: '2026-03-30'
---

# ticktick-mcp — Epic Breakdown

## Overview

Epics for evolving the ticktick-mcp fork from a working modular MCP server to a robust, feature-complete TickTick integration.

---

## Epic 1: Modularization & Foundation

**Goal**: Break monolithic server into well-organized modules with modern tooling and tests.

**Status**: DONE (completed 2026-03-30)

### Story 1.1: Extract Domain Models
Extract Task, Project, ChecklistItem, BatchResult into frozen dataclasses in `models.py`.

### Story 1.2: Extract HTTP Client
Create async `client.py` using httpx, replacing synchronous requests library.

### Story 1.3: Extract Configuration
Move env-based config to `config.py` with `TickTickConfig` frozen dataclass.

### Story 1.4: Extract Error Hierarchy
Create `errors.py` with TickTickError base and specific subtypes (Auth, API, Validation, RateLimit, NotFound).

### Story 1.5: Extract Formatters
Move output formatting to `formatters.py` (format_task, format_project, format_batch_result).

### Story 1.6: Extract Token Store
Create `token_store.py` for token persistence abstraction.

### Story 1.7: Split Tools by Domain
Break monolithic tool registration into domain modules: tasks, projects, search, batch, subtasks, gtd.

### Story 1.8: Migrate to Modern Packaging
Replace setup.py + requirements.txt with pyproject.toml (hatchling + uv).

### Story 1.9: Write Test Suite
Comprehensive pytest tests for all extracted modules. 80% coverage target.

---

## Epic 2: Bug Fixes & Reliability

**Goal**: Fix known bugs and add retry/resilience patterns.

### Story 2.1: Fix Subtask Update Logic
Fix `update_subtask()` and `complete_subtask()` in subtasks.py — items array not properly passed to API.

### Story 2.2: Add Retry with Exponential Backoff
Implement retry decorator for retryable errors (5xx, 429). Use the existing `retryable` flag on TickTickError.

### Story 2.3: Add Token Refresh CLI Command
Add `ticktick-mcp refresh-token` command for manual token refresh.

### Story 2.4: Validate Dida365 Compatibility
Test and fix auth/token flows against Dida365 API endpoints.

---

## Epic 3: Feature Expansion

**Goal**: Expose additional TickTick API capabilities as MCP tools.

### Story 3.1: Recurring Task Support
Add recurrence/repeat pattern support to task creation and updates.

### Story 3.2: Tag Support
Expose task tags in models and add tag-based filtering tools.

### Story 3.3: Task Comments
Add read/write support for task comments.

### Story 3.4: Habit Tracking
Expose TickTick habit tracking as MCP tools if API supports it.

### Story 3.5: Calendar Integration
Add tools for calendar view / date-based task visualization.

---

## Epic 4: Developer Experience

**Goal**: Improve documentation, CLI, and contributor experience.

### Story 4.1: List Available Tools CLI Command
Add `ticktick-mcp list-tools` to discover available MCP tools from CLI.

### Story 4.2: Update README for New Architecture
Update README.md to reflect modular structure, new commands, development workflow.

### Story 4.3: Add Contributing Guide
Create CONTRIBUTING.md with development setup, testing, and PR guidelines.

### Story 4.4: Add Integration Test Harness
Create optional integration test suite that runs against real TickTick API with credentials.
