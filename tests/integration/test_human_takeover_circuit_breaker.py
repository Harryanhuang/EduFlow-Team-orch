"""Controlled isolated-state simulation of the takeover circuit breaker."""
import pytest

from eduflow.runtime import human_takeover


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("EDUFLOW_STATE_DIR", str(tmp_path))


def test_failure_budget_blocks_next_automatic_side_effect_then_recovery_reenables_it():
    side_effects = []

    def automatic_switch():
        generation = human_takeover.ensure_automation_allowed()
        human_takeover.ensure_automation_allowed(expected_generation=generation)
        side_effects.append("restart")

    automatic_switch()
    assert side_effects == ["restart"]

    active = human_takeover.enter(
        reason="runtime_switch_recovery_budget_exhausted",
        source="watchdog", actor="system",
    )
    with pytest.raises(human_takeover.AutomationBlocked):
        automatic_switch()
    assert side_effects == ["restart"], "takeover must block before restart side effect"

    human_takeover.recover(actor="u_admin", reason="provider verified",
                           recovery_steps=["credential rotated", "live smoke passed"],
                           expected_generation=active["generation"])
    automatic_switch()
    assert side_effects == ["restart", "restart"]


def test_generation_cas_blocks_action_planned_before_takeover():
    planned_generation = human_takeover.ensure_automation_allowed()
    human_takeover.enter(reason="operator intervention", source="manual_cli", actor="u_admin")
    with pytest.raises(human_takeover.AutomationBlocked):
        human_takeover.ensure_automation_allowed(expected_generation=planned_generation)
