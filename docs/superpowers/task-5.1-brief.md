### Task 5.1: Add message length limit and deduplication

**Files:**
- Modify: `src/eduflow/feishu/router.py`
- Test: `tests/unit/test_feishu_router_limits.py` (new)

**Interfaces:**
- Consumes: Tunable max length from `eduflow.toml` (default 4000)
- Produces: `classify_event()` returns `DROP` for oversized or duplicate messages.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_feishu_router_limits.py
from eduflow.feishu.router import classify_event, Decision


def test_oversized_message_is_dropped():
    event = {
        "message_id": "m1",
        "sender_type": "user",
        "sender_id": "u1",
        "chat_id": "c1",
        "text": "x" * 4001,
    }
    decision = classify_event(event, agents=[], manager=None, chat_id="c1")
    assert decision.action == "DROP"


def test_duplicate_message_is_dropped():
    event = {"message_id": "m1", "sender_type": "user", "sender_id": "u1", "chat_id": "c1", "text": "hi"}
    classify_event(event, agents=[], manager=None, chat_id="c1")
    decision = classify_event(event, agents=[], manager=None, chat_id="c1")
    assert decision.action == "DROP"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_feishu_router_limits.py`
Expected: FAIL.

- [ ] **Step 3: Patch `router.py`**

Add a module-level set for seen message IDs and a max length constant:

```python
import functools
from eduflow.runtime import tunables

_MAX_MESSAGE_LEN = 4000
_SEEN_MESSAGE_IDS = set()


def _max_message_len() -> int:
    cfg = tunables.load() or {}
    return int(cfg.get("feishu", {}).get("max_message_len", _MAX_MESSAGE_LEN))


def classify_event(event, agents, manager, chat_id):
    text = event.get("text", "")
    msg_id = event.get("message_id", "")
    if len(text) > _max_message_len():
        return Decision(action="DROP", reason="message too long")
    if msg_id in _SEEN_MESSAGE_IDS:
        return Decision(action="DROP", reason="duplicate message_id")
    _SEEN_MESSAGE_IDS.add(msg_id)
    # ... existing logic ...
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_feishu_router_limits.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/feishu/router.py tests/unit/test_feishu_router_limits.py
git commit -m "security: drop oversized and duplicate feishu messages"
```
