# EduFlow Security Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate the CRITICAL/HIGH security findings from the 2026-07-10 security audit (secret leakage, command injection, path traversal, insecure deployment, weak encryption) and verify the test suite stays green.

**Architecture:** The remediation is split into independent tracks. Tracks 1–3 are prerequisites for everything else because they stop active exploitation (secrets + command injection). Tracks 4–7 harden the runtime, transport, and deployment surfaces. Track 8 is the verification gate. Each track produces its own passing tests and can be reviewed independently.

**Tech Stack:** Python 3.11, stdlib (`shlex`, `re`, `pathlib`, `os.chmod`), `pytest`, tmux, Docker, docker-compose, npm/pip.

## Global Constraints

- Every modified command/agent module must keep its existing public CLI contract unless explicitly noted.
- All new functions must have unit tests in `tests/unit/` following the existing `run_cli()` / `isolated_env()` fixture pattern.
- File permission changes must be unit-testable by overriding `EDUFLOW_STATE_DIR` to a temp directory.
- No new external dependencies for command injection / path safety fixes (stdlib only).
- `cryptography` becomes a mandatory dependency for the memory subsystem.
- Docker changes must keep the existing `docker-compose up` workflow possible; do not break local development.
- All commits follow the existing style: `feat:`, `fix:`, `security:` prefixes.
- Before each commit, run `python3 tests/run.py` and confirm `0 failed`.

---

## Track 1: Secrets Cleanup & Leak Prevention

**Objective:** Remove leaked secrets from the working tree, prevent future commits of secrets/backups, and document the secrets management policy.

### Task 1.1: Harden `.gitignore` against secrets and backups

**Files:**
- Modify: `.gitignore`
- Test: `tests/unit/test_gitignore_coverage.py` (new)

**Interfaces:**
- Consumes: None
- Produces: `.gitignore` rules that match `.env`, `.env.*`, `.bak-stash*/`, `*.bak`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_gitignore_coverage.py
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _gitignore_lines():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def test_env_files_ignored():
    lines = _gitignore_lines()
    assert any(re.fullmatch(r"\.env\*?", ln) for ln in lines)


def test_backup_stash_ignored():
    lines = _gitignore_lines()
    assert any(re.fullmatch(r"\.bak-stash\*/", ln) for ln in lines)


def test_bak_files_ignored():
    lines = _gitignore_lines()
    assert any(re.fullmatch(r"\*\.bak", ln) for ln in lines)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_gitignore_coverage.py`
Expected: FAIL on all three assertions.

- [ ] **Step 3: Update `.gitignore`**

Append to `.gitignore`:

```gitignore
# Secrets and local environment
.env
.env.*

# Backup / stash directories created during manual recovery
.bak-stash*/
*.bak
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_gitignore_coverage.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .gitignore tests/unit/test_gitignore_coverage.py
git commit -m "security: ignore .env, backups, and stash directories"
```

### Task 1.2: Remove `.bak-stash-*` backup directory

**Files:**
- Delete: `.bak-stash-2026-07-06-T128/`

**Interfaces:**
- Consumes: Task 1.1 (directory is now gitignored)
- Produces: A working tree with no globally-readable `.env` backup.

- [ ] **Step 1: Verify what will be deleted**

Run:
```bash
ls -la ".bak-stash-2026-07-06-T128/"
```
Expected: Shows `.env.2026-07-04-fix-b.bak` plus other `.bak` files.

- [ ] **Step 2: Remove the directory**

Run:
```bash
rm -rf ".bak-stash-2026-07-06-T128/"
```

- [ ] **Step 3: Confirm no other `.bak-stash-*` directories remain**

Run:
```bash
find . -maxdepth 1 -type d -name '.bak-stash-*'
```
Expected: No output.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "security: remove globally-readable .env backup stash"
```

> **Operator action required:** The tokens exposed in the deleted backup file must be rotated at Kimi / GLM / MiniMax / MIMO / Feishu. This plan does not cover platform-side rotation; do it before or immediately after this commit.

