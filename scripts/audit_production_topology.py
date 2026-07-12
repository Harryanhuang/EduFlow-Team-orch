#!/usr/bin/env python3
"""Read-only, dependency-injected audit of live EduFlow topology."""
import argparse, hashlib, json, os, re, shlex, subprocess, tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping
Run = Callable[..., subprocess.CompletedProcess]; DAEMONS = ("router", "task-publish", "watchdog")
FIELDS = "pid executable checkout commit_sha python_runtime cli_runtime config_path config_sha256 config_generation state_dir lark_profile tmux_session daemon_profile startup_entry".split()
SECRET = re.compile(r"(?i)(token|api[-_]?key|secret|password|authorization|credential)")
@dataclass(frozen=True)
class AuditDependencies:
    checkout: Path; config_path: Path; state_dir: Path
    run: Run; now: Callable[[], str]; environ: Mapping[str, str]
    expected_config_sha256: str | None = None
def _run(deps, argv, cwd=None):
    try:
        return deps.run(argv, cwd=str(cwd) if cwd else None, capture_output=True,
                        text=True, timeout=5)
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(argv, 127, "", type(exc).__name__)
def _err(errors, code, subject, detail): errors.append({"code": code, "subject": subject, "detail": detail})
def _read(path):
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
def _config(path, errors=None, subject="config"):
    path = Path(path).expanduser().resolve()
    raw = _read(path)
    if raw is None:
        if errors is not None: _err(errors, "config_unreadable", subject, "actual config cannot be read")
        return {"path": str(path), "sha256": None, "generation": None,
                "lark_profile": None, "tmux_session": None, "agent_clis": {}}
    digest = hashlib.sha256(raw.encode()).hexdigest()
    try:
        data = tomllib.loads(raw)
    except tomllib.TOMLDecodeError:
        data = {}
        if errors is not None: _err(errors, "config_corrupt", subject, "TOML cannot be parsed")
    team, registry, invalid = data.get("team", {}), data.get("runtime_registry", {}), False
    if not isinstance(team, dict): team, invalid = {}, True
    if not isinstance(registry, dict): registry, invalid = {}, True
    agents = team.get("agents", {})
    if not isinstance(agents, dict): agents, invalid = {}, True
    if any(not isinstance(value, dict) for value in registry.values()): invalid = True
    if any(not isinstance(value, dict) for value in agents.values()): invalid = True
    if invalid and errors is not None: _err(errors, "config_schema_invalid", subject, "config tables have invalid types")
    agent_clis = {name: registry.get(spec.get("runtime"), {}).get("cli")
                  for name, spec in agents.items() if isinstance(spec, dict)
                  and isinstance(registry.get(spec.get("runtime"), {}), dict)}
    return {"path": str(path), "sha256": digest, "generation": digest[:16],
            "lark_profile": data.get("lark_profile"),
            "tmux_session": team.get("session"),
            "agent_clis": agent_clis}
def _git(deps, cwd, errors, subject):
    if not cwd:
        _err(errors, "checkout_unknown", subject, "process cwd unavailable")
        return None, None
    top = _run(deps, ["git", "rev-parse", "--show-toplevel"], cwd)
    rev = _run(deps, ["git", "rev-parse", "HEAD"], cwd)
    checkout = (top.stdout or "").strip() if top.returncode == 0 else ""
    revision = (rev.stdout or "").strip() if rev.returncode == 0 else ""
    if not checkout: _err(errors, "checkout_unknown", subject, "git checkout unavailable")
    if not revision: _err(errors, "revision_unknown", subject, "git revision unavailable")
    if not checkout and not revision: _err(errors, "git_unavailable", subject, "git facts unavailable")
    return (str(Path(checkout).resolve()) if checkout else None, revision or None)
def _processes(deps, errors):
    result = _run(deps, ["ps", "-axo", "pid=,ppid=,command="])
    if result.returncode or not (result.stdout or "").strip():
        _err(errors, "ps_unavailable", "ps", "process table unavailable")
        return {}
    rows = {}
    for line in result.stdout.splitlines():
        match = re.match(r"\s*(\d+)\s+(\d+)\s+(.+)$", line)
        if match:
            pid, ppid, command = match.groups()
            rows[int(pid)] = {"pid": int(pid), "ppid": int(ppid), "command": command}
    return rows
