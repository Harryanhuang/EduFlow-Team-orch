### Task 4.2: Harden tenant token cache

**Files:**
- Modify: `src/eduflow/feishu/lark.py`
- Test: `tests/unit/test_feishu_lark_token_cache.py` (new)

**Interfaces:**
- Consumes: `state_file()` from `eduflow.runtime.paths`
- Produces: Tenant token cache is written under `state_dir()` with `0o600`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_feishu_lark_token_cache.py
import os
import stat
from pathlib import Path


def test_tenant_token_cache_uses_state_dir_and_600(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.feishu import lark
    from eduflow.runtime import paths

    cache_path = lark._tenant_token_cache_path()
    assert cache_path.parent == paths.state_dir()

    # Simulate a write
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text('{"token": "x"}', encoding="utf-8")
    os.chmod(cache_path, 0o600)

    mode = stat.S_IMODE(cache_path.stat().st_mode)
    assert mode == 0o600
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_feishu_lark_token_cache.py`
Expected: FAIL (`_tenant_token_cache_path` does not exist).

- [ ] **Step 3: Patch `lark.py`**

At the top of `lark.py`, change:
```python
_TENANT_TOKEN_CACHE = "/tmp/eduflow_tenant_token.json"
```
to:
```python
def _tenant_token_cache_path() -> Path:
    from eduflow.runtime.paths import state_file
    return state_file(".tenant_token.json")
```

Then replace every usage of `_TENANT_TOKEN_CACHE` with `_tenant_token_cache_path()`.

When writing the cache, set permissions:
```python
cache_path.write_text(json.dumps(record), encoding="utf-8")
os.chmod(cache_path, 0o600)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_feishu_lark_token_cache.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/feishu/lark.py tests/unit/test_feishu_lark_token_cache.py
git commit -m "security: move tenant token cache to state_dir with 0o600"
```
