"""File-backed loop evidence archive."""
from __future__ import annotations

import json
from pathlib import Path

from eduflow.runtime import paths
from eduflow.util import flock, now_ms, read_json, write_json


TERMINAL_STATUSES = frozenset({"passed", "stopped", "failed"})
RUN_STATUSES = frozenset({
    "running",
    "checking",
    "repair_needed",
    "passed",
    "stopped",
    "failed",
})


def _index_file() -> Path:
    return paths.state_file("loop-runs.json")


def _locked():
    return flock(_index_file().with_suffix(".lock"))


def _load() -> dict:
    return read_json(_index_file(), {"runs": [], "_meta": {"last_id": 0}})


def _save(data: dict) -> None:
    write_json(_index_file(), data)


def _next_id(data: dict) -> str:
    meta = data.setdefault("_meta", {})
    meta["last_id"] = int(meta.get("last_id") or 0) + 1
    return f"L-{meta['last_id']:06d}"


def _run_dir(loop_id: str) -> Path:
    return paths.state_dir() / "loop_runs" / loop_id


def artifact_path(loop_id: str, filename: str) -> Path:
    return _run_dir(loop_id) / filename


def evidence_ref(loop_id: str) -> str:
    return f"loop_runs/{loop_id}/meta.json"


def background_log_ref(loop_id: str) -> str:
    return f"loop_runs/{loop_id}/background.log"


def _write_meta(run: dict) -> None:
    write_json(artifact_path(str(run["id"]), "meta.json"), run)


def _sync_run(data: dict, run: dict) -> dict:
    run["updated_at"] = now_ms()
    for idx, row in enumerate(data.get("runs", [])):
        if row.get("id") == run.get("id"):
            data["runs"][idx] = run
            break
    else:
        data.setdefault("runs", []).append(run)
    _write_meta(run)
    _save(data)
    return dict(run)


def create_or_get_active(*, task_id: str, spec: str, max_cycles: int) -> dict:
    with _locked():
        data = _load()
        for run in data.get("runs", []):
            if (
                run.get("task_id") == task_id
                and run.get("spec") == spec
                and run.get("status") not in TERMINAL_STATUSES
            ):
                return dict(run)
        now = now_ms()
        run = {
            "id": _next_id(data),
            "task_id": str(task_id),
            "spec": str(spec),
            "status": "running",
            "cycle_count": 0,
            "max_cycles": max(0, int(max_cycles or 0)),
            "stop_reason": "",
            "latest_failure_fingerprint": "",
            "cycles": [],
            "created_at": now,
            "updated_at": now,
            "evidence_ref": "",
        }
        run["evidence_ref"] = evidence_ref(str(run["id"]))
        return _sync_run(data, run)


def create_new(*, task_id: str, spec: str, max_cycles: int) -> dict:
    with _locked():
        data = _load()
        now = now_ms()
        run = {
            "id": _next_id(data),
            "task_id": str(task_id),
            "spec": str(spec),
            "status": "running",
            "cycle_count": 0,
            "max_cycles": max(0, int(max_cycles or 0)),
            "stop_reason": "",
            "latest_failure_fingerprint": "",
            "cycles": [],
            "created_at": now,
            "updated_at": now,
            "evidence_ref": "",
        }
        run["evidence_ref"] = evidence_ref(str(run["id"]))
        return _sync_run(data, run)


def get(loop_id: str) -> dict | None:
    for run in _load().get("runs", []):
        if run.get("id") == loop_id:
            return dict(run)
    return None


def list_runs(*, task_id: str = "", status: str = "") -> list[dict]:
    rows = []
    for run in _load().get("runs", []):
        if task_id and run.get("task_id") != task_id:
            continue
        if status and run.get("status") != status:
            continue
        rows.append(dict(run))
    return rows


def append_cycle(
    loop_id: str,
    *,
    checker_output: str,
    diff_text: str,
    preflight: dict,
    failed_commands: list[str],
    passed_commands: list[str],
    failure_fingerprint: str,
    status: str,
    stop_reason: str,
) -> dict:
    if status not in RUN_STATUSES:
        raise ValueError(f"invalid loop run status: {status}")
    with _locked():
        data = _load()
        run = next((r for r in data.get("runs", []) if r.get("id") == loop_id), None)
        if run is None:
            raise ValueError(f"unknown loop run: {loop_id}")
        cycle = int(run.get("cycle_count") or 0) + 1
        prefix = f"cycle-{cycle:03d}"
        artifact_path(loop_id, f"{prefix}-checker.txt").parent.mkdir(parents=True, exist_ok=True)
        artifact_path(loop_id, f"{prefix}-checker.txt").write_text(
            str(checker_output or ""),
            encoding="utf-8",
        )
        artifact_path(loop_id, f"{prefix}-diff.patch").write_text(
            str(diff_text or ""),
            encoding="utf-8",
        )
        artifact_path(loop_id, f"{prefix}-preflight.json").write_text(
            json.dumps(preflight or {}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        cycle_row = {
            "cycle": cycle,
            "checker_ref": f"loop_runs/{loop_id}/{prefix}-checker.txt",
            "diff_ref": f"loop_runs/{loop_id}/{prefix}-diff.patch",
            "preflight_ref": f"loop_runs/{loop_id}/{prefix}-preflight.json",
            "failed_commands": list(failed_commands or []),
            "passed_commands": list(passed_commands or []),
            "failure_fingerprint": str(failure_fingerprint or ""),
            "status": status,
            "stop_reason": str(stop_reason or ""),
            "created_at": now_ms(),
        }
        run.setdefault("cycles", []).append(cycle_row)
        run["cycle_count"] = cycle
        run["status"] = status
        run["stop_reason"] = str(stop_reason or "")
        run["latest_failure_fingerprint"] = str(failure_fingerprint or "")
        return _sync_run(data, run)


def update_status(loop_id: str, *, status: str, stop_reason: str = "") -> dict:
    if status not in RUN_STATUSES:
        raise ValueError(f"invalid loop run status: {status}")
    with _locked():
        data = _load()
        run = next((r for r in data.get("runs", []) if r.get("id") == loop_id), None)
        if run is None:
            raise ValueError(f"unknown loop run: {loop_id}")
        run["status"] = status
        run["stop_reason"] = str(stop_reason or "")
        return _sync_run(data, run)


def attach_background_log(loop_id: str) -> dict:
    with _locked():
        data = _load()
        run = next((r for r in data.get("runs", []) if r.get("id") == loop_id), None)
        if run is None:
            raise ValueError(f"unknown loop run: {loop_id}")
        artifact_path(loop_id, "background.log").parent.mkdir(parents=True, exist_ok=True)
        artifact_path(loop_id, "background.log").touch()
        run["background_log_ref"] = background_log_ref(loop_id)
        return _sync_run(data, run)
