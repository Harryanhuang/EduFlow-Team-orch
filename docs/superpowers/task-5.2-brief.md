### Task 5.2: Add sender rate limiting

**Files:**
- Modify: `src/eduflow/feishu/router.py`
- Test: `tests/unit/test_feishu_router_rate_limit.py` (new)

**Interfaces:**
- Consumes: `time.monotonic()`
- Produces: `classify_event()` drops messages that exceed a sender rate limit.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_feishu_router_rate_limit.py
import time
from eduflow.feishu.router import classify_event


def test_sender_rate_limit(monkeypatch):
    # Allow 2 messages per 10 seconds for testing.
    monkeypatch.setattr("eduflow.feishu.router._RATE_LIMIT_MAX", 2)
    monkeypatch.setattr("eduflow.feishu.router._RATE_LIMIT_WINDOW_S", 10)

    base = {"sender_type": "user", "sender_id": "u1", "chat_id": "c1", "text": "hi"}
    assert classify_event({**base, "message_id": "m1"}, [], None, "c1").action != "DROP"
    assert classify_event({**base, "message_id": "m2"}, [], None, "c1").action != "DROP"
    assert classify_event({**base, "message_id": "m3"}, [], None, "c1").action == "DROP"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_feishu_router_rate_limit.py`
Expected: FAIL.

- [ ] **Step 3: Patch `router.py`**

Add a simple token-bucket-style per-sender rate limit:

```python
import time
from collections import deque

_RATE_LIMIT_MAX = 10          # messages
_RATE_LIMIT_WINDOW_S = 60     # seconds
_SENDER_TIMESTAMPS = {}


def _rate_limit_ok(sender_id: str) -> bool:
    now = time.monotonic()
    window = _SENDER_TIMESTAMPS.setdefault(sender_id, deque())
    while window and window[0] < now - _RATE_LIMIT_WINDOW_S:
        window.popleft()
    if len(window) >= _RATE_LIMIT_MAX:
        return False
    window.append(now)
    return True
```

In `classify_event`, before processing:
```python
if not _rate_limit_ok(event.get("sender_id", "")):
    return Decision(action="DROP", reason="rate limit exceeded")
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_feishu_router_rate_limit.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/feishu/router.py tests/unit/test_feishu_router_rate_limit.py
git commit -m "security: add per-sender feishu rate limiting"
```
