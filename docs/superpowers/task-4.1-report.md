# Task 4.1 Report: Harden `state_dir()` and `facts_dir()` creation

## What was implemented

- `src/eduflow/runtime/paths.py`:
  - `state_dir()` now creates the runtime state directory with mode `0o700` when it does not exist.
  - `facts_dir()` now creates the facts subdirectory under `state_dir()` with mode `0o700` when it does not exist.
- `tests/unit/test_runtime_paths_permissions.py` (new):
  - Two unit tests verifying that `state_dir()` and `facts_dir()` create directories with exactly `0o700` permissions.
- `tests/run.py`:
  - Extended the stdlib runner's `_MiniMonkeyPatch` shim with `setenv()` / `delenv()` so the new tests can run under `python3 tests/run.py` without pytest.
- `tests/unit/test_commands_reset.py`:
  - Updated the previously-named `test_reset_when_state_dir_does_not_exist_still_returns_zero` test. Since `state_dir()` now creates the directory on access, the "does not exist" premise became impossible through the public API. The test was renamed to `test_reset_when_state_dir_is_empty_still_returns_zero` and its assertions were adjusted to verify that `reset --yes` still returns 0 and wipes an empty state directory.

## RED / GREEN TDD evidence

### RED: new permissions test fails before the patch

```text
$ python3 tests/run.py runtime_paths_permissions
FAIL unit/test_runtime_paths_permissions: 0 passed, 2 failed
unit.test_runtime_paths_permissions::test_facts_dir_is_created_with_700
    AssertionError  # p.exists() was False
unit.test_runtime_paths_permissions::test_state_dir_is_created_with_700
    AssertionError  # p.exists() was False
```

### GREEN: new permissions test passes after the patch

```text
$ python3 tests/run.py runtime_paths_permissions
OK  unit/test_runtime_paths_permissions: 2 passed
tests: 2 passed, 0 failed
```

## Full suite results

- **Baseline (before changes):** `tests: 2279 passed, 37 failed`
- **After changes:** `tests: 2281 passed, 37 failed`

The only change is the expected **+2 passed** from the new permission tests. No new failures were introduced.

## Files changed

- `src/eduflow/runtime/paths.py`
- `tests/unit/test_runtime_paths_permissions.py` (new)
- `tests/run.py`
- `tests/unit/test_commands_reset.py`

## Commit

```text
97289dd6 security: create state and facts directories with 0o700
```

## Self-review findings

- The patch matches the brief exactly for `state_dir()` and `facts_dir()`.
- The new test file matches the brief exactly; the only deviation was adding `setenv` support to the stdlib runner so the pytest-style `monkeypatch.setenv` calls execute under `python3 tests/run.py`.
- The `test_commands_reset.py` adjustment is not a test hack: the production behavior intentionally changed, so a test that asserted the old side-effect-free behavior had to be updated to remain meaningful.
- No debug code, `TODO`, `HACK`, or `console.log` was added.
- All modified files compile (`python3 -m py_compile`).

## Concerns

- `state_dir()` and `facts_dir()` are no longer pure path-resolution functions; they now perform I/O and create directories. Callers that previously assumed these were side-effect-free (e.g., `state_file()`, `router_pid_file()`) now indirectly create the state directory. This is acceptable for runtime paths but is a subtle semantic change worth noting.
- The stdlib runner monkeypatch shim is now slightly larger. Future tests using `monkeypatch.setenv` will rely on it.
- Existing directories are **not** re-permissioned by this change; only newly created directories get `0o700`. If a deployment already has a world-readable `~/.eduflow`, an operator should manually `chmod 700` it.
