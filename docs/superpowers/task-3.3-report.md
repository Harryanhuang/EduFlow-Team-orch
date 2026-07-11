# Task 3.3 Report: Enforce validation in path resolution

## What was implemented

Added `eduflow.runtime.names.validate_agent_name` at the three filesystem path-construction sites specified in the task brief, so an invalid agent name cannot be used to build a path before the validator rejects it.

- `src/eduflow/agents/identity.py` — `identity_path(agent)` now validates the name before returning `$EDUFLOW_STATE_DIR/agents/<agent>/identity.md`.
- `src/eduflow/store/memory.py` — `_agent_dir(agent)` now validates the name before returning `$EDUFLOW_STATE_DIR/facts/<agent>`.
- `src/eduflow/runtime/lifecycle.py` — `_ensure_claude_agent_home(agent)` now validates the name before deriving the per-agent `HOME` directory.

A new unit test module exercises each of these three call sites with a traversal payload (`../etc`) and asserts that `InvalidNameError` is raised.

## RED / GREEN TDD evidence

### RED (before fix)

```bash
$ python3 -m pytest tests/unit/test_paths_agent_validation.py -v
FAILED tests/unit/test_paths_agent_validation.py::test_identity_path_rejects_traversal
FAILED tests/unit/test_paths_agent_validation.py::test_memory_agent_dir_rejects_traversal
FAILED tests/unit/test_paths_agent_validation.py::test_ensure_claude_agent_home_rejects_traversal
============================== 3 failed in 0.08s ===============================
```

### GREEN (after fix)

```bash
$ python3 tests/run.py paths_agent_validation
OK  unit/test_paths_agent_validation: 3 passed

tests: 3 passed, 0 failed
```

## Full suite test results

| Run | Passed | Failed | Notes |
|-----|--------|--------|-------|
| Baseline (before changes) | 2276 | 37 | pre-existing failures |
| After task 3.3 changes | 2279 | 37 | +3 new passing tests, no new failures |

```bash
$ python3 tests/run.py
tests: 2279 passed, 37 failed
```

The 37 failures are the same pre-existing baseline failures; no new failures were introduced.

## Files changed

- `src/eduflow/agents/identity.py`
- `src/eduflow/store/memory.py`
- `src/eduflow/runtime/lifecycle.py`
- `tests/unit/test_paths_agent_validation.py` (new)

## Commit

```
034bdbe4 security: validate agent names before building filesystem paths
```

## Self-review findings

- The validation is placed at the lowest path-building function in each file (`identity_path`, `_agent_dir`, `_ensure_claude_agent_home`), so all callers are protected without duplicate checks.
- `_spawn_once` in `lifecycle.py` already validates `agent` before calling `identity.write` and `agent_home`, so the new check in `_ensure_claude_agent_home` is defensive rather than strictly necessary on the current call path.
- Other `agent_home(agent)` call sites exist (`src/eduflow/agents/claude_code.py`, `src/eduflow/agents/codex_cli.py`, `src/eduflow/runtime/agent_auth.py`), but they are all downstream of `lifecycle._spawn_once` or `provision_pane`, which already validates the agent name. They were left untouched to stay within the task brief's explicit file list.
- No debug code, `TODO`, `HACK`, or `console.log` left behind.
- All modified files compile cleanly (`python3 -m py_compile`).

## Concerns

None. The change is minimal, follows the existing validator pattern from Task 3.2, and keeps the pre-existing test baseline unchanged.
