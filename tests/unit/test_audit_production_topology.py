from __future__ import annotations

import importlib.util
import json
import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[2] / "scripts" / "audit_production_topology.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_production_topology", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completed(argv: list[str], stdout: str = "", returncode: int = 0):
    return subprocess.CompletedProcess(argv, returncode, stdout, "")


def _fixture(tmp_path: Path):
    module = _load_module()
    checkout = tmp_path / "checkout"
    state = tmp_path / "state"
    checkout.mkdir()
    state.mkdir()
    config = checkout / "eduflow.toml"
    config.write_text(
        'lark_profile = "production-bot"\n'
        '[team]\nsession = "eduflow-team"\n'
        '[team.agents.manager]\nruntime = "manager_primary"\n',
        encoding="utf-8",
    )
    for name, pid in (("router", 101), ("task-publish", 102), ("watchdog", 103)):
        (state / f"{name}.pid").write_text(str(pid), encoding="ascii")

    pane_rows = "\n".join(
        f"eduflow-team\t{name}\t0\t{200 + i}\tpython3\t{checkout}\tpython3 -m eduflow.cli agent {name}"
        for i, name in enumerate(("manager", "worker_course", "worker_review"))
    )
    commands = {
        "git rev-parse --show-toplevel": str(checkout),
        "git rev-parse HEAD": "a" * 40,
        "python3 --version": "Python 3.14.3",
        "tmux list-panes -a": pane_rows,
        "ps -axo pid=,ppid=,command=": "\n".join(
            [
                f"101 1 python3 -m eduflow.cli router --config {config}",
                f"102 1 python3 -m eduflow.cli task-publish --config {config}",
                f"103 1 python3 -m eduflow.cli watchdog --config {config}",
                *[
                    f"{200 + i} 1 python3 -m eduflow.cli agent {name}"
                    for i, name in enumerate(("manager", "worker_course", "worker_review"))
                ],
            ]
        ),
    }
    calls: list[list[str]] = []

    def run(argv, **_kwargs):
        calls.append(argv)
        key = " ".join(str(item) for item in argv)
        for prefix, value in commands.items():
            if key.startswith(prefix):
                return _completed(argv, value + "\n")
        return _completed(argv, "", 127)

    deps = module.AuditDependencies(
        checkout=checkout,
        config_path=config,
        state_dir=state,
        run=run,
        now=lambda: "2026-07-12T12:00:00+08:00",
        environ={"LARK_TOKEN": "super-secret-token", "PATH": "/usr/bin"},
    )
    commands["_calls"] = calls
    return module, deps, commands, config, checkout, state


def test_audit_emits_deterministic_complete_schema_for_correlated_runtime(tmp_path):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)

    report = module.audit(deps)

    assert list(report) == [
        "ok", "generated_at", "checkout", "config", "state", "daemons",
        "panes", "agent_processes", "errors", "redactions",
    ]
    assert report["ok"] is True
    assert report["checkout"] == {"path": str(checkout.resolve()), "commit_sha": "a" * 40}
    assert report["config"]["path"] == str(config.resolve())
    assert len(report["config"]["sha256"]) == 64
    assert report["config"]["generation"] == report["config"]["sha256"][:16]
    assert report["state"]["path"] == str(state.resolve())
    assert {d["name"] for d in report["daemons"]} == {"router", "task-publish", "watchdog"}
    assert all(d["pid"] and d["checkout"] == str(checkout.resolve()) for d in report["daemons"])
    assert all(d["commit_sha"] == "a" * 40 and d["python_runtime"] for d in report["daemons"])
    assert all(d["config_path"] == str(config.resolve()) for d in report["daemons"])
    assert all(d["config_sha256"] == report["config"]["sha256"] for d in report["daemons"])
    assert all(d["lark_profile"] == "production-bot" for d in report["daemons"])
    assert all(d["tmux_session"] == "eduflow-team" and d["daemon_profile"] for d in report["daemons"])
    assert all(d["startup_entry"] for d in report["daemons"])
    assert len(report["panes"]) == 3
    assert len(report["agent_processes"]) == 3
    tmux_call = next(call for call in commands["_calls"] if call[:3] == ["tmux", "list-panes", "-a"])
    assert "\t" in tmux_call[-1]
    assert "\\t" not in tmux_call[-1]
    assert json.dumps(report, sort_keys=True)


