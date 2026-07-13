"""End-to-end Slash authorization and audit contract for G0.1."""
from __future__ import annotations

import json

from eduflow.feishu import slash


def _card_text(card: dict) -> str:
    return "\n".join(
        element.get("content", "")
        for element in card["body"]["elements"]
        if element.get("tag") == "markdown"
    )


def _ctx(
    sender_id: str,
    *,
    operators=(),
    admins=(),
    background=None,
) -> slash.SlashContext:
    return slash.SlashContext(
        team_agents=["manager", "worker_cc"],
        session="EduFlow",
        sender_id=sender_id,
        authority_config={
            "operators": list(operators),
            "admins": list(admins),
        },
        sleep=lambda _seconds: None,
        background=background or (lambda _callback: None),
    )


def test_member_send_is_rejected_before_pane_mutation_and_audited(monkeypatch) -> None:
    injected: list[tuple[object, str]] = []
    events: list[dict] = []
    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda target, text: injected.append((target, text)) or True,
    )
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/send worker_cc hello", _ctx("u_member", operators=("u_operator",))
    )

    assert "operator_required" in _card_text(reply)
    assert injected == []
    assert events == [
        {
            "actor": "u_member",
            "command": "/send",
            "target": "worker_cc",
            "result": "denied",
            "reason": "operator_required",
            "required_role": "operator",
        }
    ]


def test_member_team_is_rejected_before_any_pane_capture(monkeypatch) -> None:
    captures: list[object] = []
    events: list[dict] = []
    monkeypatch.setattr(
        slash.tmux,
        "capture_pane",
        lambda target, **_kwargs: captures.append(target) or "secret tail",
    )
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/team", _ctx("u_member", operators=("u_operator",))
    )

    assert "operator_required" in _card_text(reply)
    assert captures == []
    assert events[0]["result"] == "denied"


def test_operator_send_succeeds_with_structured_audit(monkeypatch) -> None:
    injected: list[tuple[object, str]] = []
    events: list[dict] = []
    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda target, text: injected.append((target, text)) or True,
    )
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/send worker_cc hello", _ctx("u_operator", operators=("u_operator",))
    )

    assert isinstance(reply, str) and reply.startswith("✅")
    assert len(injected) == 1
    assert events[0] == {
        "actor": "u_operator",
        "command": "/send",
        "target": "worker_cc",
        "result": "prepared",
        "reason": "authorized",
        "required_role": "operator",
    }
    assert events[1] == {
        "actor": "u_operator",
        "command": "/send",
        "target": "worker_cc",
        "result": "succeeded",
        "reason": "handler_completed",
        "required_role": "operator",
    }


def test_operator_clear_is_rejected_but_admin_clear_succeeds(monkeypatch) -> None:
    injected: list[str] = []
    events: list[dict] = []
    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda _target, text: injected.append(text) or True,
    )
    monkeypatch.setattr(slash.identity, "init_prompt", lambda _agent: "init")
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    denied = slash.dispatch(
        "/clear worker_cc",
        _ctx("u_operator", operators=("u_operator",), admins=("u_admin",)),
    )
    allowed = slash.dispatch(
        "/clear worker_cc",
        _ctx("u_admin", operators=("u_operator",), admins=("u_admin",)),
    )

    assert "admin_required" in _card_text(denied)
    assert injected == ["/clear", "init"]
    assert isinstance(allowed, str) and allowed.startswith("✅")
    assert [event["result"] for event in events] == [
        "denied",
        "prepared",
        "succeeded",
    ]


def test_member_stop_and_clear_are_both_rejected_and_audited(monkeypatch) -> None:
    events: list[dict] = []
    side_effects: list[str] = []
    monkeypatch.setattr(
        slash.tmux,
        "send_keys",
        lambda *_args, **_kwargs: side_effects.append("stop") or True,
    )
    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda _target, text: side_effects.append(text) or True,
    )
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    for command in ("/stop worker_cc", "/clear worker_cc"):
        reply = slash.dispatch(command, _ctx("u_member", admins=("u_admin",)))
        assert "admin_required" in _card_text(reply)

    assert side_effects == []
    assert [event["command"] for event in events] == ["/stop", "/clear"]
    assert all(event["result"] == "denied" for event in events)


