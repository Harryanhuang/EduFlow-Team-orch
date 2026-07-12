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
    checkout = tmp_path / "checkout with spaces"
    state = checkout / ".state with spaces"
    checkout.mkdir()
    state.mkdir()
    config = checkout / "eduflow.toml"
    config.write_text(
        'lark_profile = "production-bot"\n'
        '[team]\nsession = "eduflow-team"\n'
        '[runtime_registry.agent_primary]\ncli = "python3"\n'
        '[team.agents.manager]\nruntime = "agent_primary"\n'
        '[team.agents.worker_course]\nruntime = "agent_primary"\n'
        '[team.agents.worker_review]\nruntime = "agent_primary"\n',
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
        "/tmp/fake/python3 --version": "Python 3.14.3",
        "tmux list-panes -a": pane_rows,
        "ps -axo pid=,ppid=,command=": "\n".join(
            [
                f"101 1 EDUFLOW_STATE_DIR={state} python3 -m eduflow.cli router --config {config}",
                f"102 1 EDUFLOW_STATE_DIR={state} python3 -m eduflow.cli task-publish --config {config}",
                f"103 1 EDUFLOW_STATE_DIR={state} python3 -m eduflow.cli watchdog --config {config}",
                *[
                    f"{200 + i} 1 EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config} "
                    f"python3 -m eduflow.cli agent {name}"
                    for i, name in enumerate(("manager", "worker_course", "worker_review"))
                ],
            ]
        ),
    }
    calls: list[list[str]] = []

    def run(argv, **_kwargs):
        calls.append(argv)
        key = " ".join(str(item) for item in argv)
        if argv[:2] == ["lsof", "-a"]:
            pid = argv[argv.index("-p") + 1]
            value = commands.get(f"process-cwd:{pid}", str(checkout))
            return _completed(argv, f"p{pid}\nfcwd\nn{value}\n")
        if len(argv) >= 5 and argv[:2] == ["ps", "-p"] and "comm=" in argv:
            pid = argv[2]
            return _completed(argv, commands.get(f"process-exe:{pid}", "/tmp/fake/python3") + "\n")
        if len(argv) >= 5 and argv[:2] == ["ps", "eww"]:
            pid = argv[argv.index("-p") + 1]
            return _completed(argv, commands.get(f"process-env:{pid}", "") + "\n")
        if argv[:3] == ["git", "rev-parse", "--show-toplevel"]:
            cwd = Path(_kwargs.get("cwd") or checkout)
            value = commands["git rev-parse --show-toplevel"] if cwd == checkout else str(cwd)
            return _completed(argv, value + "\n")
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
        "panes", "agent_processes", "suspect_processes", "errors", "redactions",
    ]
    assert report["ok"] is True
    assert report["checkout"] == {"path": str(checkout.resolve()), "commit_sha": "a" * 40}
    assert report["config"]["path"] == str(config.resolve())
    assert len(report["config"]["sha256"]) == 64
    assert report["config"]["generation"] == report["config"]["sha256"][:16]
    assert report["state"]["path"] == str(state.resolve())
    assert {d["name"] for d in report["daemons"]} == {"router", "task-publish", "watchdog"}
    assert all(d["pid"] and d["checkout"] == str(checkout.resolve()) for d in report["daemons"])
    assert all(d["commit_sha"] == "a" * 40 and d["python_runtime"]
               and Path(d["executable"]).is_absolute() for d in report["daemons"])
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
        commands["ps -axo pid=,ppid=,command="] = "\n".join(
            line for line in commands["ps -axo pid=,ppid=,command="].splitlines()
            if not line.startswith("101 ")
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


def test_records_each_pane_and_agent_from_actual_child_process_provenance(tmp_path):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"200 1 EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config} python3 -m eduflow.cli agent manager",
        f"200 1 zsh\n250 200 EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config} "
        "python3 -m eduflow.cli agent manager",
    )

    report = module.audit(deps)

    pane = next(row for row in report["panes"] if row["window"] == "manager")
    agent = next(row for row in report["agent_processes"] if row["agent"] == "manager")
    assert pane["pid"] == 250
    assert pane["tmux_pane_pid"] == 200
    required = {
        "pid", "executable", "checkout", "commit_sha", "python_runtime", "cli_runtime",
        "config_path", "config_sha256", "config_generation", "state_dir",
        "lark_profile", "tmux_session", "daemon_profile", "startup_entry",
    }
    assert required <= pane.keys()
    assert required <= agent.keys()
    assert pane["ancestry"] == agent["ancestry"] == [250, 200]
    assert pane["checkout"] == agent["checkout"] == str(checkout.resolve())
    assert pane["config_path"] == agent["config_path"] == str(config.resolve())
    assert pane["state_dir"] == agent["state_dir"] == str(state.resolve())