def _tokens(command):
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()
def _entry(command, executable):
    tokens = _tokens(command)
    if not executable or not Path(executable).is_absolute(): return None, None, None
    name = Path(executable).name
    index = next((i for i, token in enumerate(tokens)
                  if token == executable or Path(token).name == name), None)
    if index is None: return None, None, None
    if "python" in name and tokens[index + 1:index + 3] == ["-m", "eduflow.cli"]:
        action = tokens[index + 3] if index + 3 < len(tokens) else None
        if action in (*DAEMONS, "agent"):
            return f"{name} -m eduflow.cli {action}", action, executable
    if name in {"claude", "codex", "codex-cli", "qoderclicn", "gemini", "qwen"}:
        return name, "agent", executable
    return None, None, None
def _setting(command, names):
    for env, option in names:
        match = re.search(rf"(?:^|\s){re.escape(env)}=(.*?)(?=\s+[A-Z][A-Z0-9_]*=|"
                          rf"\s+(?:python\d*(?:\.\d+)?|claude|codex|qoderclicn)\s|$)", command)
        if match:
            return match.group(1).strip(" '\"")
        match = re.search(rf"(?:^|\s){re.escape(option)}(?:=|\s+)(.*?)(?=\s+--[\w-]+|$)", command)
        if match:
            return match.group(1).strip(" '\"")
        tokens = _tokens(command)
        for index, token in enumerate(tokens):
            if token.startswith(env + "="):
                return token.split("=", 1)[1]
            if token == option and index + 1 < len(tokens):
                return tokens[index + 1]
            if token.startswith(option + "="):
                return token.split("=", 1)[1]
    return None
def _ancestry(processes, pid):
    chain, seen = [], set()
    while pid in processes and pid not in seen:
        seen.add(pid)
        chain.append(processes[pid])
        pid = processes[pid]["ppid"]
    return chain
def _executable(deps, pid):
    result = _run(deps, ["ps", "-p", str(pid), "-o", "comm="])
    value = (result.stdout or "").strip()
    return value if result.returncode == 0 and Path(value).is_absolute() else None
def _descendant(deps, processes, root, action):
    queue = [root]
    while queue:
        pid = queue.pop(0)
        row = processes.get(pid)
        if row and _entry(row["command"], _executable(deps, pid))[1] == action:
            return row
        queue.extend(sorted(p["pid"] for p in processes.values() if p["ppid"] == pid))
    return None
def _cli_name(name): return {"claude-code": "claude", "codex-cli": "codex"}.get(name, name)
def _cwd(deps, pid):
    result = _run(deps, ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
    for line in (result.stdout or "").splitlines():
        if line.startswith("n/"):
            return str(Path(line[1:]).resolve())
    return None
def _version(deps, executable):
    if not executable: return None
    result = _run(deps, [executable, "--version"])
    value = ((result.stdout or "") + (result.stderr or "")).strip()
    return value if result.returncode == 0 and 0 < len(value) <= 256 and "\n" not in value and "\r" not in value else None
def _provenance(deps, process, processes, target, errors, subject, profile):
    if not process:
        return {field: None for field in FIELDS}
    pid, command = process["pid"], process["command"]
    executable = _executable(deps, pid)
    entry, action, _ = _entry(command, executable)
    chain = _ancestry(processes, pid)
    env_result = _run(deps, ["ps", "eww", "-p", str(pid), "-o", "command="])
    combined = (env_result.stdout or "") + " " + " ".join(item["command"] for item in chain)
    cwd = _cwd(deps, pid)
    checkout, revision = _git(deps, cwd, errors, subject)
    config_path = _setting(combined, (("EDUFLOW_CONFIG_FILE", "--config"),))
    state_dir = _setting(combined, (("EDUFLOW_STATE_DIR", "--state-dir"),))
    if not config_path: _err(errors, "process_config_unknown", subject, "actual process config is not proven")
    if not state_dir: _err(errors, "process_state_unknown", subject, "actual process state dir is not proven")
    actual = _config(config_path, errors, subject) if config_path else _config(target["path"])
    if checkout != target["checkout"]:
        _err(errors, "process_checkout_mismatch", subject, "actual checkout differs from target")
    if actual["path"] != target["path"]:
        _err(errors, "process_config_mismatch", subject, "actual config differs from target")
    if state_dir and str(Path(state_dir).resolve()) != target["state_dir"]:
        _err(errors, "process_state_mismatch", subject, "actual state differs from target")
    if actual["sha256"] != target["sha256"]:
        _err(errors, "process_config_generation_mismatch", subject, "actual config hash differs")
    runtime = _version(deps, executable)
    if not entry: _err(errors, "process_entry_unknown", subject, "strict EduFlow entry not found")
    if not runtime: _err(errors, "cli_runtime_unknown", subject, "executable version unavailable")
    return {
        "pid": pid, "executable": executable, "checkout": checkout, "commit_sha": revision,
        "ancestry": [item["pid"] for item in chain],
        "python_runtime": runtime if executable and "python" in executable else "not-applicable",
        "cli_runtime": f"{executable} {runtime}" if runtime else None,
        "config_path": actual["path"], "config_sha256": actual["sha256"],
        "config_generation": actual["generation"],
        "state_dir": str(Path(state_dir).resolve()) if state_dir else None,
        "lark_profile": actual["lark_profile"], "tmux_session": actual["tmux_session"],
        "daemon_profile": profile, "startup_entry": entry,
    }
def _tmux(deps, session, errors):
    fmt = ("#{session_name}\t#{window_name}\t#{pane_index}\t#{pane_pid}\t"
           "#{pane_current_command}\t#{pane_current_path}\t#{pane_start_command}")
    result = _run(deps, ["tmux", "list-panes", "-a", "-F", fmt])
    if result.returncode or not (result.stdout or "").strip():
        _err(errors, "tmux_unavailable", "tmux", "live panes unavailable")
        return [], []
    selected, foreign = [], []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 6)
        if len(parts) != 7:
            _err(errors, "pane_row_corrupt", "tmux", "unexpected pane row")
            continue
        row = dict(zip(("session", "window", "index", "pid", "runtime", "cwd", "start"), parts))
        try:
            row["pid"] = int(row["pid"])
        except ValueError:
            _err(errors, "pane_pid_corrupt", row["session"], "pane PID is not numeric")
            continue
        (selected if row["session"] == session else foreign).append(row)
    return selected, foreign
