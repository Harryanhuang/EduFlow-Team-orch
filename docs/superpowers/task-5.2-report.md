# Task 5.2 Report: Add sender rate limiting to Feishu router

## What was implemented

Added a simple token-bucket-style per-sender rate limit to `src/eduflow/feishu/router.py`:

- `_RATE_LIMIT_MAX = 10` messages per `_RATE_LIMIT_WINDOW_S = 60` seconds.
- `_SENDER_TIMESTAMPS` stores a `deque` of `time.monotonic()` timestamps per sender.
- `_rate_limit_ok(sender_id)` drops expired timestamps and rejects the message if the sender already has `_RATE_LIMIT_MAX` entries in the current window.
- `classify_event()` now returns `Decision(action="DROP", reason="rate limit exceeded")` immediately after the cross-team check when a sender is over the limit.

A `_reset_rate_limit()` helper was added so existing tests can isolate themselves from the new module-level state. The helper is only used by tests.

## RED / GREEN TDD evidence

### RED — failing test before patch

```bash
$ python3 tests/run.py rate_limit
FAIL unit/test_feishu_router_rate_limit: 0 passed, 1 failed

unit.test_feishu_router_rate_limit::test_sender_rate_limit
Traceback (most recent call last):
  ...
  File ".../tests/unit/test_feishu_router_rate_limit.py", line 8, in test_sender_rate_limit
    monkeypatch.setattr(router, "_RATE_LIMIT_MAX", 2)
  File ".../tests/run.py", line 37, in setattr
    self._undo.append((obj, name, getattr(obj, name)))
AttributeError: module 'eduflow.feishu.router' has no attribute '_RATE_LIMIT_MAX'
```

### GREEN — passing test after patch

```bash
$ python3 tests/run.py rate_limit
OK  unit/test_feishu_router_rate_limit: 1 passed

tests: 1 passed, 0 failed
```

## Full suite test results

Baseline (without new test file):

```bash
$ python3 tests/run.py
tests: 2282 passed, 42 failed
```

After implementation:

```bash
$ python3 tests/run.py
tests: 2283 passed, 42 failed
```

The new rate-limit test adds one passing test; no new failures were introduced relative to the actual baseline.

> Note: The task brief listed the baseline as 37 pre-existing failures. On this checkout the actual baseline is 42 failures in the same modules (memory, residency, cards_v2, commands_tts/runtime_guard/task, tool_risk, integration/inprocess_chain). The 42 failures are unchanged by this change.

## Files changed

- `src/eduflow/feishu/router.py` — rate-limit logic and `_reset_rate_limit()` helper.
- `tests/unit/test_feishu_router_rate_limit.py` — new unit test (see adaptation notes below).
- `tests/unit/test_feishu_router.py` — reset rate-limit state in `_ev()` for test isolation.
- `tests/unit/test_feishu_router_limits.py` — reset rate-limit state before each test.
- `tests/unit/test_feishu_subscribe.py` — reset rate-limit state in `_wrapped()` and every `test_*` function.

## Commit

```
644b9f5a security: add per-sender feishu rate limiting
```

## Adaptations made to the brief

The brief specified the test exactly as:

```python
monkeypatch.setattr("eduflow.feishu.router._RATE_LIMIT_MAX", 2)
classify_event({**base, "message_id": "m1"}, [], None, "c1")
```

Two adaptations were required for the project’s stdlib-only test runner and current API:

1. The stdlib runner’s `_MiniMonkeyPatch.setattr()` does not support dotted import paths, so the test uses `monkeypatch.setattr(router, "_RATE_LIMIT_MAX", 2)` (object form), which works with both the stdlib runner and pytest.
2. `classify_event()` has been keyword-only after the first positional argument for some time, so the test uses keyword arguments (`agents=`, `manager=`, `chat_id=`).

The behavioral assertions (2 allowed, 3rd dropped) remain exactly as specified.

## Self-review findings

- Rate-limit constants are module-level and match the brief (`10` messages / `60` seconds).
- Decision reason string is stable (`"rate limit exceeded"`) and follows the existing reason-string convention.
- The check is placed after `cross_team` and before bot/empty/slash/text processing, so cross-team events are dropped without touching the rate-limit bucket.
- `_reset_rate_limit()` is private, documented as test-only, and does not change production behavior.
- No new external dependencies; only `time` and `collections.deque` from the stdlib.
- No `TODO`, `HACK`, `console.log`, or debug code left behind.

## Concerns

- The module-level `_SENDER_TIMESTAMPS` dict provides per-process rate limiting only. In a multi-process router deployment, a determined sender could exceed the intended limit by hitting different processes. This matches the brief’s simple token-bucket scope and is acceptable for the current single-process `commands/router.py` architecture, but should be revisited if the router is ever scaled horizontally.
- Existing tests required `_reset_rate_limit()` calls to stay green because the stdlib runner imports modules once and shares module-level state across test functions. This is a consequence of adding production-correct module-level state, not a logic issue.
