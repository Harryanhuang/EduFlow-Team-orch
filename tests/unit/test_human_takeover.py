import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from eduflow import cli
from eduflow.commands import runtime_switch
from eduflow.runtime import human_takeover


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path))


def test_missing_state_is_inactive_and_status_does_not_write():
    state = human_takeover.status()
    assert state["state"] == "inactive"
    assert state["generation"] == 0
    assert not human_takeover._state_path().exists()
    assert not human_takeover._audit_path().exists()


def test_corrupt_state_fails_closed_without_leaking_raw_content():
    path = human_takeover._state_path()
    path.parent.mkdir(parents=True)
    path.write_text('{"token":"super-secret"', encoding="utf-8")
    state = human_takeover.status()
    assert state["state"] == "active"
    assert state["reason"] == "corrupt_state"
    assert "super-secret" not in json.dumps(state)
    with pytest.raises(human_takeover.AutomationBlocked):
        human_takeover.ensure_automation_allowed()


@pytest.mark.parametrize("payload", [
    {"state": "inactive", "reason": "", "source": "", "actor": "",
     "entered_at": None, "recovery_steps": [], "generation": True},
    {"state": "inactive", "reason": "", "source": "", "actor": "",
     "entered_at": None, "recovery_steps": [], "generation": 0, "extra": "tampered"},
    {"state": "active", "reason": 123, "source": "watchdog", "actor": "system",
     "entered_at": 1.0, "recovery_steps": ["inspect"], "generation": 1},
    {"state": "active", "reason": "incident", "source": "watchdog", "actor": "system",
     "entered_at": 1.0, "recovery_steps": [], "generation": 1},
    {"state": "active", "reason": "token=raw-secret", "source": "watchdog", "actor": "system",
     "entered_at": 1.0, "recovery_steps": ["inspect"], "generation": 1},
])
def test_well_formed_but_invalid_or_tampered_state_fails_closed(payload):
    path = human_takeover._state_path()
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    state = human_takeover.status()
    assert state["state"] == "active"
    assert state["reason"] == "corrupt_state"
    assert "raw-secret" not in json.dumps(state)
    with pytest.raises(human_takeover.AutomationBlocked):
        human_takeover.ensure_automation_allowed()


def test_enter_is_idempotent_and_audited_without_secrets():
    first = human_takeover.enter(reason="provider failure API_KEY=super-secret", source="watchdog", actor="operator")
    second = human_takeover.enter(reason="ignored", source="watchdog", actor="operator")
    assert first == second
    assert first["generation"] == 1
    audit = human_takeover.audit_events()
    assert len(audit) == 1
    assert "super-secret" not in json.dumps(audit)
    assert first["recovery_steps"]
    assert all(isinstance(step, str) and step.strip() for step in first["recovery_steps"])


def test_audit_failure_prevents_takeover_state_change(monkeypatch):
    monkeypatch.setattr(human_takeover, "_audit", lambda event: (_ for _ in ()).throw(OSError("disk full")))
    with pytest.raises(OSError, match="disk full"):
        human_takeover.enter(reason="incident", source="watchdog", actor="system")
    assert human_takeover.status()["state"] == "inactive"
    assert not human_takeover._state_path().exists()


def test_state_failure_leaves_write_ahead_transition_trace(monkeypatch):
    monkeypatch.setattr(human_takeover, "_write", lambda state: (_ for _ in ()).throw(OSError("rename failed")))
    with pytest.raises(OSError, match="rename failed"):
        human_takeover.enter(reason="incident", source="watchdog", actor="system")
    assert human_takeover.status()["state"] == "inactive"
    audit = human_takeover.audit_events()
    assert len(audit) == 1
    assert audit[0]["event"] == "enter"
    assert audit[0]["phase"] == "prepared"


def test_recovery_can_resume_from_recovering_after_second_state_write_failure(monkeypatch):
    active = human_takeover.enter(reason="incident", source="watchdog", actor="system")
    original_write = human_takeover._write
    writes = 0

    def fail_second_write(state):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("inactive rename failed")
        original_write(state)

    monkeypatch.setattr(human_takeover, "_write", fail_second_write)
    with pytest.raises(OSError, match="inactive rename failed"):
        human_takeover.recover(actor="u_admin", reason="verified", recovery_steps=["smoke passed"],
                               expected_generation=active["generation"])
    recovering = human_takeover.status()
    assert recovering["state"] == "recovering"
    monkeypatch.setattr(human_takeover, "_write", original_write)
    recovered = human_takeover.recover(actor="u_admin", reason="resume", recovery_steps=[],
                                       expected_generation=recovering["generation"])
    assert recovered["state"] == "inactive"


