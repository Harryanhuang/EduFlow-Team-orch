# Task 4.3 Report: Harden SQLite Memory DB Permissions

## What was implemented

Modified `src/eduflow/memory/db.py` so that after `sqlite3.connect()` creates the SQLite memory database file, the file mode is immediately set to `0o600` (owner read/write only) via `os.chmod`. Added a unit test in `tests/unit/test_memory_db_permissions.py` that overrides `EDUFLOW_STATE_DIR` to a temporary directory, opens the DB, and asserts the resulting file mode.

A small isolation adjustment (`db.close()` before `db.get_conn()`) was added to the test so it works both when run in isolation and within the stdlib runner's single-process full suite, where a per-thread connection cache would otherwise return a connection to a previously-created DB.

## RED/GREEN TDD evidence

### Step 1-2: RED (test fails before patch)

```bash
$ python3 tests/run.py permissions
FAIL unit/test_memory_db_permissions: 0 passed, 1 failed
FAIL unit/test_runtime_paths_permissions: 2 passed

unit.test_memory_db_permissions::test_memory_db_is_600
AssertionError
```

(Filtered run showed the new test failing as expected because the DB file was created with default permissions.)

### Step 3-4: GREEN (test passes after patch)

```bash
$ python3 tests/run.py permissions
OK  unit/test_memory_db_permissions: 1 passed
OK  unit/test_runtime_paths_permissions: 2 passed

tests: 3 passed, 0 failed
```

## Full suite test results

```bash
$ python3 tests/run.py
tests: 2285 passed, 37 failed
```

Baseline before this change was `2284 passed, 37 failed`. The new test adds one passing case, and the failure count remains at the pre-existing baseline of 37. No new failures were introduced.

## Files changed

- `src/eduflow/memory/db.py`
  - Added `import os`
  - After opening the SQLite connection in `get_conn()`, call `os.chmod(db_path, 0o600)` if the file exists.
- `tests/unit/test_memory_db_permissions.py`
  - New test `test_memory_db_is_600` asserting the DB file is created with mode `0o600`.

## Commit

- **SHA:** `9978c879`
- **Subject:** `security: set memory db file permissions to 0o600`

## Self-review findings

- The patch is minimal and scoped: only the DB-file permission change and its test.
- The change uses only the stdlib (`os`, `stat`) as required.
- The test is unit-testable via `EDUFLOW_STATE_DIR` override to a temp directory, matching the global constraint.
- The production change correctly runs after `sqlite3.connect()` creates the file, ensuring new DBs get the hardened mode.
- Existing cached connections are not affected; only newly-created files are chmod'd.
- No debug/TODO/HACK comments added.
- Commit message uses the required `security:` prefix.

## Concerns

- The exact test code in the task brief omitted `db.close()`, which caused the test to fail in the full suite because the stdlib runner reuses the per-thread cached `_local.conn`. Adding `db.close()` before `db.get_conn()` resolves this and matches the existing `test_memory_manager_loop.py` pattern. This is noted as a minor deviation from the literal brief code, but it is necessary for the suite-level requirement of "no new failures."
- The `os.chmod` is only applied at creation time in `get_conn()`. If a user manually changes permissions later, EduFlow will not re-apply them on every connection. This is consistent with the task scope (harden creation).
