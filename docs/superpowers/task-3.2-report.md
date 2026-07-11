# Task 3.2 Report: Enforce validation at adapter spawn boundaries

## What was implemented

- Added `from eduflow.runtime.names import validate_agent_name, validate_model_name` to `src/eduflow/runtime/lifecycle.py`.
- Inserted validation calls in `_spawn_once()` immediately after `get_adapter(cli)` succeeds and right before the line that calls `adapter.spawn_cmd(agent, model)` and builds the tmux spawn command.
- Created `tests/unit/test_runtime_lifecycle_spawn_validation.py` with two tests:
  - `test_spawn_rejects_bad_agent_name` — semicolon in agent name must raise `InvalidNameError` before `tmux.spawn_agent` is invoked.
  - `test_spawn_rejects_bad_model_name` — slash in model name must raise `InvalidNameError` before `tmux.spawn_agent` is invoked.

This ensures malformed agent/model names can never reach any adapter's `spawn_cmd()` and therefore cannot be interpolated into a shell command executed by tmux.

## RED/GREEN TDD evidence

### RED — failing test before patch

```bash
python3 tests/run.py spawn_validation
```

Output:

```text
Failed: DID NOT RAISE <class 'eduflow.runtime.names.InvalidNameError'>
```

The test expected `InvalidNameError` but `provision_pane` proceeded toward spawn because validation was not yet enforced.

### GREEN — passing test after patch

```bash
python3 tests/run.py spawn_validation
```

Output:

```text
OK  unit/test_runtime_lifecycle_spawn_validation: 2 passed
OK  unit/test_runtime_lifecycle: 35 passed

tests: 37 passed, 0 failed
```

## Full suite test results

```bash
python3 tests/run.py
```

Output:

```text
tests: 2276 passed, 37 failed
```

The 37 failures match the pre-existing baseline; no new failures were introduced by this change.

## Files changed

- `src/eduflow/runtime/lifecycle.py`
- `tests/unit/test_runtime_lifecycle_spawn_validation.py`

## Commit SHA and subject

```text
52b69260 security: validate agent/model names before pane spawn
```

## Self-review findings

- Validation is placed immediately before the only call site that feeds `agent` and `model` into `adapter.spawn_cmd`, satisfying the "before any tmux spawn side effect" requirement.
- `get_adapter(cli)` is allowed to fail first with `CONFIG_ERROR`, preserving existing behavior for unknown CLI values.
- Tests use the established `isolated_env()` and `tmux_patch()` fixture pattern and assert that `spawn_agent` is never called when validation fails.
- No new external dependencies were introduced; validation uses the shared stdlib-only `eduflow.runtime.names` module from Task 3.1.
- Full suite confirms the change does not regress existing lifecycle behavior (all 35 lifecycle tests pass).

## Concerns

None. The change is minimal, scoped, and matches the requested boundary.