def test_audit_retries_short_os_writes(monkeypatch):
    real_write = os.write
    calls = []

    def short_write(fd, payload):
        chunk = bytes(payload[:max(1, len(payload) // 3)])
        calls.append(len(chunk))
        return real_write(fd, chunk)

    monkeypatch.setattr(human_takeover.os, "write", short_write)
    human_takeover.enter(reason="incident", source="watchdog", actor="system")
    assert len(calls) > 1
    assert human_takeover.audit_events()[0]["event"] == "enter"


def test_recover_uses_generation_cas_and_records_steps():
    active = human_takeover.enter(reason="budget", source="watchdog", actor="system")
    recovered = human_takeover.recover(
        actor="u_admin", reason="verified", recovery_steps=["credential rotated", "smoke passed"],
        expected_generation=active["generation"],
    )
    assert recovered["state"] == "inactive"
    assert recovered["generation"] == 2
    with pytest.raises(human_takeover.StaleGeneration):
        human_takeover.recover(actor="u_admin", reason="stale", recovery_steps=[], expected_generation=1)


def test_concurrent_enters_have_one_generation_and_one_audit_event():
    def do_enter(i):
        return human_takeover.enter(reason=f"failure-{i}", source="watchdog", actor="system")
    with ThreadPoolExecutor(max_workers=8) as pool:
        states = list(pool.map(do_enter, range(16)))
    assert {s["generation"] for s in states} == {1}
    assert len(human_takeover.audit_events()) == 1


def test_cli_requires_configured_operator_for_mutations(monkeypatch, capsys):
    monkeypatch.setattr("eduflow.commands.human_takeover._authorized_actors", lambda: {"u_admin"})
    rc = cli.main(["human-takeover", "enter", "--actor", "stranger", "--reason", "incident", "--json"])
    assert rc == 1
    assert "unauthorized" in capsys.readouterr().err
    assert human_takeover.status()["state"] == "inactive"


def test_cli_status_enter_recover_json(monkeypatch, capsys):
    monkeypatch.setattr("eduflow.commands.human_takeover._authorized_actors", lambda: {"u_admin"})
    assert cli.main(["human-takeover", "status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "inactive"
    assert cli.main(["human-takeover", "enter", "--actor", "u_admin", "--reason", "incident", "--json"]) == 0
    active = json.loads(capsys.readouterr().out)
    assert active["state"] == "active"
    assert cli.main(["human-takeover", "recover", "--actor", "u_admin", "--reason", "fixed",
                     "--generation", str(active["generation"]), "--step", "smoke passed", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "inactive"


def test_runtime_switch_takeover_override_requires_configured_identity(monkeypatch):
    active = {"state": "active"}
    monkeypatch.setattr(runtime_switch, "_authorized_actors", lambda: {"u_admin"})
    with pytest.raises(PermissionError):
        runtime_switch._manual_trigger(active, None)
    with pytest.raises(PermissionError):
        runtime_switch._manual_trigger(active, "stranger")
    assert runtime_switch._manual_trigger(active, "u_admin") == "manual_cli_takeover_override:u_admin"
    # Compatibility: ordinary manual switches do not suddenly require actor.
    assert runtime_switch._manual_trigger({"state": "inactive"}, None) == "manual_cli"


def test_runtime_switch_override_excludes_general_operators(monkeypatch):
    monkeypatch.setattr(runtime_switch.tunables, "load", lambda: {"team": {
        "operators": ["u_general"], "admins": ["u_admin"],
        "runtime_operators": ["u_runtime"], "runtime_operator": "u_single",
    }})
    assert runtime_switch._authorized_actors() == {"u_admin", "u_runtime", "u_single"}
    with pytest.raises(PermissionError):
        runtime_switch._manual_trigger({"state": "active"}, "u_general")


def _install_runtime_switch_mocks(monkeypatch, *, restart):
    monkeypatch.setattr(runtime_switch.config, "load_team", lambda: {
        "session": "S", "agents": {"manager": {}}})
    monkeypatch.setattr(runtime_switch.config, "runtime_config", lambda runtime: {})
    monkeypatch.setattr(runtime_switch.tmux, "has_session", lambda session: True)
    monkeypatch.setattr(runtime_switch.tmux, "has_window", lambda target: True)
    monkeypatch.setattr(runtime_switch.lifecycle, "current_runtime_status",
                        lambda agent: {"runtime": "old"})
    monkeypatch.setattr(runtime_switch.lifecycle, "restart_with_runtime", restart)
    monkeypatch.setattr("eduflow.commands.runtime_verify.compute_verdict",
                        lambda agent: {"verdict": "ready"})


def test_manual_switch_serializes_against_takeover_entry(monkeypatch):
    restart_started = threading.Event()
    allow_restart = threading.Event()
    entered = threading.Event()

    def restart(*args, **kwargs):
        restart_started.set()
        assert allow_restart.wait(2)
        return "ready"

    _install_runtime_switch_mocks(monkeypatch, restart=restart)
    monkeypatch.setattr(runtime_switch.verify, "record_switch_event", lambda **event: None)
    switch_thread = threading.Thread(target=lambda: runtime_switch.main([
        "manager", "backup", "--reason", "manual-test"]))
    switch_thread.start()
    assert restart_started.wait(1)

    def enter_takeover():
        human_takeover.enter(reason="operator intervention", source="test", actor="system")
        entered.set()

    enter_thread = threading.Thread(target=enter_takeover)
    enter_thread.start()
    time.sleep(0.1)
    assert not entered.is_set(), "takeover entry must wait rather than race the authorized restart"
    allow_restart.set()
    switch_thread.join(2)
    enter_thread.join(2)
    assert entered.is_set()
    assert human_takeover.status()["state"] == "active", "delayed takeover entry must not be lost"


def test_manual_switch_events_are_append_only_under_interleaving(monkeypatch):
    events = []

    def record(**event):
        events.append(dict(event))

    def restart(*args, **kwargs):
        record(agent="other", from_runtime="x", to_runtime="y", reason="concurrent",
               outcome="ready", trigger="watchdog", switch_id="external")
        return "ready"

    _install_runtime_switch_mocks(monkeypatch, restart=restart)
    monkeypatch.setattr(runtime_switch.verify, "record_switch_event", record)
    assert runtime_switch.main(["manager", "backup", "--reason", "manual-test"]) == 0
    assert [event["outcome"] for event in events] == ["pending", "ready", "ready"]
    manual = [event for event in events if event["agent"] == "manager"]
    assert len(manual) == 2
    assert [event["phase"] for event in manual] == ["prepared", "completed"]
    assert manual[0]["switch_id"] == manual[1]["switch_id"]
    assert manual[0]["switch_id"] != "external"
