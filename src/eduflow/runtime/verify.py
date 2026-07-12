"""Runtime verification primitives — shared by lifecycle, watchdog, deliver,
health, and the new `eduflow runtime verify` CLI.

Responsibilities:
  1. Read the actual environment of a running tmux pane's process tree
     (`pane_live_env`). Moved out of `commands/health.py` so other modules
     can verify env drift at provisioning time, not just observationally.
  2. Compare live env against a configured `env_profile` and return
     structured mismatch info (`verify_live_env_matches_profile`).
  3. Minimal API smoke test against the provider gateway
     (`api_smoke_runtime`). For anthropic-proxy runtimes we fire a real
     POST /v1/messages with max_tokens=1 and expect 2xx. For non-HTTP
     CLIs (codex, qoder) v1 only verifies env markers and reports
     `smoke_skipped`.
  4. Append-only switch event log
     (`record_switch_event` / `read_switch_events`). Every automatic
     or manual runtime switch writes one JSONL row so postmortems can
     reconstruct the failover chain.

Pure-function-first: every function takes its I/O as injectable kwargs
(`run=`, `read_environ=`) so tests pass recorders instead of hitting
tmux / subprocess / the network.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path

from eduflow.runtime import config, paths


# Env vars that identify a provider runtime. Health, verify, and lifecycle
# all compare on this exact set — single source of truth so they can't
# drift apart.
PROFILE_ENV_KEYS = (
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_REASONING_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "OPENAI_BASE_URL",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
)


# ── pane live env ─────────────────────────────────────────────────


def _child_pids(pid: str, *, run=None) -> list[str]:
    run = run or subprocess.run
    try:
        r = run(["pgrep", "-P", pid], capture_output=True, text=True, timeout=5)
    except Exception:
        return []
    if r.returncode != 0:
        return []
    return [line.strip() for line in (r.stdout or "").splitlines() if line.strip().isdigit()]


def _profile_env_from_ps(pid: str, *, run=None) -> dict[str, str]:
    run = run or subprocess.run
    try:
        r = run(["ps", "eww", "-p", pid], capture_output=True, text=True, timeout=5)
    except Exception:
        return {}
    if r.returncode != 0:
        return {}
    env: dict[str, str] = {}
    for token in " ".join((r.stdout or "").splitlines()[1:]).split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key in PROFILE_ENV_KEYS:
            env[key] = value
    return env


def _profile_env_for_pid(pid: str, *, run=None, read_environ=None) -> dict[str, str]:
    """Read provider env vars from a single pid.

    Prefer /proc/<pid>/environ on Linux (cheap, no fork); fall back to
    `ps eww -p` on macOS. Injectable `read_environ` for tests.
    """
    read_environ = read_environ or (lambda p: open(p, "rb").read())
    proc_environ = f"/proc/{pid}/environ"
    try:
        if os.path.exists(proc_environ):
            try:
                raw = read_environ(proc_environ)
            except OSError:
                return _profile_env_from_ps(pid, run=run)
            env: dict[str, str] = {}
            for item in raw.split(b"\0"):
                if b"=" not in item:
                    continue
                key, value = item.split(b"=", 1)
                decoded_key = key.decode("utf-8", "ignore")
                if decoded_key in PROFILE_ENV_KEYS:
                    env[decoded_key] = value.decode("utf-8", "ignore")
            return env
    except Exception:
        pass
    return _profile_env_from_ps(pid, run=run)


def pane_live_env(target, *, run=None, read_environ=None, tmux_display=None) -> dict[str, str]:
    """Best-effort environment snapshot for the active pane process.

    tmux `pane_pid` is sometimes the parent shell while the actual CLI
    is a child process, so walk a shallow descendant tree before giving
    up. Returns {} when the platform cannot expose env safely — callers
    treat {} as "unknown", never as "mismatched".
    """
    tmux_display = tmux_display or (lambda args: subprocess.run(
        ["tmux", "display-message", "-p", "-t", str(target)] + args,
        capture_output=True, text=True, timeout=5,
    ))
    try:
        r = tmux_display(["#{pane_pid}"])
    except Exception:
        return {}
    if r.returncode != 0:
        return {}
    pid = (r.stdout or "").strip()
    if not pid.isdigit():
        return {}
    queue = [pid]
    seen: set[str] = set()
    for _ in range(8):
        if not queue:
            break
        current = queue.pop(0)
        if current in seen:
            continue
        seen.add(current)
        env = _profile_env_for_pid(current, run=run, read_environ=read_environ)
        if env:
            return env
        queue.extend(p for p in _child_pids(current, run=run) if p not in seen)
    return {}


# ── env drift check ───────────────────────────────────────────────


def verify_live_env_matches_profile(
    target,
    env_profile_name: str,
    *,
    run=None,
    read_environ=None,
    tmux_display=None,
) -> tuple[bool, list[str]]:
    """Return `(ok, mismatches)` where `ok` is True iff the pane's live
    env vars match every non-empty var declared in `env_profile_name`.

    `mismatches` is a list of `"<key> expected=<a> live=<b>"` strings,
    suitable for direct inclusion in a health line or switch event.
    Empty env_profile_name ⇒ (True, []) — no profile, nothing to verify.
    """
    if not env_profile_name:
        return True, []
    try:
        profile = config.env_profile_config(env_profile_name)
    except KeyError:
        return False, [f"env_profile {env_profile_name!r} not in config"]
    expected = {k: str(profile[k]) for k in PROFILE_ENV_KEYS if profile.get(k)}
    if not expected:
        return True, []
    # Provider-aware skip: profiles that route through a non-Anthropic
    # provider_family (minimax, glm, kimi, dashscope_qwen, hermes_agent,
    # openai_codex, …) auto-fill ANTHROPIC_AUTH_TOKEN from the shell env
    # via config.env_profile_config's sensitive-key backfill, but the
    # pane itself never sets the token because it talks to a different
    # gateway. Treating that as drift would be a false positive — only
    # anthropic-family runtimes actually need the token in the pane env.
    # Profiles with no provider_family (older configs / test fixtures)
    # fall through to the existing check.
    provider_family = str(profile.get("provider_family") or "")
    skip_anthropic_token = bool(provider_family) and "anthropic" not in provider_family.lower()
    skip_openai_api_key = provider_family == "openai_codex"
    live = pane_live_env(target, run=run, read_environ=read_environ, tmux_display=tmux_display)
    if not live:
        return False, [f"env_profile={env_profile_name} live_env_unavailable"]
    mismatches = []
    for key, value in expected.items():
        live_value = live.get(key)
        # PROXY_MANAGED is a sentinel meaning the gateway injects auth itself
        # (team-managed reverse proxy). The pane legitimately runs with the
        # sentinel instead of the literal profile token, so it is not drift —
        # mirror the smoke-skip exemption in api_smoke_runtime().
        if key == "ANTHROPIC_AUTH_TOKEN" and live_value == "PROXY_MANAGED":
            continue
        # Provider-aware exemption: non-Anthropic provider_family profiles
        # never set ANTHROPIC_AUTH_TOKEN in the pane env, so missing live
        # is expected. See the skip_anthropic_token note above.
        if skip_anthropic_token and key == "ANTHROPIC_AUTH_TOKEN":
            continue
        # Codex can authenticate via CODEX_HOME/auth.json after a
        # non-interactive `codex login --with-api-key`, so the pane may
        # intentionally blank OPENAI_API_KEY while still being healthy.
        if skip_openai_api_key and key == "OPENAI_API_KEY":
            continue
        if live_value != value:
            shown = live_value if live_value else "<missing>"
            mismatches.append(f"{key} expected={value} live={shown}")
    return (not mismatches), mismatches


# ── API smoke ─────────────────────────────────────────────────────


def api_smoke_runtime(resolved_runtime: dict, *, run=None, timeout_s: float = 15.0) -> tuple[str, str]:
    """Run the smallest possible API probe against the provider named by
    `resolved_runtime`.

    Returns `(verdict, detail)` where `verdict` is one of:
      - "ok"        — 2xx (or equivalent) received
      - "failed"    — non-2xx, network error, or auth rejected
      - "skipped"   — runtime's CLI/provider is not one we know how to
                      probe in v1 (e.g. codex-cli, qoder); detail says why

    `resolved_runtime` needs at minimum: `cli`, `provider`, `env_profile`.
    Injectable `run` for tests — must accept the same shape as
    `subprocess.run`.
    """
    run = run or subprocess.run
    cli = resolved_runtime.get("cli", "")
    provider = resolved_runtime.get("provider", "")
    env_profile = resolved_runtime.get("env_profile", "")

    # v1: only anthropic-proxy runtimes get a real probe. codex / qoder
    # are marked skipped until we add provider-specific probes.
    if cli == "claude-code" and provider == "anthropic-proxy" and env_profile:
        try:
            profile = config.env_profile_config(env_profile)
        except KeyError:
            return "skipped", f"env_profile {env_profile!r} missing"
        base_url = str(profile.get("ANTHROPIC_BASE_URL", "")).rstrip("/")
        token = str(profile.get("ANTHROPIC_AUTH_TOKEN", ""))
        model = str(
            profile.get("ANTHROPIC_MODEL")
            or profile.get("ANTHROPIC_DEFAULT_SONNET_MODEL")
            or "sonnet"
        )
        if not base_url or not token:
            return "skipped", "anthropic-proxy missing base_url or token"
        url = f"{base_url}/v1/messages"
        payload = {
            "model": model,
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "hi"}],
        }
        try:
            r = run(
                [
                    "curl", "-sS", "-o", "/dev/null",
                    "-w", "%{http_code}",
                    "-m", str(int(timeout_s)),
                    "-X", "POST", url,
                    "-H", "Content-Type: application/json",
                    "-H", f"x-api-key: {token}",
                    "-H", "anthropic-version: 2023-06-01",
                    "-d", json.dumps(payload),
                ],
                capture_output=True, text=True, timeout=timeout_s + 5,
            )
        except (subprocess.TimeoutExpired, OSError) as e:
            return "failed", f"curl error: {type(e).__name__}: {e}"
        code = (r.stdout or "").strip()
        if not code:
            return "failed", f"curl no status code; stderr={(r.stderr or '').strip()[:120]}"
        try:
            code_int = int(code)
        except ValueError:
            return "failed", f"curl non-numeric status {code!r}"
        if 200 <= code_int < 300:
            return "ok", f"http {code_int}"
        # 429 / 5xx are both "failed" — we just want a boolean "works now".
        return "failed", f"http {code_int}"

    if cli == "codex-cli":
        return "skipped", "codex-cli smoke not implemented in v1"
    if cli in {"qoderclicn", "qwen-code", "kimi-code", "mimo-code", "mimo-cli"}:
        return "skipped", f"{cli} smoke not implemented in v1"
    return "skipped", f"unknown cli {cli!r}"


# ── switch event log ──────────────────────────────────────────────


def _switch_events_path() -> Path:
    return paths.state_file("facts/runtime-switch-events.jsonl")


def record_switch_event(
    *,
    agent: str,
    from_runtime: str,
    to_runtime: str,
    reason: str,
    outcome: str,
    trigger: str = "",
    env_ok: bool | None = None,
    smoke_ok: bool | None = None,
    inbox_ok: bool | None = None,
    switch_id: str | None = None,
    best_outcome: str = "",
    attempts: list[dict] | None = None,
    pool_switched: bool = False,
    cross_pool: bool = False,
    pool_id: str = "",
    phase: str = "",
    verdict: str = "",
    ts: float | None = None,
    **_extra: object,
) -> None:
    """Append one switch event to the JSONL log.

    Required: `agent`, `from_runtime`, `to_runtime`, `reason`, `outcome`.
    `switch_id` is auto-generated (8-char uuid4) if not provided.
    `**_extra` absorbs unknown keys for forward-compat with callers that
    pass richer dicts.
    """
    row: dict = {
        "ts": ts or time.time(),
        "switch_id": switch_id or str(uuid.uuid4())[:8],
        "agent": agent,
        "from_runtime": from_runtime,
        "to_runtime": to_runtime,
        "reason": reason,
        "trigger": trigger,
        "outcome": outcome,
        "best_outcome": best_outcome,
        "attempts": attempts or [],
        "pool_switched": pool_switched,
        "cross_pool": cross_pool,
    }
    if phase:
        row["phase"] = phase
    if verdict:
        row["verdict"] = verdict
    # Carry optional booleans only when set (keeps event compact).
    if env_ok is not None:
        row["env_ok"] = env_ok
    if smoke_ok is not None:
        row["smoke_ok"] = smoke_ok
    if inbox_ok is not None:
        row["inbox_ok"] = inbox_ok
    if pool_id:
        row["pool_id"] = pool_id
    path = _switch_events_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        payload = (json.dumps(row, ensure_ascii=False) + "\n").encode("utf-8")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            remaining = memoryview(payload)
            while remaining:
                written = os.write(fd, remaining)
                if written <= 0:
                    raise OSError("switch event append made no progress")
                remaining = remaining[written:]
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        # Event log is best-effort observability — a write failure must
        # not kill the switch path that just succeeded.
        pass


def read_switch_events(last_n: int = 20) -> list[dict]:
    """Return the most recent `last_n` switch events, newest last."""
    path = _switch_events_path()
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    events: list[dict] = []
    for line in lines[-max(last_n * 2, last_n):]:
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events[-last_n:]
