# Task 2.2 Report: Fix command injection in `agents/kimi_code.py`

## What was implemented

- Added a new unit test `tests/unit/test_agents_kimi_code.py::test_spawn_cmd_quotes_agent_name` that verifies `KimiCodeAdapter.spawn_cmd()` quotes the agent name and does not embed it unescaped in the generated shell command.
- Patched `src/eduflow/agents/kimi_code.py` to wrap `agent` with `shlex.quote()` before interpolating it into the `KIMI_AGENT=...` environment assignment.

The original implementation built the command string as:

```python
return f"DISABLE_UPDATE_CHECK=1 KIMI_AGENT={agent} kimi --yolo"
```

A malicious agent name such as `worker; echo pwned` would be interpolated verbatim, allowing arbitrary shell command execution when the command is later passed to a shell or `tmux send-keys`.

The patched implementation uses `shlex.quote(agent)` to ensure the value is treated as a single shell word.

## RED/GREEN TDD evidence

### RED — failing test before patch

```bash
$ python3 tests/run.py agents_kimi_code
FAIL unit/test_agents_kimi_code: 0 passed, 1 failed

unit.test_agents_kimi_code::test_spawn_cmd_quotes_agent_name
AssertionError
```

### GREEN — passing test after patch

```bash
$ python3 tests/run.py agents_kimi_code
OK  unit/test_agents_kimi_code: 1 passed

tests: 1 passed, 0 failed
```

## Full suite test results

Ran `python3 tests/run.py` with the patch applied and compared against a baseline run with the patch stashed:

| Run | Passed | Failed |
|-----|--------|--------|
| Baseline (patch stashed) | 2267 | 37 |
| With patch | 2269 | 37 |

No new failures were introduced by this change. The 37 pre-existing failures are in unrelated modules (`test_memory_v3_p2`, `test_memory_v3_p3`, `test_residency_sleep`, `test_residency_wake`, `test_tool_risk`, and `integration/test_inprocess_chain`) and are part of the broader branch baseline.

## Files changed

- `src/eduflow/agents/kimi_code.py`
- `tests/unit/test_agents_kimi_code.py`

## Commit

- **SHA:** `bdde0a72`
- **Subject:** `security: quote agent name in kimi spawn command`

## Self-review findings

- The fix uses only the stdlib (`shlex.quote`), satisfying the "no new external dependencies" constraint.
- The test directly exercises the injection payload `worker; echo pwned` and asserts both the positive and negative conditions.
- The change preserves the existing public CLI contract: `spawn_cmd(agent: str, model: str) -> str` signature is unchanged.
- No debug code, `TODO`, `HACK`, or `console.log` left behind.
- Diff is minimal (12 insertions, 2 deletions).

## Concerns

- The brief's sample test instantiated `KimiCodeAdapter({})`, but the current `CliAdapter` base class takes no constructor arguments. The test was adjusted to `KimiCodeAdapter()` to match the actual codebase API while preserving the intended assertion logic.
- The full integration suite has 37 pre-existing failures on this branch. The task baseline note mentioned 29; the actual observed baseline is 37. The change did not increase the failure count.
