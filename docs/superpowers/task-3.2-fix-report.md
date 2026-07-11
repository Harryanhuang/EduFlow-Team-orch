# Task 3.2 Fix Report: Enforce validation at adapter spawn boundaries

## What changed

In `src/eduflow/runtime/lifecycle.py`, the `_spawn_once()` function previously validated `agent` and `model` names immediately before calling `adapter.spawn_cmd(agent, model)`. Because the validation happened after `pane_spawn_prefix_for_runtime(resolved)` and `_write_spawn_env_file()` consumed `resolved["agent"]`, an unvalidated agent name could still influence path construction and environment-file naming.

The validation was moved to the point where `agent` and `model` are first resolved, and the validated values are now written back into `resolved` so every downstream consumer uses the sanitized values:

```python
resolved.setdefault("agent", agent)
cli = resolved.get("cli", "claude-code")
model = resolved.get("model", "opus")
agent = validate_agent_name(agent)
model = validate_model_name(model)
resolved["agent"] = agent
resolved["model"] = model
```

The old validation lines just before `adapter.spawn_cmd()` were removed.

## Test results

- Target test:
  ```
  python3 tests/run.py spawn_validation
  OK  unit/test_runtime_lifecycle_spawn_validation: 2 passed
  tests: 2 passed, 0 failed
  ```

- Full suite:
  ```
  python3 tests/run.py
  tests: 2276 passed, 37 failed
  ```
  This matches the documented baseline of 37 pre-existing failures; no new failures were introduced by this change.

## Commit

- **SHA:** `3a945cf0`
- **Subject:** `security: validate agent/model names before pane spawn`
- **Note:** amended the existing Task 3.2 commit (`52b69260`) with `--no-edit`.

## Concerns

None. The fix is minimal, keeps the existing public interface unchanged, and brings the spawn boundary into alignment with the Task 3.2 requirement that validation occur before any pane-spawn side-effect.
