# Task 2.3 Report: Fix command injection in `agents/claude_code.py`

## What was implemented

Patched `ClaudeCodeAdapter.spawn_cmd()` in `src/eduflow/agents/claude_code.py` to apply `shlex.quote()` to the `--model` and `--name` arguments. These values are derived from external/agent-controlled inputs (`agent` and `model` parameters) and were previously interpolated directly into the shell command string, allowing command injection.

Added a new unit test `tests/unit/test_agents_claude_code.py` with `test_spawn_cmd_quotes_model_and_agent()` that supplies shell metacharacters in both `agent` and `model` and asserts the resulting command contains the `shlex.quote()`-escaped forms.

## RED/GREEN TDD evidence

### RED — failing test before fix

```bash
$ python3 tests/run.py claude_code
FAIL unit/test_agents_claude_code: 0 passed, 1 failed

unit.test_agents_claude_code::test_spawn_cmd_quotes_model_and_agent
Traceback (most recent call last):
  ...
  File ".../tests/unit/test_agents_claude_code.py", line 12, in test_spawn_cmd_quotes_model_and_agent
    assert shlex.quote("a; echo pwned") in cmd
AssertionError

tests: 0 passed, 1 failed
```

### GREEN — passing test after fix

```bash
$ python3 tests/run.py claude_code
OK  unit/test_agents_claude_code: 1 passed

tests: 1 passed, 0 failed
```

## Full suite test results

```bash
$ python3 tests/run.py
...
tests: 2270 passed, 37 failed
```

Result matches the pre-existing baseline of 37 failures; no new failures were introduced by this change.

## Files changed

- `src/eduflow/agents/claude_code.py` — added `shlex.quote()` around `--model {model}` and `--name {agent}`.
- `tests/unit/test_agents_claude_code.py` — new test module verifying the quoting behavior.

## Commit

```
9b2179fc security: quote model and agent names in claude spawn command
```

## Self-review findings

- Change is minimal and targeted: only the two interpolation points were modified.
- `shlex` is already imported and used elsewhere in the same function, so no new dependencies.
- Test directly exercises shell metacharacters (`;`) in both parameters.
- No adjacent code was refactored.
- No debug/TODO/HACK code added.

## Concerns

None. The patch is a straightforward stdlib hardening consistent with the existing quoting already applied to `oauth_token`, `agent_home(agent)`, and `claude_bin` in the same command string.