@pytest.mark.parametrize(
    ("mutation", "error_code"),
    [
        ("dead_pid", "daemon_pid_not_live"),
        ("corrupt_pid", "daemon_pid_corrupt"),
        ("entry_drift", "daemon_entry_drift"),
        ("unknown_checkout", "checkout_unknown"),
        ("unknown_revision", "revision_unknown"),
        ("pane_cwd_drift", "pane_cwd_drift"),
        ("missing_tmux", "tmux_unavailable"),
        ("missing_ps", "ps_unavailable"),
        ("missing_git", "git_unavailable"),
        ("config_hash_change", "config_hash_changed"),
    ],
)
def test_audit_fails_closed_on_unverifiable_or_drifted_facts(tmp_path, mutation, error_code):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    if mutation == "dead_pid":
        commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
            f"101 1 python3 -m eduflow.cli router --config {config}\n", ""
        )
    elif mutation == "corrupt_pid":
        (state / "router.pid").write_text("not-a-pid", encoding="ascii")
    elif mutation == "entry_drift":
        commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
            "python3 -m eduflow.cli router", "python3 unrelated.py"
        )
    elif mutation == "unknown_checkout":
        commands["git rev-parse --show-toplevel"] = ""
    elif mutation == "unknown_revision":
        commands["git rev-parse HEAD"] = ""
    elif mutation == "pane_cwd_drift":
        commands["tmux list-panes -a"] = commands["tmux list-panes -a"].replace(str(checkout), "/tmp/wrong", 1)
    elif mutation == "missing_tmux":
        commands["tmux list-panes -a"] = ""
    elif mutation == "missing_ps":
        commands["ps -axo pid=,ppid=,command="] = ""
    elif mutation == "missing_git":
        commands["git rev-parse --show-toplevel"] = ""
        commands["git rev-parse HEAD"] = ""
    elif mutation == "config_hash_change":
        deps = module.AuditDependencies(**{**deps.__dict__, "expected_config_sha256": "0" * 64})

    report = module.audit(deps)

    assert report["ok"] is False
    assert error_code in {error["code"] for error in report["errors"]}


def test_report_redacts_config_values_environment_values_and_sensitive_argv(tmp_path):
    module, deps, commands, config, _checkout, _state = _fixture(tmp_path)
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n999 1 python3 -m eduflow.cli agent intruder --token super-secret-token "
        f"--api-key=abcdef123456 --config {config}"
    )

    report = module.audit(deps)
    rendered = json.dumps(report, sort_keys=True)

    assert "super-secret-token" not in rendered
    assert "abcdef123456" not in rendered
    assert "oc_" not in rendered
    assert "production-bot" in rendered  # identifier, not credential
    assert report["redactions"]["applied"] is True
    assert report["redactions"]["fields"] == ["command_arguments", "config_values", "environment_values"]


def test_cli_returns_nonzero_for_failed_audit_and_prints_json(tmp_path, capsys):
    module, deps, commands, *_ = _fixture(tmp_path)
    commands["tmux list-panes -a"] = ""

    exit_code = module.main(deps=deps)

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert output["ok"] is False


def test_default_dependencies_are_read_only_when_state_directory_is_absent(tmp_path, monkeypatch):
    module = _load_module()
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    absent_state = tmp_path / "absent-state"
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(absent_state))
    monkeypatch.setenv("EDUFLOW_CONFIG_FILE", str(checkout / "eduflow.toml"))
    args = SimpleNamespace(
        checkout=str(checkout), config=None, state_dir=None,
        expected_config_sha256=None,
    )

    deps = module._default_dependencies(args)

    assert deps.state_dir == absent_state.resolve()
    assert not absent_state.exists()