def test_actual_process_checkout_and_config_must_match_target(tmp_path):
    module, deps, commands, config, checkout, _state = _fixture(tmp_path)
    other = tmp_path / "other-checkout"
    other.mkdir()
    other_config = other / "eduflow.toml"
    other_config.write_text(config.read_text(), encoding="utf-8")
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"python3 -m eduflow.cli router --config {config}",
        f"python3 -m eduflow.cli router --config {other_config}",
    )
    commands["process-cwd:101"] = str(other)

    report = module.audit(deps)

    assert report["ok"] is False
    assert {e["code"] for e in report["errors"]} >= {"process_checkout_mismatch", "process_config_mismatch"}
    router = next(row for row in report["daemons"] if row["name"] == "router")
    assert router["checkout"] == str(other.resolve())
    assert router["config_path"] == str(other_config.resolve())
    assert any(row["kind"] == "multi_checkout" and row["pid"] == 101 for row in report["suspect_processes"])


def test_filters_other_tmux_sessions_but_reports_eduflow_legacy_and_duplicate_processes(tmp_path):
    module, deps, commands, config, checkout, _state = _fixture(tmp_path)
    commands["tmux list-panes -a"] += (
        f"\nOldEduFlow\tmanager\t0\t777\tpython3\t{checkout}\tpython3 -m eduflow.cli agent manager"
    )
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n777 1 python3 -m eduflow.cli agent manager --config {config}"
        f"\n888 1 python3 -m eduflow.cli router --config {config}"
    )

    report = module.audit(deps)

    assert len(report["panes"]) == 3
    assert any(row["kind"] == "legacy_tmux_session" for row in report["suspect_processes"])
    assert any(row["kind"] == "duplicate_daemon" and row["pid"] == 888 for row in report["suspect_processes"])
    assert {e["code"] for e in report["errors"]} >= {"legacy_tmux_session", "duplicate_daemon"}


@pytest.mark.parametrize(
    ("config_text", "code"),
    [
        ('[team]\nsession = "eduflow-team"\n', "lark_profile_missing"),
        ('lark_profile = "production-bot"\n', "tmux_session_missing"),
    ],
)
def test_profile_and_session_are_required_facts(tmp_path, config_text, code):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    config.write_text(config_text, encoding="utf-8")

    report = module.audit(deps)

    assert report["ok"] is False
    assert code in {e["code"] for e in report["errors"]}


def test_redaction_covers_every_emitted_command_shape(tmp_path):
    module, deps, commands, config, checkout, _state = _fixture(tmp_path)
    secrets = ["option-secret", "env-secret", "quoted-secret", "positional-secret"]
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"python3 -m eduflow.cli router --config {config}",
        f"TOKEN=env-secret python3 -m eduflow.cli router positional-secret "
        f"--token option-secret --label 'quoted-secret' --config {config}",
    )
    commands["tmux list-panes -a"] = commands["tmux list-panes -a"].replace(
        "python3 -m eduflow.cli agent manager",
        "python3 -m eduflow.cli agent manager positional-secret --token option-secret",
        1,
    )

    report = module.audit(deps)
    rendered = json.dumps(report, sort_keys=True)

    assert all(secret not in rendered for secret in secrets)
    assert report["redactions"]["count"] > 0


