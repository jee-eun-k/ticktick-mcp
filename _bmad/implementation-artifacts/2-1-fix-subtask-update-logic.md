# Story 2.1: Fix Subtask Update Logic

## Summary

`update_subtask()`, `complete_subtask()`, and `delete_subtask()` in `subtasks.py` modify the items array in memory but never pass it to the API via `client.update_task()`. The client's `update_task()` method also doesn't accept an `items` parameter.

## Bug Details

1. **subtasks.py:104-107** — `update_subtask` modifies items dict but calls `update_task()` without items
2. **subtasks.py:137** — `complete_subtask` sets status=1 in memory, never sends to API
3. **subtasks.py:160** — `delete_subtask` filters items, never sends filtered list to API
4. **client.py:192-214** — `update_task()` has no `items` kwarg

## Acceptance Criteria

- [ ] `client.update_task()` accepts optional `items` parameter and includes it in API payload
- [ ] `update_subtask()` passes modified items to `client.update_task(items=items)`
- [ ] `complete_subtask()` passes modified items to `client.update_task(items=items)`
- [ ] `delete_subtask()` passes filtered items to `client.update_task(items=items)`
- [ ] All existing tests still pass
- [ ] New tests cover the items-passing behavior
- [ ] 80%+ coverage maintained
