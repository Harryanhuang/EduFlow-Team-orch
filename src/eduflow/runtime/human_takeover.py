"""Durable circuit breaker for automatic runtime mutations."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from eduflow.util import atomic_write_text, file_lock


class AutomationBlocked(RuntimeError):
    pass


class StaleGeneration(RuntimeError):
    pass


class InvalidTransition(RuntimeError):
    pass


_SECRET = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+|\bsk-[A-Za-z0-9_-]+")


def _clean(value: object) -> str:
    return _SECRET.sub("[REDACTED]", str(value))[:1000]


def _state_path() -> Path:
    # Pure resolution is important: status must remain read-only, and avoiding
    # facts_dir() also avoids its check-then-mkdir race between CLI processes.
    root = Path(os.environ.get("EDUFLOW_STATE_DIR", str(Path.home() / ".eduflow")))
    return root / "facts" / "human-takeover.json"


def _audit_path() -> Path:
    return _state_path().with_name("human-takeover-audit.jsonl")


def _inactive() -> dict:
    return {"state": "inactive", "reason": "", "source": "", "actor": "",
            "entered_at": None, "recovery_steps": [], "generation": 0}


def _read() -> dict:
    path = _state_path()
    if not path.exists():
        return _inactive()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("state") not in {"inactive", "active", "recovering"}:
            raise ValueError("invalid state")
        generation = data.get("generation")
        if not isinstance(generation, int) or generation < 0:
            raise ValueError("invalid generation")
        return {**_inactive(), **data}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return {**_inactive(), "state": "active", "reason": "corrupt_state",
                "source": "state_validation", "actor": "system", "entered_at": None}


def status() -> dict:
    """Read state without creating or repairing any files."""
    return _read()


def _write(state: dict) -> None:
    atomic_write_text(_state_path(), json.dumps(state, ensure_ascii=False, sort_keys=True) + "\n")


def _audit(event: dict) -> None:
    path = _audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n").encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)


def audit_events() -> list[dict]:
    path = _audit_path()
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def enter(*, reason: str, source: str, actor: str) -> dict:
    if not reason or not actor:
        raise InvalidTransition("actor and reason are required")
    path = _state_path()
    with file_lock(path):
        current = _read()
        if current["state"] in {"active", "recovering"}:
            return current
        now = time.time()
        state = {"state": "active", "reason": _clean(reason), "source": _clean(source),
                 "actor": _clean(actor), "entered_at": now, "recovery_steps": [],
                 "generation": current["generation"] + 1}
        _write(state)
        _audit({"event": "enter", "at": now, **state})
        return state


def recover(*, actor: str, reason: str, recovery_steps: list[str], expected_generation: int) -> dict:
    if not actor or not reason:
        raise InvalidTransition("actor and reason are required")
    path = _state_path()
    with file_lock(path):
        current = _read()
        if current["generation"] != expected_generation:
            raise StaleGeneration(f"expected generation {expected_generation}; current is {current['generation']}")
        if current["state"] != "active":
            raise InvalidTransition("takeover is not active")
        now = time.time()
        generation = current["generation"] + 1
        recovering = {**current, "state": "recovering", "actor": _clean(actor),
                      "reason": _clean(reason), "recovery_steps": [_clean(x) for x in recovery_steps],
                      "generation": generation}
        _write(recovering)
        _audit({"event": "recovering", "at": now, **recovering})
        inactive = {**recovering, "state": "inactive"}
        _write(inactive)
        _audit({"event": "recovered", "at": time.time(), **inactive})
        return inactive


def ensure_automation_allowed(*, expected_generation: int | None = None) -> int:
    state = status()
    if state["state"] != "inactive":
        raise AutomationBlocked(f"automation blocked by human takeover (generation={state['generation']})")
    if expected_generation is not None and state["generation"] != expected_generation:
        raise StaleGeneration(f"expected generation {expected_generation}; current is {state['generation']}")
    return state["generation"]