def audit(deps):
    errors, suspects = [], []
    target_cfg = _config(deps.config_path, errors)
    requested_checkout = str(deps.checkout.resolve())
    verified_checkout, verified_revision = _git(deps, requested_checkout, errors, "target")
    if verified_checkout != requested_checkout:
        _err(errors, "target_checkout_mismatch", "target", "requested checkout differs from git")
    target = {**target_cfg, "checkout": verified_checkout,
              "state_dir": str(deps.state_dir.resolve())}
    if not target["lark_profile"]: _err(errors, "lark_profile_missing", "config", "Lark profile is required")
    if not target["tmux_session"]: _err(errors, "tmux_session_missing", "config", "tmux session is required")
    if deps.expected_config_sha256 and target["sha256"] != deps.expected_config_sha256:
        _err(errors, "config_hash_changed", target["path"], "config hash changed")
    processes = _processes(deps, errors)
    pane_rows, foreign = _tmux(deps, target["tmux_session"], errors)
    for row in foreign:
        if "eduflow" in row["session"].lower() or "eduflow" in row["cwd"].lower():
            suspects.append({"kind": "legacy_tmux_session", "pid": row["pid"],
                             "session": row["session"]})
            _err(errors, "legacy_tmux_session", row["session"], "possible legacy EduFlow pane")
    daemons, expected = [], set()
    for name in DAEMONS:
        raw = _read(deps.state_dir / f"{name}.pid")
        try:
            pid = int((raw or "").strip())
        except ValueError:
            pid = None
            _err(errors, "daemon_pid_corrupt" if raw else "daemon_pid_missing", name, "invalid PID file")
        process = processes.get(pid) if pid else None
        if pid and not process: _err(errors, "daemon_pid_not_live", name, "PID absent from ps")
        if process and _entry(process["command"], _executable(deps, pid))[1] != name: _err(errors, "daemon_entry_drift", name, "PID has a different strict entry")
        if pid: expected.add(pid)
        profile = "self-supervised" if name == "watchdog" else "watchdog-supervised"
        proof = _provenance(deps, process, processes, target, errors, name, profile)
        if not process: proof.update(pid=pid, daemon_profile=profile)
        daemons.append({"name": name, **proof})
        if process and proof["checkout"] != target["checkout"]:
            suspects.append({"kind": "multi_checkout", "pid": process["pid"],
                             "checkout": proof["checkout"]})
    panes, agents = [], []
    for pane in pane_rows:
        if not Path(pane["cwd"]).is_absolute() or str(Path(pane["cwd"]).resolve()) != target["checkout"]:
            _err(errors, "pane_cwd_drift", f'{pane["session"]}:{pane["window"]}.{pane["index"]}',
                 "tmux pane cwd differs from target checkout")
        process = _descendant(deps, processes, pane["pid"], "agent")
        subject = f'{pane["session"]}:{pane["window"]}.{pane["index"]}'
        if not process: _err(errors, "agent_process_missing", subject, "no strict agent child found")
        expected_cli = target["agent_clis"].get(pane["window"])
        actual_cli = Path(_entry(process["command"], _executable(deps, process["pid"]))[2]).name if process else None
        if not expected_cli: _err(errors, "agent_runtime_mapping_missing", subject, "configured CLI is unknown")
        elif _cli_name(expected_cli) != _cli_name(actual_cli): _err(errors, "agent_entry_drift", subject, "actual CLI differs from configured runtime")
        proof = _provenance(deps, process, processes, target, errors, subject, "tmux-agent")
        if process and proof["checkout"] != target["checkout"]:
            suspects.append({"kind": "multi_checkout", "pid": process["pid"],
                             "checkout": proof["checkout"]})
        panes.append({"session": pane["session"], "window": pane["window"],
                      "index": pane["index"], "tmux_pane_pid": pane["pid"], **proof})
        agents.append({"agent": pane["window"], "pane": subject, **proof})
    associated_agents = {row["pid"] for row in agents if row["pid"]}
    pane_roots = {row["pid"] for row in pane_rows}
    for process in processes.values():
        entry, action, _ = _entry(process["command"], _executable(deps, process["pid"]))
        if action in DAEMONS and process["pid"] not in expected:
            suspects.append({"kind": "duplicate_daemon", "pid": process["pid"], "entry": entry})
            _err(errors, "duplicate_daemon", str(process["pid"]), "unexpected daemon process")
        elif action == "agent" and process["pid"] not in associated_agents:
            chain = _ancestry(processes, process["pid"])
            env = _run(deps, ["ps", "eww", "-p", str(process["pid"]), "-o", "command="])
            context = (env.stdout or "") + " " + " ".join(row["command"] for row in chain)
            actual_config = _setting(context, (("EDUFLOW_CONFIG_FILE", "--config"),))
            actual_state = _setting(context, (("EDUFLOW_STATE_DIR", "--state-dir"),))
            scoped = ("eduflow.cli agent" in (entry or "") or _cwd(deps, process["pid"]) == target["checkout"]
                      or bool(pane_roots & {row["pid"] for row in chain})
                      or (actual_config and str(Path(actual_config).resolve()) == target["path"])
                      or (actual_state and str(Path(actual_state).resolve()) == target["state_dir"]))
            if scoped:
                suspects.append({"kind": "orphan_agent", "pid": process["pid"], "entry": entry})
                _err(errors, "orphan_agent", str(process["pid"]), "agent is not linked to configured pane")
        elif (Path(_tokens(process["command"])[0]).name != "tmux" and
              re.search(r"(?:eduflow\.cli|(?:^|[/\s])eduflow(?:team)?\s)",
                        process["command"].lower()) and not action):
            suspects.append({"kind": "legacy_entry", "pid": process["pid"], "entry": "unrecognized"})
            _err(errors, "legacy_entry", str(process["pid"]), "unrecognized EduFlow command")
    raw_commands = " ".join(p["command"] for p in processes.values()) + " " + " ".join(p["start"] for p in pane_rows)
    redaction_count = len(SECRET.findall(raw_commands))
    errors.sort(key=lambda e: (e["code"], e["subject"]))
    return {
        "ok": not errors, "generated_at": deps.now(),
        "checkout": {"path": target["checkout"], "commit_sha": verified_revision},
        "config": {key: target[key] for key in ("path", "sha256", "generation")},
        "state": {"path": target["state_dir"]}, "daemons": daemons,
        "panes": panes, "agent_processes": agents, "suspect_processes": suspects,
        "errors": errors, "redactions": {"applied": redaction_count > 0, "count": redaction_count,
                                           "fields": ["command_arguments", "config_values", "environment_values"]},
    }
def _default_run(argv, **kwargs): return subprocess.run(argv, **kwargs)
def _default_dependencies(args):
    checkout = Path(args.checkout).expanduser().resolve()
    config = args.config or os.environ.get("EDUFLOW_CONFIG_FILE") or checkout / "eduflow.toml"
    state = args.state_dir or os.environ.get("EDUFLOW_STATE_DIR") or Path.home() / ".eduflow"
    return AuditDependencies(checkout, Path(config).expanduser().resolve(),
                             Path(state).expanduser().resolve(), _default_run,
                             lambda: datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
                             dict(os.environ), args.expected_config_sha256)
def main(argv=None, *, deps=None):
    if deps is None:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--checkout", default=str(Path(__file__).resolve().parents[1]))
        for flag in ("--config", "--state-dir", "--expected-config-sha256"): parser.add_argument(flag)
        parser.add_argument("--json", action="store_true")
        deps = _default_dependencies(parser.parse_args(argv))
    report = audit(deps); print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1
if __name__ == "__main__":
    raise SystemExit(main())
