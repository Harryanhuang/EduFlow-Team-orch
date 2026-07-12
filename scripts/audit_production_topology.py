#!/usr/bin/env python3
"""Read-only, dependency-injected audit of live EduFlow topology."""
import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping
Run = Callable[..., subprocess.CompletedProcess]
DAEMON_NAMES = ("router", "task-publish", "watchdog")
SENSITIVE_OPTION = re.compile(
    r"(?i)^(?:--?(?:token|api[-_]?key|secret|password|authorization|credential))(?:=|$)"
)
@dataclass(frozen=True)
class AuditDependencies:
    checkout: Path
    config_path: Path
    state_dir: Path
    run: Run
    now: Callable[[], str]
    environ: Mapping[str, str]
    expected_config_sha256: str | None = None
def _run(deps: AuditDependencies, argv: list[str], *, cwd: Path | None = None):
    try:
        return deps.run(
            argv,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(argv, 127, "", type(exc).__name__)
def _error(errors: list[dict], code: str, subject: str, detail: str) -> None:
    errors.append({"code": code, "subject": subject, "detail": detail})
def _safe_read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
def _config_facts(path: Path, errors: list[dict]) -> tuple[dict, str, str]:
    raw = _safe_read(path)
    absolute = str(path.resolve())
    if raw is None:
        _error(errors, "config_unreadable", absolute, "config cannot be read")
        return ({"path": absolute, "sha256": None, "generation": None}, "", "")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    profile_match = re.search(r'^\s*lark_profile\s*=\s*["\']([^"\']*)["\']', raw, re.MULTILINE)
    session_match = re.search(r'^\s*session\s*=\s*["\']([^"\']*)["\']', raw, re.MULTILINE)
    profile = profile_match.group(1) if profile_match else ""
    session = session_match.group(1) if session_match else ""
    return ({"path": absolute, "sha256": digest, "generation": digest[:16]}, profile, session)
def _git_facts(deps: AuditDependencies, errors: list[dict]) -> tuple[str | None, str | None]:
    top = _run(deps, ["git", "rev-parse", "--show-toplevel"], cwd=deps.checkout)
    rev = _run(deps, ["git", "rev-parse", "HEAD"], cwd=deps.checkout)
    checkout = (top.stdout or "").strip() if top.returncode == 0 else ""
    revision = (rev.stdout or "").strip() if rev.returncode == 0 else ""
    if not checkout:
        _error(errors, "checkout_unknown", "git", "absolute checkout cannot be verified")
    if not revision:
        _error(errors, "revision_unknown", "git", "commit SHA cannot be verified")
    if not checkout and not revision:
        _error(errors, "git_unavailable", "git", "git facts unavailable")
    return (str(Path(checkout).resolve()) if checkout else None, revision or None)
def _process_table(deps: AuditDependencies, errors: list[dict]) -> dict[int, dict]:
    result = _run(deps, ["ps", "-axo", "pid=,ppid=,command="])
    if result.returncode != 0 or not (result.stdout or "").strip():
        _error(errors, "ps_unavailable", "ps", "process table unavailable")
        return {}
    rows: dict[int, dict] = {}
    for line in result.stdout.splitlines():
        match = re.match(r"\s*(\d+)\s+(\d+)\s+(.+)$", line)
        if not match:
            continue
        pid, ppid, command = match.groups()
        rows[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "command": command}
    return rows
def _redacted_entry(command: str) -> str:
    """Retain only the executable/module/action identity, never arguments."""
    tokens = command.split()
    if not tokens:
        return ""
    safe: list[str] = [Path(tokens[0]).name]
    index = 1
    while index < len(tokens) and len(safe) < 5:
        token = tokens[index]
        if SENSITIVE_OPTION.match(token) or token.startswith("-") and token not in {"-m"}:
            break
        safe.append(token)
        index += 1
        if len(safe) >= 4 and "eduflow.cli" in safe:
            break
    return " ".join(safe)
def _python_version(deps: AuditDependencies, executable: str) -> str | None:
    result = _run(deps, [executable, "--version"])
    output = ((result.stdout or "") + (result.stderr or "")).strip()
    return output if result.returncode == 0 and output else None
def _pane_facts(
    deps: AuditDependencies,
    checkout: str | None,
    revision: str | None,
    config: dict,
    session: str,
    errors: list[dict],
) -> list[dict]:
    result = _run(
        deps,
        [
            "tmux", "list-panes", "-a", "-F",
            "#{session_name}\t#{window_name}\t#{pane_index}\t#{pane_pid}\t"
            "#{pane_current_command}\t#{pane_current_path}\t#{pane_start_command}",
        ],
    )
    if result.returncode != 0 or not (result.stdout or "").strip():
        _error(errors, "tmux_unavailable", "tmux", "live panes unavailable")
        return []
    panes: list[dict] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 6)
        if len(parts) != 7:
            _error(errors, "pane_row_corrupt", "tmux", "pane row has unexpected shape")
            continue
        pane_session, window, index, pid_text, cli_runtime, cwd, start = parts
        try:
            pid = int(pid_text)
        except ValueError:
            pid = None
            _error(errors, "pane_pid_corrupt", f"{pane_session}:{window}.{index}", "pane PID is not numeric")
        absolute_cwd = str(Path(cwd).resolve()) if Path(cwd).is_absolute() else None
        if checkout is None or absolute_cwd != checkout:
            _error(errors, "pane_cwd_drift", f"{pane_session}:{window}.{index}", "pane cwd differs from audited checkout")
        if session and pane_session != session:
            _error(errors, "pane_session_drift", f"{pane_session}:{window}.{index}", "pane session differs from config")
        panes.append(
            {
                "session": pane_session,
                "window": window,
                "index": index,
                "pid": pid,
                "checkout": absolute_cwd,
                "commit_sha": revision,
                "cli_runtime": cli_runtime,
                "config_path": config["path"],
                "config_sha256": config["sha256"],
                "config_generation": config["generation"],
                "state_dir": str(deps.state_dir.resolve()),
                "startup_entry": _redacted_entry(start),
            }
        )
    return panes