def test_legacy_detection_is_entry_based_not_checkout_path_substring(tmp_path):
    module, deps, commands, config, checkout, _state = _fixture(tmp_path)
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n777 1 python3 -m eduflow.cli legacy-router --config {config}"
        "\n999 1 python3 audit.py --checkout /tmp/EduFlow-Team-orch"
        "\n998 1 tmux -L EduFlowTeam -f /tmp/tmux.conf"
    )

    report = module.audit(deps)
    legacy_pids = {row["pid"] for row in report["suspect_processes"] if row["kind"] == "legacy_entry"}

    assert 777 in legacy_pids
    assert 999 not in legacy_pids
    assert 998 not in legacy_pids


@pytest.mark.parametrize(
    ("command", "actual_executable"),
    [
        ("/bin/zsh -lc claude --dangerously-skip-permissions", "/bin/zsh"),
        ("/usr/bin/python3 tool.py claude --token hidden", "/usr/bin/python3"),
    ],
)
def test_entry_rejects_wrapper_or_argument_token_false_positives(command, actual_executable):
    module = _load_module()

    entry, action, executable = module._entry(command, actual_executable)

    assert (entry, action, executable) == (None, None, None)


def test_process_version_uses_actual_absolute_executable_not_path_basename(tmp_path):
    module, deps, commands, config, _checkout, state = _fixture(tmp_path)
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config} python3 -m eduflow.cli agent manager",
        f"EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config} /tmp/fake/claude --model safe",
    )
    commands["process-exe:200"] = "/tmp/fake/claude"
    commands["/tmp/fake/claude --version"] = "Trusted CLI 9.0"
    commands["claude --version"] = "PATH impostor 0.1"

    report = module.audit(deps)
    manager = next(row for row in report["agent_processes"] if row["agent"] == "manager")

    assert manager["executable"] == "/tmp/fake/claude"
    assert manager["cli_runtime"] == "/tmp/fake/claude Trusted CLI 9.0"
    assert ["/tmp/fake/claude", "--version"] in commands["_calls"]
    assert ["claude", "--version"] not in commands["_calls"]


@pytest.mark.parametrize(
    ("row", "pid"),
    [
        ("777 1 /tmp/fake/python3 -m eduflow.cli agent rogue", 777),
        ("778 1 /tmp/fake/claude --model orphan", 778),
    ],
)
def test_global_scan_rejects_unassociated_agent_processes(tmp_path, row, pid):
    module, deps, commands, *_ = _fixture(tmp_path)
    commands["ps -axo pid=,ppid=,command="] += "\n" + row
    commands[f"process-exe:{pid}"] = row.split()[2]

    report = module.audit(deps)

    assert report["ok"] is False
    assert any(item["kind"] == "orphan_agent" and item["pid"] == pid
               for item in report["suspect_processes"])
    assert any(error["code"] == "orphan_agent" and error["subject"] == str(pid)
               for error in report["errors"])


def test_global_scan_does_not_block_unscoped_standalone_cli(tmp_path):
    module, deps, commands, *_ = _fixture(tmp_path)
    unrelated = tmp_path / "unrelated checkout"
    unrelated.mkdir()
    commands["ps -axo pid=,ppid=,command="] += "\n779 1 /tmp/fake/claude --model unrelated"
    commands["process-exe:779"] = "/tmp/fake/claude"
    commands["process-cwd:779"] = str(unrelated)

    report = module.audit(deps)

    assert report["ok"] is True
    assert not any(item["kind"] == "orphan_agent" and item["pid"] == 779
                   for item in report["suspect_processes"])


def test_configured_pane_ancestry_scopes_otherwise_external_cli_as_orphan(tmp_path):
    module, deps, commands, *_ = _fixture(tmp_path)
    unrelated = tmp_path / "unrelated checkout"
    unrelated.mkdir()
    commands["ps -axo pid=,ppid=,command="] += "\n789 200 /tmp/fake/claude --model detached-child"
    commands["process-exe:789"] = "/tmp/fake/claude"
    commands["process-cwd:789"] = str(unrelated)

    report = module.audit(deps)

    assert report["ok"] is False
    assert any(item["kind"] == "orphan_agent" and item["pid"] == 789
               for item in report["suspect_processes"])


