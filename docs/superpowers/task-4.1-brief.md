### Task 4.1: Harden `state_dir()` and `facts_dir()` creation

**Files:**
- Modify: `src/eduflow/runtime/paths.py`
- Test: `tests/unit/test_runtime_paths_permissions.py` (new)

**Interfaces:**
- Consumes: `os.umask`, `Path.mkdir(mode=...)`
- Produces: `state_dir()` and `facts_dir()` are created with `0o700`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_runtime_paths_permissions.py
import os
import stat
from pathlib import Path


def test_state_dir_is_created_with_700(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.runtime import paths
    p = paths.state_dir()
    assert p.exists()
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o700


def test_facts_dir_is_created_with_700(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.runtime import paths
    p = paths.facts_dir()
    assert p.exists()
    mode = stat.S_IMODE(p.stat().st_mode)
    assert mode == 0o700
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_runtime_paths_permissions.py`
Expected: FAIL (mode is 0o755 or similar).

- [ ] **Step 3: Patch `paths.py`**

Replace `state_dir()` and `facts_dir()` with versions that create directories with `0o700`:

```python
def state_dir() -> Path:
    """Top-level directory for all runtime state."""
    path = env_path("EDUFLOW_STATE_DIR") or Path.home() / ".eduflow"
    if not path.exists():
        path.mkdir(parents=True, mode=0o700)
    return path


def facts_dir() -> Path:
    """Where local_facts stores inbox / status / log / heartbeats."""
    path = state_dir() / "facts"
    if not path.exists():
        path.mkdir(parents=True, mode=0o700)
    return path
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_runtime_paths_permissions.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/runtime/paths.py tests/unit/test_runtime_paths_permissions.py
git commit -m "security: create state and facts directories with 0o700"
```