def _daemon_facts(
    deps: AuditDependencies,
    processes: dict[int, dict],
    checkout: str | None,
    revision: str | None,
    config: dict,
    profile: str,
    session: str,
    errors: list[dict],
) -> list[dict]:
    rows: list[dict] = []
    for name in DAEMON_NAMES:
        pid_path = deps.state_dir / f"{name}.pid"
        raw_pid = _safe_read(pid_path)
        pid: int | None = None
        if raw_pid is None:
            _error(errors, "daemon_pid_missing", name, "PID file is unreadable")
        else:
            try:
                pid = int(raw_pid.strip())
            except ValueError:
                _error(errors, "daemon_pid_corrupt", name, "PID file is not numeric")
        process = processes.get(pid) if pid is not None else None
        if pid is not None and process is None:
            _error(errors, "daemon_pid_not_live", name, "PID is absent from process table")
        command = process["command"] if process else ""
        expected = f"eduflow.cli {name}"
        if process and expected not in command:
            _error(errors, "daemon_entry_drift", name, "live PID does not match daemon entrypoint")
        executable = command.split()[0] if command else ""
        python_runtime = _python_version(deps, executable) if executable else None
        if process and not python_runtime:
            _error(errors, "python_runtime_unknown", name, "Python runtime version cannot be verified")
        rows.append(
            {
                "name": name,
                "pid": pid,
                "checkout": checkout,
                "commit_sha": revision,
                "python_runtime": python_runtime,
                "cli_runtime": Path(executable).name if executable else None,
                "config_path": config["path"],
                "config_sha256": config["sha256"],
                "config_generation": config["generation"],
                "state_dir": str(deps.state_dir.resolve()),
                "lark_profile": profile or None,
                "tmux_session": session or None,
                "daemon_profile": "self-supervised" if name == "watchdog" else "watchdog-supervised",
                "startup_entry": _redacted_entry(command),
            }
        )
    return rows
def _agent_processes(panes: list[dict], processes: dict[int, dict], errors: list[dict]) -> list[dict]:
    agents: list[dict] = []
    for pane in panes:
        process = processes.get(pane["pid"])
        subject = f'{pane["session"]}:{pane["window"]}.{pane["index"]}'
        if process is None:
            _error(errors, "agent_process_missing", subject, "pane PID is absent from process table")
        agents.append(
            {
                "agent": pane["window"],
                "pid": pane["pid"],
                "pane": subject,
                "checkout": pane["checkout"],
                "commit_sha": pane["commit_sha"],
                "cli_runtime": pane["cli_runtime"],
                "startup_entry": _redacted_entry(process["command"]) if process else None,
            }
        )
    return agents
def audit(deps: AuditDependencies) -> dict:
    errors: list[dict] = []
    config, profile, session = _config_facts(deps.config_path, errors)
    if deps.expected_config_sha256 and config["sha256"] != deps.expected_config_sha256:
        _error(errors, "config_hash_changed", config["path"], "config SHA256 differs from approved generation")
    checkout, revision = _git_facts(deps, errors)
    processes = _process_table(deps, errors)
    panes = _pane_facts(deps, checkout, revision, config, session, errors)
    daemons = _daemon_facts(
        deps, processes, checkout, revision, config, profile, session, errors
    )
    agents = _agent_processes(panes, processes, errors)
    errors.sort(key=lambda item: (item["code"], item["subject"], item["detail"]))
    return {
        "ok": not errors,
        "generated_at": deps.now(),
        "checkout": {"path": checkout, "commit_sha": revision},
        "config": config,
        "state": {"path": str(deps.state_dir.resolve())},
        "daemons": daemons,
        "panes": panes,
        "agent_processes": agents,
        "errors": errors,
        "redactions": {
            "applied": True,
            "fields": ["command_arguments", "config_values", "environment_values"],
        },
    }
def _default_run(argv, **kwargs):
    return subprocess.run(argv, **kwargs)
def _default_dependencies(args) -> AuditDependencies:
    checkout = Path(args.checkout).expanduser().resolve()
    # Mirrors runtime.paths resolution without its directory-creation side effect.
    config_raw = args.config or os.environ.get("EDUFLOW_CONFIG_FILE") or str(checkout / "eduflow.toml")
    state_raw = args.state_dir or os.environ.get("EDUFLOW_STATE_DIR") or str(Path.home() / ".eduflow")
    config_path = Path(config_raw).expanduser().resolve()
    state_dir = Path(state_raw).expanduser().resolve()
    return AuditDependencies(
        checkout=checkout,
        config_path=config_path,
        state_dir=state_dir,
        run=_default_run,
        now=lambda: datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        environ=dict(os.environ),
        expected_config_sha256=args.expected_config_sha256,
    )
def main(argv: list[str] | None = None, *, deps: AuditDependencies | None = None) -> int:
    if deps is None:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--checkout", default=str(Path(__file__).resolve().parents[1]))
        parser.add_argument("--config")
        parser.add_argument("--state-dir")
        parser.add_argument("--expected-config-sha256")
        args = parser.parse_args(argv)
        deps = _default_dependencies(args)
    report = audit(deps)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=False))
    return 0 if report["ok"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
