# Task 4.2 Fix Report: Harden Tenant Token Cache Write Path

## What changed

`src/eduflow/feishu/lark.py`:

- **Atomic, restrictive cache creation.** The tenant token cache is now created with `os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)` and written through `os.fdopen`. This guarantees the file is created with `0o600` permissions from the start, eliminating the previous race window where `Path.write_text()` created the file with default umask permissions before `os.chmod(..., 0o600)` ran.
- **Defer cache path resolution.** `_ensure_tenant_token()` now keeps `cache_path` as `None` until it actually needs to read from or write to disk. When `LARKSUITE_CLI_TENANT_ACCESS_TOKEN` is already set, the function returns early without calling `_tenant_token_cache_path()` and therefore without creating the state directory.

`tests/unit/test_feishu_lark.py`:

- Added `test_ensure_tenant_token_cache_created_with_restrictive_permissions()` — verifies the cache file is created with mode `0o600`.
- Added `test_subprocess_env_does_not_create_state_dir_when_env_token_present()` — verifies `subprocess_env()` does not touch the cache path or create `EDUFLOW_STATE_DIR` when the tenant token is already present in the environment.

## Test results

Focused test file:

```
$ python3 -m pytest tests/unit/test_feishu_lark.py -v
46 passed in 0.12s
```

Full suite:

```
$ python3 tests/run.py
tests: 2284 passed, 37 failed
```

The 37 failures match the pre-existing baseline and are unrelated to this change.

## Commit

- **SHA:** `e456eb42`
- **Subject:** `security: harden tenant token cache write path`

## Concerns

None. The change is minimal, focused, and the new tests cover both the permission hardening and the lazy cache-path resolution.