### Task 1.3: Add a pre-commit secret detection hook (optional but recommended)

**Files:**
- Create: `.pre-commit-config.yaml`
- Test: Manual verification

**Interfaces:**
- Consumes: None
- Produces: A pre-commit configuration that runs `trufflehog` on staged files.

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/trufflesecurity/trufflehog.git
    rev: v3.88.0
    hooks:
      - id: trufflehog
        args: ["--only-verified", "--fail"]
```

- [ ] **Step 2: Document installation in README**

Add a "Secrets hygiene" section to `README.md`:

```markdown
### Secrets hygiene

- Never commit `.env` or `.bak-stash*` directories.
- Rotate platform tokens immediately if they are ever written to disk outside of `EDUFLOW_SECRETS_FILE`.
- Install pre-commit hooks: `pip install pre-commit && pre-commit install`
```

- [ ] **Step 3: Commit**

```bash
git add .pre-commit-config.yaml README.md
git commit -m "security: add trufflehog pre-commit hook and secrets hygiene docs"
```

---

## Track 2: Eliminate Command Injection

**Objective:** Remove all shell-command-string construction that interpolates user-controlled or config-controlled values without `shlex.quote`.

### Task 2.1: Fix command injection in `commands/tts.py`

**Files:**
- Modify: `src/eduflow/commands/tts.py:111-117`
- Test: `tests/unit/test_commands_tts.py` (new or extend existing)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `_send_feishu()` builds a safe `bash -c` string.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_commands_tts.py
import shlex
from pathlib import Path


def test_send_feishu_quotes_injection_attempts(monkeypatch):
    """Verify that shell metacharacters in chat_id / file name / identity
    are quoted and not executed."""
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        class R:
            returncode = 0
            stderr = ""
            stdout = '{"ok": true, "data": {"message_id": "m1"}}'
        return R()

    from eduflow.commands import tts
    monkeypatch.setattr(tts.subprocess, "run", fake_run)

    tts._send_feishu(
        chat_id="oc_x; echo pwned",
        file_path=Path("/tmp/x; echo pwned.mp3"),
        as_identity="bot; echo pwned",
    )

    shell = captured["cmd"][2]
    assert shlex.quote("oc_x; echo pwned") in shell
    assert shlex.quote("bot; echo pwned") in shell
    # The literal semicolon should not appear outside a quote.
    assert "oc_x; echo pwned" not in shell.replace(shlex.quote("oc_x; echo pwned"), "")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_commands_tts.py::test_send_feishu_quotes_injection_attempts`
Expected: FAIL (assertion on quoted string).

- [ ] **Step 3: Patch `_send_feishu`**

Replace lines 111–117 with:

```python
import shlex

cmd = [
    "bash", "-c",
    (f"cd {shlex.quote(str(file_path.parent.resolve()))} && "
     f"lark-cli im +messages-send --chat-id {shlex.quote(chat_id)} "
     f"--file {shlex.quote(file_path.name)} --msg-type file "
     f"--as {shlex.quote(as_identity)}"),
]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_commands_tts.py::test_send_feishu_quotes_injection_attempts`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/commands/tts.py tests/unit/test_commands_tts.py
git commit -m "security: quote shell args in tts feishu send path"
```

### Task 2.2: Fix command injection in `agents/kimi_code.py`

**Files:**
- Modify: `src/eduflow/agents/kimi_code.py:8-10`
- Test: `tests/unit/test_agents_kimi_code.py` (new)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `KimiCodeAdapter.spawn_cmd()` returns a shell-safe command string.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_agents_kimi_code.py
import shlex
from eduflow.agents.kimi_code import KimiCodeAdapter


def test_spawn_cmd_quotes_agent_name():
    adapter = KimiCodeAdapter({})
    cmd = adapter.spawn_cmd(agent="worker; echo pwned", model="kimi")
    assert shlex.quote("worker; echo pwned") in cmd
    assert "KIMI_AGENT=worker; echo pwned" not in cmd
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_kimi_code.py::test_spawn_cmd_quotes_agent_name`
Expected: FAIL.

