"""Administrative controls for G0.2 dead-letter recovery."""
from __future__ import annotations

from helpers import attr_patch, env_patch, isolated_env, run_cli
from eduflow.commands import message_delivery as command
from eduflow.feishu.router import Action, Decision
from eduflow.store import message_delivery


def _dead_letter() -> None:
    decision = Decision(
        action=Action.ROUTE,
        targets=["manager"],
        text="recoverable message",
        msg_id="om_cli_dead_letter",
        create_time="1777777777000",
    )
    message_delivery.prepare(decision)
    message_delivery.record_retryable_failure(decision, "inbox_write_failed")


def _admin_config():
    return {"team": {"operators": [], "admins": ["u_admin"]}}


def test_dead_letter_list_and_replay_require_a_configured_admin():
    with isolated_env(), env_patch(EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS="1"):
        _dead_letter()
        with attr_patch(command.tunables, load=_admin_config):
            denied_rc, _, denied_err = run_cli([
                "message-delivery", "list", "--actor", "u_runtime",
            ])
            rc, out, err = run_cli([
                "message-delivery", "replay", "om_cli_dead_letter",
                "--actor", "u_admin", "--reason", "inbox storage restored", "--json",
            ])
        audit = message_delivery.audit_events("om_cli_dead_letter")
        pending = message_delivery.pending_decisions()

    assert denied_rc == 1
    assert "configured admin" in denied_err
    assert rc == 0, err
    assert "queued_for_retry" in out
    assert [decision.msg_id for decision in pending] == ["om_cli_dead_letter"]
    replay = [row for row in audit if row["event"] == "dead_letter_replayed"]
    assert replay and replay[-1]["actor"] == "u_admin"