def test_default_audit_is_append_only_structured_json(monkeypatch) -> None:
    rows: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        slash.local_facts,
        "append_log",
        lambda agent, kind, content, **_kwargs: rows.append((agent, kind, content))
        or "log_1",
    )

    slash._audit_authorization(
        {
            "actor": "u_admin",
            "command": "/stop",
            "target": "worker_cc",
            "result": "succeeded",
            "reason": "handler_completed",
            "required_role": "admin",
        }
    )

    assert rows[0][:2] == ("control_plane", "slash_authorization")
    assert json.loads(rows[0][2]) == {
        "actor": "u_admin",
        "command": "/stop",
        "reason": "handler_completed",
        "required_role": "admin",
        "result": "succeeded",
        "target": "worker_cc",
    }


def test_audit_storage_failure_blocks_write_before_side_effect(monkeypatch) -> None:
    injected: list[str] = []
    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda _target, text: injected.append(text) or True,
    )
    monkeypatch.setattr(
        slash,
        "_audit_authorization",
        lambda _event: (_ for _ in ()).throw(OSError("disk full")),
    )

    reply = slash.dispatch(
        "/send worker_cc hello", _ctx("u_operator", operators=("u_operator",))
    )

    assert "audit_unavailable" in _card_text(reply)
    assert injected == []


def test_handler_reported_failure_is_not_audited_as_success(monkeypatch) -> None:
    events: list[dict] = []
    monkeypatch.setattr(slash.tmux, "send_keys", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/stop worker_cc", _ctx("u_admin", admins=("u_admin",))
    )

    assert isinstance(reply, str) and reply.startswith("❌")
    assert [event["result"] for event in events] == ["prepared", "failed"]
    assert events[-1]["reason"] == "handler_reported_failure"


def test_completion_audit_failure_leaves_durable_prepared_event(monkeypatch) -> None:
    events: list[dict] = []
    injected: list[str] = []

    def audit(event: dict) -> None:
        if events:
            raise OSError("disk full")
        events.append(event)

    monkeypatch.setattr(
        slash.tmux,
        "inject",
        lambda _target, text: injected.append(text) or True,
    )
    monkeypatch.setattr(slash, "_audit_authorization", audit)

    reply = slash.dispatch(
        "/send worker_cc hello", _ctx("u_operator", operators=("u_operator",))
    )

    assert injected == ["hello"]
    assert [event["result"] for event in events] == ["prepared"]
    assert "audit_completion_failed" in _card_text(reply)


def test_handler_exception_plus_terminal_audit_failure_is_contained(monkeypatch) -> None:
    events: list[dict] = []

    def audit(event: dict) -> None:
        if events:
            raise OSError("disk full")
        events.append(event)

    monkeypatch.setattr(
        slash.tmux,
        "send_keys",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(slash, "_audit_authorization", audit)

    reply = slash.dispatch(
        "/stop worker_cc", _ctx("u_admin", admins=("u_admin",))
    )

    assert [event["result"] for event in events] == ["prepared"]
    assert "audit_completion_failed" in _card_text(reply)


def test_dispatch_transition_failure_is_reported_and_audited(monkeypatch) -> None:
    events: list[dict] = []
    monkeypatch.setattr(slash.tasks, "create_flow", lambda *_args, **_kwargs: "T-9")
    monkeypatch.setattr(slash.tasks, "transition_flow", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/dispatch worker_cc build title", _ctx("u_admin", admins=("u_admin",))
    )

    assert isinstance(reply, str) and reply.startswith("⚠️")
    assert [event["result"] for event in events] == ["prepared", "failed"]
    assert "T-9" in reply


def test_compact_audit_stays_scheduled_until_background_terminal_event(
    monkeypatch,
) -> None:
    events: list[dict] = []
    callbacks: list[object] = []
    injections = iter((True, False))
    monkeypatch.setattr(
        slash.tmux, "inject", lambda *_args, **_kwargs: next(injections)
    )
    monkeypatch.setattr(slash.tmux, "capture_pane", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(slash.identity, "init_prompt", lambda _agent: "init")
    monkeypatch.setattr(slash, "_audit_authorization", events.append)

    reply = slash.dispatch(
        "/compact worker_cc",
        _ctx(
            "u_admin",
            admins=("u_admin",),
            background=callbacks.append,
        ),
    )

    assert isinstance(reply, str) and reply.startswith("✅")
    assert [event["result"] for event in events] == ["prepared", "scheduled"]
    assert len(callbacks) == 1

    callbacks[0]()

    assert [event["result"] for event in events] == [
        "prepared",
        "scheduled",
        "failed",
    ]
    assert events[-1]["reason"] == "background_reidentify_failed"
