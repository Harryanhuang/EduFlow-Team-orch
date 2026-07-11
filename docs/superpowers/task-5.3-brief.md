### Task 5.3: Restrict slash command `/send` to privileged senders

**Files:**
- Modify: `src/eduflow/feishu/slash.py`
- Test: `tests/unit/test_feishu_slash_authorization.py` (new)

**Interfaces:**
- Consumes: `team.json` or `eduflow.toml` `[team.operators]` whitelist
- Produces: `/send` returns an error card if the caller is not in the operator list.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_feishu_slash_authorization.py
import pytest
from eduflow.feishu.slash import handle_send


def test_send_rejected_for_unauthorized_user(monkeypatch):
    monkeypatch.setattr("eduflow.feishu.slash._operator_ids", {"u_admin"})
    result = handle_send(sender_id="u_attacker", argv=["worker_cc", "hello"])
    assert result.get("allowed") is False


def test_send_allowed_for_operator(monkeypatch):
    monkeypatch.setattr("eduflow.feishu.slash._operator_ids", {"u_admin"})
    result = handle_send(sender_id="u_admin", argv=["worker_cc", "hello"])
    assert result.get("allowed") is not False
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_feishu_slash_authorization.py`
Expected: FAIL.

- [ ] **Step 3: Patch `slash.py`**

Load operators from config:
```python
from eduflow.runtime import config


def _operator_ids() -> set[str]:
    cfg = config.load_team() or {}
    operators = cfg.get("team", {}).get("operators", [])
    return set(operators)
```

In the `/send` handler:
```python
if sender_id not in _operator_ids():
    return {"allowed": False, "message": "只有操作员可以执行 /send"}
```

Update `eduflow.toml` schema docs to include:
```toml
[team]
operators = ["u_<admin_feishu_id>"]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_feishu_slash_authorization.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/feishu/slash.py tests/unit/test_feishu_slash_authorization.py eduflow.toml
git commit -m "security: restrict /send slash command to configured operators"
```