def test_explicit_eduflow_agent_is_orphan_even_outside_target_checkout(tmp_path):
    module, deps, commands, *_ = _fixture(tmp_path)
    unrelated = tmp_path / "unrelated checkout"
    unrelated.mkdir()
    commands["ps -axo pid=,ppid=,command="] += (
        "\n790 1 /tmp/fake/python3 -m eduflow.cli agent rogue"
    )
    commands["process-exe:790"] = "/tmp/fake/python3"
    commands["process-cwd:790"] = str(unrelated)

    report = module.audit(deps)

    assert report["ok"] is False
    assert any(item["kind"] == "orphan_agent" and item["pid"] == 790
               for item in report["suspect_processes"])


def test_config_reads_only_canonical_toml_paths_not_same_named_decoys(tmp_path):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    config.write_text(
        '[decoy]\nlark_profile = "wrong-profile"\nsession = "wrong-session"\n'
        '[team]\nsession = "eduflow-team"\n',
        encoding="utf-8",
    )

    report = module.audit(deps)

    assert report["ok"] is False
    assert "lark_profile_missing" in {error["code"] for error in report["errors"]}
    assert "tmux_session_missing" not in {error["code"] for error in report["errors"]}


def test_json_flag_is_accepted_and_preserves_nonzero_cli_result(tmp_path, monkeypatch, capsys):
    module, deps, commands, *_ = _fixture(tmp_path)
    commands["tmux list-panes -a"] = ""
    monkeypatch.setattr(module, "_default_dependencies", lambda _args: deps)

    exit_code = module.main(["--json"])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False


@pytest.mark.parametrize("failure", ["missing", "permission", "timeout", "nonzero"])
def test_runtime_version_failures_are_unknown_and_never_render_exception_text(tmp_path, failure):
    module, deps, _commands, *_ = _fixture(tmp_path)
    original_run = deps.run

    def failing_run(argv, **kwargs):
        if argv == ["/tmp/fake/python3", "--version"]:
            if failure == "missing":
                raise FileNotFoundError("sensitive missing path")
            if failure == "permission":
                raise PermissionError("sensitive permission detail")
            if failure == "timeout":
                raise subprocess.TimeoutExpired(argv, 5, stderr="sensitive timeout detail")
            return subprocess.CompletedProcess(argv, 9, "", "sensitive nonzero detail")
        return original_run(argv, **kwargs)

    deps = module.AuditDependencies(**{**deps.__dict__, "run": failing_run})
    report = module.audit(deps)
    rendered = json.dumps(report, sort_keys=True)

    assert report["ok"] is False
    assert "cli_runtime_unknown" in {error["code"] for error in report["errors"]}
    assert all(row["cli_runtime"] is None for row in report["daemons"])
    assert "sensitive" not in rendered
    assert failure not in rendered


@pytest.mark.parametrize("version", ["line one\nline two", "V" * 300])
def test_runtime_version_must_be_single_line_and_bounded(tmp_path, version):
    module, deps, commands, *_ = _fixture(tmp_path)
    commands["/tmp/fake/python3 --version"] = version

    report = module.audit(deps)

    assert report["ok"] is False
    assert "cli_runtime_unknown" in {error["code"] for error in report["errors"]}
    assert all(row["cli_runtime"] is None for row in report["daemons"])


