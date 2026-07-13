"""Contract tests for durable inbound-message acknowledgement.

G0.2 deliberately distinguishes a durable inbox record from best-effort
pane injection.  The router may advance its cursor only for a durable
delivery (or a terminal drop), never because ``apply`` merely returned.
"""
from __future__ import annotations

import json

from helpers import isolated_env
from eduflow.feishu.deliver import apply
from eduflow.feishu.router import Action, Decision
from eduflow.feishu.subscribe import process_lines
from eduflow.store import local_facts


class _FakeAdapter:
    def submit_keys(self):
        return ["Enter"]

    def spawn_cmd(self, agent, model):
        return f"fake-cli {agent} {model}"

    def ready_markers(self):
        return ["fake-ready"]

    def rate_limit_markers(self):
        return []


def _adapter_factory(_agent):
    return _FakeAdapter()


def _route(*, targets=None, msg_id="om_delivery") -> Decision:
    return Decision(
        action=Action.ROUTE,
        targets=targets or ["worker_a"],
        sender="manager",
        text="durable delivery",
        msg_id=msg_id,
        create_time="1777777777000",
    )


def test_inbox_permission_error_is_retryable_not_durable():
    def denied(*_args, **_kwargs):
        raise PermissionError("inbox is read-only")

    report = apply(
        _route(),
        adapter_for_agent=_adapter_factory,
        append_message=denied,
        tmux_inject=lambda *_args, **_kwargs: True,
        session="S",
    )

    assert report.durable_success is False
    assert report.retryable_failure is True
    assert report.terminal_failure is False
    assert report.failure_reason == "inbox_write_failed"


def test_inbox_lock_timeout_is_retryable_not_durable():
    def timed_out(*_args, **_kwargs):
        raise TimeoutError("facts lock timed out")

    report = apply(
        _route(),
        adapter_for_agent=_adapter_factory,
        append_message=timed_out,
        tmux_inject=lambda *_args, **_kwargs: True,
        session="S",
    )

    assert report.durable_success is False
    assert report.retryable_failure is True
    assert report.failure_reason == "inbox_write_failed"


def test_partial_multi_target_persist_is_not_a_durable_ack():
    writes = []

    def append_once_then_fail(agent, *_args, **_kwargs):
        writes.append(agent)
        if agent == "worker_b":
            raise OSError("disk full")
        return "msg_worker_a"

    report = apply(
        _route(targets=["worker_a", "worker_b"]),
        adapter_for_agent=_adapter_factory,
        append_message=append_once_then_fail,
        tmux_inject=lambda *_args, **_kwargs: True,
        session="S",
    )

    assert writes == ["worker_a", "worker_b"]
    assert report.written == ["worker_a"]
    assert report.durable_success is False
    assert report.retryable_failure is True


def test_pane_inject_failure_after_persist_is_still_durable():
    with isolated_env():
        report = apply(
            _route(),
            adapter_for_agent=_adapter_factory,
            tmux_inject=lambda *_args, **_kwargs: False,
            session="S",
        )

    assert report.written == ["worker_a"]
    assert report.failed_inject == ["worker_a"]
    assert report.durable_success is True
    assert report.retryable_failure is False


def test_replaying_after_persist_before_ack_keeps_one_canonical_inbox_row():
    decision = _route(msg_id="om_persist_then_crash")
    with isolated_env():
        for _ in range(2):
            report = apply(
                decision,
                adapter_for_agent=_adapter_factory,
                tmux_inject=lambda *_args, **_kwargs: True,
                session="S",
            )
            assert report.durable_success is True
        rows = local_facts.list_messages("worker_a")

    assert len(rows) == 1
    assert rows[0]["source_message_id"] == "om_persist_then_crash"


def test_terminal_drop_advances_seen_and_progress_cursor():
    event = json.dumps({
        "event": {
            "message": {
                "message_id": "om_terminal_drop",
                "chat_id": "oc_team",
                "message_type": "text",
                "content": json.dumps({"text": "ignored bot message"}),
                "create_time": "1777777777000",
            },
            "sender": {"sender_id": {"open_id": "ou_bot"}},
        }
    })
    seen: set[str] = set()
    progressed = []

    stats = process_lines(
        [event],
        team_agents=["manager"],
        chat_id="oc_team",
        bot_id="ou_bot",
        apply_fn=lambda _decision: None,
        on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
        seen_msg_ids=seen,
    )

    assert stats.dropped == 1
    assert seen == {"om_terminal_drop"}
    assert progressed == ["om_terminal_drop"]


def test_missing_delivery_report_cannot_ack_a_message():
    event = json.dumps({
        "event": {
            "message": {
                "message_id": "om_unproven_callback",
                "chat_id": "oc_team",
                "message_type": "text",
                "content": json.dumps({"text": "please help"}),
                "create_time": "1777777777000",
            },
            "sender": {"sender_id": {"open_id": "ou_user"}},
        }
    })
    seen: set[str] = set()
    progressed = []

    with isolated_env():
        stats = process_lines(
            [event],
            team_agents=["manager"],
            chat_id="oc_team",
            apply_fn=lambda _decision: None,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )

    assert stats.handled == 0
    assert "om_unproven_callback" not in seen
    assert progressed == []
    assert stats.drops_by_reason["delivery_retryable"] == 1