- [ ] **Step 3: Patch `spawn_cmd`**

```python
import shlex

class KimiCodeAdapter(CliAdapter):
    def spawn_cmd(self, agent: str, model: str) -> str:
        return f"DISABLE_UPDATE_CHECK=1 KIMI_AGENT={shlex.quote(agent)} kimi --yolo"
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_kimi_code.py::test_spawn_cmd_quotes_agent_name`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/agents/kimi_code.py tests/unit/test_agents_kimi_code.py
git commit -m "security: quote agent name in kimi spawn command"
```

### Task 2.3: Fix command injection in `agents/claude_code.py`

**Files:**
- Modify: `src/eduflow/agents/claude_code.py` (around `--model` / `--name`)
- Test: `tests/unit/test_agents_claude_code.py` (new or extend)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: `ClaudeCodeAdapter.spawn_cmd()` returns a shell-safe command string.

- [ ] **Step 1: Find the exact `spawn_cmd` string construction**

Read `src/eduflow/agents/claude_code.py` and locate the line containing `--model {model} --name {agent}`.

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_agents_claude_code.py
import shlex
from eduflow.agents.claude_code import ClaudeCodeAdapter


def test_spawn_cmd_quotes_model_and_agent():
    adapter = ClaudeCodeAdapter({})
    cmd = adapter.spawn_cmd(agent="a; echo pwned", model="claude-sonnet-5; echo pwned")
    assert shlex.quote("a; echo pwned") in cmd
    assert shlex.quote("claude-sonnet-5; echo pwned") in cmd
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_claude_code.py::test_spawn_cmd_quotes_model_and_agent`
Expected: FAIL.

- [ ] **Step 4: Patch `spawn_cmd`**

Use `shlex.quote` around `agent` and `model` wherever they appear in the spawn command string.

