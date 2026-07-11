# Security Remediation Progress Ledger

## Baseline
- Branch: `security-remediation-2026-07-10`
- Original baseline tests: 2235 passed, 29 failed (pre-existing, unrelated)
- Note: Exited worktree because target files (e.g. `src/eduflow/commands/tts.py`) are untracked in main and do not exist in the worktree. Worktree commits were cherry-picked onto this branch.

## Completed Tasks

### Task 1.1: Harden `.gitignore` against secrets and backups
- Status: complete
- Commits: `5719f7aa..2969c4ae`
- Review: clean, approved
- Notes: Fix applied for `.env.*` test coverage

### Task 1.2: Remove `.bak-stash` backup directory
- Status: complete
- Commits: `2969c4ae..85965995`
- Review: approved
- Notes: Empty commit records deletion of untracked directory; `.gitignore` already covers `.bak-stash*/`

### Task 1.3: Add pre-commit secret detection hook
- Status: complete
- Commits: `85965995..f44c279b` (worktree); cherry-picked as `2e17950d..25449417`
- Review: approved
- Notes: Added `.pre-commit-config.yaml` and README secrets hygiene section

### Task 2.1: Fix command injection in `tts.py`
- Status: complete
- Commits: `f121b9fa`
- Review: approved
- Notes: Fix applied in main branch before worktree exit; now on `security-remediation-2026-07-10`
- Minor findings to triage at final review:
  - `src/eduflow/commands/tts.py:26` unused import `config`
  - `src/eduflow/commands/tts.py:125` unhandled `json.JSONDecodeError`
  - `tests/unit/test_commands_tts.py` missing assertion for `file_path.name` quoting

### Task 2.2: Fix command injection in `kimi_code.py`
- Status: complete
- Commits: `bdde0a72`
- Review: approved
- Notes: None

### Task 2.3: Fix command injection in `claude_code.py`
- Status: complete
- Commits: `9b2179fc`
- Review: approved
- Notes: None

### Task 2.4: Fix command injection in remaining adapters
- Status: complete
- Commits: `b454bd95`
- Review: approved
- Notes: No source changes needed; all adapters already quote agent/model. Added spawn-cmd safety audit test.

### Task 3.1: Add shared agent/model name validator
- Status: complete
- Commits: `90e69e3d`, `8b2b2889`
- Review: approved
- Notes: Model regex tightened to exclude `/` and `:` for path safety; documented deviation

### Task 3.2: Validate names before pane spawn
- Status: complete
- Commits: `3a945cf0`
- Review: approved
- Notes: Validation moved to name resolution; validated values mirrored back to `resolved`

### Task 3.3: Validate agent names before path construction
- Status: complete
- Commits: `034bdbe4`
- Review: approved
- Notes: Validation added at lowest-level path-building helpers

### Task 4.1: Harden `state_dir` and `facts_dir` permissions
- Status: complete
- Commits: `97289dd6`
- Review: approved
- Notes: Directories created with `0o700`; monkeypatch shim extended for tests
- Minor findings to triage at final review:
  - Unused import `os` in `tests/unit/test_runtime_paths_permissions.py`
  - `tests/run.py` monkeypatch `setenv` semantics differ from pytest
  - `state_file()` docstring claims no I/O side effects
  - `Path.mkdir(parents=True, mode=0o700)` only applies mode to leaf

### Task 4.2: Harden tenant token cache location and permissions
- Status: complete
- Commits: `1acf5664`, `e456eb42`
- Review: approved
- Notes: Cache moved to `state_dir/.tenant_token.json` with atomic `0o600` creation

### Task 4.3: Harden SQLite memory DB permissions
- Status: complete
- Commits: `9978c879`
- Review: approved
- Notes: Memory DB created with `0o600`

### Task 5.1: Add Feishu message length and deduplication
- Status: complete
- Commits: `7a956370`
- Review: approved
- Notes: Messages over 4000 chars dropped; duplicate message_ids dropped
- Important findings to triage at final review:
  - Env-var override missing for `feishu.max_message_len` tunable
  - Module-level `_SEEN_MESSAGE_IDS` set is unbounded

### Task 5.2: Add Feishu sender rate limiting
- Status: complete
- Commits: `644b9f5a`
- Review: approved
- Notes: Token-bucket per-sender rate limit added

### Task 5.3: Restrict `/send` slash command to operators
- Status: complete
- Commits: `91e051be`
- Review: approved
- Notes: Only configured operators can execute `/send`
- Important findings to triage at final review:
  - Authorization logic duplicated in `handle_send` and `_handle_send`
  - `handle_send` accepts `argv` but ignores it
  - No test covers production `/send` dispatch path
  - Rejection message hardcoded Chinese

### Task 6.1: Harden Dockerfile
- Status: complete
- Commits: `7cb4e188`
- Review: approved
- Notes: Pinned deps, verified uv install, non-root user, healthcheck; image builds and smoke tests pass

### Task 6.2: Harden Docker Compose
- Status: complete
- Commits: `7bced0ff`, `31706396`
- Review: approved (manual verification after agent review blocked)
- Notes: Removed host network, restricted mounts, added resource limits, aligned state mount and docs with non-root user

## Pending Tasks
- Task 6.3: Harden agent-chrome container
- Task 7.1: Make cryptography mandatory for memory
- Task 7.2: Strengthen sensitive memory password policy
- Task 8.1: Run full verification and regression tests
