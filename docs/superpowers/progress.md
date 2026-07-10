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

## Pending Tasks
- Task 3.1: Add shared agent/model name validator
- Task 3.2: Validate names before pane spawn
- Task 3.3: Validate agent names before path construction
- Task 4.1: Harden `state_dir` and `facts_dir` permissions
- Task 4.2: Harden tenant token cache location and permissions
- Task 4.3: Harden SQLite memory DB permissions
- Task 5.1: Add Feishu message length and deduplication
- Task 5.2: Add Feishu sender rate limiting
- Task 5.3: Restrict `/send` slash command to operators
- Task 6.1: Harden Dockerfile
- Task 6.2: Harden Docker Compose
- Task 6.3: Harden agent-chrome container
- Task 7.1: Make cryptography mandatory for memory
- Task 7.2: Strengthen sensitive memory password policy
- Task 8.1: Run full verification and regression tests
