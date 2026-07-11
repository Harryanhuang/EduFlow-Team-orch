"""Single source of truth for runtime filesystem paths.

All paths derive from `$EDUFLOW_STATE_DIR` (re-read on every call so
tests get isolation by setting the env, not by monkey-patching).  When
not set, falls back to `~/.eduflow`.

Layout:
    $EDUFLOW_STATE_DIR/
        facts/             ← inbox.json, status.json, logs.jsonl, heartbeats.json
        agents/<name>/     ← per-agent identity.md
        router.pid         ← daemon pid files
        watchdog.pid
        router.cursor      ← catchup replay state
"""
from __future__ import annotations

from pathlib import Path

from eduflow.util import env_path


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


def state_file(name: str) -> Path:
    """A file under state_dir. Caller is responsible for mkdir before writing
    — pure path resolution, no I/O side effects."""
    return state_dir() / name


def router_pid_file() -> Path:
    return state_file("router.pid")


def router_cursor_file() -> Path:
    return state_file("router.cursor")


def router_log_file() -> Path:
    return state_file("router.log")


def router_seen_file() -> Path:
    return state_file("router.seen")


def router_stall_reason_file() -> Path:
    return state_file("router.stall_reason")


def task_publish_cursor_file() -> Path:
    return state_file("task-publish.cursor")


def task_publish_explanations_file() -> Path:
    return state_file("task-publish.explanations.json")


def task_publish_pending_file() -> Path:
    return state_file("task-publish.pending.json")


def task_publish_close_loop_file() -> Path:
    return state_file("task-publish.close-loop.json")


def task_supervisor_state_file() -> Path:
    return state_file("task-supervisor.state.json")


def hermes_supervisor_pid_file() -> Path:
    return state_file("hermes-supervisor.pid")


def hermes_supervisor_log_file() -> Path:
    return state_file("hermes-supervisor.log")


def task_events_file() -> Path:
    return state_file("task-events.jsonl")


def runtime_status_file() -> Path:
    return facts_dir() / "runtime-status.json"


def runtime_guard_state_file() -> Path:
    return facts_dir() / "runtime-guard-state.json"


def config_file() -> Path:
    """Path to the unified TOML config file (replaces team.json +
    runtime_config.json). Override via EDUFLOW_CONFIG_FILE env, else
    looks for `./eduflow.toml` relative to cwd."""
    from eduflow.util import env_path
    return env_path("EDUFLOW_CONFIG_FILE") or Path.cwd() / "eduflow.toml"


def watchdog_pid_file() -> Path:
    return state_file("watchdog.pid")


def watchdog_log_file() -> Path:
    return state_file("watchdog.log")


def task_publish_pid_file() -> Path:
    return state_file("task-publish.pid")


def task_publish_log_file() -> Path:
    return state_file("task-publish.log")


def ensure_state_dir() -> Path:
    """Create state_dir if missing and return it. Use when about to write."""
    sd = state_dir()
    sd.mkdir(parents=True, exist_ok=True)
    return sd


def memory_db_file() -> Path:
    """SQLite database for active constraints and task capsules."""
    return state_file("eduflow_memory.db")
