"""Workspace policy preflight for loop checks."""
from __future__ import annotations

import subprocess
from pathlib import Path


def _git_status(cwd: Path, run) -> dict:
    try:
        proc = run(
            ["git", "status", "--short"],
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=30,
        )
        if proc is None or getattr(proc, "returncode", 1) != 0:
            return {"git_status_unavailable": True}
        lines = str(getattr(proc, "stdout", "") or "").splitlines()[:50]
        return {
            "git_dirty": bool(lines),
            "git_status_short": lines,
        }
    except Exception:
        return {"git_status_unavailable": True}


def check_workspace(
    *,
    workspace_mode: str,
    workspace_path: str,
    allow_unscoped: bool,
    cwd: Path,
    run=subprocess.run,
) -> dict:
    mode = str(workspace_mode or "").strip()
    path = str(workspace_path or "").strip()
    root = Path(path) if path else Path(cwd)
    result = {
        "ok": True,
        "workspace_mode": mode,
        "workspace_path": path,
        "allow_unscoped": bool(allow_unscoped),
        "shared_workspace_risk": False,
    }

    if not mode:
        if not allow_unscoped:
            result.update({"ok": False, "reason": "workspace_policy_missing"})
            return result
        result["reason"] = "unscoped_workspace_allowed"
        root = Path(cwd)
    elif mode == "worktree":
        if not path or not root.exists():
            result.update({"ok": False, "reason": "workspace_path_missing"})
            return result
    elif mode == "shared":
        result["shared_workspace_risk"] = True
        root = Path(cwd)
    elif mode in {"container", "external_artifact"}:
        result.update({"ok": False, "reason": "unsupported_workspace_mode_for_loop"})
        return result
    else:
        result.update({"ok": False, "reason": "unknown_workspace_mode"})
        return result

    result.update(_git_status(root, run))
    return result
