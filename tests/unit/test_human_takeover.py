import json
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
