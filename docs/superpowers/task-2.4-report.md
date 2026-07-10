# Task 2.4 Report: Audit and fix command injection in remaining adapters

## Status
DONE — no adapter code changes were required; all audited adapters already quote agent/model values. Added a security regression test to prevent future regressions.

## Adapters audited

| Adapter | File | Uses `agent`? | Uses `model`? | Quotes values? | Patched? |
|---|---|---|---|---|---|
| Codex CLI | `src/eduflow/agents/codex_cli.py` | env + path | dropped unless OpenAI prefix | yes | no |
| Gemini CLI | `src/eduflow/agents/gemini_cli.py` | env | not used | yes | no |
| Qwen Code | `src/eduflow/agents/qwen_code.py` | env | not used | yes | no |
| MiMo Code | `src/eduflow/agents/mimo_code.py` | env | argv | yes | no |
| Qoder CLI CN | `src/eduflow/agents/qoder_cli_cn.py` | argv `--name` | argv `--model` | yes (per-arg shlex.quote) | no |
| Hermes Agent | `src/eduflow/agents/hermes_agent.py` | prefixed `eduflow-<agent>` in `--source` | argv `--model` | yes (per-arg shlex.quote) | no |

## RED/GREEN TDD evidence

### Initial strict-test attempt (RED)

Wrote the literal test from the brief using `shlex.quote(payload) in cmd`:

```text
AssertionError: codex: model value not quoted in spawn command:
  HOME='.../a; echo pwned' CODEX_HOME='...' CODEX_AGENT='a; echo pwned' codex --dangerously-bypass-approvals-and-sandbox

gemini: model value not quoted in spawn command:
  DISABLE_UPDATE_CHECK=1 GEMINI_AGENT='a; echo pwned' gemini --approval-mode=yolo

qwen: model value not quoted in spawn command:
  DISABLE_UPDATE_CHECK=1 QWEN_AGENT_NAME='a; echo pwned' qwen --yolo

hermes: agent value not quoted in spawn command:
  cd '...' && hermes chat --cli --model 'm; echo pwned' --provider "${HERMES_PROVIDER:-minimax}" --source 'eduflow-a; echo pwned'
```

These failures were false positives: codex/gemini/qwen legitimately drop or ignore `model`, and hermes prefixes the agent with `eduflow-` before quoting. The literal substring test does not measure the actual security property.

### Corrected security-test (GREEN)

Replaced the assertion with a shell-tokenization check: `shlex.split(cmd)` must not expose `echo` or `pwned` as top-level tokens.

```bash
$ python3 tests/run.py spawn_safety
OK  unit/test_agents_spawn_safety: 1 passed

tests: 1 passed, 0 failed
```

## Full suite results

```bash
$ python3 tests/run.py
tests: 2271 passed, 37 failed
```

The failure count matches the pre-existing baseline of 37 failures; no new failures were introduced by the added test.

## Files changed

- `tests/unit/test_agents_spawn_safety.py` (new)

No adapter source files were modified because all audited adapters already use `shlex.quote` or equivalent per-argument quoting.

## Commit

- SHA: `b454bd95`
- Subject: `security: add spawn-cmd injection safety audit for remaining adapters`

## Self-review findings

- The new test works with the stdlib-only runner (`tests/run.py`) by avoiding pytest parametrization and looping internally.
- The test imports only `shlex` from the stdlib and uses no external dependencies.
- No `TODO`, `HACK`, `debugger`, or `print` statements were left in the new test.
- The test documents why adapters that drop/transform values are still covered.

## Concerns

None. The brief's literal assertion (`shlex.quote(payload) in cmd`) was adjusted to verify the real security property (no shell-token breakout). This deviation is documented above and in the test docstring.
