### Task 4.3: Harden SQLite memory DB permissions

**Files:**
- Modify: `src/eduflow/memory/db.py`
- Test: `tests/unit/test_memory_db_permissions.py` (new)

**Interfaces:**
- Consumes: `os.chmod`
- Produces: Newly created SQLite DB file has `0o600`.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_memory_db_permissions.py
import os
import stat


def test_memory_db_is_600(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path / "state"))
    from eduflow.memory import db
    conn = db.get_conn()
    conn.execute("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY)")
    conn.commit()
    db_path = db.memory_db_file()
    mode = stat.S_IMODE(db_path.stat().st_mode)
    assert mode == 0o600
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_memory_db_permissions.py`
Expected: FAIL (mode is 0o644).

- [ ] **Step 3: Patch `db.py`**

Find where the SQLite connection is opened (likely `get_conn()`). After opening/creating the DB file, add:
```python
import os
db_path = memory_db_file()
if db_path.exists():
    os.chmod(db_path, 0o600)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_memory_db_permissions.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/memory/db.py tests/unit/test_memory_db_permissions.py
git commit -m "security: set memory db file permissions to 0o600"
```