@pytest.mark.parametrize(
    "invalid_toml",
    [
        'lark_profile = "p"\nteam = "not-a-table"\n',
        'lark_profile = "p"\n[team]\nsession = "eduflow-team"\nagents = "not-a-table"\n',
        'lark_profile = "p"\n[team]\nsession = "eduflow-team"\n'
        '[runtime_registry]\nagent_primary = "not-a-table"\n'
        '[team.agents.manager]\nruntime = "agent_primary"\n',
        'lark_profile = "p"\n[team]\nsession = "eduflow-team"\n'
        '[team.agents]\nmanager = "not-a-table"\n',
    ],
)
def test_legal_toml_with_invalid_config_types_fails_closed_as_json(tmp_path, invalid_toml):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    config.write_text(invalid_toml, encoding="utf-8")

    report = module.audit(deps)

    assert report["ok"] is False
    assert "config_schema_invalid" in {error["code"] for error in report["errors"]}
    assert json.loads(json.dumps(report))["ok"] is False


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("lark_profile", "1"), ("lark_profile", "[]"), ("lark_profile", '""'),
        ("session", "1"), ("session", "[]"), ("session", '""'),
        ("registry_key", '""'),
        ("cli", "1"), ("cli", "[]"), ("cli", '""'),
        ("runtime", "1"), ("runtime", "[]"), ("runtime", '""'),
    ],
)
def test_config_string_properties_fail_closed_for_numbers_lists_and_empty_values(
    tmp_path, field, invalid_value
):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    values = {
        "lark_profile": '"production-bot"', "session": '"eduflow-team"',
        "registry_key": "agent_primary", "cli": '"python3"',
        "runtime": '"agent_primary"',
    }
    values[field] = invalid_value
    config.write_text(
        f'lark_profile = {values["lark_profile"]}\n'
        f'[runtime_registry.{values["registry_key"]}]\ncli = {values["cli"]}\n'
        f'[team]\nsession = {values["session"]}\n'
        f'[team.agents.manager]\nruntime = {values["runtime"]}\n',
        encoding="utf-8",
    )

    report = module.audit(deps)

    assert report["ok"] is False
    assert "config_schema_invalid" in {error["code"] for error in report["errors"]}
    assert json.loads(json.dumps(report))["ok"] is False


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("lark_profile", '{ secret = "nested-profile-secret" }'),
        ("lark_profile", '["list-profile-secret"]'),
        ("lark_profile", "1979-05-27T07:32:00Z"),
        ("session", '{ secret = "nested-session-secret" }'),
        ("session", '["list-session-secret"]'),
        ("session", "1979-05-27T07:32:00Z"),
    ],
)
def test_invalid_canonical_values_are_normalized_without_raw_or_secret_output(
    tmp_path, field, invalid_value
):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    values = {"lark_profile": '"production-bot"', "session": '"eduflow-team"'}
    values[field] = invalid_value
    config.write_text(
        f'lark_profile = {values["lark_profile"]}\n'
        '[runtime_registry.agent_primary]\ncli = "python3"\n'
        f'[team]\nsession = {values["session"]}\n'
        '[team.agents.manager]\nruntime = "agent_primary"\n',
        encoding="utf-8",
    )

    report = module.audit(deps)
    rendered = json.dumps(report, sort_keys=True)

    assert report["ok"] is False
    assert "config_schema_invalid" in {error["code"] for error in report["errors"]}
    assert "secret" not in rendered
    for row in [*report["daemons"], *report["panes"], *report["agent_processes"]]:
        assert row["lark_profile" if field == "lark_profile" else "tmux_session"] is None


def test_json_cli_serializes_invalid_canonical_values_without_secret(tmp_path, monkeypatch, capsys):
    module, deps, _commands, config, *_ = _fixture(tmp_path)
    config.write_text(
        'lark_profile = ["cli-secret"]\n'
        '[team]\nsession = 1979-05-27T07:32:00Z\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "_default_dependencies", lambda _args: deps)

    exit_code = module.main(["--json"])
    rendered = capsys.readouterr().out

    assert exit_code == 1
    assert json.loads(rendered)["ok"] is False
    assert "cli-secret" not in rendered


def test_entry_recognizes_capital_python_only_when_kernel_executable_matches():
    module = _load_module()
    executable = "/Frameworks/Python.app/Contents/MacOS/Python"
    command = f"{executable} -m eduflow.cli router"

    entry, action, actual = module._entry(command, executable)

    assert (entry, action, actual) == ("Python -m eduflow.cli router", "router", executable)
    assert module._entry("/bin/zsh -lc 'Python -m eduflow.cli router'", "/bin/zsh") == (None, None, None)


def test_capital_python_full_provenance_records_python_runtime(tmp_path):
    module, deps, commands, config, _checkout, _state = _fixture(tmp_path)
    executable = "/Frameworks/Python.app/Contents/MacOS/Python"
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"python3 -m eduflow.cli router --config {config}",
        f"{executable} -m eduflow.cli router --config {config}",
    )
    commands["process-exe:101"] = executable
    commands[f"{executable} --version"] = "Python 3.14.3"

    report = module.audit(deps)
    router = next(row for row in report["daemons"] if row["name"] == "router")

    assert router["startup_entry"] == "Python -m eduflow.cli router"
    assert router["python_runtime"] == "Python 3.14.3"


