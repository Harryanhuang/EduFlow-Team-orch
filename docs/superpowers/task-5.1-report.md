# Task 5.1 Report: Add message length limit and deduplication to Feishu router

## What was implemented

- Added a tunable message-length limit to `src/eduflow/feishu/router.py`.
  - Default: 4000 characters.
  - Override: `[feishu]` table in `eduflow.toml`, key `max_message_len`.
- Added duplicate-message detection based on `message_id`.
  - Callers that already pass `seen_msg_ids` keep the existing `dedup` drop reason.
  - Callers without a dedup set use a module-level `_SEEN_MESSAGE_IDS` set and get the new `duplicate message_id` drop reason.
  - Routed messages are recorded; dropped messages are not, so unrelated fixtures/tests that reuse a message id do not false-positive as duplicates.
- Made `classify_event()` accept the brief's `agents=` keyword while keeping backward compatibility with the existing `team_agents=` keyword.
- Changed `Action` to a `str`-mixin enum with uppercase values so the brief's `decision.action == "DROP"` assertion passes while preserving all existing `is Action.DROP` identity checks.
- Updated `tests/unit/test_feishu_router.py` `_ev()` helper to generate unique `message_id`s per call, and adjusted the one test that explicitly relied on the fixed `"om_1"` default.

## RED/GREEN TDD evidence

### Step 1: Failing test written exactly as specified

File: `tests/unit/test_feishu_router_limits.py`

### Step 2: RED — run the new test before patch

```bash
python3 tests/run.py feishu_router_limits
```

Output:

```
FAIL unit/test_feishu_router_limits: 0 passed, 2 failed
...
TypeError: classify_event() got an unexpected keyword argument 'agents'
```

### Step 3: Patch applied to `src/eduflow/feishu/router.py`

### Step 4: GREEN — run the new test after patch

```bash
python3 tests/run.py feishu_router_limits
```

Output:

```
OK  unit/test_feishu_router_limits: 2 passed

tests: 2 passed, 0 failed
```

## Full suite test results

```bash
python3 tests/run.py
```

Output:

```
tests: 2287 passed, 37 failed
```

This matches the stated pre-existing baseline of 37 failures; no new failures were introduced.

## Files changed

- `src/eduflow/feishu/router.py`
- `tests/unit/test_feishu_router_limits.py` (new)
- `tests/unit/test_feishu_router.py`

## Commit

- SHA: `7a956370`
- Subject: `security: drop oversized and duplicate feishu messages`

## Self-review findings

- All modified and new files pass the project test runner.
- No new external dependencies were added (uses stdlib `Enum` mixin + existing `eduflow.runtime.tunables`).
- The change keeps the existing `seen_msg_ids` parameter semantics; production callers (`feishu/subscribe.py`) are unaffected.
- The `Action` enum change is backward-compatible for all in-repo callers because they use identity checks (`is Action.X`) or construct with `Action.X`, and no code depends on the previous lowercase `.value`.
- Leftover debug code check: no `print`, `TODO`, `HACK`, or `debugger` statements added.

## Concerns

- The module-level `_SEEN_MESSAGE_IDS` set is unbounded. Production callers pass their own bounded `seen_msg_ids`, so this only affects test/convenience callers. In a future hardening pass, consider capping or trimming the module set using the existing `router.seen_max_lines` tunable.
- The brief's test imports `Decision` but does not use it; the file is kept exactly as specified.
