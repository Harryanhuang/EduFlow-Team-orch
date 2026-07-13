"""End-to-end G0.2 retry and acknowledgement contracts."""
from __future__ import annotations

import json
import threading

from helpers import attr_patch, env_patch, isolated_env
from eduflow.feishu import deliver as deliver_module
from eduflow.feishu.deliver import apply
from eduflow.feishu.router import Action, Decision
from eduflow.feishu.subscribe import (
    process_lines,
    process_pending_acknowledgements,
    process_pending_decisions,
)
from eduflow.runtime import human_takeover
from eduflow.store import message_delivery


_TEAM = ["manager"]


class _FakeAdapter:
    def submit_keys(self):
        return ["Enter"]

    def spawn_cmd(self, agent, model):
        return f"fake {agent} {model}"

    def ready_markers(self):
        return ["fake-ready"]

    def rate_limit_markers(self):
        return []


def _event(message_id: str, text: str) -> str:
    return json.dumps({
        "event": {
            "message": {
                "message_id": message_id,
                "chat_id": "oc_team",
                "message_type": "text",
                "content": json.dumps({"text": text}),
                "create_time": "1777777777000",
            },
            "sender": {"sender_id": {"open_id": "ou_operator"}},
        }
    })


def test_retryable_inbox_failure_does_not_advance_seen_or_cursor():
    seen: set[str] = set()
    progressed = []

    def apply_with_denied_inbox(decision):
        return apply(
            decision,
            append_message=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                PermissionError("inbox denied")),
            tmux_inject=lambda *_args, **_kwargs: True,
            session="S",
        )

    with isolated_env():
        stats = process_lines(
            [_event("om_inbox_denied", "please help")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=apply_with_denied_inbox,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )

    assert stats.handled == 0
    assert "om_inbox_denied" not in seen
    assert progressed == []


def test_slash_reply_retry_does_not_reexecute_the_command():
    seen: set[str] = set()
    progressed = []
    calls = {"dispatch": 0, "send": 0}

    def dispatch_once(_text, _ctx):
        calls["dispatch"] += 1
        return "command completed"

    def fail_once_then_send(*_args, **_kwargs):
        calls["send"] += 1
        return None if calls["send"] == 1 else {"message_id": "om_reply"}

    def apply_slash(decision):
        return apply(
            decision,
            slash_dispatch=dispatch_once,
            chat_send=fail_once_then_send,
            chat_id="oc_team",
            session="S",
        )

    with isolated_env():
        first = process_lines(
            [_event("om_slash_retry", "/send worker_a manager do work")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=apply_slash,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )
        due = message_delivery.claim_due_retry_decisions(now=10 ** 18)
        second = process_pending_decisions(
            due,
            apply_fn=apply_slash,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )

    assert first.handled == 0
    assert second.handled == 1
    assert [decision.msg_id for decision in due] == ["om_slash_retry"]
    assert calls == {"dispatch": 1, "send": 2}
    assert seen == {"om_slash_retry"}
    assert progressed == ["om_slash_retry"]


def test_retry_limit_dead_letters_with_query_replay_and_audit():
    seen: set[str] = set()
    progressed = []

    def always_fails(decision):
        return apply(
            decision,
            append_message=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                TimeoutError("facts lock timed out")),
            tmux_inject=lambda *_args, **_kwargs: True,
            session="S",
        )

    with isolated_env(), env_patch(EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS="2"):
        first = process_lines(
            [_event("om_dead_letter", "please help")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=always_fails,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )
        due = message_delivery.claim_due_retry_decisions(now=10 ** 18)
        second = process_pending_decisions(
            due,
            apply_fn=always_fails,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=seen,
        )
        dead_letters = message_delivery.list_dead_letters()
        takeover_state = human_takeover.status()
        human_takeover.recover(
            actor="u_admin",
            reason="inbox storage restored",
            recovery_steps=["verified inbox storage is writable"],
            expected_generation=takeover_state["generation"],
        )
        replay = message_delivery.replay_dead_letter(
            "om_dead_letter", actor="u_admin", reason="inbox storage restored")
        recovered = process_pending_decisions(
            [replay] if replay is not None else [],
            apply_fn=lambda decision: apply(
                decision,
                adapter_for_agent=lambda _agent: _FakeAdapter(),
                tmux_inject=lambda *_args, **_kwargs: True,
                session="S",
            ),
            seen_msg_ids=seen,
        )
        remaining_dead_letters = message_delivery.list_dead_letters()
        audit = message_delivery.audit_events("om_dead_letter")

    assert first.handled == 0
    assert second.handled == 1
    assert [decision.msg_id for decision in due] == ["om_dead_letter"]
    assert seen == {"om_dead_letter"}
    assert progressed == ["om_dead_letter"]
    assert len(dead_letters) == 1
    assert dead_letters[0]["attempts"] == 2
    assert dead_letters[0]["failure_reason"] == "inbox_write_failed"
    assert takeover_state["state"] == "active"
    assert replay is not None
    assert replay.action is Action.ROUTE
    assert replay.msg_id == "om_dead_letter"
    assert recovered.handled == 1
    assert remaining_dead_letters == []
    assert any(row["event"] == "dead_letter" for row in audit)
    assert any(row["event"] == "dead_letter_replayed" for row in audit)
    assert any(row["event"] == "acknowledged" for row in audit)


def test_first_failed_event_is_recovered_from_the_durable_ledger_on_restart():
    first_seen: set[str] = set()
    restart_seen: set[str] = set()
    progressed = []

    def denied_inbox(decision):
        return apply(
            decision,
            append_message=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                PermissionError("inbox denied")),
            tmux_inject=lambda *_args, **_kwargs: True,
            session="S",
        )

    def recovered_apply(decision):
        return apply(
            decision,
            adapter_for_agent=lambda _agent: _FakeAdapter(),
            tmux_inject=lambda *_args, **_kwargs: True,
            session="S",
        )

    with isolated_env():
        first = process_lines(
            [_event("om_first_failure", "please help")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=denied_inbox,
            seen_msg_ids=first_seen,
        )
        pending = message_delivery.pending_decisions()
        recovered = process_pending_decisions(
            pending,
            apply_fn=recovered_apply,
            on_progress=lambda decision, _stats: progressed.append(decision.msg_id),
            seen_msg_ids=restart_seen,
        )

    assert first.handled == 0
    assert first_seen == set()
    assert [decision.msg_id for decision in pending] == ["om_first_failure"]
    assert recovered.handled == 1
    assert restart_seen == {"om_first_failure"}
    assert progressed == ["om_first_failure"]


def test_ack_audit_failure_never_replays_an_already_published_slash_reply():
    seen: set[str] = set()
    calls = {"dispatch": 0, "send": 0, "ack": 0}

    def dispatch(_text, _ctx):
        calls["dispatch"] += 1
        return "command completed"

    def send(*_args, **_kwargs):
        calls["send"] += 1
        return {"message_id": "om_reply"}

    def apply_slash(decision):
        return apply(
            decision,
            slash_dispatch=dispatch,
            chat_send=send,
            chat_id="oc_team",
            session="S",
        )

    with isolated_env():
        real_ack = message_delivery.record_acknowledged

        def fail_first_ack(*args, **kwargs):
            calls["ack"] += 1
            if calls["ack"] == 1:
                raise OSError("delivery ledger temporarily unavailable")
            return real_ack(*args, **kwargs)

        with attr_patch(message_delivery, record_acknowledged=fail_first_ack):
            first = process_lines(
                [_event("om_ack_audit", "/send worker_a manager do work")],
                team_agents=_TEAM,
                chat_id="oc_team",
                apply_fn=apply_slash,
                seen_msg_ids=seen,
            )
            pending_delivery = message_delivery.pending_decisions()
            pending_ack = message_delivery.pending_acknowledgements()
            recovered = process_pending_acknowledgements(
                pending_ack,
                seen_msg_ids=seen,
            )

    assert first.handled == 1
    assert calls == {"dispatch": 1, "send": 1, "ack": 2}
    assert pending_delivery == []
    assert [decision.msg_id for decision in pending_ack] == ["om_ack_audit"]
    assert recovered.handled == 1


def test_progress_crash_after_slash_publication_recovers_only_the_ack():
    seen: set[str] = set()
    calls = {"dispatch": 0, "send": 0}

    def dispatch(_text, _ctx):
        calls["dispatch"] += 1
        return "command completed"

    def send(*_args, **_kwargs):
        calls["send"] += 1
        return {"message_id": "om_reply"}

    def apply_slash(decision):
        return apply(
            decision,
            slash_dispatch=dispatch,
            chat_send=send,
            chat_id="oc_team",
            session="S",
        )

    with isolated_env():
        first = process_lines(
            [_event("om_published_before_ack", "/send worker_a manager do work")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=apply_slash,
            on_progress=lambda *_args: (_ for _ in ()).throw(OSError("cursor disk full")),
            seen_msg_ids=seen,
        )
        pending_delivery = message_delivery.pending_decisions()
        pending_ack = message_delivery.pending_acknowledgements()
        recovered = process_pending_acknowledgements(
            pending_ack,
            seen_msg_ids=seen,
        )

    assert first.handled == 0
    assert first.drops_by_reason["ack_progress_failed"] == 1
    assert pending_delivery == []
    assert [item.msg_id for item in pending_ack] == ["om_published_before_ack"]
    assert recovered.handled == 1
    assert calls == {"dispatch": 1, "send": 1}


def test_uncertain_slash_execution_requires_human_resolution_not_replay():
    decision = Decision(
        action=Action.SLASH,
        text="/send worker_a manager do work",
        msg_id="om_uncertain_slash",
        create_time="1777777777000",
    )
    with isolated_env(), env_patch(EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS="1"):
        message_delivery.prepare(decision)
        assert message_delivery.begin_slash_execution(decision) == "execute"
        message_delivery.record_retryable_failure(
            decision, "slash_reply_journal_failed")
        replay = message_delivery.replay_dead_letter(
            "om_uncertain_slash", actor="u_admin", reason="retry after incident")
        resolved = message_delivery.resolve_uncertain_slash(
            "om_uncertain_slash", actor="u_admin", reason="human verified command outcome")
        audit = message_delivery.audit_events("om_uncertain_slash")

    assert replay is None
    assert resolved is True
    assert any(row["event"] == "dead_letter_replay_refused" for row in audit)
    resolution = [row for row in audit if row["event"] == "uncertain_slash_resolved"]
    assert resolution and resolution[-1]["actor"] == "u_admin"


def test_ambiguous_slash_timeout_never_reposts_the_reply():
    seen: set[str] = set()
    calls = {"dispatch": 0, "send": 0}

    def dispatch(_text, _ctx):
        calls["dispatch"] += 1
        return "command completed"

    def ambiguous_timeout(*_args, **_kwargs):
        calls["send"] += 1
        return None

    def apply_slash(decision):
        return apply(
            decision,
            slash_dispatch=dispatch,
            chat_id="oc_team",
            session="S",
        )

    with isolated_env(), env_patch(EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS="2"), \
            attr_patch(
                deliver_module._chat, send_text=ambiguous_timeout
            ), attr_patch(
                deliver_module._lark, last_failure_kind=lambda: "ambiguous"
            ):
        first = process_lines(
            [_event("om_ambiguous_timeout", "/send worker_a manager do work")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=apply_slash,
            seen_msg_ids=seen,
        )
        due = message_delivery.claim_due_retry_decisions(now=10 ** 18)
        second = process_pending_decisions(
            due,
            apply_fn=apply_slash,
            seen_msg_ids=seen,
        )
        dead_letters = message_delivery.list_dead_letters()

    assert first.handled == 0
    assert second.handled == 1
    assert calls == {"dispatch": 1, "send": 1}
    assert len(dead_letters) == 1
    assert dead_letters[0]["failure_reason"] == "slash_publication_recovery_required"


def test_delivery_lease_allows_only_one_concurrent_apply():
    decision = Decision(
        action=Action.ROUTE,
        targets=["manager"],
        text="do once",
        msg_id="om_concurrent_lease",
        create_time="1777777777000",
    )
    entered = threading.Event()
    release = threading.Event()
    calls = []
    primary_stats = []

    def slow_apply(item):
        calls.append(item.msg_id)
        entered.set()
        assert release.wait(timeout=2)
        return deliver_module.DeliveryReport(durable_success=True)

    with isolated_env():
        worker = threading.Thread(
            target=lambda: primary_stats.append(process_pending_decisions(
                [decision], apply_fn=slow_apply
            )),
        )
        worker.start()
        assert entered.wait(timeout=2)
        competing = process_pending_decisions(
            [decision],
            apply_fn=lambda item: calls.append(f"duplicate:{item.msg_id}") or deliver_module.DeliveryReport(
                durable_success=True
            ),
        )
        release.set()
        worker.join(timeout=2)

    assert not worker.is_alive()
    assert calls == ["om_concurrent_lease"]
    assert competing.handled == 0
    assert competing.drops_by_reason["delivery_inflight"] == 1
    assert primary_stats[0].handled == 1


def test_router_restart_reclaims_an_abandoned_delivery_lease():
    decision = Decision(
        action=Action.ROUTE,
        targets=["manager"],
        text="recover after crash",
        msg_id="om_abandoned_lease",
        create_time="1777777777000",
    )
    applied = []

    with isolated_env():
        message_delivery.prepare(decision)
        assert message_delivery.claim_delivery(decision)
        recovered = process_pending_decisions(
            [decision],
            apply_fn=lambda item: applied.append(item.msg_id) or deliver_module.DeliveryReport(
                durable_success=True
            ),
            restart_recovery=True,
        )

    assert applied == ["om_abandoned_lease"]
    assert recovered.handled == 1


def test_human_takeover_journals_but_blocks_automated_delivery():
    seen: set[str] = set()
    applied = []

    with isolated_env():
        human_takeover.enter(
            reason="operator investigating delivery incident",
            source="test",
            actor="u_admin",
        )
        stats = process_lines(
            [_event("om_takeover_blocked", "please help")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=lambda item: applied.append(item) or deliver_module.DeliveryReport(
                durable_success=True
            ),
            seen_msg_ids=seen,
        )
        pending = message_delivery.pending_decisions()

    assert applied == []
    assert stats.handled == 0
    assert stats.drops_by_reason["human_takeover"] == 1
    assert seen == set()
    assert [item.msg_id for item in pending] == ["om_takeover_blocked"]


def test_takeover_entered_after_lease_claim_blocks_apply_before_side_effect():
    seen: set[str] = set()
    applied = []
    event = _event("om_takeover_race", "please help")

    with isolated_env():
        real_claim = message_delivery.claim_delivery

        def claim_then_take_over(decision, **kwargs):
            token = real_claim(decision, **kwargs)
            human_takeover.enter(
                reason="operator intervened during claim",
                source="test",
                actor="u_admin",
            )
            return token

        with attr_patch(message_delivery, claim_delivery=claim_then_take_over):
            stats = process_lines(
                [event],
                team_agents=_TEAM,
                chat_id="oc_team",
                apply_fn=lambda item: applied.append(item) or deliver_module.DeliveryReport(
                    durable_success=True
                ),
                seen_msg_ids=seen,
            )
        pending = message_delivery.pending_decisions()

    assert applied == []
    assert stats.handled == 0
    assert stats.drops_by_reason["human_takeover"] == 1
    assert seen == set()
    assert [item.msg_id for item in pending] == ["om_takeover_race"]


def test_takeover_persistence_failure_enters_emergency_automation_hold():
    seen: set[str] = set()
    applied = []

    def exhausted_failure(_decision):
        return deliver_module.DeliveryReport(
            retryable_failure=True,
            failure_reason="inbox_write_failed",
        )

    with isolated_env(), env_patch(EDUFLOW_MESSAGE_DELIVERY_MAX_ATTEMPTS="1"):
        with attr_patch(
            human_takeover,
            enter=lambda **_kwargs: (_ for _ in ()).throw(OSError("takeover disk full")),
        ):
            exhausted = process_lines(
                [_event("om_takeover_write_failure", "please help")],
                team_agents=_TEAM,
                chat_id="oc_team",
                apply_fn=exhausted_failure,
                seen_msg_ids=seen,
            )
        blocked = process_lines(
            [_event("om_hold_blocks_next", "please help")],
            team_agents=_TEAM,
            chat_id="oc_team",
            apply_fn=lambda item: applied.append(item) or deliver_module.DeliveryReport(
                durable_success=True
            ),
            seen_msg_ids=seen,
        )
        held = message_delivery.automation_hold_active()
        cleared = message_delivery.clear_automation_hold(
            actor="u_admin", reason="takeover storage repaired",
        )

    assert exhausted.handled == 0
    assert exhausted.drops_by_reason["automation_hold"] == 1
    assert blocked.handled == 0
    assert blocked.drops_by_reason["automation_hold"] == 1
    assert applied == []
    assert held is True
    assert cleared is True