def test_hermes_python_wrapper_uses_adjacent_absolute_script_and_package_version(tmp_path):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    scripts = tmp_path / "hermes venv" / "bin"
    scripts.mkdir(parents=True)
    python = scripts / "python3"
    canonical_hermes = scripts / "hermes"
    python.touch()
    canonical_hermes.touch()
    canonical_hermes.chmod(0o755)
    alias_dir = tmp_path / "aliases"
    alias_dir.mkdir()
    hermes = alias_dir / "hermes"
    hermes.symlink_to(canonical_hermes)
    config.write_text(
        config.read_text(encoding="utf-8")
        + '[runtime_registry.hermes_primary]\ncli = "hermes-agent"\n'
        + '[team.agents.Hermes]\nruntime = "hermes_primary"\n',
        encoding="utf-8",
    )
    commands["tmux list-panes -a"] += (
        f"\neduflow-team\tHermes\t0\t300\tPython\t/tmp/hermes-duty\t{python} {hermes} chat --source eduflow-hermes"
    )
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n300 1 EDUFLOW_ROOT={checkout} EDUFLOW_CONFIG_FILE={config} EDUFLOW_STATE_DIR={state} "
        f"{python} {hermes} chat --source eduflow-hermes"
    )
    commands["process-exe:300"] = str(python)
    commands["process-cwd:300"] = "/tmp/hermes-duty"
    commands[f"{python} --version"] = "Python 3.11.15"
    proof_argv = [str(python), "-c", module.HERMES_PROBE_CODE]
    commands[" ".join(proof_argv)] = json.dumps({
        "scripts": str(scripts), "version": "0.16.0",
        "entrypoint": "hermes_agent.cli:app",
    }, separators=(",", ":"))

    report = module.audit(deps)
    row = next(item for item in report["agent_processes"] if item["agent"] == "Hermes")

    assert row["executable"] == str(python)
    assert row["startup_entry"] == "python3 hermes chat"
    assert row["python_runtime"] == "Python 3.11.15"
    assert row["cli_runtime"] == f"{hermes} 0.16.0"
    assert proof_argv in commands["_calls"]
    assert "pane_cwd_drift" not in {e["code"] for e in report["errors"] if e["subject"].endswith("Hermes.0")}


def test_hermes_wrapper_outside_distribution_scripts_is_rejected(tmp_path):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    python = "/tmp/hermes-venv/bin/python3"
    hermes = "/tmp/bin/hermes"
    commands["tmux list-panes -a"] += (
        f"\neduflow-team\tHermes\t0\t300\tPython\t{checkout}\t{python} {hermes} chat"
    )
    config.write_text(config.read_text() + '[runtime_registry.hermes_primary]\ncli="hermes-agent"\n'
                      '[team.agents.Hermes]\nruntime="hermes_primary"\n')
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n300 1 EDUFLOW_ROOT={checkout} EDUFLOW_CONFIG_FILE={config} EDUFLOW_STATE_DIR={state} "
        f"{python} {hermes} chat"
    )
    commands["process-exe:300"] = python
    commands[f"{python} --version"] = "Python 3.11.15"
    commands[f"{python} -c {module.HERMES_PROBE_CODE}"] = json.dumps({
        "scripts": "/tmp/hermes-venv/bin", "version": "0.16.0",
        "entrypoint": "hermes_agent.cli:app",
    }, separators=(",", ":"))

    report = module.audit(deps)

    assert report["ok"] is False
    assert "hermes_distribution_mismatch" in {e["code"] for e in report["errors"]}
    row = next(item for item in report["agent_processes"] if item["agent"] == "Hermes")
    assert row["cli_runtime"] is None