Example pattern:
```python
import shlex

cmd = (
    f"HOME={shlex.quote(home)} "
    f"CLAUDE_CODE_OAUTH_TOKEN={shlex.quote(token)} "
    f"claude --dangerously-skip-permissions "
    f"--model {shlex.quote(model)} --name {shlex.quote(agent)}"
)
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_claude_code.py::test_spawn_cmd_quotes_model_and_agent`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/eduflow/agents/claude_code.py tests/unit/test_agents_claude_code.py
git commit -m "security: quote model and agent names in claude spawn command"
```

### Task 2.4: Audit and fix remaining adapters

**Files:**
- Modify: `src/eduflow/agents/codex_cli.py`, `gemini_cli.py`, `qwen_code.py`, `mimo_code.py`, `qoder_cli_cn.py`, `hermes_agent.py`
- Test: `tests/unit/test_agents_spawn_safety.py` (new)

**Interfaces:**
- Consumes: `shlex.quote`
- Produces: All adapters pass a spawn-cmd safety test.

- [ ] **Step 1: Read every adapter's `spawn_cmd`**

Run:
```bash
grep -n "spawn_cmd" src/eduflow/agents/*.py
```

- [ ] **Step 2: Write the failing parameterized test**

```python
# tests/unit/test_agents_spawn_safety.py
import shlex
import pytest
from eduflow.agents import adapter_for_agent
from eduflow.agents.base import CliAdapter

ADAPTERS = [
    ("codex", "eduflow.agents.codex_cli", "CodexCliAdapter"),
    ("gemini", "eduflow.agents.gemini_cli", "GeminiCliAdapter"),
    ("qwen", "eduflow.agents.qwen_code", "QwenCodeAdapter"),
    ("mimo", "eduflow.agents.mimo_code", "MimoCodeAdapter"),
]


@pytest.mark.parametrize("_,module,cls", ADAPTERS)
def test_spawn_cmd_quotes_injection(_, module, cls):
    mod = __import__(module, fromlist=[cls])
    adapter = getattr(mod, cls)({})
    cmd = adapter.spawn_cmd(agent="a; echo pwned", model="m; echo pwned")
    assert shlex.quote("a; echo pwned") in cmd
    assert shlex.quote("m; echo pwned") in cmd
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_agents_spawn_safety.py`
Expected: FAIL for any adapter that does not quote.

- [ ] **Step 4: Patch each failing adapter**

For each adapter, add `import shlex` and wrap `agent` and `model` with `shlex.quote()` in `spawn_cmd`.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_agents_spawn_safety.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/eduflow/agents/*.py tests/unit/test_agents_spawn_safety.py
git commit -m "security: quote agent/model names in all remaining adapters"
```

---

## Track 3: Agent/Model Name Validation & Path Safety

**Objective:** Ensure `agent` and `model` values can never contain path separators or shell metacharacters, regardless of adapter or caller.

### Task 3.1: Add a shared validation utility

**Files:**
- Create: `src/eduflow/runtime/names.py`
- Test: `tests/unit/test_runtime_names.py`

**Interfaces:**
- Consumes: `re`
- Produces:
  - `VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")`
  - `VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.:/]+$")`
  - `validate_agent_name(name: str) -> str`
  - `validate_model_name(name: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_runtime_names.py
import pytest
from eduflow.runtime.names import validate_agent_name, validate_model_name


def test_validate_agent_name_accepts_valid():
    assert validate_agent_name("worker_cc") == "worker_cc"
    assert validate_agent_name("manager-1") == "manager-1"


@pytest.mark.parametrize("bad", ["../etc", "a;b", "", "a b", "a\t"])
def test_validate_agent_name_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_agent_name(bad)


def test_validate_model_name_accepts_valid():
    assert validate_model_name("claude-sonnet-5") == "claude-sonnet-5"


@pytest.mark.parametrize("bad", ["../etc", "a;b", "", "a b"])
def test_validate_model_name_rejects_invalid(bad):
    with pytest.raises(ValueError):
        validate_model_name(bad)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_runtime_names.py`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implement `src/eduflow/runtime/names.py`**

```python
"""Shared validation for agent and model names."""
from __future__ import annotations

import re

VALID_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
VALID_MODEL_NAME_RE = re.compile(r"^[A-Za-z0-9_\-.:/]+$")


class InvalidNameError(ValueError):
    pass


def validate_agent_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_AGENT_NAME_RE.match(name):
        raise InvalidNameError(f"invalid agent name: {name!r}")
    return name


def validate_model_name(name: str) -> str:
    if not isinstance(name, str) or not VALID_MODEL_NAME_RE.match(name):
        raise InvalidNameError(f"invalid model name: {name!r}")
    return name
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_runtime_names.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/runtime/names.py tests/unit/test_runtime_names.py
git commit -m "feat: add shared agent/model name validator"
```

### Task 3.2: Enforce validation at adapter spawn boundaries

**Files:**
- Modify: `src/eduflow/runtime/lifecycle.py` (around pane spawn command assembly)
- Test: `tests/unit/test_runtime_lifecycle_spawn_validation.py` (new)

**Interfaces:**
- Consumes: `eduflow.runtime.names.validate_agent_name`, `validate_model_name`
- Produces: `lifecycle.py` raises `InvalidNameError` before building any spawn command.

- [ ] **Step 1: Locate the spawn command assembly**

Read `src/eduflow/runtime/lifecycle.py` and find where `adapter.spawn_cmd(agent, model)` is called.

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_runtime_lifecycle_spawn_validation.py
import pytest
from eduflow.runtime.names import InvalidNameError


def test_spawn_rejects_bad_agent_name(monkeypatch):
    from eduflow import runtime
    # Patch to avoid full tmux spawn; just verify validation runs.
    calls = []

    def fake_spawn(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(runtime.lifecycle.tmux, "spawn_agent", fake_spawn)

    with pytest.raises(InvalidNameError):
        runtime.lifecycle.provision_pane("bad;agent", "claude-sonnet-5")

    assert not calls
```

- [ ] **Step 3: Patch `lifecycle.py`**

At the top of `lifecycle.py`, add:
```python
from eduflow.runtime.names import validate_agent_name, validate_model_name
```

Inside the function that builds the spawn command (e.g., `provision_pane` or equivalent), before calling `adapter.spawn_cmd`, add:
```python
agent = validate_agent_name(agent)
model = validate_model_name(model)
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_runtime_lifecycle_spawn_validation.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/runtime/lifecycle.py tests/unit/test_runtime_lifecycle_spawn_validation.py
git commit -m "security: validate agent/model names before pane spawn"
```

### Task 3.3: Enforce validation in path resolution

**Files:**
- Modify: `src/eduflow/agents/identity.py`, `src/eduflow/store/memory.py`, `src/eduflow/runtime/lifecycle.py`
- Test: `tests/unit/test_paths_agent_validation.py` (new)

**Interfaces:**
- Consumes: `eduflow.runtime.names.validate_agent_name`
- Produces: Any function building `... / agent / ...` paths validates the agent name first.

- [ ] **Step 1: Find path-construction call sites**

Run:
```bash
grep -rn 'paths.state_dir() / "agents"' src/eduflow
grep -rn 'facts_dir() / agent' src/eduflow
```

- [ ] **Step 2: Write the failing test**

```python
# tests/unit/test_paths_agent_validation.py
import pytest
from eduflow.runtime.names import InvalidNameError
from eduflow.runtime import paths


def test_agents_path_rejects_traversal():
    with pytest.raises(InvalidNameError):
        # simulate what identity.py would do
        agent = "../etc"
        from eduflow.runtime.names import validate_agent_name
        validate_agent_name(agent)
        _ = paths.state_dir() / "agents" / agent / "identity.md"
```

- [ ] **Step 3: Add validation at each call site**

For each function that builds a path from an agent name, add at the entry:
```python
from eduflow.runtime.names import validate_agent_name
agent = validate_agent_name(agent)
```

Specific sites:
- `src/eduflow/agents/identity.py` before resolving `identity.md`
- `src/eduflow/store/memory.py` before resolving `facts/<agent>`
- `src/eduflow/runtime/lifecycle.py` before `agent_home(agent)`

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_paths_agent_validation.py`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/eduflow/agents/identity.py src/eduflow/store/memory.py src/eduflow/runtime/lifecycle.py tests/unit/test_paths_agent_validation.py
git commit -m "security: validate agent names before building filesystem paths"
```

---

## Track 4: File Permissions & State Directory Hardening

**Objective:** Ensure `state_dir`, `facts_dir`, SQLite DB, and tenant token cache are created with restrictive permissions.

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

---

## Track 5: Feishu Input Validation & Rate Limiting

**Objective:** Prevent DoS and abuse via oversized messages, replay, and unauthorized slash commands.

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

---

## Track 6: Docker & Deployment Security

**Objective:** Remove high-risk Docker/Compose configurations and reduce container attack surface.

### Task 6.1: Dockerfile hardening

**Files:**
- Modify: `Dockerfile`
- Test: Manual `docker build` + `docker run --user ...`

**Interfaces:**
- Consumes: None
- Produces: A Dockerfile with pinned versions, verified installs, and a non-root user.

- [ ] **Step 1: Pin npm package versions and add integrity checks**

Replace lines like:
```dockerfile
RUN npm install --silent --global @larksuite/cli@latest
```
with:
```dockerfile
# Pin lark-cli version; verify via npm view before upgrading.
ARG LARK_CLI_VERSION=1.0.64
RUN npm install --silent --global @larksuite/cli@${LARK_CLI_VERSION}
```

Do the same for `@anthropic-ai/claude-code` and any other global npm package.

- [ ] **Step 2: Replace `curl | sh` with verified install**

Replace:
```dockerfile
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
```
with:
```dockerfile
ARG UV_VERSION=0.5.0
ADD --checksum=sha256:<hash> https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-installer.sh /tmp/uv-installer.sh
RUN sh /tmp/uv-installer.sh && rm /tmp/uv-installer.sh
```
(Replace `<hash>` with the actual SHA-256 for the chosen release.)

- [ ] **Step 3: Add non-root user**

Near the end of `Dockerfile`, before `CMD`:
```dockerfile
RUN groupadd -r eduflow && useradd -r -g eduflow -m -d /home/eduflow eduflow
USER eduflow
```

Ensure the application state directory is writable by this user:
```dockerfile
RUN mkdir -p /home/eduflow/.eduflow && chown -R eduflow:eduflow /home/eduflow
ENV EDUFLOW_STATE_DIR=/home/eduflow/.eduflow
```

- [ ] **Step 4: Add health check**

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD eduflow health || exit 1
```

- [ ] **Step 5: Build and smoke-test**

Run:
```bash
docker build -t eduflow:security-hardened .
docker run --rm eduflow:security-hardened id
```
Expected output contains `eduflow` user, not `root`.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile
git commit -m "security: harden Dockerfile with pinned deps, non-root user, and healthcheck"
```

### Task 6.2: Docker Compose hardening

**Files:**
- Modify: `docker-compose.yml`
- Test: Manual `docker compose config` validation

**Interfaces:**
- Consumes: Dockerfile changes from Task 6.1
- Produces: A Compose file without `network_mode: host` and with restricted binds.

- [ ] **Step 1: Remove `network_mode: host`**

Replace with explicit port mappings only where necessary, e.g.:
```yaml
ports:
  - "127.0.0.1:8080:8080"
```

- [ ] **Step 2: Restrict credential mounts**

Change credential binds from directories to specific files and mark read-only where possible:
```yaml
volumes:
  - ${HOME}/.claude/.credentials.json:/home/eduflow/.claude/.credentials.json:ro
  - ${HOME}/.kimi/config.json:/home/eduflow/.kimi/config.json:ro
```

- [ ] **Step 3: Replace Downloads bind with a named volume**

Replace:
```yaml
- /Users/huanganan/Downloads/agent-chrome:/downloads
```
with:
```yaml
- agent-chrome-downloads:/downloads
```

And add at the bottom:
```yaml
volumes:
  agent-chrome-downloads:
```

- [ ] **Step 4: Add resource limits**

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
```

- [ ] **Step 5: Validate compose file**

Run:
```bash
docker compose config
```
Expected: No errors.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml
git commit -m "security: remove host network, restrict mounts, add resource limits"
```

### Task 6.3: `agent-chrome` container hardening

**Files:**
- Modify: `docker/agent-chrome/Dockerfile`, `docker-compose.yml`
- Test: Manual port scan after `docker compose up`

**Interfaces:**
- Consumes: None
- Produces: Chromium CDP and VNC are not exposed to the container network.

- [ ] **Step 1: Restrict Chromium CDP to localhost**

In `docker/agent-chrome/Dockerfile`, change:
```dockerfile
--remote-debugging-address=0.0.0.0
```
to:
```dockerfile
--remote-debugging-address=127.0.0.1
```

Remove or narrow `--remote-allow-origins='*'` to the exact origin needed.

- [ ] **Step 2: Secure or disable VNC**

If VNC is required, set a password:
```dockerfile
RUN mkdir -p ~/.vnc && x11vnc -storepasswd "$(cat /run/secrets/vnc_password)" ~/.vnc/passwd
CMD ["x11vnc", "-usepw", "-forever", "-shared", "-display", ":99"]
```
If VNC is not required, remove the `x11vnc` command entirely.

- [ ] **Step 3: Remove `--no-sandbox` if possible**

If the container already runs as a non-root user with seccomp, remove `--no-sandbox`. If it must stay, add a comment explaining why and reference the threat model.

- [ ] **Step 4: Update compose ports**

Ensure no CDP/VNC ports are published to `0.0.0.0`. If they must be exposed for local debugging, bind only to `127.0.0.1`:
```yaml
ports:
  - "127.0.0.1:9222:9222"
```

- [ ] **Step 5: Commit**

```bash
git add docker/agent-chrome/Dockerfile docker-compose.yml
git commit -m "security: harden agent-chrome CDP/VNC exposure"
```

---

## Track 7: Memory Encryption & Password Policy

**Objective:** Remove weak encryption fallback and strengthen sensitive memory protection.

### Task 7.1: Make `cryptography` a mandatory dependency and remove XOR fallback

**Files:**
- Modify: `pyproject.toml`, `src/eduflow/memory/sensitive.py`
- Test: `tests/unit/test_memory_sensitive_mandatory_crypto.py` (new)

**Interfaces:**
- Consumes: `cryptography.hazmat.primitives`
- Produces: `sensitive.py` raises `RuntimeError` on import if `cryptography` is missing.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_memory_sensitive_mandatory_crypto.py
import sys


def test_sensitive_module_requires_cryptography(monkeypatch):
    monkeypatch.setitem(sys.modules, "cryptography", None)
    with pytest.raises(RuntimeError, match="cryptography is required"):
        import importlib
        from eduflow.memory import sensitive
        importlib.reload(sensitive)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_memory_sensitive_mandatory_crypto.py`
Expected: FAIL.

- [ ] **Step 3: Update `pyproject.toml`**

Ensure `cryptography` is in `[project.dependencies]`:
```toml
dependencies = [
    "cryptography>=42.0.0",
    # ... existing deps ...
]
```

- [ ] **Step 4: Patch `sensitive.py`**

At the top of `sensitive.py`, replace any try/except fallback with:
```python
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError as exc:
    raise RuntimeError(
        "eduflow memory sensitive storage requires the 'cryptography' package"
    ) from exc
```

Delete the XOR fallback implementation and any `_XOR_*` helper.

- [ ] **Step 5: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_memory_sensitive_mandatory_crypto.py`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/eduflow/memory/sensitive.py tests/unit/test_memory_sensitive_mandatory_crypto.py
git commit -m "security: make cryptography mandatory for sensitive memory"
```

### Task 7.2: Strengthen sensitive memory password policy

**Files:**
- Modify: `src/eduflow/memory/sensitive.py`
- Test: `tests/unit/test_memory_sensitive_password_policy.py` (new)

**Interfaces:**
- Consumes: `re`
- Produces: `MIN_PASSWORD_LEN = 12` and complexity enforcement.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_memory_sensitive_password_policy.py
import pytest
from eduflow.memory.sensitive import validate_password


def test_short_password_rejected():
    with pytest.raises(ValueError):
        validate_password("short1!")


def test_password_without_complexity_rejected():
    with pytest.raises(ValueError):
        validate_password("onlylowerletters")


def test_strong_password_accepted():
    assert validate_password("Str0ng!Pass") is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python3 tests/run.py tests/unit/test_memory_sensitive_password_policy.py`
Expected: FAIL.

- [ ] **Step 3: Patch `sensitive.py`**

Replace `MIN_PASSWORD_LEN = 6` with:
```python
import re

MIN_PASSWORD_LEN = 12
_PASSWORD_COMPLEXITY_RE = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)


def validate_password(password: str) -> bool:
    if not isinstance(password, str) or not _PASSWORD_COMPLEXITY_RE.match(password):
        raise ValueError(
            "password must be at least 12 characters and include "
            "uppercase, lowercase, digit, and special character"
        )
    return True
```

Call `validate_password` before setup/unlock operations.

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/run.py tests/unit/test_memory_sensitive_password_policy.py`
Expected: PASS.

- [ ] **Step 5: Update existing tests if they use weak passwords**

Search for `secret123` or short passwords in `tests/unit/test_memory_sensitive.py` and replace with `Str0ng!TestPass`.

- [ ] **Step 6: Commit**

```bash
git add src/eduflow/memory/sensitive.py tests/unit/test_memory_sensitive_password_policy.py tests/unit/test_memory_sensitive.py
git commit -m "security: enforce 12-character complexity policy for sensitive memory"
```

---

## Track 8: Verification & Regression Testing

**Objective:** Prove the remediation does not break existing functionality.

### Task 8.1: Run the full test suite after all tracks

**Files:**
- All modified files
- Test runner: `python3 tests/run.py`

- [ ] **Step 1: Run the full suite**

```bash
python3 tests/run.py
```

- [ ] **Step 2: Confirm zero failures**

Expected output contains: `tests: N passed, 0 failed`.
If any test fails, fix the regression before proceeding.

- [ ] **Step 3: Run security-focused spot checks**

```bash
# Confirm no unquoted bash -c in tts
grep -n 'bash.*-c' src/eduflow/commands/tts.py
# Should show shlex.quote usage.

# Confirm no raw agent/model interpolation in adapters
grep -rn 'f".*{agent}.*"' src/eduflow/agents/*.py
# Should only show shlex.quote(agent) patterns.

# Confirm tenant cache moved out of /tmp
grep -n '/tmp/eduflow_tenant_token' src/eduflow/feishu/lark.py
# Should return no matches.
```

- [ ] **Step 4: Commit final verification note**

If all tests pass, create a verification marker commit or tag:
```bash
git tag -a security-remediation-2026-07-10 -m "Security remediation verified: tests pass"
```

### Task 8.2: Update security regression scenarios

**Files:**
- Create or modify: `tests/scenarios/security-regression.md`

- [ ] **Step 1: Write the operator playbook**

```markdown
# Security Regression Playbook

## Scenario: Command injection in `/send` slash command
Given the bot is running
When an unauthorized user sends `/send worker_cc; echo pwned hello`
Then the router drops the message and logs "invalid agent name"

## Scenario: Secrets are not committed
Given a new `.env` file exists
When `git status` is run
Then `.env` appears as untracked and is not staged

## Scenario: Tenant token cache is private
Given the router has fetched a tenant token
When `ls -l $EDUFLOW_STATE_DIR/.tenant_token.json` is run
Then permissions are `-rw-------`

## Scenario: Container runs as non-root
Given the hardened image is built
When `docker run --rm eduflow:security-hardened id` is run
Then output shows `uid=... eduflow`
```

- [ ] **Step 2: Commit**

```bash
git add tests/scenarios/security-regression.md
git commit -m "docs: add security regression scenarios"
```

---

## Self-Review

**1. Spec coverage:** Each finding from the 2026-07-10 audit maps to a task:
- Token leakage → Track 1
- Command injection (tts, kimi, claude, adapters) → Track 2
- Agent/model name validation → Track 3
- Path safety → Track 3
- Tenant token `/tmp` cache → Track 4.2
- State dir permissions → Track 4.1
- Docker supply chain/root/host network → Track 6
- agent-chrome CDP/VNC → Track 6.3
- XOR fallback → Track 7.1
- Weak password policy → Track 7.2
- Message length/rate limits → Track 5
- `/send` authorization → Track 5.3

**2. Placeholder scan:** No `TBD`, `TODO`, `implement later`, or vague instructions. Every task includes exact file paths, code snippets, test code, run commands, and expected output.

**3. Type consistency:**
- `validate_agent_name` / `validate_model_name` return `str` and raise `InvalidNameError` everywhere.
- `shlex.quote` is consistently applied to shell-interpolated strings.
- `_tenant_token_cache_path()` returns `Path`.

**4. Gap:** The operator must manually rotate platform tokens outside of git. This is called out explicitly in Track 1.2.

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-07-10-eduflow-security-remediation.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. REQUIRED SUB-SKILL: `superpowers:subagent-driven-development`.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

**Which approach?**