@pytest.mark.parametrize(
    "proof",
    [
        {"scripts": "", "version": "0.16.0", "entrypoint": "hermes_agent.cli:app"},
        {"scripts": "/tmp/hermes-venv/bin", "version": "0.16.0", "entrypoint": ""},
        {"scripts": "/tmp/hermes-venv/bin", "version": "one\ntwo", "entrypoint": "hermes_agent.cli:app"},
    ],
)
def test_incomplete_hermes_distribution_proof_fails_closed(tmp_path, proof):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    python = "/tmp/hermes-venv/bin/python3"
    hermes = "/tmp/hermes-venv/bin/hermes"
    config.write_text(config.read_text() + '[runtime_registry.hermes_primary]\ncli="hermes-agent"\n'
                      '[team.agents.Hermes]\nruntime="hermes_primary"\n')
    commands["tmux list-panes -a"] += f"\neduflow-team\tHermes\t0\t300\tPython\t{checkout}\t{python} {hermes} chat"
    commands["ps -axo pid=,ppid=,command="] += (
        f"\n300 1 EDUFLOW_ROOT={checkout} EDUFLOW_CONFIG_FILE={config} EDUFLOW_STATE_DIR={state} {python} {hermes} chat"
    )
    commands["process-exe:300"] = python
    commands[f"{python} --version"] = "Python 3.11.15"
    commands[f"{python} -c {module.HERMES_PROBE_CODE}"] = json.dumps(proof, separators=(",", ":"))

    report = module.audit(deps)

    assert report["ok"] is False
    assert "cli_runtime_unknown" in {e["code"] for e in report["errors"]}


def test_eduflow_root_allows_duty_cwd_but_is_recorded_as_checkout_source(tmp_path):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    duty_cwd = tmp_path / "duty cwd"
    duty_cwd.mkdir()
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"200 1 EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config}",
        f"200 1 EDUFLOW_ROOT={checkout} EDUFLOW_STATE_DIR={state} EDUFLOW_CONFIG_FILE={config}",
    )
    commands["process-cwd:200"] = str(duty_cwd)
    commands["tmux list-panes -a"] = commands["tmux list-panes -a"].replace(
        f"eduflow-team\tmanager\t0\t200\tpython3\t{checkout}",
        f"eduflow-team\tmanager\t0\t200\tpython3\t{duty_cwd}",
    )

    report = module.audit(deps)
    manager = next(row for row in report["panes"] if row["window"] == "manager")

    assert report["ok"] is True
    assert manager["process_cwd"] == str(duty_cwd.resolve())
    assert manager["checkout"] == str(checkout.resolve())
    assert manager["checkout_source"] == "EDUFLOW_ROOT"


@pytest.mark.parametrize("root_present", [True, False])
def test_unrelated_root_or_fallback_cwd_fails_closed(tmp_path, root_present):
    module, deps, commands, config, checkout, state = _fixture(tmp_path)
    unrelated = tmp_path / "unrelated root"
    unrelated.mkdir()
    prefix = f"EDUFLOW_ROOT={unrelated} " if root_present else ""
    commands["ps -axo pid=,ppid=,command="] = commands["ps -axo pid=,ppid=,command="].replace(
        f"101 1 EDUFLOW_STATE_DIR={state}",
        f"101 1 {prefix}EDUFLOW_STATE_DIR={state}",
    )
    if not root_present:
        commands["process-cwd:101"] = str(unrelated)

    report = module.audit(deps)
    router = next(row for row in report["daemons"] if row["name"] == "router")

    assert report["ok"] is False
    assert "process_checkout_mismatch" in {e["code"] for e in report["errors"]}
    assert router["checkout"] == str(unrelated.resolve())
    assert router["checkout_source"] == ("EDUFLOW_ROOT" if root_present else "process_cwd")
